"""
Create geospatial index on MongoDB POI collection

This enables efficient location-based queries like:
- Find POIs within X km radius
- Find nearest POIs to a location

Run with: python scripts/create_geo_index.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.core.mongo import connect_to_mongo, get_database
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_geospatial_indexes():
    """Create geospatial and other useful indexes on POI collections"""
    
    logger.info("="*70)
    logger.info("Creating MongoDB Geospatial Indexes")
    logger.info("="*70)
    
    # Connect to MongoDB
    await connect_to_mongo()
    db = get_database()
    
    # 1. OSM POIs Collection
    logger.info("\n📍 Creating indexes on 'osm_pois' collection...")
    
    try:
        # Geospatial index (2dsphere) on location field
        await db.pois.create_index([("location", "2dsphere")])
        logger.info("   ✅ Created 2dsphere index on 'location'")
        
        # City index for filtering
        await db.pois.create_index("city")
        logger.info("   ✅ Created index on 'city'")
        
        # Category index for filtering
        await db.pois.create_index("category")
        logger.info("   ✅ Created index on 'category'")
        
        # Tags index for filtering
        await db.pois.create_index("tags.amenity")
        logger.info("   ✅ Created index on 'tags.amenity'")
        
        await db.pois.create_index("tags.cuisine")
        logger.info("   ✅ Created index on 'tags.cuisine'")
        
        # Opening hours index
        await db.pois.create_index("tags.opening_hours")
        logger.info("   ✅ Created index on 'tags.opening_hours'")
        
        # Compound index for common queries
        await db.pois.create_index([("city", 1), ("category", 1)])
        logger.info("   ✅ Created compound index on 'city' + 'category'")
        
    except Exception as e:
        logger.error(f"   ❌ Error creating indexes on osm_pois: {e}")
    
    # 2. Foursquare Tips Collection
    logger.info("\n📍 Creating indexes on 'foursquare_tips' collection...")
    
    try:
        # Geospatial index on location
        await db.foursquare_tips.create_index([("location", "2dsphere")])
        logger.info("   ✅ Created 2dsphere index on 'location'")
        
        # City index
        await db.foursquare_tips.create_index("city")
        logger.info("   ✅ Created index on 'city'")
        
        # POI ID reference
        await db.foursquare_tips.create_index("poi_id")
        logger.info("   ✅ Created index on 'poi_id'")
        
    except Exception as e:
        logger.error(f"   ❌ Error creating indexes on foursquare_tips: {e}")
    
    # 3. Blog Posts Collection
    logger.info("\n📍 Creating indexes on 'blog_posts' collection...")
    
    try:
        # City index
        await db.blog_posts.create_index("city")
        logger.info("   ✅ Created index on 'city'")
        
        # Source index
        await db.blog_posts.create_index("source")
        logger.info("   ✅ Created index on 'source'")
        
        # Published date index
        await db.blog_posts.create_index("published_date")
        logger.info("   ✅ Created index on 'published_date'")
        
    except Exception as e:
        logger.error(f"   ❌ Error creating indexes on blog_posts: {e}")
    
    # 4. List all indexes
    logger.info("\n" + "="*70)
    logger.info("📊 Current Indexes Summary")
    logger.info("="*70)
    
    for collection_name in ["osm_pois", "foursquare_tips", "blog_posts"]:
        try:
            collection = db[collection_name]
            indexes = await collection.list_indexes().to_list(None)
            
            logger.info(f"\n{collection_name}:")
            for idx in indexes:
                idx_name = idx.get('name', 'unknown')
                idx_keys = idx.get('key', {})
                logger.info(f"   • {idx_name}: {dict(idx_keys)}")
        except Exception as e:
            logger.error(f"   ❌ Error listing indexes for {collection_name}: {e}")
    
    logger.info("\n" + "="*70)
    logger.info("✅ Geospatial indexes created successfully!")
    logger.info("="*70)


if __name__ == "__main__":
    try:
        asyncio.run(create_geospatial_indexes())
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
