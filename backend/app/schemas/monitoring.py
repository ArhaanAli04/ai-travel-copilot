"""
Pydantic schemas for monitoring and health check endpoints
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class ServiceHealth(BaseModel):
    """Health status of a service"""
    service_name: str
    status: str = Field(..., description="healthy, degraded, or unhealthy")
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class HealthCheckResponse(BaseModel):
    """Complete health check response"""
    status: str = Field(..., description="Overall system status")
    timestamp: datetime
    services: Dict[str, ServiceHealth]
    version: str = "0.1.0"
    environment: str


class CollectionStats(BaseModel):
    """Statistics for a Qdrant collection"""
    collection_name: str
    vectors_count: int
    storage_mb: float
    storage_gb: float
    status: str


class StorageMonitoring(BaseModel):
    """Storage usage monitoring"""
    total_vectors: int
    total_storage_mb: float
    total_storage_gb: float
    free_tier_limit_gb: float = 1.0
    usage_percentage: float
    remaining_mb: float
    remaining_gb: float
    alert: Optional[str] = None
    collections: Dict[str, CollectionStats]


class IngestionJobStats(BaseModel):
    """Statistics for a background ingestion job"""
    job_id: str
    job_name: str
    next_run_time: Optional[datetime] = None
    last_run_time: Optional[datetime] = None
    status: str


class MonitoringResponse(BaseModel):
    """Complete monitoring dashboard response"""
    timestamp: datetime
    health: HealthCheckResponse
    storage: StorageMonitoring
    scheduler_jobs: List[IngestionJobStats]
    alerts: List[str] = []


class AlertConfig(BaseModel):
    """Alert configuration"""
    storage_threshold_mb: float = 850.0  # Alert at 850 MB (85% of 1GB)
    storage_critical_mb: float = 950.0   # Critical at 950 MB (95% of 1GB)
    email_recipients: List[str] = []
    webhook_url: Optional[str] = None
