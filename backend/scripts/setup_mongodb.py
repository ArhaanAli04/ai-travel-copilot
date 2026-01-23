"""
Setup MongoDB collections and indexes for Local Discovery feature
Run this once after creating the POI models
"""
import sys
from pathlib import Path
import asyncio

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.mongo import connect_to_mongo, get_database, close_mongo_connection
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def setup_collections():
    """Create MongoDB collections and indexes"""
    
    # Connect to MongoDB
    await connect_to_mongo()
    db = get_database()
    
    logger.info("🔧 Setting up MongoDB collections and indexes...")
    
    # 1. POIs collection with geospatial index
    logger.info("Creating 'pois' collection...")
    pois = db["pois"]
    
    # Create indexes
    await pois.create_index([("location", "2dsphere")])  # Geospatial index
    await pois.create_index("city")
    await pois.create_index("osm_id", unique=True)  # Prevent duplicates
    await pois.create_index("category")
    logger.info("✅ 'pois' collection ready with indexes")
    
    # 2. Reddit posts collection
    logger.info("Creating 'reddit_posts' collection...")
    reddit_posts = db["reddit_posts"]
    
    await reddit_posts.create_index("reddit_id", unique=True)  # Prevent duplicates
    await reddit_posts.create_index("city")
    await reddit_posts.create_index("subreddit")
    await reddit_posts.create_index("scraped_at")
    logger.info("✅ 'reddit_posts' collection ready with indexes")
    
    # 3. Blog posts collection
    logger.info("Creating 'blog_posts' collection...")
    blog_posts = db["blog_posts"]
    
    await blog_posts.create_index("url", unique=True)  # Prevent duplicates
    await blog_posts.create_index("city")
    await blog_posts.create_index("blog_name")
    await blog_posts.create_index("published_at")
    logger.info("✅ 'blog_posts' collection ready with indexes")
    
    # 4. User feedback collection
    logger.info("Creating 'user_feedback' collection...")
    user_feedback = db["user_feedback"]
    
    await user_feedback.create_index("poi_id")
    await user_feedback.create_index("user_id")
    await user_feedback.create_index("created_at")
    logger.info("✅ 'user_feedback' collection ready with indexes")
    
    # 5. Ingestion metadata collection
    logger.info("Creating 'ingestion_metadata' collection...")
    ingestion_metadata = db["ingestion_metadata"]
    
    await ingestion_metadata.create_index([("source", 1), ("city", 1)], unique=True)
    await ingestion_metadata.create_index("last_scraped_at")
    logger.info("✅ 'ingestion_metadata' collection ready with indexes")
    
    logger.info("\n🎉 MongoDB setup complete!")
    
    # Close connection
    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(setup_collections())
