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

    def check_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Get detailed statistics about a collection
        
        Args:
            collection_name: Name of the collection
        
        Returns:
            Dictionary with collection statistics
        """
        client = get_qdrant_client()
        
        try:
            collection_info = client.get_collection(collection_name)
            
            # Extract key metrics - prioritize points_count over vectors_count
            # In some Qdrant versions, vectors_count is None but points_count works
            points_count = collection_info.points_count or 0
            vectors_count = collection_info.vectors_count or points_count  # Fallback to points_count
            indexed_vectors = collection_info.indexed_vectors_count or 0
            
            # Get vector dimension from config
            vector_size = collection_info.config.params.vectors.size
            
            # Calculate storage estimate
            # Use points_count (actual data) instead of vectors_count
            actual_count = points_count  # This is the real count
            
            # Formula: vectors × dimensions × 4 bytes (float32) + metadata overhead
            vector_storage_bytes = actual_count * vector_size * 4
            metadata_overhead = actual_count * 1024  # ~1KB per point for metadata
            total_storage_bytes = vector_storage_bytes + metadata_overhead
            
            storage_mb = total_storage_bytes / (1024 * 1024)
            storage_gb = storage_mb / 1024
            
            # Safely get segments count (may not exist in all Qdrant versions)
            segments_count = 0
            try:
                if hasattr(collection_info, 'segments') and collection_info.segments:
                    segments_count = len(collection_info.segments)
            except:
                pass
            
            # Safely get optimizer status
            optimizer_status = "unknown"
            try:
                if hasattr(collection_info, 'optimizer_status'):
                    optimizer_status = str(collection_info.optimizer_status)
            except:
                pass
            
            stats = {
                "collection_name": collection_name,
                "vectors_count": actual_count,  # Use actual_count (points_count)
                "indexed_vectors_count": indexed_vectors,
                "points_count": points_count,
                "segments_count": segments_count,
                "status": str(collection_info.status),
                "optimizer_status": optimizer_status,
                "vector_size": vector_size,
                "storage_estimate_mb": round(storage_mb, 2),
                "storage_estimate_gb": round(storage_gb, 3),
                "payload_schema": collection_info.payload_schema or {},
            }
            
            logger.info(f"📊 Stats for '{collection_name}': {actual_count} vectors, {storage_mb:.2f} MB")
            return stats
        
        except Exception as e:
            logger.error(f"❌ Error getting stats for '{collection_name}': {e}")
            return {
                "collection_name": collection_name,
                "error": str(e),
                "vectors_count": 0,
                "storage_estimate_mb": 0,
                "storage_estimate_gb": 0,
            }

    
    def get_all_collections_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for all collections
        
        Returns:
            Dictionary mapping collection names to their stats
        """
        client = get_qdrant_client()
        
        try:
            collections = client.get_collections().collections
            all_stats = {}
            
            for collection in collections:
                stats = self.check_collection_stats(collection.name)
                all_stats[collection.name] = stats
            
            return all_stats
        
        except Exception as e:
            logger.error(f"❌ Error getting all collection stats: {e}")
            return {}
    
    def calculate_storage_usage(self) -> Dict[str, Any]:
        """
        Calculate total storage usage across all collections
        
        Returns:
            Dictionary with total storage metrics and free tier usage
        """
        all_stats = self.get_all_collections_stats()
        
        total_vectors = sum(stats.get("vectors_count", 0) for stats in all_stats.values())
        total_mb = sum(stats.get("storage_estimate_mb", 0) for stats in all_stats.values())
        total_gb = total_mb / 1024
        
        # Qdrant Cloud free tier: 1 GB
        free_tier_limit_gb = 1.0
        free_tier_limit_mb = free_tier_limit_gb * 1024
        
        usage_percentage = (total_mb / free_tier_limit_mb) * 100
        remaining_mb = free_tier_limit_mb - total_mb
        remaining_gb = remaining_mb / 1024
        
        return {
            "total_vectors": total_vectors,
            "total_storage_mb": round(total_mb, 2),
            "total_storage_gb": round(total_gb, 3),
            "free_tier_limit_gb": free_tier_limit_gb,
            "usage_percentage": round(usage_percentage, 2),
            "remaining_mb": round(remaining_mb, 2),
            "remaining_gb": round(remaining_gb, 3),
            "collections": all_stats,
            "alert": "WARNING: Approaching storage limit!" if usage_percentage > 80 else None
        }
    
    def estimate_ingestion_impact(
        self,
        num_vectors: int,
        vector_dimension: int = 768
    ) -> Dict[str, Any]:
        """
        Estimate storage impact before ingesting new vectors
        
        Args:
            num_vectors: Number of vectors to ingest
            vector_dimension: Dimension of vectors (default: 768)
        
        Returns:
            Dictionary with impact estimates
        """
        # Calculate new vector storage
        vector_storage_bytes = num_vectors * vector_dimension * 4
        metadata_overhead = num_vectors * 1024  # ~1KB per point
        total_new_bytes = vector_storage_bytes + metadata_overhead
        
        new_storage_mb = total_new_bytes / (1024 * 1024)
        new_storage_gb = new_storage_mb / 1024
        
        # Get current usage
        current_usage = self.calculate_storage_usage()
        current_mb = current_usage["total_storage_mb"]
        
        # Calculate projected usage
        projected_mb = current_mb + new_storage_mb
        projected_gb = projected_mb / 1024
        
        free_tier_limit_mb = 1024  # 1 GB
        projected_percentage = (projected_mb / free_tier_limit_mb) * 100
        
        # Determine if ingestion is safe
        is_safe = projected_percentage < 80
        warning = None
        
        if projected_percentage > 100:
            warning = "❌ CRITICAL: Would exceed free tier limit!"
        elif projected_percentage > 80:
            warning = "⚠️ WARNING: Would exceed 80% threshold!"
        
        return {
            "num_vectors_to_add": num_vectors,
            "vector_dimension": vector_dimension,
            "new_storage_mb": round(new_storage_mb, 2),
            "new_storage_gb": round(new_storage_gb, 3),
            "current_storage_mb": current_mb,
            "projected_storage_mb": round(projected_mb, 2),
            "projected_storage_gb": round(projected_gb, 3),
            "projected_usage_percentage": round(projected_percentage, 2),
            "is_safe": is_safe,
            "warning": warning,
        }
    
    def verify_vector_dimensions(self, collection_name: str) -> Dict[str, Any]:
        """
        Verify that all vectors in a collection have consistent dimensions
        
        Args:
            collection_name: Name of collection to check
        
        Returns:
            Dictionary with verification results
        """
        client = get_qdrant_client()
        
        try:
            collection_info = client.get_collection(collection_name)
            expected_dim = collection_info.config.params.vectors.size
            
            # Scroll through sample of points to verify
            points, _ = client.scroll(
                collection_name=collection_name,
                limit=100,
                with_vectors=True
            )
            
            if not points:
                return {
                    "collection_name": collection_name,
                    "expected_dimension": expected_dim,
                    "verified": True,
                    "sample_size": 0,
                    "issues": []
                }
            
            issues = []
            for point in points:
                if point.vector:
                    actual_dim = len(point.vector)
                    if actual_dim != expected_dim:
                        issues.append({
                            "point_id": point.id,
                            "expected": expected_dim,
                            "actual": actual_dim
                        })
            
            return {
                "collection_name": collection_name,
                "expected_dimension": expected_dim,
                "verified": len(issues) == 0,
                "sample_size": len(points),
                "issues_found": len(issues),
                "issues": issues[:10]  # First 10 issues
            }
        
        except Exception as e:
            logger.error(f"❌ Error verifying dimensions: {e}")
            return {
                "collection_name": collection_name,
                "error": str(e),
                "verified": False
            }

# Singleton instance
qdrant_service = QdrantService()
