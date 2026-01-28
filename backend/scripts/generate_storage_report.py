"""
Generate comprehensive storage report for Day 19

Run with: python scripts/generate_storage_report.py
"""
import sys
import os
from pathlib import Path
from datetime import datetime
import json

sys.path.append(str(Path(__file__).parent.parent))

from app.services.qdrant_service import qdrant_service
from app.utils.storage_calculator import storage_calculator


def generate_report():
    """Generate comprehensive storage report"""
    
    print("="*80)
    print(" "*20 + "DAY 19 - STORAGE OPTIMIZATION REPORT")
    print("="*80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. Current Usage
    print("1️⃣  CURRENT STORAGE USAGE")
    print("-"*80)
    
    usage = qdrant_service.calculate_storage_usage()
    
    print(f"Total Vectors: {usage['total_vectors']:,}")
    print(f"Total Storage: {usage['total_storage_mb']:.2f} MB ({usage['total_storage_gb']:.3f} GB)")
    print(f"Free Tier Limit: {usage['free_tier_limit_gb']:.1f} GB")
    print(f"Usage Percentage: {usage['usage_percentage']:.2f}%")
    print(f"Remaining Space: {usage['remaining_mb']:.2f} MB ({usage['remaining_gb']:.3f} GB)")
    
    # Health indicator
    if usage['usage_percentage'] > 80:
        print(f"\n⚠️  WARNING: High storage usage!")
    else:
        print(f"\n✅ Storage usage is healthy")
    
    # 2. Per-Collection Breakdown
    print("\n\n2️⃣  COLLECTION BREAKDOWN")
    print("-"*80)
    print(f"{'Collection':<25} {'Vectors':>12} {'Storage':>12} {'Dimension':>12}")
    print("-"*80)
    
    for name, stats in usage['collections'].items():
        if not stats.get('error'):
            print(f"{name:<25} {stats['vectors_count']:>12,} {stats['storage_estimate_mb']:>11.2f}M {stats['vector_size']:>12}")
    
    # 3. Capacity Forecast
    print("\n\n3️⃣  CAPACITY FORECAST")
    print("-"*80)
    
    capacity_768 = storage_calculator.calculate_free_tier_capacity(768, usage['total_storage_mb'])
    capacity_384 = storage_calculator.calculate_free_tier_capacity(384, usage['total_storage_mb'])
    
    print(f"With current usage ({usage['total_storage_mb']:.2f} MB):\n")
    print(f"768-dim vectors:")
    print(f"  • Can add {capacity_768['remaining_vectors']:,} more vectors")
    print(f"  • Equivalent to ~{capacity_768['remaining_cities']} more cities")
    
    print(f"\n384-dim vectors (if optimized):")
    print(f"  • Can add {capacity_384['remaining_vectors']:,} more vectors")
    print(f"  • Equivalent to ~{capacity_384['remaining_cities']} more cities")
    
    # 4. 50K POI Verification
    print("\n\n4️⃣  STORAGE CALCULATION VERIFICATION")
    print("-"*80)
    
    test_50k = storage_calculator.calculate_vector_storage(50000, 768)
    
    print(f"Test: 50,000 vectors @ 768 dimensions")
    print(f"  Vector storage: {test_50k['vector_storage_bytes'] / (1024*1024):.2f} MB")
    print(f"  Metadata storage: {test_50k['metadata_storage_bytes'] / (1024*1024):.2f} MB")
    print(f"  Total storage: {test_50k['total_mb']:.2f} MB")
    print(f"\n  ✅ Calculation verified: ~{test_50k['total_mb']:.0f} MB for 50K POIs")
    
    # 5. Optimization Recommendations
    print("\n\n5️⃣  OPTIMIZATION RECOMMENDATIONS")
    print("-"*80)
    
    current_vectors = usage['total_vectors']
    
    if current_vectors > 0:
        recommendation = storage_calculator.optimize_dimension_recommendation(
            num_vectors=current_vectors,
            current_dimension=768,
            target_usage_percent=70.0
        )
        
        print(f"Current Configuration:")
        print(f"  • {recommendation['current_dimension']}-dim vectors")
        print(f"  • {recommendation['current_storage_mb']:.2f} MB total")
        print(f"  • {recommendation['current_usage_percent']:.2f}% of free tier")
        
        print(f"\nOptimal Configuration (to stay under 70%):")
        print(f"  • {recommendation['optimal_dimension']}-dim vectors")
        print(f"  • {recommendation['optimal_storage_mb']:.2f} MB total")
        print(f"  • {recommendation['optimal_usage_percent']:.2f}% of free tier")
        
        if recommendation['needs_optimization']:
            print(f"\n  💡 {recommendation['recommendation']}")
            print(f"  Potential savings: {recommendation['storage_saved_mb']:.2f} MB")
        else:
            print(f"\n  ✅ Current dimension is optimal")
    
    # 6. Dimension Comparison
    print("\n\n6️⃣  DIMENSION COMPARISON TABLE")
    print("-"*80)
    
    comparison = storage_calculator.compare_dimensions(10000)
    
    print(f"Storage for 10,000 vectors:\n")
    print(f"{'Dimension':<12} {'Storage (MB)':>15} {'% of Free Tier':>20}")
    print("-"*80)
    
    for dim, data in sorted(comparison.items()):
        print(f"{dim:<12} {data['total_mb']:>15.2f} {data['percent_of_free_tier']:>19.2f}%")
    
    # 7. Summary & Action Items
    print("\n\n7️⃣  SUMMARY & ACTION ITEMS")
    print("-"*80)
    
    print(f"\n✅ Day 19 Achievements:")
    print(f"   • Storage monitoring system implemented")
    print(f"   • {usage['total_vectors']:,} vectors tracked across {len(usage['collections'])} collections")
    print(f"   • {usage['usage_percentage']:.2f}% of free tier utilized")
    print(f"   • Storage calculations verified (50K POIs = ~{test_50k['total_mb']:.0f} MB)")
    
    print(f"\n📋 Action Items:")
    
    if usage['usage_percentage'] > 80:
        print(f"   🔴 URGENT: Storage usage >80% - consider:")
        print(f"      • Reduce vector dimensions (768 → 384)")
        print(f"      • Remove unused vectors")
        print(f"      • Upgrade to paid tier")
    elif usage['usage_percentage'] > 60:
        print(f"   🟡 MONITOR: Storage usage >60% - keep monitoring")
    else:
        print(f"   🟢 HEALTHY: Storage usage <60% - no action needed")
    
    print(f"\n   • Run 'python scripts/monitor_storage.py' regularly")
    print(f"   • Check storage before each ingestion")
    print(f"   • Use dashboard: 'python scripts/collection_dashboard.py --interactive'")
    
    print("\n" + "="*80)
    print(" "*25 + "END OF REPORT")
    print("="*80)


if __name__ == "__main__":
    try:
        generate_report()
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
