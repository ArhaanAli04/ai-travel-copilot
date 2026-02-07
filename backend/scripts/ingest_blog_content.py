"""
Ingest blog posts from RSS feeds into MongoDB and Qdrant
Run with: python scripts/ingest_blog_content.py mumbai
"""
import sys
import os
from pathlib import Path
import asyncio
import argparse
import time
import re
from datetime import datetime, timedelta,timezone
# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.rss_service import rss_service
from app.services.embedding_service import embedding_service
from app.services.qdrant_service import qdrant_service
from app.core.mongo import connect_to_mongo, close_mongo_connection, get_database
from app.models.poi import BlogPost
from typing import List
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def chunk_text(text: str, max_tokens: int = 500) -> List[str]:
    """
    Chunk long text into smaller pieces
    
    Args:
        text: Text to chunk
        max_tokens: Maximum tokens per chunk (rough estimate: 1 token ≈ 4 chars)
    
    Returns:
        List of text chunks
    """
    # Rough estimate: 500 tokens ≈ 2000 characters
    max_chars = max_tokens * 4
    
    # If text is short enough, return as is
    if len(text) <= max_chars:
        return [text]
    
    # Split by paragraphs first
    paragraphs = text.split('\n\n')
    
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        # If adding this paragraph would exceed limit
        if len(current_chunk) + len(para) > max_chars:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = para
            else:
                # Paragraph itself is too long, split by sentences
                sentences = re.split(r'[.!?]+', para)
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) > max_chars:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence
                    else:
                        current_chunk += sentence + ". "
        else:
            current_chunk += para + "\n\n"
    
    # Add remaining chunk
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks


