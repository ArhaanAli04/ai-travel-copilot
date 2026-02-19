"""
Monitoring service for system health and metrics
"""
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy import text

from app.core.postgres import engine
from app.core.mongo import get_database
from app.core.qdrant import get_qdrant_client
from app.services.qdrant_service import qdrant_service
from app.services.scheduler_service import scheduler_service
from app.schemas.monitoring import (
    ServiceHealth,
    HealthCheckResponse,
    StorageMonitoring,
    CollectionStats,
    IngestionJobStats,
    MonitoringResponse,
)
from app.core.config import settings


logger = logging.getLogger(__name__)


class MonitoringService:
    """Centralized monitoring for all services"""
    
    def __init__(self):
        self.storage_threshold_mb = 850.0  # 85% of 1GB free tier
        self.storage_critical_mb = 950.0   # 95% of 1GB
    
    async def check_postgres_health(self) -> ServiceHealth:
        """Check PostgreSQL connection and response time"""
        start_time = datetime.now()
        
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return ServiceHealth(
                service_name="PostgreSQL",
                status="healthy",
                response_time_ms=round(response_time, 2),
                details={"database": "travel_copilot"}
            )
        
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            return ServiceHealth(
                service_name="PostgreSQL",
                status="unhealthy",
                error_message=str(e)
            )
    
    async def check_mongo_health(self) -> ServiceHealth:
        """Check MongoDB connection and response time"""
        start_time = datetime.now()
        
        try:
            # ✅ CHANGED: Use get_database() function
            database = get_database()
            
            if database is None:
                raise Exception("MongoDB database not initialized")
            
            # Test connection with ping
            await database.command('ping')
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
             # Get collection count
            collections = await database.list_collection_names()
            return ServiceHealth(
                service_name="MongoDB",
                status="healthy",
                response_time_ms=round(response_time, 2),
                details={
                    "database": "travel_copilot",
                    "collections_count": len(collections),
                    "collections": collections
                }
            )
        
        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}")
            return ServiceHealth(
                service_name="MongoDB",
                status="unhealthy",
                error_message=str(e)
            )
    
    async def check_qdrant_health(self) -> ServiceHealth:
        """Check Qdrant connection and response time"""
        start_time = datetime.now()
        
        try:
            client = get_qdrant_client()
            
            # Get collections
            collections = client.get_collections()
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return ServiceHealth(
                service_name="Qdrant",
                status="healthy",
                response_time_ms=round(response_time, 2),
                details={
                    "collections_count": len(collections.collections),
                    "collections": [c.name for c in collections.collections]
                }
            )
        
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return ServiceHealth(
                service_name="Qdrant",
                status="unhealthy",
                error_message=str(e)
            )
    
    async def check_scheduler_health(self) -> ServiceHealth:
        """Check APScheduler status"""
        try:
            if not scheduler_service.is_running:
                return ServiceHealth(
                    service_name="Scheduler",
                    status="unhealthy",
                    error_message="Scheduler is not running"
                )
            
            jobs = scheduler_service.get_jobs()
            
            return ServiceHealth(
                service_name="Scheduler",
                status="healthy",
                details={
                    "jobs_count": len(jobs),
                    "jobs": [{"id": j.id, "name": j.name} for j in jobs]
                }
            )
        
        except Exception as e:
            logger.error(f"Scheduler health check failed: {e}")
            return ServiceHealth(
                service_name="Scheduler",
                status="unhealthy",
                error_message=str(e)
            )
    
    async def get_complete_health(self) -> HealthCheckResponse:
        """Get complete system health status"""
        postgres_health = await self.check_postgres_health()
        mongo_health = await self.check_mongo_health()
        qdrant_health = await self.check_qdrant_health()
        scheduler_health = await self.check_scheduler_health()
        
        services = {
            "postgres": postgres_health,
            "mongodb": mongo_health,
            "qdrant": qdrant_health,
            "scheduler": scheduler_health,
        }
        
        # Determine overall status
        statuses = [s.status for s in services.values()]
        
        if all(s == "healthy" for s in statuses):
            overall_status = "healthy"
        elif any(s == "unhealthy" for s in statuses):
            overall_status = "unhealthy"
        else:
            overall_status = "degraded"
        
        return HealthCheckResponse(
            status=overall_status,
            timestamp=datetime.now(timezone.utc),
            services=services,
            version="0.1.0",
            environment=settings.ENV
        )
    
    def get_storage_monitoring(self) -> StorageMonitoring:
        """Get storage usage across all collections"""
        try:
            storage_data = qdrant_service.calculate_storage_usage()
            
            # Convert to Pydantic models
            collections_stats = {}
            for name, stats in storage_data.get("collections", {}).items():
                collections_stats[name] = CollectionStats(
                    collection_name=name,
                    vectors_count=stats.get("vectors_count", 0),
                    storage_mb=stats.get("storage_estimate_mb", 0),
                    storage_gb=stats.get("storage_estimate_gb", 0),
                    status=stats.get("status", "unknown")
                )
            
            return StorageMonitoring(
                total_vectors=storage_data.get("total_vectors", 0),
                total_storage_mb=storage_data.get("total_storage_mb", 0),
                total_storage_gb=storage_data.get("total_storage_gb", 0),
                free_tier_limit_gb=1.0,
                usage_percentage=storage_data.get("usage_percentage", 0),
                remaining_mb=storage_data.get("remaining_mb", 0),
                remaining_gb=storage_data.get("remaining_gb", 0),
                alert=storage_data.get("alert"),
                collections=collections_stats
            )
        
        except Exception as e:
            logger.error(f"Error getting storage monitoring: {e}")
            return StorageMonitoring(
                total_vectors=0,
                total_storage_mb=0,
                total_storage_gb=0,
                usage_percentage=0,
                remaining_mb=0,
                remaining_gb=0,
                collections={}
            )
    
    def get_scheduler_jobs_stats(self) -> List[IngestionJobStats]:
        """Get scheduler job statistics"""
        try:
            if not scheduler_service.is_running:
                return []
            
            jobs = scheduler_service.get_jobs()
            
            return [
                IngestionJobStats(
                    job_id=job.id,
                    job_name=job.name,
                    next_run_time=job.next_run_time,
                    status="scheduled" if job.next_run_time else "pending"
                )
                for job in jobs
            ]
        
        except Exception as e:
            logger.error(f"Error getting scheduler stats: {e}")
            return []
    
    async def get_monitoring_dashboard(self) -> MonitoringResponse:
        """Get complete monitoring dashboard data"""
        health = await self.get_complete_health()
        storage = self.get_storage_monitoring()
        jobs = self.get_scheduler_jobs_stats()
        
        # Generate alerts
        alerts = []
        
        # Storage alerts
        if storage.total_storage_mb > self.storage_critical_mb:
            alerts.append(
                f"🚨 CRITICAL: Storage at {storage.usage_percentage:.1f}% ({storage.total_storage_mb:.0f} MB). "
                f"Approaching 1GB free tier limit!"
            )
        elif storage.total_storage_mb > self.storage_threshold_mb:
            alerts.append(
                f"⚠️ WARNING: Storage at {storage.usage_percentage:.1f}% ({storage.total_storage_mb:.0f} MB). "
                f"Consider cleanup or upgrade."
            )
        
        # Service health alerts
        for service_name, service_health in health.services.items():
            if service_health.status == "unhealthy":
                alerts.append(
                    f"🚨 CRITICAL: {service_health.service_name} is unhealthy - {service_health.error_message}"
                )
            elif service_health.status == "degraded":
                alerts.append(
                    f"⚠️ WARNING: {service_health.service_name} is degraded"
                )
        
        # Scheduler alerts
        if not scheduler_service.is_running:
            alerts.append("⚠️ WARNING: Background job scheduler is not running")
        
        return MonitoringResponse(
            timestamp=datetime.now(timezone.utc),
            health=health,
            storage=storage,
            scheduler_jobs=jobs,
            alerts=alerts
        )


# Singleton instance
monitoring_service = MonitoringService()
