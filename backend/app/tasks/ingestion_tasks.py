"""
Background ingestion tasks for OSM POIs and RSS blog content
Scheduled using APScheduler
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import List
from app.services.qdrant_service import qdrant_service
from app.services.alert_service import alert_service
from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# TASK WRAPPERS (call existing ingestion scripts)
# ============================================================================

async def ingest_osm_task(cities: List[str] = None):
    """
    Background task: Ingest OSM POIs for specified cities
    
    ✨ ENHANCED: Now includes storage monitoring and failure alerts
    """
    if cities is None:
        cities = settings.osm_cities_list
    
    start_time = datetime.now(timezone.utc)
    logger.info(f"🔄 Starting scheduled OSM ingestion for cities: {cities}")
    
    # ✨ NEW: Check storage before ingestion
    storage = qdrant_service.calculate_storage_usage()
    logger.info(f"📊 Current storage: {storage['total_storage_mb']:.2f} MB ({storage['usage_percentage']:.1f}%)")
    
    if storage['usage_percentage'] > 90:
        error_msg = f"Storage usage at {storage['usage_percentage']:.1f}% - aborting ingestion"
        logger.error(f"❌ {error_msg}")
        
        # Send alert
        if settings.ALERTS_ENABLED and settings.alert_recipients_list:
            await alert_service.send_ingestion_failure_alert(
                to_emails=settings.alert_recipients_list,
                job_name="OSM POI Ingestion",
                error_message=error_msg,
                cities=cities
            )
        return
    
    # Import the ingestion function
    from scripts.ingest_osm_pois import ingest_city_pois
    
    success_count = 0
    failed_cities = []
    error_messages = []
    
    for city in cities:
        try:
            logger.info(f"  Processing {city}...")
            await ingest_city_pois(city, categories=None)
            success_count += 1
            logger.info(f"  ✅ Completed {city}")
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"  ❌ Failed to ingest {city}: {error_msg}")
            failed_cities.append(city)
            error_messages.append(f"{city}: {error_msg}")
    
    # ✨ NEW: Log storage after ingestion
    storage_after = qdrant_service.calculate_storage_usage()
    logger.info(f"📊 Storage after ingestion: {storage_after['total_storage_mb']:.2f} MB ({storage_after['usage_percentage']:.1f}%)")
    
    # Summary
    duration = (datetime.now(timezone.utc) - start_time).total_seconds()
    logger.info(f"📊 OSM Ingestion Summary:")
    logger.info(f"   Total cities: {len(cities)}")
    logger.info(f"   Successful: {success_count}")
    logger.info(f"   Failed: {len(failed_cities)}")
    if failed_cities:
        logger.info(f"   Failed cities: {', '.join(failed_cities)}")
    logger.info(f"   Duration: {duration:.1f}s")
    logger.info(f"   Storage used: {storage_after['total_storage_mb']:.2f} MB")
    logger.info(f"✅ Scheduled OSM ingestion completed")
    
    # ✨ NEW: Send failure alert if needed
    if failed_cities and settings.ALERTS_ENABLED and settings.alert_recipients_list:
        await alert_service.send_ingestion_failure_alert(
            to_emails=settings.alert_recipients_list,
            job_name="OSM POI Ingestion",
            error_message="\n".join(error_messages),
            cities=failed_cities
        )


async def ingest_rss_task(cities: List[str] = None, days_back: int = None):
    """
    Background task: Ingest blog posts from RSS feeds
    
    ✨ ENHANCED: Now includes storage monitoring and failure alerts
    """
    if cities is None:
        cities = settings.rss_cities_list
    
    if days_back is None:
        days_back = settings.RSS_INGESTION_DAYS_BACK
    
    start_time = datetime.now(timezone.utc)
    logger.info(f"🔄 Starting scheduled RSS ingestion for cities: {cities} (last {days_back} days)")
    
    # ✨ NEW: Check storage before ingestion
    storage = qdrant_service.calculate_storage_usage()
    logger.info(f"📊 Current storage: {storage['total_storage_mb']:.2f} MB ({storage['usage_percentage']:.1f}%)")
    
    if storage['usage_percentage'] > 90:
        error_msg = f"Storage usage at {storage['usage_percentage']:.1f}% - aborting ingestion"
        logger.error(f"❌ {error_msg}")
        
        # Send alert
        if settings.ALERTS_ENABLED and settings.alert_recipients_list:
            await alert_service.send_ingestion_failure_alert(
                to_emails=settings.alert_recipients_list,
                job_name="RSS Blog Ingestion",
                error_message=error_msg,
                cities=cities
            )
        return
    
    # Import the ingestion function
    from scripts.ingest_blog_content import ingest_city_blogs
    
    success_count = 0
    failed_cities = []
    error_messages = []
    
    for city in cities:
        try:
            logger.info(f"  Processing {city}...")
            await ingest_city_blogs(
                city=city,
                days_back=days_back,
                include_general=True
            )
            success_count += 1
            logger.info(f"  ✅ Completed {city}")
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"  ❌ Failed to ingest {city}: {error_msg}")
            failed_cities.append(city)
            error_messages.append(f"{city}: {error_msg}")
    
    # ✨ NEW: Log storage after ingestion
    storage_after = qdrant_service.calculate_storage_usage()
    logger.info(f"📊 Storage after ingestion: {storage_after['total_storage_mb']:.2f} MB ({storage_after['usage_percentage']:.1f}%)")
    
    # Summary
    duration = (datetime.now(timezone.utc) - start_time).total_seconds()
    logger.info(f"📊 RSS Ingestion Summary:")
    logger.info(f"   Total cities: {len(cities)}")
    logger.info(f"   Successful: {success_count}")
    logger.info(f"   Failed: {len(failed_cities)}")
    if failed_cities:
        logger.info(f"   Failed cities: {', '.join(failed_cities)}")
    logger.info(f"   Duration: {duration:.1f}s")
    logger.info(f"   Storage used: {storage_after['total_storage_mb']:.2f} MB")
    logger.info(f"✅ Scheduled RSS ingestion completed")
    
    # ✨ NEW: Send failure alert if needed
    if failed_cities and settings.ALERTS_ENABLED and settings.alert_recipients_list:
        await alert_service.send_ingestion_failure_alert(
            to_emails=settings.alert_recipients_list,
            job_name="RSS Blog Ingestion",
            error_message="\n".join(error_messages),
            cities=failed_cities
        )


# ============================================================================
# SYNCHRONOUS WRAPPERS (required by APScheduler)
# ============================================================================

def run_osm_ingestion():
    """Sync wrapper for OSM ingestion (called by APScheduler)"""
    try:
        asyncio.run(ingest_osm_task())
    except Exception as e:
        logger.error(f"❌ OSM scheduled job failed: {e}")


def run_rss_ingestion():
    """Sync wrapper for RSS ingestion (called by APScheduler)"""
    try:
        asyncio.run(ingest_rss_task())
    except Exception as e:
        logger.error(f"❌ RSS scheduled job failed: {e}")
