"""
Resume embedding generation for POIs that don't have embeddings yet
"""
import asyncio
import sys
from pathlib import Path
import time

sys.path.append(str(Path(__file__).parent.parent))

from app.core.mongo import connect_to_mongo, get_database
from app.services.embedding_service import embedding_service
from app.services.qdrant_service import qdrant_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def resume_embeddings(city: str, batch_size: int = 10, delay: int = 60):
    """
    Generate embeddings for POIs that don't have them yet
    
    Args:
        city: City name
        batch_size: Number of POIs to embed per batch (small to avoid rate limits)
        delay: Delay in seconds between batches (60s = 1 minute)
    """
    await connect_to_mongo()
    db = get_database()
    
    logger.info(f"{'='*70}")
    logger.info(f"Resuming embeddings for {city.upper()}")
    logger.info(f"{'='*70}")
    
    try:
        # Get all POIs for this city
        pois_cursor = db.pois.find({"city": city.lower()})
        all_pois = await pois_cursor.to_list(length=None)
        
        logger.info(f"\nTotal POIs in {city}: {len(all_pois)}")
        
        # Check which ones already have embeddings in Qdrant
        existing_ids = set()
        try:
            # Get existing points from Qdrant
            scroll_result = qdrant_service.client.scroll(
                collection_name="local_discovery",
                scroll_filter={
                    "must": [
                        {"key": "city", "match": {"value": city.lower()}},
                        {"key": "source", "match": {"value": "osm"}}
                    ]
                },
                limit=10000,
                with_payload=True
            )
            
            for point in scroll_result[0]:
                poi_id = point.payload.get("poi_id")
                if poi_id:
                    existing_ids.add(poi_id)
            
            logger.info(f"POIs with embeddings: {len(existing_ids)}")
        except Exception as e:
            logger.warning(f"Could not check existing embeddings: {e}")
        
        # Filter POIs without embeddings
        pois_to_embed = [
            poi for poi in all_pois 
            if str(poi["_id"]) not in existing_ids
        ]
        
        logger.info(f"POIs needing embeddings: {len(pois_to_embed)}")
        
        if not pois_to_embed:
            logger.info("✅ All POIs already have embeddings!")
            return
        
        # Process in small batches with delays
        total_embedded = 0
        total_uploaded = 0
        
        for i in range(0, len(pois_to_embed), batch_size):
            batch = pois_to_embed[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(pois_to_embed) - 1) // batch_size + 1
            
            logger.info(f"\n{'='*70}")
            logger.info(f"Batch {batch_num}/{total_batches} ({len(batch)} POIs)")
            logger.info(f"{'='*70}")
            
            # Prepare texts
            texts = [poi.get("description", "") for poi in batch]
            
            # Generate embeddings with retry
            max_retries = 3
            embeddings = None
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"  Generating embeddings (attempt {attempt + 1})...")
                    embeddings = embedding_service.generate_embeddings(
                        texts,
                        task_type="RETRIEVAL_DOCUMENT"
                    )
                    logger.info(f"  ✅ Generated {len(embeddings)} embeddings")
                    break
                    
                except Exception as e:
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        if attempt < max_retries - 1:
                            wait_time = 65  # Wait 65 seconds for quota to reset
                            logger.warning(f"  ⚠️ Rate limit hit, waiting {wait_time}s...")
                            time.sleep(wait_time)
                        else:
                            logger.error(f"  ❌ Failed after {max_retries} attempts")
                            break
                    else:
                        logger.error(f"  ❌ Error: {e}")
                        break
            
            if not embeddings:
                logger.warning("  Skipping this batch due to errors")
                continue
            
            # Prepare points for Qdrant
            points = []
            for poi, embedding in zip(batch, embeddings):
                points.append({
                    "id": str(poi["osm_id"]),
                    "vector": embedding,
                    "payload": {
                        "poi_id": str(poi["_id"]),
                        "name": poi["name"],
                        "city": poi["city"],
                        "category": poi["category"],
                        "tags": poi.get("tags", {}),
                        "source": "osm",
                        "description": poi.get("description", "")
                    }
                })
            
            # Upload to Qdrant
            try:
                logger.info(f"  Uploading {len(points)} vectors to Qdrant...")
                qdrant_service.upsert_points(
                    collection_name="local_discovery",
                    points=points
                )
                logger.info(f"  ✅ Uploaded {len(points)} vectors")
                total_uploaded += len(points)
            except Exception as e:
                logger.error(f"  ❌ Upload failed: {e}")
            
            total_embedded += len(embeddings)
            
            # Progress update
            logger.info(f"\nProgress: {total_embedded}/{len(pois_to_embed)} POIs embedded")
            
            # Delay between batches (except for last batch)
            if i + batch_size < len(pois_to_embed):
                logger.info(f"Waiting {delay}s before next batch (rate limit protection)...")
                time.sleep(delay)
        
        logger.info(f"\n{'='*70}")
        logger.info(f"EMBEDDING RESUME COMPLETE")
        logger.info(f"{'='*70}")
        logger.info(f"Total POIs embedded: {total_embedded}")
        logger.info(f"Total vectors uploaded: {total_uploaded}")
        logger.info(f"{'='*70}")
    
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Resume embedding generation")
    parser.add_argument("city", type=str, help="City name")
    parser.add_argument("--batch-size", type=int, default=10, help="POIs per batch (default: 10)")
    parser.add_argument("--delay", type=int, default=60, help="Delay between batches in seconds (default: 60)")
    
    args = parser.parse_args()
    
    asyncio.run(resume_embeddings(args.city, args.batch_size, args.delay))
