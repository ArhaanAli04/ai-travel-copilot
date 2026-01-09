from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams,PayloadSchemaType
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Global Qdrant client
qdrant_client: QdrantClient = None


def connect_to_qdrant():
    """
    Connect to Qdrant Cloud
    """
    global qdrant_client
    try:
        qdrant_client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
        )
        
        # Test connection by listing collections
        collections = qdrant_client.get_collections()
        logger.info(f"✅ Qdrant connection successful. Collections: {len(collections.collections)}")

        # AUTO-CREATE COLLECTION IF IT DOESN'T EXIST
        create_collection_if_not_exists(
            settings.QDRANT_COLLECTION_NAME,
            vector_size=3072  # ✅ IMPORTANT: Use 3072 for your Gemini model
        )
        return qdrant_client
    except Exception as e:
        logger.error(f"❌ Qdrant connection failed: {e}")
        raise


def get_qdrant_client():
    """
    Get Qdrant client instance
    """
    if qdrant_client is None:
        connect_to_qdrant()
    return qdrant_client


def create_collection_if_not_exists(collection_name: str, vector_size: int = 3072):
    """
    Create a Qdrant collection if it doesn't exist
    
    Args:
        collection_name: Name of the collection
        vector_size: Dimension of vectors (3072 for Gemini embeddings)
    """
    client = get_qdrant_client()
    try:
        # Check if collection exists
        client.get_collection(collection_name)
        logger.info(f"✅ Collection '{collection_name}' already exists")
        
        # ✅ CREATE PAYLOAD INDEXES (even if collection exists)
        try:
            # Create index for 'city' field
            client.create_payload_index(
                collection_name=collection_name,
                field_name="city",
                field_schema=PayloadSchemaType.KEYWORD
            )
            logger.info(f"✅ Created index for 'city' field")
        except Exception as e:
            if "already exists" not in str(e).lower():
                logger.warning(f"⚠️ Could not create city index: {e}")
        
        try:
            # Create index for 'theme' field
            client.create_payload_index(
                collection_name=collection_name,
                field_name="theme",
                field_schema=PayloadSchemaType.KEYWORD
            )
            logger.info(f"✅ Created index for 'theme' field")
        except Exception as e:
            if "already exists" not in str(e).lower():
                logger.warning(f"⚠️ Could not create theme index: {e}")
        
    except Exception:
        # Collection doesn't exist, create it
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
        logger.info(f"✅ Created collection '{collection_name}'")
        
        # ✅ CREATE PAYLOAD INDEXES FOR NEW COLLECTION
        client.create_payload_index(
            collection_name=collection_name,
            field_name="city",
            field_schema=PayloadSchemaType.KEYWORD
        )
        client.create_payload_index(
            collection_name=collection_name,
            field_name="theme",
            field_schema=PayloadSchemaType.KEYWORD
        )
        logger.info(f"✅ Created payload indexes for '{collection_name}'")

def get_collection_name() -> str:
    """Get the active collection name"""
    return settings.QDRANT_COLLECTION_NAME