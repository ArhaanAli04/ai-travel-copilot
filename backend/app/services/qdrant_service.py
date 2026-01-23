"""
Qdrant service for Local Discovery vector operations
Uses the existing Qdrant connection from app.core.qdrant
"""
from qdrant_client.models import Distance, VectorParams, PointStruct, PayloadSchemaType
from typing import List, Dict, Any, Optional
from app.core.qdrant import get_qdrant_client, create_collection_if_not_exists
import logging


logger = logging.getLogger(__name__)


class QdrantService:
    """Service for Local Discovery vector database operations"""
    
    def __init__(self):
        self.dimension = 768  # Local Discovery uses 768-dim embeddings
        logger.info("✅ QdrantService initialized for Local Discovery")
    
    def ensure_collection(self, collection_name: str):
        """
        Create Local Discovery collection if it doesn't exist
        
        Note: This uses 768 dimensions (not 3072 like travel guides/policies)
        """
        client = get_qdrant_client()
        
        try:
            client.get_collection(collection_name)
            logger.info(f"Collection '{collection_name}' already exists")
        except Exception:
            logger.info(f"Creating Local Discovery collection '{collection_name}' with 768 dimensions...")
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.dimension,  # 768 dims for local discovery
                    distance=Distance.COSINE
                )
            )
            logger.info(f"✅ Created collection '{collection_name}'")
            
            # Create indexes for local discovery
            self._create_local_discovery_indexes(client, collection_name)
    
    def _create_local_discovery_indexes(self, client, collection_name: str):
        """Create indexes for local discovery collection"""
        indexes = [
            ("city", PayloadSchemaType.KEYWORD),
            ("category", PayloadSchemaType.KEYWORD),
            ("source", PayloadSchemaType.KEYWORD),  # osm, reddit, blog
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
    
    def upsert_points(
        self,
        collection_name: str,
        points: List[Dict[str, Any]]
    ):
        """
        Upsert points into Qdrant collection
        
        Args:
            collection_name: Name of the collection
            points: List of points with format:
                    [{"id": "...", "vector": [...], "payload": {...}}]
        """
        # Ensure collection exists with correct dimensions
        self.ensure_collection(collection_name)
        
        client = get_qdrant_client()
        
        # Convert to PointStruct
        qdrant_points = []
        for point in points:
            # Handle both string and int IDs
            point_id = point["id"]
            if isinstance(point_id, str):
                # Use hash for string IDs (Qdrant prefers int)
                point_id = abs(hash(point_id)) % (10 ** 10)
            
            qdrant_points.append(
                PointStruct(
                    id=point_id,
                    vector=point["vector"],
                    payload=point.get("payload", {})
                )
            )
        
        # Upsert to Qdrant
        client.upsert(
            collection_name=collection_name,
            points=qdrant_points
        )
        
        logger.info(f"✅ Upserted {len(qdrant_points)} points to '{collection_name}'")
    
    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        query_filter: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search for similar vectors in Qdrant
        
        Args:
            collection_name: Name of the collection
            query_vector: Query embedding vector (768 dimensions)
            limit: Number of results to return
            query_filter: Optional Qdrant filter
        
        Returns:
            List of search results with payload and score
        """
        client = get_qdrant_client()
        
        results = client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            query_filter=query_filter
        )
        
        return [
            {
                "id": result.id,
                "score": result.score,
                "payload": result.payload
            }
            for result in results
        ]
    
    def get_collection_info(self, collection_name: str) -> Dict:
        """Get collection statistics"""
        client = get_qdrant_client()
        
        try:
            info = client.get_collection(collection_name)
            
            # Calculate storage estimate (768 dims * 4 bytes * points)
            storage_mb = (info.points_count * self.dimension * 4) / (1024 * 1024)
            
            return {
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status,
                "storage_estimate_mb": round(storage_mb, 2),
                "dimension": self.dimension
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {}


# Singleton instance
qdrant_service = QdrantService()
