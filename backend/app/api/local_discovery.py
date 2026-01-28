"""
API routes for Local Discovery - Hybrid search for POIs, tips, and blogs
"""
from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from pydantic import BaseModel, Field
import logging

from app.services.local_discovery_service import local_discovery_service
from app.utils.geo_utils import get_city_coordinates

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


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "local_discovery",
        "version": "1.0.0"
    }
