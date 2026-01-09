from typing import List
from serpapi import GoogleSearch
from app.core.config import settings
from app.schemas.guide import WebSearchResult
import logging

logger = logging.getLogger(__name__)


class WebSearchService:
    """Service for fetching web search results for travel guides"""
    
    def __init__(self):
        self.provider = settings.WEB_SEARCH_PROVIDER
        self.max_results = settings.MAX_SEARCH_RESULTS
    
    def search_travel_guides(
        self, 
        city: str, 
        theme: str
    ) -> List[WebSearchResult]:
        """
        Search for travel guides about a city and theme
        
        Args:
            city: City name (e.g., "Paris")
            theme: Travel theme (e.g., "food", "culture", "attractions")
            
        Returns:
            List of web search results
        """
        if self.provider == "serpapi":
            return self._search_serpapi(city, theme)
        else:
            raise ValueError(f"Unsupported search provider: {self.provider}")
    
    def _search_serpapi(self, city: str, theme: str) -> List[WebSearchResult]:
        """Search using SerpAPI Google Search"""
        
        if not settings.SERPAPI_KEY:
            logger.error("❌ SERPAPI_KEY not configured")
            return []
        
        # Build search query
        query = self._build_search_query(city, theme)
        
        params = {
            "engine": "google",
            "q": query,
            "num": self.max_results,
            "api_key": settings.SERPAPI_KEY,
            "gl": "us",
            "hl": "en",
        }
        
        logger.info(f"🔍 Searching: {query}")
        
        try:
            search = GoogleSearch(params)
            results = search.get_dict()
            
            if "error" in results:
                logger.error(f"❌ SerpAPI error: {results['error']}")
                return []
            
            # Parse organic results
            organic_results = results.get("organic_results", [])
            
            parsed_results = []
            for idx, result in enumerate(organic_results[:self.max_results]):
                parsed_results.append(WebSearchResult(
                    title=result.get("title", ""),
                    url=result.get("link", ""),
                    snippet=result.get("snippet", ""),
                    position=idx + 1
                ))
            
            logger.info(f"✅ Found {len(parsed_results)} search results for {city} - {theme}")
            return parsed_results
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return []
    
    def _build_search_query(self, city: str, theme: str) -> str:
        """Build optimized search query based on theme"""
        
        theme_queries = {
            "food": f"best restaurants and local food in {city}",
            "culture": f"cultural attractions and experiences in {city}",
            "attractions": f"top tourist attractions and things to do in {city}",
            "adventure": f"adventure activities and outdoor experiences in {city}",
            "nightlife": f"nightlife and entertainment in {city}",
            "shopping": f"best shopping areas and markets in {city}",
            "history": f"historical sites and museums in {city}",
            "nature": f"parks gardens and nature in {city}",
        }
        
        return theme_queries.get(theme.lower(), f"{theme} in {city}")


# Singleton instance
web_search_service = WebSearchService()
