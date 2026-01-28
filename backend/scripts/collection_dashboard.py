"""
Interactive CLI dashboard for Qdrant collection health monitoring

Run with:
    python scripts/collection_dashboard.py
    python scripts/collection_dashboard.py --collection local_discovery
"""
import sys
import os
from pathlib import Path
import argparse
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.qdrant_service import qdrant_service
from app.utils.storage_calculator import storage_calculator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def print_header(title: str, width: int = 80):
    """Print formatted header"""
    print(f"\n{'='*width}")
    print(f"{title.center(width)}")
    print(f"{'='*width}")


def print_collection_health(collection_name: str):
    """Print detailed health report for a collection"""
    print_header(f"Collection Health: {collection_name}")
    
    # Get stats
    stats = qdrant_service.check_collection_stats(collection_name)
    
    if stats.get('error'):
        print(f"❌ Error: {stats['error']}")
        return
    
    # Basic info
    print(f"\n📊 Basic Information:")
    print(f"   Vectors: {stats['vectors_count']:,}")
    print(f"   Indexed: {stats['indexed_vectors_count']:,}")
    print(f"   Dimension: {stats['vector_size']}")
    print(f"   Status: {stats['status']}")
    print(f"   Segments: {stats['segments_count']}")
    
    # Storage
    print(f"\n💾 Storage:")
    print(f"   Total: {stats['storage_estimate_mb']:.2f} MB ({stats['storage_estimate_gb']:.3f} GB)")
    
    free_tier_mb = 1024
    usage_pct = (stats['storage_estimate_mb'] / free_tier_mb) * 100
    print(f"   Free Tier Usage: {usage_pct:.2f}%")
    
    # Storage bar
    bar_width = 50
    filled = int((usage_pct / 100) * bar_width)
    bar = '█' * filled + '░' * (bar_width - filled)
    print(f"   [{bar}]")
    
    # Health status
    print(f"\n🏥 Health Status:")
    if usage_pct > 90:
        print(f"   ❌ CRITICAL: Very high storage usage")
    elif usage_pct > 80:
        print(f"   ⚠️  WARNING: High storage usage")
    elif usage_pct > 60:
        print(f"   ⚡ GOOD: Moderate storage usage")
    else:
        print(f"   ✅ EXCELLENT: Low storage usage")
    
    # Optimizer status
    if stats.get('optimizer_status'):
        opt_status = stats['optimizer_status']
        print(f"\n⚙️  Optimizer:")
        print(f"   Status: {opt_status.status if hasattr(opt_status, 'status') else 'Running'}")
    
    # Verify dimensions
    print(f"\n🔍 Dimension Verification:")
    verification = qdrant_service.verify_vector_dimensions(collection_name)
    
    if verification['verified']:
        print(f"   ✅ All vectors have correct dimension ({verification['expected_dimension']})")
        print(f"   Verified sample: {verification['sample_size']} vectors")
    else:
        print(f"   ❌ Dimension mismatches found!")
        print(f"   Issues: {verification['issues_found']}")
        for issue in verification['issues'][:5]:
            print(f"      Point {issue['point_id']}: {issue['actual']} (expected {issue['expected']})")


def print_all_collections_summary():
    """Print summary of all collections"""
    print_header("All Collections Summary")
    
    all_stats = qdrant_service.get_all_collections_stats()
    
    if not all_stats:
        print("No collections found or error retrieving stats")
        return
    
    # Table header
    print(f"\n{'Collection':<25} {'Vectors':>12} {'Storage (MB)':>15} {'Dimension':>12}")
    print(f"{'-'*25} {'-'*12} {'-'*15} {'-'*12}")
    
    # Collection rows
    total_vectors = 0
    total_mb = 0
    
    for name, stats in all_stats.items():
        if not stats.get('error'):
            vectors = stats['vectors_count']
            storage = stats['storage_estimate_mb']
            dimension = stats['vector_size']
            
            print(f"{name:<25} {vectors:>12,} {storage:>15.2f} {dimension:>12}")
            
            total_vectors += vectors
            total_mb += storage
    
    # Totals
    print(f"{'-'*25} {'-'*12} {'-'*15} {'-'*12}")
    print(f"{'TOTAL':<25} {total_vectors:>12,} {total_mb:>15.2f}")
    
    # Free tier info
    total_gb = total_mb / 1024
    usage_pct = (total_mb / 1024) * 100
    
    print(f"\n📊 Free Tier Usage: {usage_pct:.2f}% ({total_gb:.3f} GB / 1.0 GB)")


