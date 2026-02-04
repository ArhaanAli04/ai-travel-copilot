"""
API routes for Local Discovery - Hybrid search for POIs, tips, and blogs
"""
from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional,Dict
from pydantic import BaseModel, Field
import logging
from app.ai.local_agent import local_agent
from app.services.local_discovery_service import local_discovery_service
from app.utils.geo_utils import get_city_coordinates
from app.models.local_discovery import SuggestRequest, SuggestResponse, POIFeedbackResponse, POIFeedbackSubmit, TrendingPOI, TrendingResponse, AnalyticsStats, UserPreferencesSave,UserPreferencesResponse,SavePreferencesResponse, UserPreferences
import time
from datetime import datetime
from app.services.feedback_service import feedback_service
from app.services.analytics_service import analytics_service
from app.services.preferences_service import preferences_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/local", tags=["Local Discovery"])


# Request/Response Models
class LocationInput(BaseModel):
    """User location input"""
    lat: float = Field(..., description="Latitude", ge=-90, le=90)
    lon: float = Field(..., description="Longitude", ge=-180, le=180)


class HybridSearchRequest(BaseModel):
    """Hybrid search request"""
    query: str = Field(..., description="Search query (e.g., 'vegetarian restaurants')")
    location: LocationInput = Field(..., description="User's current location")
    city: str = Field(..., description="City name")
    radius_km: float = Field(5.0, description="Search radius in kilometers", ge=0.1, le=50)
    categories: Optional[List[str]] = Field(None, description="Filter by categories")
    cuisines: Optional[List[str]] = Field(None, description="Filter by cuisines")
    limit: int = Field(20, description="Maximum number of results", ge=1, le=100)
    include_context: bool = Field(True, description="Include blog/tip context")


class POIResponse(BaseModel):
    """Single POI response"""
    id: str
    name: str
    category: str
    location: dict
    distance_km: Optional[float] = None
    distance_text: Optional[str] = None
    relevance_score: Optional[float] = None
    tags: dict = {}


class HybridSearchResponse(BaseModel):
    """Hybrid search response"""
    query: str
    location: LocationInput
    city: str
    radius_km: float
    total_pois: int
    pois: List[dict]
    context: List[dict]
    filters_applied: dict


