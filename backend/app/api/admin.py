"""
Admin API endpoints for data ingestion and management
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks,status
from pydantic import BaseModel
from typing import Optional, List
import subprocess
import sys
from pathlib import Path
import logging

from app.schemas.admin import (
    IngestCityRequest,
    IngestCityResponse,
    EnrichFoursquareRequest,
    IngestBlogRequest,
    TriggerIngestionRequest,
    TriggerIngestionResponse,
    SchedulerStatusResponse,
    ScheduledJobInfo,
    HealthCheckResponse
)

from app.schemas.monitoring import MonitoringResponse
from app.services.monitoring_service import monitoring_service
from app.services.alert_service import alert_service
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/ingest-city", response_model=IngestCityResponse)
async def ingest_city(
    request: IngestCityRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger OSM POI ingestion for a specific city
    
    This endpoint runs the ingestion script in the background.
    TODO: Add authentication middleware for admin-only access
    """
    # Validate city
    valid_cities = ["mumbai", "goa", "delhi"]
    if request.city.lower() not in valid_cities:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid city. Valid options: {valid_cities}"
        )
    
    # Add background task to run ingestion script
    background_tasks.add_task(
        run_ingestion_script,
        request.city,
        request.categories
    )
    
    logger.info(f"🚀 Started background ingestion for {request.city}")
    
    return IngestCityResponse(
        message=f"Ingestion started for {request.city}. Check logs for progress.",
        city=request.city,
        status="processing"
    )

