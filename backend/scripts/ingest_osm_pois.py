"""
Ingest POIs for a city from OSM into MongoDB and Qdrant
Run with: python scripts/ingest_osm_pois.py mumbai
"""
import sys
import os
from pathlib import Path
import asyncio
import argparse
import time

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from app.services.osm_service import osm_service
from app.services.embedding_service import embedding_service
from app.services.qdrant_service import qdrant_service
from app.core.mongo import connect_to_mongo, close_mongo_connection
from typing import List
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def ingest_city_pois(city: str, categories: List[str] = None):
    """
    Ingest POIs for a city from OSM into MongoDB and Qdrant
    
    Args:
        city: City name (mumbai, goa, delhi)
        categories: Optional list of categories to ingest
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Starting POI ingestion for {city.upper()}")
    logger.info(f"{'='*60}\n")
    
    # Connect to MongoDB
    await connect_to_mongo()
    
    try:
        # Step 1: Fetch POIs from Overpass API (synchronous API call)
        logger.info("Step 1: Fetching POIs from OpenStreetMap...")
        pois = osm_service.fetch_overpass_pois(city, categories=categories)
        
        if not pois:
            logger.warning(f"No POIs found for {city}")
            return
        
        logger.info(f"✅ Fetched {len(pois)} POIs\n")
        
        # Step 2: Store POIs in MongoDB (async)
        logger.info("Step 2: Storing POIs in MongoDB...")
        stored_count = await osm_service.store_pois(pois)
        logger.info(f"✅ Stored {stored_count} POIs in MongoDB\n")
        
        # Step 3: Generate embeddings and store in Qdrant
        logger.info("Step 3: Generating embeddings and storing in Qdrant...")
        
        # Prepare texts for embedding
        texts = [poi.description for poi in pois if poi.description]
        
        if not texts:
            logger.warning("No descriptions to embed")
            return
        
        # ✅ REDUCED BATCH SIZES for better reliability
        embedding_batch_size = 50  # Reduced from 100
        qdrant_batch_size = 20     # Small batches for Qdrant Cloud
        
        total_embedded = 0
        all_points = []  # Collect all points first
        
        # Generate embeddings in batches
        for i in range(0, len(texts), embedding_batch_size):
            batch_texts = texts[i:i+embedding_batch_size]
            batch_pois = pois[i:i+embedding_batch_size]
            
            logger.info(f"  Embedding batch {i//embedding_batch_size + 1}/{(len(texts)-1)//embedding_batch_size + 1}...")
            
            try:
                # Generate embeddings (synchronous Gemini API call)
                embeddings = embedding_service.generate_embeddings(
                    batch_texts,
                    task_type="RETRIEVAL_DOCUMENT"
                )
                
                # Prepare points
                for poi, embedding in zip(batch_pois, embeddings):
                    all_points.append({
                        "id": str(poi.osm_id),
                        "vector": embedding,
                        "payload": {
                            "poi_id": str(poi.id),
                            "name": poi.name,
                            "city": poi.city,
                            "category": poi.category,
                            "tags": poi.tags,
                            "source": "osm",
                            "description": poi.description
                        }
                    })
                
                total_embedded += len(embeddings)
                
            except Exception as e:
                logger.error(f"❌ Failed to embed batch: {e}")
                continue
        
        logger.info(f"✅ Generated {total_embedded} embeddings\n")
        
        # Step 4: Upload to Qdrant in small batches with retry
        logger.info("Step 4: Uploading vectors to Qdrant...")
        
        uploaded_count = 0
        for i in range(0, len(all_points), qdrant_batch_size):
            batch = all_points[i:i+qdrant_batch_size]
            batch_num = i//qdrant_batch_size + 1
            total_batches = (len(all_points)-1)//qdrant_batch_size + 1
            
            logger.info(f"  Uploading Qdrant batch {batch_num}/{total_batches} ({len(batch)} points)...")
            
            # Retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    qdrant_service.upsert_points(
                        collection_name="local_discovery",
                        points=batch
                    )
                    uploaded_count += len(batch)
                    break  # Success, exit retry loop
                    
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 2  # 2, 4, 6 seconds
                        logger.warning(f"⚠️ Upload failed (attempt {attempt+1}/{max_retries}), retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"❌ Failed to upload batch after {max_retries} attempts: {e}")
            
            # Small delay between batches to avoid overwhelming Qdrant Cloud
            time.sleep(0.5)
        
        logger.info(f"✅ Uploaded {uploaded_count} vectors to Qdrant\n")
        
        # Step 5: Print summary
        logger.info(f"{'='*60}")
        logger.info(f"INGESTION COMPLETE for {city.upper()}")
        logger.info(f"{'='*60}")
        logger.info(f"Total POIs processed: {len(pois)}")
        logger.info(f"Stored in MongoDB: {stored_count}")
        logger.info(f"Embeddings generated: {total_embedded}")
        logger.info(f"Vectors uploaded to Qdrant: {uploaded_count}")
        logger.info(f"{'='*60}\n")
    
    except Exception as e:
        logger.error(f"❌ Error during ingestion: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    finally:
        # Close MongoDB connection
        await close_mongo_connection()


async def main():
    """Main entry point for script"""
    parser = argparse.ArgumentParser(description="Ingest OSM POIs for a city")
    parser.add_argument(
        "city",
        type=str,
        choices=["mumbai", "goa", "delhi", "all"],
        help="City to ingest (or 'all' for all cities)"
    )
    parser.add_argument(
        "--categories",
        type=str,
        nargs="+",
        help="Optional: Specific categories to ingest (restaurant, cafe, etc.)"
    )
    
    args = parser.parse_args()
    
    if args.city == "all":
        cities = ["mumbai", "goa", "delhi"]
    else:
        cities = [args.city]
    
    for city in cities:
        try:
            await ingest_city_pois(city, categories=args.categories)
        except Exception as e:
            logger.error(f"❌ Error ingesting {city}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