@router.post("/search", response_model=HybridSearchResponse)
async def hybrid_search(request: HybridSearchRequest):
    """
    Hybrid search combining geospatial and semantic search
    
    Returns POIs within radius + relevant blog/tip context
    """
    try:
        result = await local_discovery_service.hybrid_search(
            query=request.query,
            user_location={"lat": request.location.lat, "lon": request.location.lon},
            city=request.city,
            radius_km=request.radius_km,
            categories=request.categories,
            cuisines=request.cuisines,
            limit=request.limit,
            include_context=request.include_context
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error in hybrid search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def hybrid_search_get(
    query: str = Query(..., description="Search query"),
    lat: float = Query(..., description="User latitude"),
    lon: float = Query(..., description="User longitude"),
    city: str = Query(..., description="City name"),
    radius_km: float = Query(5.0, description="Search radius in km"),
    categories: Optional[str] = Query(None, description="Comma-separated categories"),
    cuisines: Optional[str] = Query(None, description="Comma-separated cuisines"),
    limit: int = Query(20, description="Max results"),
    include_context: bool = Query(True, description="Include context")
):
    """
    Hybrid search (GET method for easier testing)
    
    Example:
    /local/search?query=vegetarian%20restaurants&lat=19.0596&lon=72.8295&city=mumbai&radius_km=3
    """
    try:
        # Parse comma-separated lists
        categories_list = categories.split(",") if categories else None
        cuisines_list = cuisines.split(",") if cuisines else None
        
        result = await local_discovery_service.hybrid_search(
            query=query,
            user_location={"lat": lat, "lon": lon},
            city=city,
            radius_km=radius_km,
            categories=categories_list,
            cuisines=cuisines_list,
            limit=limit,
            include_context=include_context
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error in hybrid search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/poi/{poi_id}")
async def get_poi(poi_id: str):
    """Get a single POI by ID"""
    try:
        poi = await local_discovery_service.get_poi_by_id(poi_id)
        
        if not poi:
            raise HTTPException(status_code=404, detail="POI not found")
        
        return poi
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching POI: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories/{city}")
async def get_categories(city: str):
    """Get all available categories for a city"""
    try:
        categories = await local_discovery_service.get_categories_by_city(city)
        
        return {
            "city": city,
            "categories": categories,
            "total": len(categories)
        }
    
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cuisines/{city}")
async def get_cuisines(city: str):
    """Get all available cuisines for a city"""
    try:
        cuisines = await local_discovery_service.get_cuisines_by_city(city)
        
        return {
            "city": city,
            "cuisines": cuisines,
            "total": len(cuisines)
        }
    
    except Exception as e:
        logger.error(f"Error fetching cuisines: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/category/{city}/{category}")
async def search_by_category(
    city: str,
    category: str,
    lat: Optional[float] = Query(None, description="User latitude"),
    lon: Optional[float] = Query(None, description="User longitude"),
    limit: int = Query(20, description="Max results")
):
    """Search POIs by category"""
    try:
        user_location = None
        if lat is not None and lon is not None:
            user_location = {"lat": lat, "lon": lon}
        
        pois = await local_discovery_service.search_by_category(
            city=city,
            category=category,
            user_location=user_location,
            limit=limit
        )
        
        return {
            "city": city,
            "category": category,
            "total": len(pois),
            "pois": pois
        }
    
    except Exception as e:
        logger.error(f"Error in category search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cities")
async def get_available_cities():
    """Get list of available cities with coordinates"""
    from app.utils.geo_utils import CITY_COORDINATES
    
    return {
        "cities": [
            {
                "name": city_data["name"],
                "key": city_key,
                "lat": city_data["lat"],
                "lon": city_data["lon"]
            }
            for city_key, city_data in CITY_COORDINATES.items()
        ],
        "total": len(CITY_COORDINATES)
    }

@router.post("/suggest", response_model=SuggestResponse)
async def suggest_local_experiences(request: SuggestRequest):
    """
    Generate personalized local recommendations using RAG
    
    Example request:
    ```json
    {
        "query": "romantic dinner spot",
        "user_location": {"lat": 19.0596, "lon": 72.8295},
        "city": "mumbai",
        "preferences": {
            "dietary": ["vegetarian"],
            "budget": "moderate"
        }
    }
    ```
    """
    start_time = time.time()
    try:
        # Call agent
        result = await local_agent.suggest_local_experiences(
            user_query=request.query,
            lat=request.user_location.lat,
            lon=request.user_location.lon,
            city=request.city,
            preferences=request.preferences.model_dump() if request.preferences else None,
            radius_km=request.radius_km,
            max_results=request.max_results
        )
        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000
        # Log analytics (async, non-blocking)
        await analytics_service.log_query(
            query_text=request.query,
            city=request.city,
            user_location={"lat": request.user_location.lat, "lon": request.user_location.lon},
            preferences=request.preferences.model_dump() if request.preferences else None,
            results_count=len(result.get("recommendations", [])),
            response_time_ms=response_time_ms,
            user_id=None  # Add user_id from auth in future
        )

        return result
    
    except Exception as e:
        logger.error(f"Error in suggest endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pois/{poi_id}", response_model=Dict)
async def get_poi_details(poi_id: str):
    """
    Get full POI details from MongoDB
    
    Args:
        poi_id: MongoDB ObjectId of the POI
        
    Returns:
        Complete POI document with all fields
    """
    try:
        poi = await local_agent.get_poi_details(poi_id)
        
        if not poi:
            raise HTTPException(status_code=404, detail=f"POI {poi_id} not found")
        
        return poi
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching POI {poi_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feedback", response_model=POIFeedbackResponse)
async def submit_poi_feedback(feedback: POIFeedbackSubmit):
    """
    Submit user feedback for a POI
    
    Example request:
    ```json
    {
        "poi_id": "6973c6ad1a88ce574ab68798",
        "user_id": "user_123",
        "feedback_type": "thumbs_up",
        "rating": 5,
        "visited_at": "2026-01-29T12:00:00Z",
        "comment": "Great coffee and ambiance!",
        "tags": ["quiet", "good_wifi", "friendly_staff"]
    }
    ```
    """
    try:
        result = await feedback_service.submit_feedback(
            poi_id=feedback.poi_id,
            user_id=feedback.user_id,
            feedback_type=feedback.feedback_type.value,
            rating=feedback.rating,
            visited_at=feedback.visited_at,
            comment=feedback.comment,
            tags=feedback.tags
        )
        
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trending", response_model=TrendingResponse)
async def get_trending_pois(
    city: str = Query(..., description="City name"),
    category: Optional[str] = Query(None, description="Optional category filter"),
    limit: int = Query(10, description="Max results", ge=1, le=50),
    min_feedback: int = Query(3, description="Minimum feedback count", ge=1),
    days: int = Query(30, description="Look back period in days", ge=1, le=90)
):
    """
    Get trending POIs based on recent feedback and ratings
    
    Example:
    /local/trending?city=mumbai&category=restaurant&limit=10
    """
    try:
        trending_pois = await feedback_service.get_trending_pois(
            city=city,
            category=category,
            limit=limit,
            min_feedback_count=min_feedback,
            days=days
        )
        
        return {
            "city": city,
            "category": category,
            "trending_pois": trending_pois,
            "total": len(trending_pois),
            "time_range": f"last_{days}_days"
        }
    
    except Exception as e:
        logger.error(f"Error getting trending POIs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ANALYTICS ENDPOINTS (Day 22)
# ============================================================================

@router.get("/analytics/summary", response_model=AnalyticsStats)
async def get_analytics_summary(
    city: Optional[str] = Query(None, description="Optional city filter"),
    days: int = Query(7, description="Look back period", ge=1, le=90)
):
    """
    Get analytics summary for queries
    
    Returns:
    - Total queries
    - Popular cities
    - Popular search times
    - Common preferences
    - Average response time
    """
    try:
        summary = await analytics_service.get_analytics_summary(city=city, days=days)
        
        return {
            "total_queries": summary.get("total_queries", 0),
            "popular_cities": summary.get("popular_cities", []),
            "popular_categories": summary.get("common_preferences", {}).get("categories", []),
            "popular_times": summary.get("popular_times", []),
            "common_preferences": summary.get("common_preferences", {}),
            "avg_response_time_ms": summary.get("avg_response_time_ms", 0)
        }
    
    except Exception as e:
        logger.error(f"Error getting analytics summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/preferences", response_model=SavePreferencesResponse)
async def save_user_preferences(request: UserPreferencesSave):
    """
    Save user preferences for persistence across sessions
    
    Example request:
    ```json
    {
        "user_id": "user_123",
        "preferences": {
            "dietary": ["vegetarian"],
            "cuisines": ["Italian", "Japanese"],
            "budget": "moderate",
            "group_size": 2
        }
    }
    ```
    """
    try:
        result = await preferences_service.save_preferences(
            user_id=request.user_id,
            preferences=request.preferences.model_dump()
        )
        
        return {
            "success": True,
            "message": "Preferences saved successfully",
            "user_id": result["user_id"],
            "preferences": UserPreferences(**result["preferences"])
        }
    
    except Exception as e:
        logger.error(f"Error saving preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(
    user_id: str = Query(..., description="User ID")
):
    """
    Get saved user preferences
    
    Example:
    /local/preferences?user_id=user_123
    """
    try:
        result = await preferences_service.get_preferences(user_id)
        
        if not result:
            # Return empty preferences if not found
            return {
                "user_id": user_id,
                "preferences": UserPreferences(),
                "updated_at": datetime.utcnow()
            }
        
        return {
            "user_id": result["user_id"],
            "preferences": UserPreferences(**result["preferences"]),
            "updated_at": result["updated_at"]
        }
    
    except Exception as e:
        logger.error(f"Error getting preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/preferences")
async def delete_user_preferences(
    user_id: str = Query(..., description="User ID")
):
    """
    Delete user preferences
    
    Example:
    DELETE /local/preferences?user_id=user_123
    """
    try:
        deleted = await preferences_service.delete_preferences(user_id)
        
        if deleted:
            return {
                "success": True,
                "message": "Preferences deleted successfully",
                "user_id": user_id
            }
        else:
            return {
                "success": False,
                "message": "No preferences found to delete",
                "user_id": user_id
            }
    
    except Exception as e:
        logger.error(f"Error deleting preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "local_discovery",
        "version": "1.0.0"
    }
