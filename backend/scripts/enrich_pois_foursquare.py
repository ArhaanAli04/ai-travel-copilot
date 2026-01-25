"""
Enrich OSM POIs with Foursquare tips and reviews
Run with: python scripts/enrich_pois_foursquare.py mumbai
"""
import sys
import os
from pathlib import Path
import asyncio
import argparse
import time

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.foursquare_service import foursquare_service
from app.services.embedding_service import embedding_service
from app.services.qdrant_service import qdrant_service
from app.core.mongo import connect_to_mongo, close_mongo_connection, get_database
from app.models.poi import POI
from bson import ObjectId
from typing import List,Optional
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def enrich_city_pois(
    city: str,
    limit: Optional[int] = None,
    categories: Optional[List[str]] = None
):
    """
    Enrich POIs for a city with Foursquare data
    
    Args:
        city: City name
        limit: Optional limit on number of POIs to process (for testing)
        categories: Optional list of categories to filter
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Starting Foursquare enrichment for {city.upper()}")
    logger.info(f"{'='*60}\n")
    
    # Connect to MongoDB
    await connect_to_mongo()
    
    try:
        # Step 1: Fetch OSM POIs from MongoDB
        logger.info("Step 1: Fetching OSM POIs from MongoDB...")
        
        db = get_database()
        pois_collection = db["pois"]
        
        # Build query
        query = {"city": city.lower()}
        if categories:
            query["category"] = {"$in": categories}
        
        # Get POIs
        cursor = pois_collection.find(query)
        if limit:
            cursor = cursor.limit(limit)
        
        pois_docs = await cursor.to_list(length=limit or 10000)
        pois = [POI(**doc) for doc in pois_docs]
        
        logger.info(f"✅ Found {len(pois)} POIs to enrich\n")
        
        if not pois:
            logger.warning("No POIs found")
            return
        
        # Step 2: Enrich POIs with Foursquare data
        logger.info("Step 2: Matching POIs with Foursquare...")
        
        enriched_count = 0
        skipped_count = 0
        failed_count = 0
        
        for i, poi in enumerate(pois, 1):
            logger.info(f"[{i}/{len(pois)}] Processing: {poi.name}")
            
            try:
                tip_obj = await foursquare_service.enrich_poi_with_tips(
                    poi_id=str(poi.id),
                    latitude=poi.location.coordinates[1],
                    longitude=poi.location.coordinates[0]
                )
                
                if tip_obj:
                    enriched_count += 1
                else:
                    failed_count += 1
                
                time.sleep(2) 
                # Rate limiting: Process in batches of 50 with 1s delay
                if i % 50 == 0:
                    logger.info(f"  Processed {i} POIs, sleeping 1s...")
                    time.sleep(1)
            
            except Exception as e:
                logger.error(f"❌ Error enriching {poi.name}: {e}")
                failed_count += 1
                time.sleep(2)
                continue
        
        logger.info(f"\n✅ Enrichment complete:")
        logger.info(f"  - Enriched: {enriched_count}")
        logger.info(f"  - Failed/No match: {failed_count}")
        
        # Step 3: Update Qdrant with enriched descriptions
        logger.info("\nStep 3: Updating Qdrant with enriched descriptions...")
        
        tips_collection = db["foursquare_tips"]
        enriched_tips = await tips_collection.find({"city": city.lower()}).to_list(length=10000)
        
        updated_count = 0
        all_points = []
        
        for tip_doc in enriched_tips:
            # Get corresponding POI
            poi_doc = await pois_collection.find_one({"_id": ObjectId(tip_doc["poi_id"])})
            if not poi_doc:
                continue
            
            poi = POI(**poi_doc)
            
            # Combine POI + tips
            from app.models.poi import FoursquareTip
            tip_obj = FoursquareTip(**tip_doc)
            enriched_text = foursquare_service.combine_poi_with_tips(poi, tip_obj)
            
            # Generate new embedding
            embedding = embedding_service.generate_single_embedding(
                enriched_text,
                task_type="RETRIEVAL_DOCUMENT"
            )
            
            # Prepare point for Qdrant (update existing)
            all_points.append({
                "id": str(poi.osm_id),  # Same ID as original OSM point
                "vector": embedding,
                "payload": {
                    "poi_id": str(poi.id),
                    "name": poi.name,
                    "city": poi.city,
                    "category": poi.category,
                    "tags": poi.tags,
                    "source": "osm_foursquare",  # Updated source
                    "description": enriched_text,
                    "has_foursquare_data": True,
                    "tip_count": len(tip_obj.tips),
                    "fsq_place_id": tip_obj.fsq_place_id,
                    "fsq_rating": tip_obj.rating
                }
            })
        
        # Upload to Qdrant in batches
        qdrant_batch_size = 20
        
        for i in range(0, len(all_points), qdrant_batch_size):
            batch = all_points[i:i+qdrant_batch_size]
            batch_num = i//qdrant_batch_size + 1
            total_batches = (len(all_points)-1)//qdrant_batch_size + 1
            
            logger.info(f"  Uploading batch {batch_num}/{total_batches} ({len(batch)} points)...")
            
            # Retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    qdrant_service.upsert_points(
                        collection_name="local_discovery",
                        points=batch
                    )
                    updated_count += len(batch)
                    break
                
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 2
                        logger.warning(f"⚠️ Upload failed, retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"❌ Failed to upload batch: {e}")
            
            time.sleep(0.5)
        
        logger.info(f"✅ Updated {updated_count} POIs in Qdrant\n")
        
        # Step 4: Print summary
        logger.info(f"{'='*60}")
        logger.info(f"FOURSQUARE ENRICHMENT COMPLETE for {city.upper()}")
        logger.info(f"{'='*60}")
        logger.info(f"POIs processed: {len(pois)}")
        logger.info(f"Successfully enriched: {enriched_count}")
        logger.info(f"Failed/No match: {failed_count}")
        logger.info(f"Qdrant points updated: {updated_count}")
        logger.info(f"{'='*60}\n")
    
    except Exception as e:
        logger.error(f"❌ Error during enrichment: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    finally:
        await close_mongo_connection()


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Enrich POIs with Foursquare data")
    parser.add_argument(
        "city",
        type=str,
        choices=["mumbai", "goa", "delhi", "bangalore", "pune"],
        help="City to enrich"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of POIs to process (for testing)"
    )
    parser.add_argument(
        "--categories",
        type=str,
        nargs="+",
        help="Filter by categories (restaurant, cafe, etc.)"
    )
    
    args = parser.parse_args()
    
    # Import here to avoid circular dependency
    from bson import ObjectId
    
    await enrich_city_pois(
        city=args.city,
        limit=args.limit,
        categories=args.categories
    )


if __name__ == "__main__":
    asyncio.run(main())
