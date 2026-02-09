"""
Pydantic schemas for Admin API endpoints
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============================================================================
# Existing Schemas (migrated from admin.py)
# ============================================================================

class IngestCityRequest(BaseModel):
    """Request to ingest OSM POIs for a city"""
    city: str = Field(..., description="City name", example="mumbai")
    categories: Optional[List[str]] = Field(
        default=None, 
        description="Optional categories to ingest (restaurant, cafe, etc.)"
    )


class IngestCityResponse(BaseModel):
    """Response after triggering city ingestion"""
    message: str
    city: str
    status: str


class EnrichFoursquareRequest(BaseModel):
    """Request to enrich POIs with Foursquare data"""
    city: str = Field(..., description="City name", example="mumbai")
    limit: Optional[int] = Field(
        default=None, 
        description="Maximum number of POIs to enrich"
    )
    categories: Optional[List[str]] = Field(
        default=None,
        description="Optional categories to enrich"
    )


class IngestBlogRequest(BaseModel):
    """Request to ingest blog posts from RSS feeds"""
    city: str = Field(..., description="City name", example="mumbai")
    days_back: Optional[int] = Field(
        default=7, 
        description="Number of days back to fetch blog posts"
    )
    include_general: Optional[bool] = Field(
        default=True,
        description="Include general India travel blogs"
    )


# ============================================================================
# New Scheduler Schemas (Day 28)
# ============================================================================

class TriggerIngestionRequest(BaseModel):
    """Request to manually trigger a scheduled ingestion job"""
    source: str = Field(
        ..., 
        description="Ingestion source type",
        example="osm"
    )
    cities: Optional[List[str]] = Field(
        default=None,
        description="List of cities to ingest (overrides config defaults)",
        example=["mumbai", "goa"]
    )
    days_back: Optional[int] = Field(
        default=None,
        description="For RSS ingestion: days to look back (overrides config default)",
        example=7
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "source": "osm",
                "cities": ["mumbai", "goa"]
            }
        }


class TriggerIngestionResponse(BaseModel):
    """Response after triggering manual ingestion"""
    message: str = Field(..., description="Status message")
    source: str = Field(..., description="Ingestion source (osm or rss)")
    cities: List[str] = Field(..., description="Cities being processed")
    status: str = Field(..., description="Job status (triggered, running, etc.)")


class ScheduledJobInfo(BaseModel):
    """Information about a scheduled job"""
    id: str = Field(..., description="Job ID")
    name: str = Field(..., description="Human-readable job name")
    next_run_time: Optional[str] = Field(
        None, 
        description="Next scheduled run time (ISO format)"
    )
    trigger: str = Field(..., description="Trigger configuration (cron expression)")


class SchedulerStatusResponse(BaseModel):
    """Current status of the background scheduler"""
    is_running: bool = Field(..., description="Whether scheduler is active")
    total_jobs: int = Field(..., description="Total number of scheduled jobs")
    timezone: Optional[str] = Field(
        default=None,
        description="Scheduler timezone"
    )
    jobs: List[ScheduledJobInfo] = Field(
        default=[],
        description="List of scheduled jobs with details"
    )


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    message: str
