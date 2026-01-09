from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class GuideQuery(BaseModel):
    """Input schema for guide retrieval"""
    city: str = Field(..., description="City name (e.g., 'Paris', 'Tokyo')")
    themes: List[str] = Field(
        default=["attractions", "food", "culture"], 
        description="Travel themes (e.g., 'food', 'culture', 'adventure')"
    )
    preferences: Optional[Dict] = Field(
        default=None,
        description="User preferences (budget, interests, etc.)"
    )
    force_refresh: bool = Field(
        default=False,
        description="Force fetch fresh data even if cache exists"
    )

class GuideChunk(BaseModel):
    """Single chunk of travel guide content"""
    id: str
    content: str
    city: str
    theme: str
    source_url: Optional[str] = None
    ingested_at: datetime
    expiry_date: datetime
    relevance_score: Optional[float] = None

class GuideResponse(BaseModel):
    """Response with retrieved guide chunks"""
    city: str
    themes: List[str]
    chunks: List[GuideChunk]
    cache_hit: bool
    total_chunks: int
    sources: List[str]

class WebSearchResult(BaseModel):
    """Raw web search result"""
    title: str
    url: str
    snippet: str
    position: int

class CacheStats(BaseModel):
    """Statistics about cache usage"""
    total_chunks: int
    cities_cached: int
    cache_hit_rate: float
    oldest_entry: Optional[datetime] = None
    newest_entry: Optional[datetime] = None

class SemanticSearchRequest(BaseModel):
    """Request model for semantic search"""
    city: str
    query: str
    themes: Optional[List[str]] = ["attractions", "food", "culture"]
    k: int = 5
