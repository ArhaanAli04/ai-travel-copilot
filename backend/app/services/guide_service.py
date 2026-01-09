#main caching logic - core service that implements the caching strategy!
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue
import uuid
import logging

from app.core.config import settings
from app.core.qdrant import get_qdrant_client, get_collection_name
from app.schemas.guide import GuideQuery, GuideChunk, GuideResponse, WebSearchResult
from app.services.web_search_service import web_search_service
from app.services.chunking_service import chunking_service
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


class GuideService:
    """Main service for fetching and caching travel guides with RAG"""
    
    def __init__(self):
        self.qdrant_client = get_qdrant_client()
        self.collection_name = get_collection_name()
        self.ttl_days = settings.CACHE_TTL_DAYS
        self.api_call_count = 0  # Track API usage for cost optimization
    
    def fetch_and_cache_guides(
        self, 
        query: GuideQuery
    ) -> GuideResponse:
        """
        Main method: Check cache, fetch if needed, return guides
        
        This implements the caching strategy:
        1. Check Qdrant cache for city + theme
        2. If fresh data exists → return it (cache hit)
        3. If no data or stale → fetch from web, embed, cache, return
        
        Args:
            query: GuideQuery with city, themes, preferences
            
        Returns:
            GuideResponse with chunks and cache status
        """
        logger.info(f"📖 Fetching guides for {query.city} - Themes: {query.themes}")
        
        all_chunks = []
        all_sources = []
        cache_hit = True
        
        for theme in query.themes:
            # Step 1: Check cache
            if not query.force_refresh:
                cached_chunks = self._search_cache(query.city, theme)
                
                if cached_chunks and not self._is_stale(cached_chunks):
                    logger.info(f"✅ Cache hit for {query.city} - {theme}")
                    all_chunks.extend(cached_chunks)
                    continue
                else:
                    logger.info(f"⚠️ Cache miss or stale data for {query.city} - {theme}")
            
            # Step 2: Cache miss → fetch fresh data
            cache_hit = False
            fresh_chunks = self._fetch_and_ingest(query.city, theme)
            all_chunks.extend(fresh_chunks)
            
            # Collect sources
            for chunk in fresh_chunks:
                source_url = chunk.get("source_url") if isinstance(chunk, dict) else getattr(chunk, "source_url", None)
                if source_url and source_url not in all_sources:
                    all_sources.append(source_url)
        
        # Convert to GuideChunk schema
        guide_chunks = []
        for chunk in all_chunks:
            try:
                # Handle dict format (from cache or fresh)
                if isinstance(chunk, dict):
                    chunk_id = chunk.get("id", str(uuid.uuid4()))
                    
                    # Parse datetime fields if they're strings
                    ingested_at = chunk.get("ingested_at")
                    if isinstance(ingested_at, str):
                        ingested_at = datetime.fromisoformat(ingested_at)
                    elif ingested_at is None:
                        ingested_at = datetime.now()
                    
                    expiry_date = chunk.get("expiry_date")
                    if isinstance(expiry_date, str):
                        expiry_date = datetime.fromisoformat(expiry_date)
                    elif expiry_date is None:
                        expiry_date = datetime.now() + timedelta(days=self.ttl_days)
                    
                    guide_chunks.append(GuideChunk(
                        id=chunk_id,
                        content=chunk.get("content", ""),
                        city=chunk.get("city", query.city),
                        theme=chunk.get("theme", ""),
                        source_url=chunk.get("source_url"),
                        ingested_at=ingested_at,
                        expiry_date=expiry_date,
                        relevance_score=chunk.get("score")
                    ))
                elif isinstance(chunk, GuideChunk):
                    # Already a GuideChunk object
                    guide_chunks.append(chunk)
            except Exception as e:
                logger.warning(f"⚠️ Failed to convert chunk to GuideChunk: {e}")
                continue
        
        logger.info(f"✅ Returning {len(guide_chunks)} chunks (cache_hit={cache_hit})")
        
        return GuideResponse(
            city=query.city,
            themes=query.themes,
            chunks=guide_chunks,
            cache_hit=cache_hit,
            total_chunks=len(guide_chunks),
            sources=all_sources
        )
    
    def _search_cache(self, city: str, theme: str) -> List[Dict]:
        """
        Search Qdrant cache for existing chunks
        
        Args:
            city: City name
            theme: Travel theme
            
        Returns:
            List of cached chunks with scores
        """
        try:
            # Search with filters
            results = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="city",
                            match=MatchValue(value=city.lower())
                        ),
                        FieldCondition(
                            key="theme",
                            match=MatchValue(value=theme.lower())
                        )
                    ]
                ),
                limit=50,  # Get up to 50 cached chunks
                with_payload=True,
                with_vectors=False
            )
            
            chunks = []
            for point in results[0]:
                chunk_data = point.payload
                chunk_data["id"] = point.id
                chunks.append(chunk_data)
            
            logger.info(f"🔍 Found {len(chunks)} cached chunks for {city} - {theme}")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Cache search failed: {e}")
            return []
    
    def _is_stale(self, chunks: List[Dict]) -> bool:
        """
        Check if cached chunks are stale (older than TTL)
        
        Args:
            chunks: List of cached chunks
            
        Returns:
            True if data is stale, False if fresh
        """
        if not chunks:
            return True
        
        # Check the first chunk's expiry date
        first_chunk = chunks[0]
        expiry_date_str = first_chunk.get("expiry_date")
        
        if not expiry_date_str:
            return True
        
        # Parse expiry date
        if isinstance(expiry_date_str, str):
            expiry_date = datetime.fromisoformat(expiry_date_str)
        else:
            expiry_date = expiry_date_str
        
        # Check if expired
        is_stale = datetime.now() > expiry_date
        
        if is_stale:
            logger.info(f"⚠️ Data is stale (expired: {expiry_date})")
        
        return is_stale
    
    def _fetch_and_ingest(self, city: str, theme: str) -> List[Dict]:
        """
        Fetch fresh data from web, process, embed, and cache
        
        This is the main ingestion pipeline:
        1. Web search (SerpAPI)
        2. Chunk text
        3. Embed chunks (Gemini)
        4. Upsert to Qdrant
        
        Args:
            city: City name
            theme: Travel theme
            
        Returns:
            List of newly ingested chunks
        """
        logger.info(f"🌐 Fetching fresh data for {city} - {theme}")
        
        # Step 1: Web search
        web_results = web_search_service.search_travel_guides(city, theme)
        self.api_call_count += 1  # Track API usage
        
        if not web_results:
            logger.warning(f"⚠️ No web results found for {city} - {theme}")
            return []
        
        # Step 2: Chunk the results
        chunks = chunking_service.chunk_web_results(
            web_results,
            city,
            theme
        )
        
        if not chunks:
            logger.warning(f"⚠️ No chunks created from web results")
            return []
        
        # Step 3: Generate embeddings
        embedded_chunks = embedding_service.embed_chunks(chunks)
        
        if not embedded_chunks:
            logger.warning(f"⚠️ No embeddings generated")
            return []
        
        # Step 4: Upsert to Qdrant
        self._upsert_to_qdrant(embedded_chunks, city, theme)
        
        return embedded_chunks
    
    def _upsert_to_qdrant(self, chunks: List[Dict], city: str, theme: str):
        """
        Upsert chunks to Qdrant with metadata
        
        Args:
            chunks: List of chunks with embeddings
            city: City name
            theme: Travel theme
        """
        try:
            now = datetime.now()
            expiry = now + timedelta(days=self.ttl_days)
            
            points = []
            for chunk in chunks:
                point_id = str(uuid.uuid4())
                
                points.append(PointStruct(
                    id=point_id,
                    vector=chunk["embedding"],
                    payload={
                        "content": chunk["content"],
                        "city": city.lower(),
                        "theme": theme.lower(),
                        "source_url": chunk.get("source_url"),
                        "source_title": chunk.get("source_title"),
                        "ingested_at": now.isoformat(),
                        "expiry_date": expiry.isoformat(),
                        "chunk_index": chunk.get("chunk_index", 0),
                    }
                ))
            
            # Upsert to Qdrant
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"✅ Upserted {len(points)} chunks to Qdrant for {city} - {theme}")
            
        except Exception as e:
            logger.error(f"❌ Failed to upsert to Qdrant: {e}")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        try:
            collection_info = self.qdrant_client.get_collection(self.collection_name)
            
            return {
                "total_chunks": collection_info.points_count,
                "api_calls_made": self.api_call_count,
                "cache_ttl_days": self.ttl_days
            }
        except Exception as e:
            logger.error(f"❌ Failed to get cache stats: {e}")
            return {}


# Global instance
guide_service = GuideService()

