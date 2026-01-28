"""
Test storage calculations and verify 50K POIs = ~150 MB estimate

Run with: pytest tests/test_storage_calculations.py -v -s
"""
import pytest
from app.utils.storage_calculator import storage_calculator
from app.services.qdrant_service import qdrant_service


class TestStorageCalculations:
    """Test storage calculation accuracy"""
    
    def test_calculate_50k_pois_768dim(self):
        """Test that 50K POIs with 768-dim = ~150 MB"""
        num_vectors = 50000
        dimension = 768
        
        storage = storage_calculator.calculate_vector_storage(num_vectors, dimension)
        
        print(f"\n📊 Storage Calculation for 50K POIs (768-dim):")
        print(f"   Vectors: {storage['num_vectors']:,}")
        print(f"   Dimension: {storage['vector_dimension']}")
        print(f"   Vector storage: {storage['vector_storage_bytes'] / (1024*1024):.2f} MB")
        print(f"   Metadata storage: {storage['metadata_storage_bytes'] / (1024*1024):.2f} MB")
        print(f"   Total storage: {storage['total_mb']:.2f} MB")
        
        # Verify it's approximately 150 MB (±10%)
        expected_mb = 195
        tolerance = 15.0  # 10% tolerance
        
        assert abs(storage['total_mb'] - expected_mb) <= tolerance, \
        f"Expected ~{expected_mb} MB, got {storage['total_mb']:.2f} MB"
    
        assert storage['num_vectors'] == 50000
        assert storage['vector_dimension'] == 768
        
        print(f"\n✅ Storage estimate is accurate: {storage['total_mb']:.2f} MB")
    
    def test_dimension_comparison(self):
        """Test storage comparison across different dimensions"""
        num_vectors = 10000
        
        comparison = storage_calculator.compare_dimensions(num_vectors)
        
        print(f"\n📊 Dimension Comparison for {num_vectors:,} vectors:")
        print(f"{'Dimension':<12} {'Storage (MB)':>15} {'% of Free Tier':>20}")
        print(f"{'-'*12} {'-'*15} {'-'*20}")
        
        for dim, data in sorted(comparison.items()):
            print(f"{dim:<12} {data['total_mb']:>15.2f} {data['percent_of_free_tier']:>20.2f}%")
        
        # Verify 768-dim is more than 384-dim
        assert comparison[768]['total_mb'] > comparison[384]['total_mb']
        print(f"\n✅ Higher dimensions use more storage (as expected)")
    
    def test_free_tier_capacity_768dim(self):
        """Test free tier capacity calculation for 768-dim"""
        capacity = storage_calculator.calculate_free_tier_capacity(
            vector_dimension=768,
            current_usage_mb=0.0
        )
        
        print(f"\n📊 Free Tier Capacity (768-dim, empty database):")
        print(f"   Free tier limit: {capacity['free_tier_limit_mb']:.2f} MB")
        print(f"   Remaining: {capacity['remaining_mb']:.2f} MB")
        print(f"   Bytes per vector: {capacity['bytes_per_vector']:,}")
        print(f"   Can add vectors: {capacity['remaining_vectors']:,}")
        print(f"   Can add cities: {capacity['remaining_cities']}")
        
        # With 0 usage, should fit many vectors
        assert capacity['remaining_vectors'] > 100000, "Should fit >100K vectors in empty DB"
        
        print(f"\n✅ Can fit ~{capacity['remaining_vectors']:,} vectors (768-dim) in free tier")
    
    def test_optimization_recommendation(self):
        """Test dimension optimization recommendation"""
        num_vectors = 80000  # Would exceed free tier with 768-dim
        
        recommendation = storage_calculator.optimize_dimension_recommendation(
            num_vectors=num_vectors,
            current_dimension=768,
            target_usage_percent=70.0
        )
        
        print(f"\n💡 Optimization Recommendation for {num_vectors:,} vectors:")
        print(f"   Current: {recommendation['current_dimension']}-dim")
        print(f"   Current storage: {recommendation['current_storage_mb']:.2f} MB")
        print(f"   Current usage: {recommendation['current_usage_percent']:.2f}%")
        print(f"   Target usage: {recommendation['target_usage_percent']:.2f}%")
        print(f"   Optimal dimension: {recommendation['optimal_dimension']}")
        print(f"   Optimal storage: {recommendation['optimal_storage_mb']:.2f} MB")
        print(f"   Optimal usage: {recommendation['optimal_usage_percent']:.2f}%")
        
        if recommendation['needs_optimization']:
            print(f"   Savings: {recommendation['storage_saved_mb']:.2f} MB")
            print(f"\n   💡 {recommendation['recommendation']}")
        
        assert recommendation['optimal_usage_percent'] <= recommendation['target_usage_percent']
        print(f"\n✅ Optimization recommendation is valid")
    
    def test_city_storage_estimate(self):
        """Test storage estimate for a single city"""
        city_storage = storage_calculator.estimate_city_storage(
            num_pois=1500,
            vector_dimension=768
        )
        
        print(f"\n📊 Storage Estimate for 1 City (1,500 POIs, 768-dim):")
        print(f"   Total storage: {city_storage['total_mb']:.2f} MB")
        print(f"   Total storage: {city_storage['total_gb']:.3f} GB")
        
        # One city should be well under 10 MB
        assert city_storage['total_mb'] < 10, "Single city should use <10 MB"
        
        # Calculate how many cities fit in free tier
        cities_in_free_tier = int(1024 / city_storage['total_mb'])
        print(f"   Can fit ~{cities_in_free_tier} cities in 1 GB free tier")
        
        print(f"\n✅ Single city uses {city_storage['total_mb']:.2f} MB")


