"""
Monitor Qdrant storage usage and generate alerts

Run with:
    python scripts/monitor_storage.py
    python scripts/monitor_storage.py --detailed
    python scripts/monitor_storage.py --alert-threshold 75
"""
import sys
import os
from pathlib import Path
import argparse
from datetime import datetime
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.qdrant_service import qdrant_service
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def format_bytes(bytes_value: float) -> str:
    """Format bytes into human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} TB"


def print_collection_stats(stats: dict, detailed: bool = False):
    """Print formatted collection statistics"""
    print(f"\n{'='*70}")
    print(f"📊 Collection: {stats['collection_name']}")
    print(f"{'='*70}")
    print(f"Vectors: {stats['vectors_count']:,}")
    print(f"Indexed: {stats.get('indexed_vectors_count', 0):,}")
    print(f"Dimension: {stats['vector_size']}")
    print(f"Storage: {stats['storage_estimate_mb']:.2f} MB ({stats['storage_estimate_gb']:.3f} GB)")
    print(f"Status: {stats.get('status', 'unknown')}")
    print(f"Segments: {stats.get('segments_count', 0)}")
    
    if detailed and stats.get('payload_schema'):
        print(f"\nPayload Schema:")
        for field, schema in stats['payload_schema'].items():
            print(f"  - {field}: {schema}")


def print_storage_summary(usage: dict, alert_threshold: float = 80.0):
    """Print storage usage summary with alerts"""
    print(f"\n{'='*70}")
    print(f"🗄️  TOTAL STORAGE USAGE")
    print(f"{'='*70}")
    print(f"Total Vectors: {usage['total_vectors']:,}")
    print(f"Total Storage: {usage['total_storage_mb']:.2f} MB ({usage['total_storage_gb']:.3f} GB)")
    print(f"Free Tier Limit: {usage['free_tier_limit_gb']:.1f} GB")
    print(f"Usage: {usage['usage_percentage']:.2f}%")
    print(f"Remaining: {usage['remaining_mb']:.2f} MB ({usage['remaining_gb']:.3f} GB)")
    
    # Alert logic
    usage_pct = usage['usage_percentage']
    
    if usage_pct > 100:
        print(f"\n❌ CRITICAL: Storage limit exceeded!")
        print(f"   You are over the free tier limit by {usage_pct - 100:.2f}%")
    elif usage_pct > alert_threshold:
        print(f"\n⚠️  WARNING: Approaching storage limit!")
        print(f"   You are at {usage_pct:.2f}% of the free tier limit")
        print(f"   Consider:")
        print(f"   • Reducing vector dimensions (768 → 384)")
        print(f"   • Removing old/unused vectors")
        print(f"   • Upgrading to paid tier")
    else:
        print(f"\n✅ Storage usage is healthy ({usage_pct:.2f}%)")


def estimate_capacity(usage: dict):
    """Estimate how many more vectors can be added"""
    remaining_mb = usage['remaining_mb']
    
    # Estimate for 768-dim vectors
    bytes_per_vector_768 = (768 * 4) + 1024  # vector + metadata
    mb_per_vector_768 = bytes_per_vector_768 / (1024 * 1024)
    capacity_768 = int(remaining_mb / mb_per_vector_768)
    
    # Estimate for 384-dim vectors
    bytes_per_vector_384 = (384 * 4) + 1024
    mb_per_vector_384 = bytes_per_vector_384 / (1024 * 1024)
    capacity_384 = int(remaining_mb / mb_per_vector_384)
    
    print(f"\n{'='*70}")
    print(f"📈 CAPACITY ESTIMATE")
    print(f"{'='*70}")
    print(f"Remaining space: {remaining_mb:.2f} MB")
    print(f"\nCan still add approximately:")
    print(f"  • {capacity_768:,} vectors (768-dim)")
    print(f"  • {capacity_384:,} vectors (384-dim)")
    
    # POI estimates
    avg_pois_per_city = 1500
    cities_768 = capacity_768 // avg_pois_per_city
    cities_384 = capacity_384 // avg_pois_per_city
    
    print(f"\nIn terms of cities (~1,500 POIs each):")
    print(f"  • {cities_768} more cities (768-dim)")
    print(f"  • {cities_384} more cities (384-dim)")


def verify_all_dimensions():
    """Verify vector dimensions across all collections"""
    print(f"\n{'='*70}")
    print(f"🔍 VECTOR DIMENSION VERIFICATION")
    print(f"{'='*70}")
    
    all_stats = qdrant_service.get_all_collections_stats()
    
    for collection_name in all_stats.keys():
        verification = qdrant_service.verify_vector_dimensions(collection_name)
        
        if verification.get('error'):
            print(f"\n❌ {collection_name}: Error - {verification['error']}")
            continue
        
        status = "✅" if verification['verified'] else "❌"
        print(f"\n{status} {collection_name}")
        print(f"   Expected dimension: {verification['expected_dimension']}")
        print(f"   Sample size: {verification['sample_size']}")
        
        if not verification['verified']:
            print(f"   ⚠️  Issues found: {verification['issues_found']}")
            for issue in verification['issues'][:3]:
                print(f"      Point {issue['point_id']}: {issue['actual']} dims (expected {issue['expected']})")


def save_report(usage: dict, filename: str = "storage_report.json"):
    """Save storage report to JSON file"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_vectors": usage['total_vectors'],
            "total_storage_mb": usage['total_storage_mb'],
            "total_storage_gb": usage['total_storage_gb'],
            "usage_percentage": usage['usage_percentage'],
            "remaining_mb": usage['remaining_mb'],
        },
        "collections": usage['collections']
    }
    
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    filepath = reports_dir / filename
    with open(filepath, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"✅ Report saved to {filepath}")