#  NEW ENDPOINT
@router.post("/enrich-city-foursquare", response_model=IngestCityResponse)
async def enrich_city_foursquare(
    request: EnrichFoursquareRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger Foursquare enrichment for a city's POIs
    """
    valid_cities = ["mumbai", "goa", "delhi", "bangalore", "pune"]
    if request.city.lower() not in valid_cities:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid city. Valid options: {valid_cities}"
        )
    
    background_tasks.add_task(
        run_foursquare_enrichment,
        request.city,
        request.limit,
        request.categories
    )
    
    logger.info(f"🚀 Started Foursquare enrichment for {request.city}")
    
    return IngestCityResponse(
        message=f"Foursquare enrichment started for {request.city}",
        city=request.city,
        status="processing"
    )

#  ADD THIS ENDPOINT
@router.post("/ingest-blogs", response_model=IngestCityResponse)
async def ingest_blogs(
    request: IngestBlogRequest,
    background_tasks: BackgroundTasks
):
    """Trigger blog RSS ingestion for a city"""
    valid_cities = ["mumbai", "delhi", "goa", "bangalore", "pune"]
    if request.city.lower() not in valid_cities:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid city. Valid options: {valid_cities}"
        )
    
    background_tasks.add_task(
        run_blog_ingestion,
        request.city,
        request.days_back,
        request.include_general
    )
    
    logger.info(f"🚀 Started blog ingestion for {request.city}")
    
    return IngestCityResponse(
        message=f"Blog ingestion started for {request.city}",
        city=request.city,
        status="processing"
    )

# ============================================================================
# New Scheduler Endpoints (Day 28)
# ============================================================================

@router.post("/trigger-ingestion", response_model=TriggerIngestionResponse)
async def trigger_ingestion(
    request: TriggerIngestionRequest,
    background_tasks: BackgroundTasks
):
    """
    Manually trigger a scheduled ingestion job
    
    Bypasses the scheduler and runs the job immediately in the background.
    
    **Supported Sources:**
    - `osm`: OpenStreetMap POI ingestion
    - `rss`: Blog RSS feed ingestion
    
    **Examples:**
    
    Trigger OSM ingestion:
    ```json
    {
        "source": "osm",
        "cities": ["mumbai", "goa"]
    }
    ```
    
    Trigger RSS ingestion:
    ```json
    {
        "source": "rss",
        "cities": ["mumbai"],
        "days_back": 7
    }
    ```
    """
    from app.core.config import settings
    
    # Validate source
    if request.source not in ["osm", "rss"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid source. Must be 'osm' or 'rss'"
        )
    
    # Get cities (use provided or default from config)
    if request.cities:
        cities = request.cities
    else:
        if request.source == "osm":
            cities = settings.osm_cities_list
        else:
            cities = settings.rss_cities_list
    
    # Validate cities
    valid_cities = ["mumbai", "goa", "delhi", "bangalore", "pune"]
    invalid_cities = [c for c in cities if c.lower() not in valid_cities]
    if invalid_cities:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid cities: {invalid_cities}. Valid options: {valid_cities}"
        )
    
    # Trigger the appropriate job
    if request.source == "osm":
        background_tasks.add_task(
            trigger_osm_job_manually,
            cities
        )
        logger.info(f"🚀 Manually triggered OSM ingestion for: {', '.join(cities)}")
        message = f"OSM ingestion triggered for {len(cities)} cities"
    
    else:  # rss
        days_back = request.days_back or settings.RSS_INGESTION_DAYS_BACK
        background_tasks.add_task(
            trigger_rss_job_manually,
            cities,
            days_back
        )
        logger.info(f"🚀 Manually triggered RSS ingestion for: {', '.join(cities)} (last {days_back} days)")
        message = f"RSS ingestion triggered for {len(cities)} cities"
    
    return TriggerIngestionResponse(
        message=message,
        source=request.source,
        cities=cities,
        status="triggered"
    )


@router.get("/scheduler/status", response_model=SchedulerStatusResponse)
async def get_scheduler_status():
    """
    Get current scheduler status and list all scheduled jobs
    
    Returns:
    - Whether scheduler is running
    - Total number of jobs
    - Details of each job (name, next run time, trigger config)
    
    **Response Example:**
    ```json
    {
        "is_running": true,
        "total_jobs": 2,
        "timezone": "Asia/Kolkata",
        "jobs": [
            {
                "id": "osm_monthly_ingestion",
                "name": "Monthly OSM POI Ingestion",
                "next_run_time": "2026-03-01T02:00:00+05:30",
                "trigger": "cron[day='1', hour='2', minute='0']"
            }
        ]
    }
    ```
    """
    from app.services.scheduler_service import scheduler_service
    from app.core.config import settings
    
    if not scheduler_service.is_running:
        return SchedulerStatusResponse(
            is_running=False,
            total_jobs=0,
            timezone=None,
            jobs=[]
        )
    
    jobs = scheduler_service.get_jobs()
    
    job_details = []
    for job in jobs:
        job_details.append(
            ScheduledJobInfo(
                id=job.id,
                name=job.name,
                next_run_time=job.next_run_time.isoformat() if job.next_run_time else None,
                trigger=str(job.trigger)
            )
        )
    
    return SchedulerStatusResponse(
        is_running=True,
        total_jobs=len(jobs),
        timezone=settings.SCHEDULER_TIMEZONE,
        jobs=job_details
    )

@router.get(
    "/monitoring",
    response_model=MonitoringResponse,
    summary="Monitoring Dashboard",
    description="Complete monitoring dashboard with health, storage, jobs, and alerts"
)
async def get_monitoring_dashboard() -> MonitoringResponse:
    """
    Get comprehensive monitoring dashboard
    
    Returns:
        - System health status
        - Storage usage and alerts
        - Scheduler job status
        - Active alerts and warnings
    """
    try:
        dashboard = await monitoring_service.get_monitoring_dashboard()
        
        # Check if alerts need to be sent
        if settings.ALERTS_ENABLED and dashboard.alerts:
            await _send_alerts_if_needed(dashboard)
        
        return dashboard
    
    except Exception as e:
        logger.error(f"Failed to get monitoring dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve monitoring data"
        )


async def _send_alerts_if_needed(dashboard: MonitoringResponse):
    """
    Send alerts if critical thresholds are exceeded
    
    This is called automatically by the monitoring endpoint
    """
    if not settings.alert_recipients_list:
        logger.warning("⚠️ No alert recipients configured")
        return
    
    # Check storage alerts
    storage = dashboard.storage
    
    if storage.total_storage_mb > settings.STORAGE_CRITICAL_THRESHOLD_MB:
        logger.warning(f"🚨 CRITICAL: Storage at {storage.usage_percentage:.1f}%")
        
        await alert_service.send_storage_alert(
            to_emails=settings.alert_recipients_list,
            storage_mb=storage.total_storage_mb,
            usage_percentage=storage.usage_percentage,
            collections={k: v.dict() for k, v in storage.collections.items()}
        )
    
    elif storage.total_storage_mb > settings.STORAGE_ALERT_THRESHOLD_MB:
        logger.warning(f"⚠️ WARNING: Storage at {storage.usage_percentage:.1f}%")
        
        # Send alert only once per day (implement cooldown in production)
        await alert_service.send_storage_alert(
            to_emails=settings.alert_recipients_list,
            storage_mb=storage.total_storage_mb,
            usage_percentage=storage.usage_percentage,
            collections={k: v.dict() for k, v in storage.collections.items()}
        )
    
    # Check service health alerts
    for service_name, service_health in dashboard.health.services.items():
        if service_health.status == "unhealthy":
            logger.error(f"🚨 Service down: {service_name}")
            
            await alert_service.send_service_down_alert(
                to_emails=settings.alert_recipients_list,
                service_name=service_health.service_name,
                error_message=service_health.error_message or "Unknown error"
            )


# ============================================================
# NEW: Manual Alert Test Endpoint ✨
# ============================================================

@router.post(
    "/test-alert",
    summary="Test Alert System",
    description="Send a test alert email to configured recipients"
)
async def test_alert_system():
    """
    Send a test alert to verify email configuration
    
    Useful for testing Resend API integration
    """
    if not settings.ALERTS_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alerts are disabled in configuration"
        )
    
    if not settings.alert_recipients_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No alert recipients configured. Set ALERT_EMAIL_RECIPIENTS in .env"
        )
    
    try:
        success = await alert_service.send_email_alert(
            to_emails=settings.alert_recipients_list,
            subject="🧪 Test Alert - AI Travel Copilot",
            message="This is a test alert to verify the email configuration is working correctly.",
            priority="low"
        )
        
        if success:
            return {
                "status": "success",
                "message": f"Test alert sent to {len(settings.alert_recipients_list)} recipients",
                "recipients": settings.alert_recipients_list
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send test alert"
            )
    
    except Exception as e:
        logger.error(f"Test alert failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test alert failed: {str(e)}"
        )


# ============================================================================
# Background Task Helper Functions
# ============================================================================

def run_blog_ingestion(
    city: str,
    days_back: int = 7,
    include_general: bool = True
):
    """Run blog ingestion script"""
    script_path = Path(__file__).parent.parent.parent / "scripts" / "ingest_blog_content.py"
    
    cmd = [sys.executable, str(script_path), city, "--days", str(days_back)]
    
    if not include_general:
        cmd.append("--no-general")
    
    logger.info(f"Running: {' '.join(cmd)}")
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(timeout=600)
        
        if process.returncode == 0:
            logger.info(f"✅ Blog ingestion completed for {city}")
            for line in stdout.split('\n'):
                if any(kw in line for kw in ['fetched', 'Stored', 'Generated', 'Uploaded']):
                    logger.info(f"  {line.strip()}")
        else:
            logger.error(f"❌ Blog ingestion failed for {city}")
            if stderr:
                logger.error(stderr[:500])
    
    except Exception as e:
        logger.error(f"❌ Exception during blog ingestion: {e}")


def run_foursquare_enrichment(
    city: str,
    limit: Optional[int] = None,
    categories: Optional[List[str]] = None
):
    """Run Foursquare enrichment script"""
    script_path = Path(__file__).parent.parent.parent / "scripts" / "enrich_pois_foursquare.py"
    
    cmd = [sys.executable, str(script_path), city]
    
    if limit:
        cmd.extend(["--limit", str(limit)])
    
    if categories:
        cmd.extend(["--categories"] + categories)
    
    logger.info(f"Running: {' '.join(cmd)}")
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(timeout=1800)  # 30 min timeout
        
        if process.returncode == 0:
            logger.info(f"✅ Foursquare enrichment completed for {city}")
            # Log summary
            for line in stdout.split('\n'):
                if any(kw in line for kw in ['enriched', 'updated', 'Failed', 'processed']):
                    logger.info(f"  {line.strip()}")
        else:
            logger.error(f"❌ Foursquare enrichment failed for {city}")
            if stderr:
                logger.error(stderr[:500])
    
    except Exception as e:
        logger.error(f"❌ Exception during Foursquare enrichment: {e}")

def run_ingestion_script(city: str, categories: Optional[List[str]] = None):
    """Run the ingestion script as a subprocess"""
    script_path = Path(__file__).parent.parent.parent / "scripts" / "ingest_osm_pois.py"
    
    cmd = [sys.executable, str(script_path), city]
    
    if categories:
        cmd.extend(["--categories"] + categories)
    
    logger.info(f"Running command: {' '.join(cmd)}")
    
    try:
        # ✅ Better subprocess handling
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        stdout, stderr = process.communicate(timeout=600)
        
        if process.returncode == 0:
            logger.info(f"✅ Ingestion completed for {city}")
            # Log key metrics from output
            if "INGESTION COMPLETE" in stdout:
                for line in stdout.split('\n'):
                    if any(keyword in line for keyword in ['Total POIs', 'Stored', 'Embedded', 'Uploaded']):
                        logger.info(f"  {line.strip()}")
        else:
            logger.error(f"❌ Ingestion failed for {city}")
            if stderr:
                logger.error(f"Error output: {stderr[:500]}")  # First 500 chars
    
    except subprocess.TimeoutExpired:
        logger.error(f"⏱️ Ingestion timeout for {city}")
        process.kill()
    except Exception as e:
        logger.error(f"❌ Ingestion exception for {city}: {e}")

def trigger_osm_job_manually(cities: List[str]):
    """Manually trigger OSM ingestion job"""
    import asyncio
    from app.tasks.ingestion_tasks import ingest_osm_task
    
    try:
        asyncio.run(ingest_osm_task(cities))
        logger.info(f"✅ Manual OSM ingestion completed for: {', '.join(cities)}")
    except Exception as e:
        logger.error(f"❌ Manual OSM ingestion failed: {e}")

def trigger_rss_job_manually(cities: List[str], days_back: int):
    """Manually trigger RSS ingestion job"""
    import asyncio
    from app.tasks.ingestion_tasks import ingest_rss_task
    
    try:
        asyncio.run(ingest_rss_task(cities, days_back))
        logger.info(f"✅ Manual RSS ingestion completed for: {', '.join(cities)}")
    except Exception as e:
        logger.error(f"❌ Manual RSS ingestion failed: {e}")

@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint for admin API"""
    return HealthCheckResponse(
        status="ok",
        message="Admin API is running"
    )
