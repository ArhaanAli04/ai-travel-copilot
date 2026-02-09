"""
APScheduler service for background job scheduling
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from datetime import datetime, timezone

from app.core.config import settings
from app.tasks.ingestion_tasks import run_osm_ingestion, run_rss_ingestion

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Background job scheduler using APScheduler
    
    Manages scheduled ingestion tasks:
    - Monthly OSM POI ingestion
    - Weekly RSS blog content ingestion
    """
    
    def __init__(self):
        self.scheduler = None
        self.is_running = False
    
    def _job_listener(self, event):
        """Listen to job execution events for logging"""
        if event.exception:
            logger.error(f"❌ Scheduled job failed: {event.job_id}")
            logger.error(f"   Exception: {event.exception}")
        else:
            logger.info(f"✅ Scheduled job completed: {event.job_id}")
    
    def start(self):
        """
        Start the scheduler and register all jobs
        """
        if not settings.SCHEDULER_ENABLED:
            logger.info("⏸️  Scheduler disabled in config")
            return
        
        if self.is_running:
            logger.warning("⚠️  Scheduler already running")
            return
        
        logger.info("🕐 Starting APScheduler...")
        
        # Initialize scheduler
        self.scheduler = BackgroundScheduler(
            timezone=settings.SCHEDULER_TIMEZONE,
            daemon=True
        )
        
        # Add job execution listener
        self.scheduler.add_listener(
            self._job_listener,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )
        
        # ============================================================
        # Job 1: Monthly OSM POI Ingestion
        # ============================================================
        osm_trigger = CronTrigger(
            day=settings.OSM_INGESTION_CRON_DAY,
            hour=settings.OSM_INGESTION_CRON_HOUR,
            minute=settings.OSM_INGESTION_CRON_MINUTE,
            timezone=settings.SCHEDULER_TIMEZONE
        )
        
        self.scheduler.add_job(
            func=run_osm_ingestion,
            trigger=osm_trigger,
            id="osm_monthly_ingestion",
            name="Monthly OSM POI Ingestion",
            replace_existing=True,
            max_instances=1,  # Prevent overlapping runs
            misfire_grace_time=3600  # Allow 1 hour grace if server was down
        )
        
        logger.info(f"  ✅ Registered: Monthly OSM ingestion")
        logger.info(f"     Schedule: Day {settings.OSM_INGESTION_CRON_DAY} at {settings.OSM_INGESTION_CRON_HOUR}:{settings.OSM_INGESTION_CRON_MINUTE:02d}")
        logger.info(f"     Cities: {', '.join(settings.osm_cities_list)}")
        
        # ============================================================
        # Job 2: Weekly RSS Blog Ingestion
        # ============================================================
        rss_trigger = CronTrigger(
            day_of_week=settings.RSS_INGESTION_CRON_DAY_OF_WEEK,
            hour=settings.RSS_INGESTION_CRON_HOUR,
            minute=settings.RSS_INGESTION_CRON_MINUTE,
            timezone=settings.SCHEDULER_TIMEZONE
        )
        
        self.scheduler.add_job(
            func=run_rss_ingestion,
            trigger=rss_trigger,
            id="rss_weekly_ingestion",
            name="Weekly RSS Blog Ingestion",
            replace_existing=True,
            max_instances=1,
            misfire_grace_time=3600
        )
        
        logger.info(f"  ✅ Registered: Weekly RSS ingestion")
        logger.info(f"     Schedule: Every {settings.RSS_INGESTION_CRON_DAY_OF_WEEK} at {settings.RSS_INGESTION_CRON_HOUR}:{settings.RSS_INGESTION_CRON_MINUTE:02d}")
        logger.info(f"     Cities: {', '.join(settings.rss_cities_list)}")
        
        # Start the scheduler
        self.scheduler.start()
        self.is_running = True
        
        logger.info("✅ Scheduler started successfully")
        logger.info(f"   Timezone: {settings.SCHEDULER_TIMEZONE}")
        logger.info(f"   Total jobs: {len(self.scheduler.get_jobs())}")
        
        # Print next run times
        self._print_next_runs()
    
    def shutdown(self):
        """Stop the scheduler"""
        if self.scheduler and self.is_running:
            logger.info("🛑 Shutting down scheduler...")
            self.scheduler.shutdown(wait=False)
            self.is_running = False
            logger.info("✅ Scheduler shut down")
    
    def get_jobs(self):
        """Get all scheduled jobs"""
        if not self.scheduler:
            return []
        return self.scheduler.get_jobs()
    
    def _print_next_runs(self):
        """Log next run times for all jobs"""
        jobs = self.get_jobs()
        if jobs:
            logger.info("📅 Next scheduled runs:")
            for job in jobs:
                next_run = job.next_run_time
                if next_run:
                    logger.info(f"   • {job.name}: {next_run.strftime('%Y-%m-%d %H:%M:%S %Z')}")


# Global scheduler instance
scheduler_service = SchedulerService()
