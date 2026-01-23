from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PayloadSchemaType
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

        # AUTO-CREATE TRAVEL GUIDES COLLECTION
        create_collection_if_not_exists(
            settings.QDRANT_COLLECTION_NAME,
            vector_size=3072
        )
        
        # ✅ NEW: AUTO-CREATE POLICIES COLLECTION
        create_collection_if_not_exists(
            settings.QDRANT_POLICIES_COLLECTION,
            vector_size=3072,
            is_policies=True  # Special handling for policies
        )
        logger.info("✅ Qdrant setup complete (local_discovery collection will be created on first use)")
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



def create_collection_if_not_exists(
    collection_name: str, 
    vector_size: int = 3072,
    is_policies: bool = False  # ✅ NEW parameter
):
    """
    Create a Qdrant collection if it doesn't exist
    
    Args:
        collection_name: Name of the collection
        vector_size: Dimension of vectors (3072 for Gemini embeddings)
        is_policies: Whether this is the policies collection (different indexes)
    """
    client = get_qdrant_client()
    try:
        # Check if collection exists
        client.get_collection(collection_name)
        logger.info(f"✅ Collection '{collection_name}' already exists")
        
        # ✅ CREATE PAYLOAD INDEXES based on collection type
        if is_policies:
            # Policies collection indexes
            _create_policies_indexes(client, collection_name)
        else:
            # Travel guides collection indexes
            _create_guides_indexes(client, collection_name)
        
    except Exception:
        # Collection doesn't exist, create it
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
        logger.info(f"✅ Created collection '{collection_name}'")
        
        # Create appropriate indexes
        if is_policies:
            _create_policies_indexes(client, collection_name)
        else:
            _create_guides_indexes(client, collection_name)


def _create_guides_indexes(client: QdrantClient, collection_name: str):
    """Create indexes for travel guides collection"""
    indexes = [
        ("city", PayloadSchemaType.KEYWORD),
        ("theme", PayloadSchemaType.KEYWORD),
    ]
    
    for field_name, schema_type in indexes:
        try:
            client.create_payload_index(
                collection_name=collection_name,
                field_name=field_name,
                field_schema=schema_type
            )
            logger.info(f"✅ Created index for '{field_name}' field")
        except Exception as e:
            if "already exists" not in str(e).lower():
                logger.warning(f"⚠️ Could not create {field_name} index: {e}")


def _create_policies_indexes(client: QdrantClient, collection_name: str):
    """Create indexes for policies collection"""
    indexes = [
        ("type", PayloadSchemaType.KEYWORD),  # airline, hotel, insurance
        ("provider_name", PayloadSchemaType.KEYWORD),  # airline name
        ("region", PayloadSchemaType.KEYWORD),  # EU, US, UK, etc.
        ("disruption_type", PayloadSchemaType.KEYWORD),  # delay, cancellation
        ("policy_version", PayloadSchemaType.KEYWORD),  # 2026-Q1
    ]
    
    for field_name, schema_type in indexes:
        try:
            client.create_payload_index(
                collection_name=collection_name,
                field_name=field_name,
                field_schema=schema_type
            )
            logger.info(f"✅ Created policy index for '{field_name}' field")
        except Exception as e:
            if "already exists" not in str(e).lower():
                logger.warning(f"⚠️ Could not create {field_name} index: {e}")


def get_collection_name() -> str:
    """Get the active travel guides collection name"""
    return settings.QDRANT_COLLECTION_NAME


def get_policies_collection_name() -> str:
    """Get the policies collection name"""
    return settings.QDRANT_POLICIES_COLLECTION
