"""
Script to set up chat_sessions collection with indexes
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


async def setup_chat_sessions_collection():
    """Create chat_sessions collection with proper indexes"""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(
        settings.MONGODB_URL,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=10000,
        socketTimeoutMS=10000
    )
    
    db = client.get_database("travel_copilot")
    chat_sessions_collection = db["chat_sessions"]
    
    logger.info("📊 Setting up chat_sessions collection...")
    
    # Create indexes for efficient queries
    await chat_sessions_collection.create_index([("user_id", 1), ("updated_at", -1)])  # User's sessions sorted by recent
    await chat_sessions_collection.create_index([("created_at", -1)])  # Recent sessions
    await chat_sessions_collection.create_index([("city", 1)])  # Filter by city
    
    logger.info("✅ Chat sessions indexes created")
    
    # Create TTL index (auto-delete sessions older than 90 days)
    await chat_sessions_collection.create_index(
        [("updated_at", 1)],
        expireAfterSeconds=90 * 24 * 60 * 60  # 90 days
    )
    
    logger.info("✅ TTL index created (90 days retention)")
    
    client.close()
    logger.info("🎉 Chat sessions setup complete!")


if __name__ == "__main__":
    asyncio.run(setup_chat_sessions_collection())