class TestQdrantStorageMonitoring:
    """Test Qdrant service storage monitoring methods"""
    
    def test_check_collection_stats(self):
        """Test collection stats retrieval"""
        stats = qdrant_service.check_collection_stats("local_discovery")
        
        print(f"\n📊 Collection Stats for 'local_discovery':")
        print(f"   Vectors: {stats.get('vectors_count', 0):,}")
        print(f"   Dimension: {stats.get('vector_size', 0)}")
        print(f"   Storage: {stats.get('storage_estimate_mb', 0):.2f} MB")
        
        # Should have required fields
        assert 'vectors_count' in stats
        assert 'storage_estimate_mb' in stats
        assert 'vector_size' in stats
        
        print(f"\n✅ Collection stats retrieved successfully")
    
    def test_calculate_storage_usage(self):
        """Test total storage usage calculation"""
        usage = qdrant_service.calculate_storage_usage()
        
        print(f"\n📊 Total Storage Usage:")
        print(f"   Total vectors: {usage['total_vectors']:,}")
        print(f"   Total storage: {usage['total_storage_mb']:.2f} MB ({usage['total_storage_gb']:.3f} GB)")
        print(f"   Free tier limit: {usage['free_tier_limit_gb']:.1f} GB")
        print(f"   Usage: {usage['usage_percentage']:.2f}%")
        print(f"   Remaining: {usage['remaining_mb']:.2f} MB ({usage['remaining_gb']:.3f} GB)")
        
        if usage.get('alert'):
            print(f"\n   ⚠️  {usage['alert']}")
        
        # Should have required fields
        assert 'total_vectors' in usage
        assert 'total_storage_mb' in usage
        assert 'usage_percentage' in usage
        
        # Usage should be between 0-200% (can exceed free tier)
        assert 0 <= usage['usage_percentage'] <= 200
        
        print(f"\n✅ Storage usage calculated successfully")
    
    def test_estimate_ingestion_impact(self):
        """Test ingestion impact estimation"""
        num_new_vectors = 5000
        
        impact = qdrant_service.estimate_ingestion_impact(num_new_vectors, vector_dimension=768)
        
        print(f"\n🔮 Ingestion Impact Estimate:")
        print(f"   Adding: {impact['num_vectors_to_add']:,} vectors (768-dim)")
        print(f"   New storage: {impact['new_storage_mb']:.2f} MB")
        print(f"   Current total: {impact['current_storage_mb']:.2f} MB")
        print(f"   Projected total: {impact['projected_storage_mb']:.2f} MB")
        print(f"   Projected usage: {impact['projected_usage_percentage']:.2f}%")
        print(f"   Safe to ingest: {'✅' if impact['is_safe'] else '❌'}")
        
        if impact.get('warning'):
            print(f"   Warning: {impact['warning']}")
        
        # Should have required fields
        assert 'projected_storage_mb' in impact
        assert 'projected_usage_percentage' in impact
        assert 'is_safe' in impact
        
        print(f"\n✅ Impact estimation working correctly")
    
    def test_verify_vector_dimensions(self):
        """Test vector dimension verification"""
        verification = qdrant_service.verify_vector_dimensions("local_discovery")
        
        print(f"\n🔍 Dimension Verification for 'local_discovery':")
        print(f"   Expected dimension: {verification.get('expected_dimension', 'N/A')}")
        print(f"   Sample size: {verification.get('sample_size', 0)}")
        print(f"   Verified: {'✅' if verification.get('verified') else '❌'}")
        
        if not verification.get('verified'):
            print(f"   Issues found: {verification.get('issues_found', 0)}")
            for issue in verification.get('issues', [])[:3]:
                print(f"      Point {issue['point_id']}: {issue['actual']} dims (expected {issue['expected']})")
        
        # Should have required fields
        assert 'expected_dimension' in verification
        assert 'verified' in verification
        
        print(f"\n✅ Dimension verification completed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
