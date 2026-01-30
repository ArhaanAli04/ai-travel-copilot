"""
Script to update POI schema with feedback fields
Adds: user_feedback, average_rating, feedback_count
"""
import asyncio
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import certifi
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def update_poi_schema():
    """Add feedback fields to all POIs"""
    
    # Connect to MongoDB (same way as mongo.py)
    client = AsyncIOMotorClient(
        settings.MONGODB_URL,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=10000,
        socketTimeoutMS=10000
    )
    
    # Use same database name as in mongo.py
    db = client.get_database("travel_copilot")
    pois_collection = db["pois"]
    
    logger.info("🔄 Updating POI schema with feedback fields...")
    
    # First, check current POI count
    total_pois = await pois_collection.count_documents({})
    logger.info(f"   Total POIs in database: {total_pois}")
    
    # Update all POIs that don't have feedback fields
    result = await pois_collection.update_many(
        {
            "$or": [
                {"user_feedback": {"$exists": False}},
                {"average_rating": {"$exists": False}},
                {"feedback_count": {"$exists": False}}
            ]
        },
        {
            "$set": {
                "user_feedback": [],  # Array of feedback objects
                "average_rating": 0.0,  # Average rating (0-5)
                "feedback_count": 0,  # Total feedback count
                "positive_feedback_count": 0,  # Thumbs up count
                "negative_feedback_count": 0,  # Thumbs down count
                "last_feedback_at": None  # Timestamp of last feedback
            }
        }
    )
    
    logger.info(f"✅ Updated {result.modified_count} POIs with feedback fields")
    
    # Create indexes on feedback fields for efficient queries
    logger.info("📊 Creating indexes on feedback fields...")
    
    await pois_collection.create_index([("average_rating", -1)])
    await pois_collection.create_index([("feedback_count", -1)])
    await pois_collection.create_index([("city", 1), ("average_rating", -1)])
    await pois_collection.create_index([("city", 1), ("category", 1), ("average_rating", -1)])
    await pois_collection.create_index([("last_feedback_at", -1)])
    
    logger.info("✅ Indexes created successfully")
    
    # Show sample updated POI
    sample_poi = await pois_collection.find_one()
    if sample_poi:
        logger.info(f"\n📝 Sample POI structure:")
        logger.info(f"   Name: {sample_poi.get('name')}")
        logger.info(f"   Feedback array: {sample_poi.get('user_feedback', [])}")
        logger.info(f"   Average rating: {sample_poi.get('average_rating', 0)}")
        logger.info(f"   Feedback count: {sample_poi.get('feedback_count', 0)}")
        logger.info(f"   Positive feedback: {sample_poi.get('positive_feedback_count', 0)}")
        logger.info(f"   Negative feedback: {sample_poi.get('negative_feedback_count', 0)}")
    
    client.close()
    logger.info("\n🎉 Schema update complete!")


if __name__ == "__main__":
    asyncio.run(update_poi_schema())
