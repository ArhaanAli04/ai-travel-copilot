"""
Storage calculator utilities for Qdrant vector database
"""
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class StorageCalculator:
    """Calculate storage requirements for Qdrant vectors"""
    
    # Constants
    BYTES_PER_FLOAT32 = 4
    METADATA_OVERHEAD_PER_POINT = 1024  # ~1KB per point for payload
    FREE_TIER_LIMIT_GB = 1.0
    
    @staticmethod
    def calculate_vector_storage(
        num_vectors: int,
        vector_dimension: int,
        include_metadata: bool = True
    ) -> Dict[str, float]:
        """
        Calculate storage requirements for vectors
        
        Args:
            num_vectors: Number of vectors
            vector_dimension: Dimension of each vector
            include_metadata: Include metadata overhead
        
        Returns:
            Dictionary with storage breakdown in bytes, KB, MB, GB
        """
        # Calculate vector storage
        vector_bytes = num_vectors * vector_dimension * StorageCalculator.BYTES_PER_FLOAT32
        
        # Add metadata overhead
        metadata_bytes = 0
        if include_metadata:
            metadata_bytes = num_vectors * StorageCalculator.METADATA_OVERHEAD_PER_POINT
        
        total_bytes = vector_bytes + metadata_bytes
        
        return {
            "num_vectors": num_vectors,
            "vector_dimension": vector_dimension,
            "vector_storage_bytes": vector_bytes,
            "metadata_storage_bytes": metadata_bytes,
            "total_bytes": total_bytes,
            "total_kb": total_bytes / 1024,
            "total_mb": total_bytes / (1024 * 1024),
            "total_gb": total_bytes / (1024 * 1024 * 1024),
        }
    
    @staticmethod
    def estimate_city_storage(
        num_pois: int = 1500,
        vector_dimension: int = 768
    ) -> Dict[str, float]:
        """
        Estimate storage for a city's POIs
        
        Args:
            num_pois: Average POIs per city (default: 1500)
            vector_dimension: Vector dimension (default: 768)
        
        Returns:
            Storage estimate dictionary
        """
        return StorageCalculator.calculate_vector_storage(num_pois, vector_dimension)
    
    @staticmethod
    def calculate_free_tier_capacity(
        vector_dimension: int = 768,
        current_usage_mb: float = 0.0
    ) -> Dict[str, any]:
        """
        Calculate how many vectors can fit in free tier
        
        Args:
            vector_dimension: Vector dimension
            current_usage_mb: Current storage usage in MB
        
        Returns:
            Dictionary with capacity information
        """
        free_tier_mb = StorageCalculator.FREE_TIER_LIMIT_GB * 1024
        remaining_mb = free_tier_mb - current_usage_mb
        remaining_bytes = remaining_mb * 1024 * 1024
        
        # Calculate bytes per vector
        bytes_per_vector = (vector_dimension * StorageCalculator.BYTES_PER_FLOAT32 + 
                           StorageCalculator.METADATA_OVERHEAD_PER_POINT)
        
        # Calculate capacity
        remaining_vectors = int(remaining_bytes / bytes_per_vector)
        
        # Estimate cities (assuming 1500 POIs per city)
        avg_pois_per_city = 1500
        remaining_cities = remaining_vectors // avg_pois_per_city
        
        return {
            "free_tier_limit_mb": free_tier_mb,
            "current_usage_mb": current_usage_mb,
            "remaining_mb": remaining_mb,
            "remaining_gb": remaining_mb / 1024,
            "bytes_per_vector": bytes_per_vector,
            "remaining_vectors": remaining_vectors,
            "remaining_cities": remaining_cities,
            "vector_dimension": vector_dimension,
        }
    
    @staticmethod
    def compare_dimensions(num_vectors: int) -> Dict[int, Dict[str, float]]:
        """
        Compare storage requirements for different vector dimensions
        
        Args:
            num_vectors: Number of vectors to compare
        
        Returns:
            Dictionary mapping dimensions to storage requirements
        """
        dimensions = [384, 512, 768, 1024, 1536]
        comparison = {}
        
        for dim in dimensions:
            storage = StorageCalculator.calculate_vector_storage(num_vectors, dim)
            comparison[dim] = {
                "total_mb": storage["total_mb"],
                "total_gb": storage["total_gb"],
                "percent_of_free_tier": (storage["total_mb"] / 1024) * 100,
            }
        
        return comparison
    
    @staticmethod
    def optimize_dimension_recommendation(
        num_vectors: int,
        current_dimension: int = 768,
        target_usage_percent: float = 70.0
    ) -> Dict[str, any]:
        """
        Recommend optimal dimension to stay under target usage
        
        Args:
            num_vectors: Expected number of vectors
            current_dimension: Current vector dimension
            target_usage_percent: Target usage percentage of free tier
        
        Returns:
            Optimization recommendations
        """
        target_mb = (target_usage_percent / 100) * 1024  # Target in MB
        
        # Calculate current storage
        current_storage = StorageCalculator.calculate_vector_storage(num_vectors, current_dimension)
        current_mb = current_storage["total_mb"]
        current_percent = (current_mb / 1024) * 100
        
        # Find optimal dimension
        dimensions = [384, 512, 768, 1024, 1536]
        optimal_dim = current_dimension
        
        for dim in dimensions:
            test_storage = StorageCalculator.calculate_vector_storage(num_vectors, dim)
            test_percent = (test_storage["total_mb"] / 1024) * 100
            
            if test_percent <= target_usage_percent:
                optimal_dim = dim
                break
        
        optimal_storage = StorageCalculator.calculate_vector_storage(num_vectors, optimal_dim)
        optimal_percent = (optimal_storage["total_mb"] / 1024) * 100
        
        needs_optimization = current_percent > target_usage_percent
        
        return {
            "num_vectors": num_vectors,
            "current_dimension": current_dimension,
            "current_storage_mb": current_mb,
            "current_usage_percent": current_percent,
            "target_usage_percent": target_usage_percent,
            "optimal_dimension": optimal_dim,
            "optimal_storage_mb": optimal_storage["total_mb"],
            "optimal_usage_percent": optimal_percent,
            "needs_optimization": needs_optimization,
            "storage_saved_mb": current_mb - optimal_storage["total_mb"] if needs_optimization else 0,
            "recommendation": (
                f"Reduce dimension from {current_dimension} to {optimal_dim} to stay under {target_usage_percent}% usage"
                if needs_optimization
                else f"Current dimension ({current_dimension}) is optimal for {target_usage_percent}% target"
            )
        }
    
    @staticmethod
    def format_storage_report(storage_data: Dict) -> str:
        """Format storage data into readable report"""
        lines = [
            f"Vectors: {storage_data['num_vectors']:,}",
            f"Dimension: {storage_data['vector_dimension']}",
            f"Vector Storage: {storage_data['total_mb']:.2f} MB",
            f"Percentage of Free Tier: {(storage_data['total_mb'] / 1024) * 100:.2f}%",
        ]
        return "\n".join(lines)


# Singleton instance
storage_calculator = StorageCalculator()
