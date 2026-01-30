"""
Pydantic models for Local Discovery API
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class UserLocation(BaseModel):
    """User location coordinates"""
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")


class UserPreferences(BaseModel):
    """User preferences for recommendations"""
    dietary: Optional[List[str]] = Field(default=None, description="Dietary preferences (vegetarian, vegan, halal, etc.)")
    cuisines: Optional[List[str]] = Field(default=None, description="Preferred cuisines")
    categories: Optional[List[str]] = Field(default=None, description="Preferred categories (restaurant, cafe, museum, etc.)")
    budget: Optional[str] = Field(default=None, description="Budget level (low, moderate, high)")
    time_constraint: Optional[str] = Field(default=None, description="Available time (e.g., '30 minutes', '1-2 hours')")
    group_size: Optional[int] = Field(default=None, description="Number of people")


class SuggestRequest(BaseModel):
    """Request for personalized recommendations"""
    query: str = Field(..., description="User's search query", example="romantic dinner spot")
    user_location: UserLocation = Field(..., description="User's current location")
    city: str = Field(..., description="City name", example="mumbai")
    preferences: Optional[UserPreferences] = Field(default=None, description="User preferences")
    radius_km: Optional[float] = Field(default=5.0, description="Search radius in kilometers", ge=0.1, le=50)
    max_results: Optional[int] = Field(default=5, description="Maximum number of recommendations", ge=1, le=10)


class POIRecommendation(BaseModel):
    """Single POI recommendation"""
    poi_id: str
    name: str
    category: str
    distance_km: float
    distance_text: str
    location: Dict
    address: Optional[str]
    phone: Optional[str]
    website: Optional[str]
    hours: Optional[str]
    tags: Dict
    reason: str = Field(..., description="Why this place is recommended")
    highlights: List[str] = Field(default=[], description="Key features")
    best_for: str = Field(..., description="Best use case")
    relevance_score: Optional[float]
    # Feedback fields (Day 22)
    average_rating: Optional[float] = Field(default=0.0, description="Average user rating (0-5)")
    feedback_count: Optional[int] = Field(default=0, description="Total feedback count")
    positive_feedback_count: Optional[int] = Field(default=0, description="Thumbs up count")
    negative_feedback_count: Optional[int] = Field(default=0, description="Thumbs down count")


class Source(BaseModel):
    """Source information"""
    type: str = Field(..., description="Source type (blog, local_tip, etc.)")
    title: Optional[str] = None
    url: Optional[str] = None
    blog_name: Optional[str] = None
    text: Optional[str] = None


class SuggestResponse(BaseModel):
    """Response with recommendations"""
    recommendations: List[POIRecommendation]
    total_found: int
    query: str
    location: UserLocation
    city: str
    sources: List[Source]
    search_radius_km: float

class FeedbackType(str, Enum):
    """Feedback type enum"""
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    RATING = "rating"  # 1-5 stars


class POIFeedbackSubmit(BaseModel):
    """Request to submit feedback for a POI"""
    poi_id: str = Field(..., description="MongoDB POI ID")
    user_id: str = Field(..., description="User ID (can be session ID for anonymous)")
    feedback_type: FeedbackType = Field(..., description="Type of feedback")
    rating: Optional[int] = Field(None, description="Rating (1-5) if feedback_type is 'rating'", ge=1, le=5)
    visited_at: Optional[datetime] = Field(default_factory=datetime.utcnow, description="When user visited")
    comment: Optional[str] = Field(None, description="Optional comment", max_length=500)
    tags: Optional[List[str]] = Field(default=None, description="Experience tags (e.g., ['romantic', 'quiet', 'good_service'])")


class POIFeedbackResponse(BaseModel):
    """Response after submitting feedback"""
    success: bool
    message: str
    poi_id: str
    feedback_id: str
    updated_stats: Dict[str, Any] = Field(default={}, description="Updated POI stats (avg_rating, feedback_count)")


class TrendingPOI(BaseModel):
    """Trending POI with stats"""
    poi_id: str
    name: str
    category: str
    city: str
    location: Dict
    address: Optional[str]
    average_rating: float = Field(..., description="Average rating (1-5)")
    feedback_count: int = Field(..., description="Total feedback count")
    positive_feedback_count: int = Field(..., description="Thumbs up count")
    negative_feedback_count: int = Field(..., description="Thumbs down count")
    recent_comments: List[str] = Field(default=[], description="Recent user comments")
    tags: Dict = Field(default={}, description="POI tags from OSM")
    trending_score: float = Field(..., description="Trending score (recency + rating weighted)")


class TrendingResponse(BaseModel):
    """Response for trending POIs"""
    city: str
    category: Optional[str]
    trending_pois: List[TrendingPOI]
    total: int
    time_range: str = Field(default="last_30_days", description="Time range for trending calculation")


class AnalyticsQuery(BaseModel):
    """Analytics query log entry"""
    query_id: str
    query_text: str
    city: str
    user_location: UserLocation
    preferences: Optional[Dict] = None
    results_count: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    response_time_ms: float
    user_id: Optional[str] = None


class AnalyticsStats(BaseModel):
    """Analytics statistics response"""
    total_queries: int
    popular_cities: List[Dict[str, Any]]
    popular_categories: List[Dict[str, Any]]
    popular_times: List[Dict[str, Any]]
    common_preferences: Dict[str, Any]
    avg_response_time_ms: float
