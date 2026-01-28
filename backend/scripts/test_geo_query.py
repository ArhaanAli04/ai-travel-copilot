"""
Test geospatial query directly
"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.core.mongo import connect_to_mongo, get_database
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_geo_query():
    """Test geospatial query"""
    
    await connect_to_mongo()
    db = get_database()
    
    logger.info("="*70)
    logger.info("Testing Geospatial Query")
    logger.info("="*70)
    
    # Test location: Bandra, Mumbai
    lat = 19.0596
    lon = 72.8295
    radius_km = 2.0
    
    logger.info(f"\nQuery parameters:")
    logger.info(f"  Location: ({lat}, {lon})")
    logger.info(f"  Radius: {radius_km} km")
    logger.info(f"  City: mumbai")
    
    # Test 1: Count all POIs in Mumbai
    total_mumbai = await db.pois.count_documents({"city": "mumbai"})
    logger.info(f"\nTotal POIs in Mumbai: {total_mumbai}")
    
    # Test 2: Simple geo query (no city filter)
    query_simple = {
        "location": {
            "$near": {
                "$geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat]
                },
                "$maxDistance": radius_km * 1000  # km to meters
            }
        }
    }
    
    logger.info(f"\nTest 1: Simple geo query (no city filter)")
    try:
        cursor = db.pois.find(query_simple).limit(5)
        results = await cursor.to_list(length=5)
        logger.info(f"  Found: {len(results)} POIs")
        
        if results:
            for poi in results[:3]:
                logger.info(f"    - {poi['name']} ({poi.get('city', 'N/A')})")
    except Exception as e:
        logger.error(f"  ❌ Error: {e}")
    
    # Test 3: Geo query with city filter
    query_with_city = {
        "city": "mumbai",
        "location": {
            "$near": {
                "$geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat]
                },
                "$maxDistance": radius_km * 1000
            }
        }
    }
    
    logger.info(f"\nTest 2: Geo query with city filter")
    try:
        cursor = db.pois.find(query_with_city).limit(5)
        results = await cursor.to_list(length=5)
        logger.info(f"  Found: {len(results)} POIs")
        
        if results:
            for poi in results[:3]:
                logger.info(f"    - {poi['name']} in {poi.get('city', 'N/A')}")
    except Exception as e:
        logger.error(f"  ❌ Error: {e}")
    
    # Test 4: Sample POI location
    sample = await db.pois.find_one({"city": "mumbai"})
    if sample:
        logger.info(f"\nSample POI:")
        logger.info(f"  Name: {sample['name']}")
        logger.info(f"  Location: {sample['location']}")
        
        # Calculate distance manually
        from app.utils.geo_utils import calculate_distance
        poi_lat = sample['location']['coordinates'][1]
        poi_lon = sample['location']['coordinates'][0]
        
        distance = calculate_distance(lat, lon, poi_lat, poi_lon)
        logger.info(f"  Distance from Bandra: {distance:.2f} km")
    
    logger.info("\n" + "="*70)


if __name__ == "__main__":
    try:
        asyncio.run(test_geo_query())
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
