from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
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


def create_collection_if_not_exists(collection_name: str, vector_size: int = 768):
    """
    Create a Qdrant collection if it doesn't exist
    
    Args:
        collection_name: Name of the collection
        vector_size: Dimension of vectors (768 for Gemini embeddings)
    """
    client = get_qdrant_client()
    try:
        client.get_collection(collection_name)
        logger.info(f"Collection '{collection_name}' already exists")
    except Exception:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
        logger.info(f"✅ Created collection '{collection_name}'")