def main():
    """Main monitoring function"""
    parser = argparse.ArgumentParser(description="Monitor Qdrant storage usage")
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed collection information"
    )
    parser.add_argument(
        "--alert-threshold",
        type=float,
        default=80.0,
        help="Alert threshold percentage (default: 80)"
    )
    parser.add_argument(
        "--verify-dimensions",
        action="store_true",
        help="Verify vector dimensions across collections"
    )
    parser.add_argument(
        "--save-report",
        action="store_true",
        help="Save report to JSON file"
    )
    parser.add_argument(
        "--estimate-impact",
        type=int,
        metavar="NUM_VECTORS",
        help="Estimate impact of adding N vectors"
    )
    
    args = parser.parse_args()
    
    print(f"\n{'='*70}")
    print(f"🗄️  QDRANT STORAGE MONITOR")
    print(f"{'='*70}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Qdrant URL: {settings.QDRANT_URL}")
    
    try:
        # Get storage usage
        usage = qdrant_service.calculate_storage_usage()
        
        # Print per-collection stats
        if args.detailed:
            for collection_name, stats in usage['collections'].items():
                if not stats.get('error'):
                    print_collection_stats(stats, detailed=True)
        
        # Print summary
        print_storage_summary(usage, args.alert_threshold)
        
        # Estimate remaining capacity
        estimate_capacity(usage)
        
        # Verify dimensions if requested
        if args.verify_dimensions:
            verify_all_dimensions()
        
        # Estimate ingestion impact if requested
        if args.estimate_impact:
            print(f"\n{'='*70}")
            print(f"🔮 INGESTION IMPACT ESTIMATE")
            print(f"{'='*70}")
            
            impact = qdrant_service.estimate_ingestion_impact(args.estimate_impact)
            
            print(f"Adding: {impact['num_vectors_to_add']:,} vectors ({impact['vector_dimension']}-dim)")
            print(f"New storage: {impact['new_storage_mb']:.2f} MB")
            print(f"Current total: {impact['current_storage_mb']:.2f} MB")
            print(f"Projected total: {impact['projected_storage_mb']:.2f} MB")
            print(f"Projected usage: {impact['projected_usage_percentage']:.2f}%")
            
            if impact['warning']:
                print(f"\n{impact['warning']}")
            else:
                print(f"\n✅ Safe to ingest")
        
        # Save report if requested
        if args.save_report:
            save_report(usage)
        
        # Exit with error code if over threshold
        if usage['usage_percentage'] > args.alert_threshold:
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"❌ Error monitoring storage: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