def print_optimization_recommendations(num_vectors: int = 50000):
    """Print optimization recommendations for expected vectors"""
    print_header("Optimization Recommendations")
    
    print(f"\nAssuming {num_vectors:,} total vectors across all collections:")
    
    # Compare dimensions
    comparison = storage_calculator.compare_dimensions(num_vectors)
    
    print(f"\n{'Dimension':<12} {'Storage (MB)':>15} {'Storage (GB)':>15} {'Free Tier %':>15}")
    print(f"{'-'*12} {'-'*15} {'-'*15} {'-'*15}")
    
    for dim, data in sorted(comparison.items()):
        print(f"{dim:<12} {data['total_mb']:>15.2f} {data['total_gb']:>15.3f} {data['percent_of_free_tier']:>15.2f}%")
    
    # Get recommendation
    recommendation = storage_calculator.optimize_dimension_recommendation(
        num_vectors=num_vectors,
        current_dimension=768,
        target_usage_percent=70.0
    )
    
    print(f"\n💡 Recommendation:")
    print(f"   {recommendation['recommendation']}")
    
    if recommendation['needs_optimization']:
        print(f"\n   Current: {recommendation['current_dimension']}-dim = {recommendation['current_storage_mb']:.2f} MB ({recommendation['current_usage_percent']:.1f}%)")
        print(f"   Optimal: {recommendation['optimal_dimension']}-dim = {recommendation['optimal_storage_mb']:.2f} MB ({recommendation['optimal_usage_percent']:.1f}%)")
        print(f"   Savings: {recommendation['storage_saved_mb']:.2f} MB")


def print_capacity_forecast():
    """Print capacity forecast"""
    print_header("Capacity Forecast")
    
    # Get current usage
    usage = qdrant_service.calculate_storage_usage()
    current_mb = usage['total_storage_mb']
    remaining_mb = usage['remaining_mb']
    
    print(f"\nCurrent Usage: {current_mb:.2f} MB ({usage['usage_percentage']:.2f}%)")
    print(f"Remaining: {remaining_mb:.2f} MB ({usage['remaining_gb']:.3f} GB)")
    
    # Calculate capacities for different dimensions
    print(f"\n{'Dimension':<12} {'Can Add Vectors':>20} {'Can Add Cities':>20}")
    print(f"{'-'*12} {'-'*20} {'-'*20}")
    
    for dim in [384, 512, 768, 1024]:
        capacity = storage_calculator.calculate_free_tier_capacity(dim, current_mb)
        remaining_vectors = capacity['remaining_vectors']
        remaining_cities = capacity['remaining_cities']
        
        print(f"{dim:<12} {remaining_vectors:>20,} {remaining_cities:>20}")
    
    # Warnings
    if usage['usage_percentage'] > 80:
        print(f"\n⚠️  WARNING: You are at {usage['usage_percentage']:.1f}% capacity")
        print(f"   Consider optimization or cleanup before adding more data")


def interactive_menu():
    """Display interactive menu"""
    while True:
        print_header("Qdrant Collection Dashboard", 80)
        print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\nOptions:")
        print(f"  1. View all collections summary")
        print(f"  2. View specific collection health")
        print(f"  3. View optimization recommendations")
        print(f"  4. View capacity forecast")
        print(f"  5. Run full health check")
        print(f"  0. Exit")
        
        choice = input(f"\nEnter choice (0-5): ").strip()
        
        if choice == "0":
            print(f"\n👋 Goodbye!")
            break
        elif choice == "1":
            print_all_collections_summary()
        elif choice == "2":
            collection = input(f"Enter collection name (default: local_discovery): ").strip() or "local_discovery"
            print_collection_health(collection)
        elif choice == "3":
            vectors = input(f"Expected total vectors (default: 50000): ").strip()
            vectors = int(vectors) if vectors else 50000
            print_optimization_recommendations(vectors)
        elif choice == "4":
            print_capacity_forecast()
        elif choice == "5":
            print_all_collections_summary()
            print_capacity_forecast()
            print_optimization_recommendations()
        else:
            print(f"\n❌ Invalid choice")
        
        input(f"\nPress Enter to continue...")


def main():
    """Main dashboard function"""
    parser = argparse.ArgumentParser(description="Qdrant Collection Health Dashboard")
    parser.add_argument(
        "--collection",
        type=str,
        help="Specific collection to analyze"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Launch interactive menu"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show summary of all collections"
    )
    
    args = parser.parse_args()
    
    try:
        if args.interactive:
            interactive_menu()
        elif args.collection:
            print_collection_health(args.collection)
        elif args.summary:
            print_all_collections_summary()
        else:
            # Default: show everything
            print_all_collections_summary()
            print_capacity_forecast()
            print_optimization_recommendations()
    
    except KeyboardInterrupt:
        print(f"\n\n👋 Interrupted by user")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
