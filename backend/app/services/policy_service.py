"""
Policy Service - Fetch, cache, and manage travel policies
Handles airline policies, passenger rights (EU261, DOT), hotel policies
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta, timezone
from serpapi import GoogleSearch
import logging
import hashlib
import re

from app.core.config import settings
from app.core.qdrant import get_qdrant_client
from app.services.embedding_service import embedding_service
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue


logger = logging.getLogger(__name__)


class PolicyService:
    """
    Service for fetching and caching travel policies
    
    Features:
    - Web search for airline/hotel policies
    - Caching in Qdrant (90-day TTL)
    - Chunking and embedding of policy documents
    - Regional passenger rights (EU261, DOT, etc.)
    """
    
    def __init__(self):
        self.collection_name = settings.QDRANT_POLICIES_COLLECTION
        self.cache_ttl_days = settings.POLICY_CACHE_TTL_DAYS
        self.chunk_size = settings.POLICY_CHUNK_SIZE
        self.chunk_overlap = settings.POLICY_CHUNK_OVERLAP
        self.max_results = settings.MAX_POLICY_SEARCH_RESULTS
    
    async def fetch_and_cache_policies(
        self,
        airline: Optional[str] = None,
        region: Optional[str] = None,
        disruption_type: Optional[str] = None,
        provider_type: str = "airline",  # airline, hotel, insurance
        force_refresh: bool = False
    ) -> List[Dict]:
        """
        Fetch and cache policies from web search or Qdrant cache
        
        Args:
            airline: Airline name/code (e.g., "American Airlines", "AA")
            region: Region code (e.g., "EU", "US", "UK")
            disruption_type: Type of disruption (delay, cancellation, etc.)
            provider_type: Type of provider (airline, hotel, insurance)
            force_refresh: Force web search even if cached
            
        Returns:
            List of policy chunks with metadata
        """
        try:
            logger.info(f"🔍 Fetching policies: airline={airline}, region={region}, type={disruption_type}")
            
            # 1. Check cache first (unless force refresh)
            if not force_refresh:
                cached_policies = await self._get_cached_policies(
                    airline=airline,
                    region=region,
                    disruption_type=disruption_type,
                    provider_type=provider_type
                )
                
                if cached_policies:
                    logger.info(f"✅ Found {len(cached_policies)} cached policy chunks")
                    return cached_policies
            
            # 2. No cache or force refresh - fetch from web
            logger.info(f"🌐 Fetching fresh policies from web search")
            
            search_results = await self._search_policies_web(
                airline=airline,
                region=region,
                disruption_type=disruption_type,
                provider_type=provider_type
            )
            
            if not search_results:
                logger.warning(f"⚠️ No policy results found")
                return []
            
            # 3. Process and chunk policy text
            policy_chunks = await self._process_policy_results(
                search_results=search_results,
                airline=airline,
                region=region,
                disruption_type=disruption_type,
                provider_type=provider_type
            )
            
            # 4. Embed and cache in Qdrant
            if policy_chunks:
                await self._cache_policies(policy_chunks)
                logger.info(f"✅ Cached {len(policy_chunks)} policy chunks")
            
            return policy_chunks
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch policies: {e}")
            return []
    
    async def _get_cached_policies(
        self,
        airline: Optional[str],
        region: Optional[str],
        disruption_type: Optional[str],
        provider_type: str
    ) -> List[Dict]:
        """
        Retrieve cached policies from Qdrant
        
        Checks:
        - Matching airline/region/type
        - Not expired (< 90 days old)
        """
        try:
            qdrant_client = get_qdrant_client()
            
            # Build filter conditions
            must_conditions = []
            
            if airline:
                must_conditions.append(
                    FieldCondition(
                        key="provider_name",
                        match=MatchValue(value=airline.lower())
                    )
                )
            
            if region:
                must_conditions.append(
                    FieldCondition(
                        key="region",
                        match=MatchValue(value=region.upper())
                    )
                )
            
            if disruption_type:
                must_conditions.append(
                    FieldCondition(
                        key="disruption_type",
                        match=MatchValue(value=disruption_type.lower())
                    )
                )
            
            must_conditions.append(
                FieldCondition(
                    key="type",
                    match=MatchValue(value=provider_type)
                )
            )
            
            # Search with filters
            if must_conditions:
                search_filter = Filter(must=must_conditions)
                
                results = qdrant_client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=search_filter,
                    limit=100,
                    with_payload=True,
                    with_vectors=False
                )
                
                points = results[0]  # scroll returns (points, next_offset)
                
                # Filter out expired policies
                valid_policies = []
                expiry_threshold = datetime.now(timezone.utc) - timedelta(days=self.cache_ttl_days)
                
                for point in points:
                    ingested_at_str = point.payload.get("ingested_at")
                    
                    if ingested_at_str:
                        ingested_at = datetime.fromisoformat(ingested_at_str.replace("Z", "+00:00"))
                        
                        if ingested_at > expiry_threshold:
                            valid_policies.append(point.payload)
                        else:
                            logger.info(f"⏰ Policy expired: {point.id}")
                
                return valid_policies
            
            return []
            
        except Exception as e:
            logger.error(f"❌ Cache retrieval failed: {e}")
            return []
    
    async def _search_policies_web(
        self,
        airline: Optional[str],
        region: Optional[str],
        disruption_type: Optional[str],
        provider_type: str
    ) -> List[Dict]:
        """
        Search for policies using SerpAPI
        """
        try:
            # Build search queries
            queries = self._build_policy_search_queries(
                airline=airline,
                region=region,
                disruption_type=disruption_type,
                provider_type=provider_type
            )
            
            all_results = []
            
            for query in queries:
                params = {
                    "engine": "google",
                    "q": query,
                    "num": self.max_results,
                    "api_key": settings.SERPAPI_KEY,
                    "gl": "us",
                    "hl": "en",
                }
                
                logger.info(f"🔍 Searching: {query}")
                
                search = GoogleSearch(params)
                results = search.get_dict()
                
                if "error" in results:
                    logger.error(f"❌ SerpAPI error: {results['error']}")
                    continue
                
                organic_results = results.get("organic_results", [])
                
                for result in organic_results[:self.max_results]:
                    all_results.append({
                        "title": result.get("title", ""),
                        "url": result.get("link", ""),
                        "snippet": result.get("snippet", ""),
                        "query": query
                    })
            
            logger.info(f"✅ Found {len(all_results)} policy search results")
            return all_results
            
        except Exception as e:
            logger.error(f"❌ Web search failed: {e}")
            return []
    
    def _build_policy_search_queries(
        self,
        airline: Optional[str],
        region: Optional[str],
        disruption_type: Optional[str],
        provider_type: str
    ) -> List[str]:
        """
        Build optimized search queries for policies
        """
        queries = []
        current_year = datetime.now().year
        
        if provider_type == "airline" and airline:
            # Airline-specific queries
            airline_clean = airline.replace(" ", "+")
            
            if disruption_type == "cancellation":
                queries.append(f"{airline_clean} flight cancellation policy {current_year}")
                queries.append(f"{airline_clean} refund policy cancellation")
            elif disruption_type == "delay":
                queries.append(f"{airline_clean} flight delay compensation policy")
                queries.append(f"{airline_clean} delay refund rights")
            else:
                queries.append(f"{airline_clean} passenger rights policy {current_year}")
                queries.append(f"{airline_clean} terms and conditions")
        
        # Regional passenger rights
        if region:
            if region.upper() == "EU":
                queries.append(f"EU261 compensation rules {airline if airline else 'airlines'}")
                queries.append(f"EU passenger rights flight cancellation delay")
            elif region.upper() == "US":
                queries.append(f"DOT airline passenger rights {airline if airline else ''}")
                queries.append(f"US flight delay cancellation compensation rules")
            elif region.upper() == "UK":
                queries.append(f"UK flight delay compensation {airline if airline else ''}")
                queries.append(f"CAA passenger rights UK")
        
        # Hotel policies
        if provider_type == "hotel":
            queries.append(f"hotel cancellation refund policy {region if region else ''}")
        
        # Insurance policies
        if provider_type == "insurance":
            queries.append(f"travel insurance flight cancellation coverage")
        
        return queries[:3]  # Limit to top 3 queries to save API calls
    
    async def _process_policy_results(
        self,
        search_results: List[Dict],
        airline: Optional[str],
        region: Optional[str],
        disruption_type: Optional[str],
        provider_type: str
    ) -> List[Dict]:
        """
        Process search results into policy chunks
        
        Steps:
        1. Extract text from snippets
        2. Chunk into 400-600 token segments
        3. Add metadata
        """
        policy_chunks = []
        
        for idx, result in enumerate(search_results):
            # Use snippet as policy text (in production, you'd scrape full page)
            policy_text = result.get("snippet", "")
            
            if not policy_text or len(policy_text) < 50:
                continue
            
            # Create chunks (for now, using full snippet as one chunk)
            # TODO: Implement proper chunking for scraped full documents
            chunks = self._chunk_text(policy_text)
            
            for chunk_idx, chunk in enumerate(chunks):
                policy_chunk = {
                    "content": chunk,
                    "type": provider_type,
                    "provider_name": airline.lower() if airline else "general",
                    "region": region.upper() if region else "GLOBAL",
                    "disruption_type": disruption_type.lower() if disruption_type else "general",
                    "source_url": result.get("url"),
                    "source_title": result.get("title"),
                    "query": result.get("query"),
                    "chunk_index": chunk_idx,
                    "ingested_at": datetime.now(timezone.utc).isoformat(),
                    "policy_version": f"{datetime.now().year}-Q{(datetime.now().month-1)//3 + 1}",
                    "expiry_date": (datetime.now(timezone.utc) + timedelta(days=self.cache_ttl_days)).isoformat()
                }
                
                policy_chunks.append(policy_chunk)
        
        return policy_chunks
    
    def _chunk_text(self, text: str) -> List[str]:
        """
        Chunk text into segments with overlap
        
        Uses character-based chunking (roughly 400-600 tokens = 1600-2400 chars)
        """
        # Rough estimate: 1 token ≈ 4 characters
        max_chars = self.chunk_size * 4
        overlap_chars = self.chunk_overlap * 4
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + max_chars
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for period, exclamation, or question mark
                last_period = text.rfind(".", start, end)
                last_exclamation = text.rfind("!", start, end)
                last_question = text.rfind("?", start, end)
                
                sentence_end = max(last_period, last_exclamation, last_question)
                
                if sentence_end > start:
                    end = sentence_end + 1
            
            chunk = text[start:end].strip()
            
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap_chars
        
        return chunks if chunks else [text]
    
    async def _cache_policies(self, policy_chunks: List[Dict]):
        """
        Embed and store policy chunks in Qdrant
        """
        try:
            qdrant_client = get_qdrant_client()
            
            # Generate embeddings
            texts = [chunk["content"] for chunk in policy_chunks]
            embeddings = embedding_service.embed_batch(texts)
            
            # Create points
            points = []
            for idx, (chunk, embedding) in enumerate(zip(policy_chunks, embeddings)):
                point_id = self._generate_point_id(chunk)
                
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=chunk
                )
                points.append(point)
            
            # Upsert to Qdrant
            qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"✅ Cached {len(points)} policy chunks in Qdrant")
            
        except Exception as e:
            logger.error(f"❌ Failed to cache policies: {e}")
    
    def _generate_point_id(self, chunk: Dict) -> str:
        """
        Generate unique ID for policy chunk
        
        Uses hash of: provider + region + type + chunk_index
        """
        unique_string = f"{chunk['provider_name']}_{chunk['region']}_{chunk['disruption_type']}_{chunk['chunk_index']}_{chunk['ingested_at']}"
        
        hash_object = hashlib.md5(unique_string.encode())
        hash_int = int(hash_object.hexdigest(), 16)
        
        # Qdrant requires positive integer IDs
        return abs(hash_int) % (10 ** 10)


# Singleton instance
policy_service = PolicyService()