async def ingest_city_blogs(
    city: str,
    days_back: int = 7,
    include_general: bool = True
):
    """
    Ingest blog posts for a city into MongoDB and Qdrant
    
    Args:
        city: City name
        days_back: How many days back to fetch
        include_general: Include general India feeds
    """
    # NEW: Check storage before ingestion
    logger.info("Checking storage capacity...")
    
    # Estimate: assume ~1500 POIs per city
    estimated_vectors = 1500
    impact = qdrant_service.estimate_ingestion_impact(estimated_vectors, vector_dimension=768)
    
    if not impact['is_safe']:
        logger.error(f"❌ {impact['warning']}")
        logger.error(f"   Projected usage: {impact['projected_usage_percentage']:.2f}%")
        response = input("Continue anyway? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("Ingestion cancelled")
            return
    else:
        logger.info(f"✅ Storage check passed ({impact['projected_usage_percentage']:.2f}% projected)")

    logger.info(f"\n{'='*60}")
    logger.info(f"Starting Blog RSS ingestion for {city.upper()}")
    logger.info(f"{'='*60}\n")
    
    # Connect to MongoDB
    await connect_to_mongo()
    
    try:
        # Step 1: Check last ingestion time
        logger.info("Step 1: Checking last ingestion time...")
        last_ingested = await rss_service.get_last_ingested_date("blog", city)
        
        if last_ingested:
            days_since = (datetime.now(timezone.utc) - last_ingested).total_seconds() / 86400
            logger.info(f"  Last ingested: {last_ingested.strftime('%Y-%m-%d %H:%M:%S')} ({days_since:.1f} days ago)")
            
            # Adjust days_back for incremental update
            if days_since < days_back:
                days_back = max(int(days_since) + 1, 1)
                logger.info(f"  Adjusting to {days_back} days for incremental update")
        else:
            logger.info("  First time ingesting blogs for this city")
        
        # Step 2: Fetch blog posts from RSS feeds
        logger.info(f"\nStep 2: Fetching blog posts (last {days_back} days)...")
        posts = rss_service.fetch_blog_feeds(
            city=city,
            days_back=days_back,
            include_general=include_general
        )
        
        if not posts:
            logger.warning(f"No blog posts found for {city}")
            await rss_service.update_ingestion_metadata("blog", city, 0, "success")
            return
        
        logger.info(f"✅ Fetched {len(posts)} blog posts\n")
        
        # Step 3: Store posts in MongoDB
        logger.info("Step 3: Storing posts in MongoDB...")
        stored_count = await rss_service.store_blog_posts(posts)
        logger.info(f"✅ Stored {stored_count} posts in MongoDB\n")
        
        # Step 4: Chunk long posts and generate embeddings
        logger.info("Step 4: Chunking posts and generating embeddings...")
        
        all_chunks = []
        chunk_metadata = []
        
        for post in posts:
            # Combine title and content
            full_text = f"{post.title}\n\n{post.content}"
            
            # Chunk if needed
            chunks = chunk_text(full_text, max_tokens=500)
            
            logger.info(f"  {post.title[:50]}... -> {len(chunks)} chunk(s)")
            
            for chunk_idx, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                chunk_metadata.append({
                    "post": post,
                    "chunk_idx": chunk_idx,
                    "total_chunks": len(chunks)
                })
        
        logger.info(f"✅ Total chunks to embed: {len(all_chunks)}\n")
        
        # Generate embeddings in batches
        logger.info("Step 5: Generating embeddings...")
        batch_size = 50
        all_embeddings = []
        
        for i in range(0, len(all_chunks), batch_size):
            batch = all_chunks[i:i+batch_size]
            batch_num = i//batch_size + 1
            total_batches = (len(all_chunks)-1)//batch_size + 1
            
            logger.info(f"  Embedding batch {batch_num}/{total_batches}...")
            
            embeddings = embedding_service.generate_embeddings(
                batch,
                task_type="RETRIEVAL_DOCUMENT"
            )
            all_embeddings.extend(embeddings)
        
        logger.info(f"✅ Generated {len(all_embeddings)} embeddings\n")
        
        # Step 6: Prepare points for Qdrant
        logger.info("Step 6: Preparing Qdrant points...")
        qdrant_points = []
        
        for i, (embedding, metadata) in enumerate(zip(all_embeddings, chunk_metadata)):
            post = metadata["post"]
            chunk_idx = metadata["chunk_idx"]
            
            # Create unique ID for chunk
            point_id = f"blog_{post.url.split('/')[-1]}_{chunk_idx}"
            
            qdrant_points.append({
                "id": point_id,
                "vector": embedding,
                "payload": {
                    "blog_post_id": str(post.id),
                    "title": post.title,
                    "blog_name": post.blog_name,
                    "city": post.city,
                    "source": "blog",
                    "url": post.url,
                    "published_at": post.published_at.isoformat(),
                    "tags": post.tags,
                    "chunk_idx": chunk_idx,
                    "total_chunks": metadata["total_chunks"],
                    "content_preview": all_chunks[i][:200]
                }
            })
        
        logger.info(f"✅ Prepared {len(qdrant_points)} points\n")
        
        # Step 7: Upload to Qdrant
        logger.info("Step 7: Uploading to Qdrant...")
        qdrant_batch_size = 20
        uploaded_count = 0
        
        for i in range(0, len(qdrant_points), qdrant_batch_size):
            batch = qdrant_points[i:i+qdrant_batch_size]
            batch_num = i//qdrant_batch_size + 1
            total_batches = (len(qdrant_points)-1)//qdrant_batch_size + 1
            
            logger.info(f"  Uploading batch {batch_num}/{total_batches} ({len(batch)} points)...")
            
            # Retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    qdrant_service.upsert_points(
                        collection_name="local_discovery",
                        points=batch
                    )
                    uploaded_count += len(batch)
                    break
                
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 2
                        logger.warning(f"⚠️ Upload failed, retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"❌ Failed to upload batch: {e}")
            
            time.sleep(0.5)
        
        logger.info(f"✅ Uploaded {uploaded_count} vectors to Qdrant\n")
        
        # Step 8: Update metadata
        
        await rss_service.update_ingestion_metadata(
            source="blog",
            city=city,
            records_processed=len(posts),
            status="success"
        )
        
        # Step 9: Print summary
        logger.info(f"{'='*60}")
        logger.info(f"BLOG RSS INGESTION COMPLETE for {city.upper()}")
        logger.info(f"{'='*60}")
        logger.info(f"Blog posts fetched: {len(posts)}")
        logger.info(f"Stored in MongoDB: {stored_count}")
        logger.info(f"Text chunks created: {len(all_chunks)}")
        logger.info(f"Embeddings generated: {len(all_embeddings)}")
        logger.info(f"Vectors uploaded to Qdrant: {uploaded_count}")
        logger.info(f"{'='*60}\n")
    
    except Exception as e:
        logger.error(f"❌ Error during ingestion: {e}")
        await rss_service.update_ingestion_metadata(
            source="blog",
            city=city,
            records_processed=0,
            status="failed",
            error_message=str(e)
        )
        import traceback
        traceback.print_exc()
        raise
    
    finally:
        await close_mongo_connection()


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Ingest blog posts from RSS feeds")
    parser.add_argument(
        "city",
        type=str,
        choices=["mumbai", "delhi", "goa", "bangalore", "pune", "all"],
        help="City to ingest blog content for"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days back to fetch (default: 7)"
    )
    parser.add_argument(
        "--no-general",
        action="store_true",
        help="Skip general India feeds"
    )
    
    args = parser.parse_args()
    
    if args.city == "all":
        cities = ["mumbai", "delhi", "goa"]
    else:
        cities = [args.city]
    
    for city in cities:
        try:
            await ingest_city_blogs(
                city,
                days_back=args.days,
                include_general=not args.no_general
            )
        except Exception as e:
            logger.error(f"❌ Error ingesting {city}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
