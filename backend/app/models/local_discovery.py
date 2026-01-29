"""
Pydantic models for Local Discovery API
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


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
