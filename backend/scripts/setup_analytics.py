"""
Script to set up analytics collection with indexes
"""
import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import certifi
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def setup_analytics_collection():
    """Create analytics collection with proper indexes"""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(
        settings.MONGODB_URL,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=10000,
        socketTimeoutMS=10000
    )
    
    db = client.get_database("travel_copilot")
    
    # Create analytics collection
    analytics_collection = db["analytics_queries"]
    
    logger.info("📊 Setting up analytics collection...")
    
    # Create indexes for efficient queries
    await analytics_collection.create_index([("timestamp", -1)])  # Recent queries
    await analytics_collection.create_index([("city", 1), ("timestamp", -1)])  # City analytics
    await analytics_collection.create_index([("query_text", "text")])  # Full-text search
    await analytics_collection.create_index([("user_id", 1)])  # User-specific queries
    
    logger.info("✅ Analytics indexes created")
    
    # Create TTL index (auto-delete logs older than 90 days)
    await analytics_collection.create_index(
        [("timestamp", 1)],
        expireAfterSeconds=90 * 24 * 60 * 60  # 90 days
    )
    
    logger.info("✅ TTL index created (90 days retention)")
    
    # Test insert
    test_doc = {
        "query_text": "test query",
        "city": "mumbai",
        "timestamp": asyncio.get_event_loop().time()
    }
    
    client.close()
    logger.info("🎉 Analytics setup complete!")


if __name__ == "__main__":
    asyncio.run(setup_analytics_collection())
