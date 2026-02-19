"""
Enhanced health check and monitoring endpoints
"""
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
import logging

from app.schemas.monitoring import (
    HealthCheckResponse,
    MonitoringResponse,
    StorageMonitoring,
)
from app.services.monitoring_service import monitoring_service
from app.core.config import settings


logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health & Monitoring"])


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Complete System Health Check",
    description="Check health of all services (PostgreSQL, MongoDB, Qdrant, Scheduler)"
)
async def health_check() -> HealthCheckResponse:
    """
    Comprehensive health check for all system components
    
    Returns:
        - Overall system status
        - Individual service health
        - Response times
        - Service-specific details
    """
    try:
        health = await monitoring_service.get_complete_health()
        return health
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Health check failed"
        )


@router.get(
    "/health/storage",
    response_model=StorageMonitoring,
    summary="Storage Monitoring",
    description="Get Qdrant storage usage and free tier monitoring"
)
async def storage_monitoring() -> StorageMonitoring:
    """
    Get detailed storage usage across all Qdrant collections
    
    Returns:
        - Total storage used
        - Per-collection breakdown
        - Free tier usage percentage
        - Remaining capacity
        - Alerts if approaching limits
    """
    try:
        storage = monitoring_service.get_storage_monitoring()
        return storage
    
    except Exception as e:
        logger.error(f"Storage monitoring failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve storage metrics"
        )


@router.get(
    "/health/simple",
    summary="Simple Health Check",
    description="Lightweight health check (for load balancers)"
)
async def simple_health_check() -> Dict[str, Any]:
    """
    Lightweight health check endpoint
    
    Used by load balancers and monitoring tools that need
    a fast response without detailed checks.
    """
    return {
        "status": "ok",
        "service": "ai-travel-copilot",
        "version": "0.1.0",
        "environment": settings.ENV
    }
