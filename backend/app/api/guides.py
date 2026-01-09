from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.schemas.guide import GuideQuery, GuideResponse, CacheStats,SemanticSearchRequest
from app.services.guide_service import guide_service
from app.ai.retrievers import create_travel_guide_retriever
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/guides", tags=["Travel Guides"])


@router.post("/search", response_model=GuideResponse)
async def search_guides(query: GuideQuery):
    """
    Search for travel guides with intelligent caching
    
    **Caching Strategy:**
    1. Checks Qdrant cache for city + themes
    2. If fresh data exists → returns cached (no API cost)
    3. If no data or stale → fetches from web, embeds, caches, returns
    
    **Example Request:**
    ```json
    {
        "city": "Paris",
        "themes": ["food", "culture"],
        "force_refresh": false
    }
    ```
    """
    try:
        logger.info(f"📖 Guide search request: {query.city} - {query.themes}")
        
        response = guide_service.fetch_and_cache_guides(query)
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Guide search failed: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch travel guides: {str(e)}"
        )


@router.get("/search", response_model=GuideResponse)
async def search_guides_get(
    city: str = Query(..., description="City name (e.g., 'Paris')"),
    themes: str = Query(
        default="attractions,food,culture",
        description="Comma-separated themes (e.g., 'food,culture,nightlife')"
    ),
    force_refresh: bool = Query(
        default=False,
        description="Force fetch fresh data even if cache exists"
    )
):
    """
    GET version of guide search (easier for testing in browser)
    
    **Example:**
    ```
    GET /api/guides/search?city=Paris&themes=food,culture&force_refresh=false
    ```
    """
    # Parse themes from comma-separated string
    theme_list = [t.strip() for t in themes.split(",") if t.strip()]
    
    query = GuideQuery(
        city=city,
        themes=theme_list,
        force_refresh=force_refresh
    )
    
    return await search_guides(query)


@router.post("/retrieve")
async def retrieve_with_query(request: SemanticSearchRequest):
    """
    Semantic search using LangChain retriever
    
    Uses cached embeddings to find most relevant chunks for a query.
    """
    try:
        # First, ensure data is cached
        guide_query = GuideQuery(
            city=request.city,
            themes=request.themes,
            force_refresh=False
        )
        
        # Fetch/cache data
        response = guide_service.fetch_and_cache_guides(guide_query)
        
        if not response.chunks:
            return {
                "city": request.city,
                "query": request.query,
                "results": [],
                "total_results": 0
            }
        
        # Create retriever
        retriever = create_travel_guide_retriever(
            city=request.city,
            themes=request.themes,
            k=request.k,
            use_cache=True
        )
        
        # Retrieve documents
        documents = retriever._get_relevant_documents(request.query)
        
        # Format response
        results = []
        for doc in documents:
            results.append({
                "content": doc.page_content,
                "metadata": doc.metadata
            })
        
        return {
            "city": request.city,
            "query": request.query,
            "results": results,
            "total_results": len(results)
        }
        
    except Exception as e:
        logger.error(f"❌ Retrieval failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve documents: {str(e)}"
        )

@router.get("/stats", response_model=dict)
async def get_cache_stats():
    """
    Get cache statistics
    
    Returns information about cache usage, API calls, and cost optimization.
    """
    try:
        stats = guide_service.get_cache_stats()
        return stats
        
    except Exception as e:
        logger.error(f"❌ Failed to get stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get cache stats: {str(e)}"
        )


@router.delete("/cache")
async def clear_cache(
    city: Optional[str] = None,
    theme: Optional[str] = None
):
    """
    Clear cached data
    
    - If no params: clears entire cache
    - If city only: clears all data for that city
    - If city + theme: clears specific city-theme combination
    """
    try:
        from app.core.qdrant import get_qdrant_client, get_collection_name
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        client = get_qdrant_client()
        collection_name = get_collection_name()
        
        if not city and not theme:
            # Clear entire collection
            client.delete_collection(collection_name)
            # Recreate empty collection
            from app.core.qdrant import create_collection_if_not_exists
            create_collection_if_not_exists(collection_name)
            return {"message": "Entire cache cleared"}
        
        # Build filter
        filter_conditions = []
        if city:
            filter_conditions.append(
                FieldCondition(key="city", match=MatchValue(value=city.lower()))
            )
        if theme:
            filter_conditions.append(
                FieldCondition(key="theme", match=MatchValue(value=theme.lower()))
            )
        
        # Delete matching points
        client.delete(
            collection_name=collection_name,
            points_selector=Filter(must=filter_conditions)
        )
        
        return {
            "message": f"Cache cleared for city={city}, theme={theme}"
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to clear cache: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}"
        )
