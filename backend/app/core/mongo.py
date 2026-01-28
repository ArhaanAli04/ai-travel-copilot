from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import logging
import certifi
logger = logging.getLogger(__name__)

# Global MongoDB client
mongo_client: AsyncIOMotorClient = None
database = None


async def connect_to_mongo():
    """
    Connect to MongoDB Atlas
    """
    global mongo_client, database
    try:
        mongo_client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            tlsCAFile=certifi.where(),  # Use certifi's certificate bundle
            serverSelectionTimeoutMS=5000,  # 5 second timeout
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,    
        )
        # Get database name from connection string or use default
        database = mongo_client.get_database("travel_copilot")
        
        # Test connection
        await mongo_client.admin.command('ping')
        logger.info("✅ MongoDB connection successful")
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        raise


async def close_mongo_connection():
    """
    Close MongoDB connection
    """
    global mongo_client
    if mongo_client:
        mongo_client.close()
        logger.info("🔒 MongoDB connection closed")


def get_database():
    """
    Get MongoDB database instance
    """
    return database
