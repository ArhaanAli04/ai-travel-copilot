from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun

from app.core.qdrant import get_qdrant_client, get_collection_name,get_policies_collection_name
from app.services.embedding_service import embedding_service
from app.services.guide_service import guide_service
from app.services.policy_service import policy_service
from app.schemas.guide import GuideQuery
import logging

logger = logging.getLogger(__name__)


class TravelGuideRetriever(BaseRetriever):
    """
    LangChain-compatible retriever for travel guides
    
    Wraps Qdrant cache + web search fallback in LangChain interface.
    Can be used with LangChain agents, chains, and RAG pipelines.
    """
    
    city: str
    themes: List[str]
    k: int = 5  # Number of top results to return
    use_cache: bool = True
    
    class Config:
        arbitrary_types_allowed = True
    
    def _get_relevant_documents(
        self, 
        query: str, 
        *, 
        run_manager: CallbackManagerForRetrieverRun = None
    ) -> List[Document]:
        """
        Retrieve relevant documents for a query
        
        Args:
            query: User's search query
            run_manager: LangChain callback manager
            
        Returns:
            List of LangChain Document objects
        """
        logger.info(f"🔍 Retrieving documents for query: {query}")
        
        try:
            # Use guide service to get cached or fresh data
            guide_query = GuideQuery(
                city=self.city,
                themes=self.themes,
                force_refresh=not self.use_cache
            )
            
            response = guide_service.fetch_and_cache_guides(guide_query)
            
            # If we have cached chunks, do semantic search on them
            if response.chunks:
                documents = self._search_with_query_embedding(query, response.chunks)
            else:
                documents = []
            
            logger.info(f"✅ Retrieved {len(documents)} documents")
            return documents[:self.k]
            
        except Exception as e:
            logger.error(f"❌ Retrieval failed: {e}")
            return []
    
    def _search_with_query_embedding(
        self, 
        query: str, 
        cached_chunks: List[Any]
    ) -> List[Document]:
        """
        Perform semantic search using query embedding
        
        Args:
            query: Search query
            cached_chunks: List of cached guide chunks
            
        Returns:
            Ranked list of Document objects
        """
        try:
            # Generate query embedding
            query_embedding = embedding_service.embed_query(query)
            
            # Search Qdrant with the query embedding
            qdrant_client = get_qdrant_client()
            collection_name = get_collection_name()
            
            search_results = qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=self.k,
                with_payload=True
            )
            
            # Convert to LangChain Documents
            documents = []
            for result in search_results:
                doc = Document(
                    page_content=result.payload["content"],
                    metadata={
                        "city": result.payload["city"],
                        "theme": result.payload["theme"],
                        "source_url": result.payload.get("source_url"),
                        "source_title": result.payload.get("source_title"),
                        "relevance_score": result.score,
                        "ingested_at": result.payload.get("ingested_at")
                    }
                )
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"❌ Semantic search failed: {e}")
            # Fallback: return cached chunks without ranking
            return [
                Document(
                    page_content=chunk.content,
                    metadata={
                        "city": chunk.city,
                        "theme": chunk.theme,
                        "source_url": chunk.source_url
                    }
                )
                for chunk in cached_chunks[:self.k]
            ]
    
    async def _aget_relevant_documents(
        self, 
        query: str, 
        *, 
        run_manager: CallbackManagerForRetrieverRun = None
    ) -> List[Document]:
        """Async version of retrieval (calls sync version for now)"""
        return self._get_relevant_documents(query, run_manager=run_manager)



class RightsRetriever(BaseRetriever):
    """
    LangChain-compatible retriever for passenger rights and travel policies
    
    Retrieves:
    - Airline-specific policies (cancellation, refund, compensation)
    - Regional passenger rights (EU261, DOT, CAA)
    - Hotel cancellation policies
    - Travel insurance coverage
    """
    
    airline: Optional[str] = None
    origin_country: Optional[str] = None
    destination_country: Optional[str] = None
    disruption_type: Optional[str] = None
    provider_type: str = "airline"  # airline, hotel, insurance
    k: int = 5
    use_cache: bool = True
    
    class Config:
        arbitrary_types_allowed = True
    
    async def _aget_relevant_documents(
        self, 
        query: str, 
        *, 
        run_manager: CallbackManagerForRetrieverRun = None
    ) -> List[Document]:
        """
        Retrieve relevant policy documents
        
        Args:
            query: User's query (e.g., "What are my compensation rights?")
            
        Returns:
            List of policy documents
        """
        logger.info(f"🔍 Retrieving rights for: airline={self.airline}, region={self.origin_country}")
        
        try:
            # Determine region based on origin/destination
            region = self._determine_region()
            
            # Fetch or retrieve cached policies
            policy_chunks = await policy_service.fetch_and_cache_policies(
                airline=self.airline,
                region=region,
                disruption_type=self.disruption_type,
                provider_type=self.provider_type,
                force_refresh=not self.use_cache
            )
            
            if not policy_chunks:
                logger.warning(f"⚠️ No policies found")
                return []
            
            # If we have a specific query, do semantic search
            if query:
                documents = await self._semantic_search(query, policy_chunks)
            else:
                # Return all chunks
                documents = [
                    Document(
                        page_content=chunk["content"],
                        metadata={
                            "type": chunk["type"],
                            "provider_name": chunk["provider_name"],
                            "region": chunk["region"],
                            "disruption_type": chunk["disruption_type"],
                            "source_url": chunk.get("source_url"),
                            "source_title": chunk.get("source_title"),
                            "policy_version": chunk.get("policy_version"),
                            "ingested_at": chunk.get("ingested_at")
                        }
                    )
                    for chunk in policy_chunks[:self.k]
                ]
            
            logger.info(f"✅ Retrieved {len(documents)} policy documents")
            return documents
            
        except Exception as e:
            logger.error(f"❌ Rights retrieval failed: {e}")
            return []
    
    def _get_relevant_documents(
        self, 
        query: str, 
        *, 
        run_manager: CallbackManagerForRetrieverRun = None
    ) -> List[Document]:
        """Sync wrapper for async retrieval"""
        import asyncio
        return asyncio.run(self._aget_relevant_documents(query, run_manager=run_manager))
    
    async def _semantic_search(
    self,
    query: str,
    policy_chunks: List[Dict]
) -> List[Document]:
        """
        Perform semantic search on policy chunks using query embedding
        """
        try:
            # Generate query embedding
            query_embedding = embedding_service.embed_query(query)
            
            qdrant_client = get_qdrant_client()
            collection_name = get_policies_collection_name()
            
            # ✅ BUILD FILTERS for airline/region/type
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            must_conditions = []
            
            # Filter by airline
            if self.airline:
                must_conditions.append(
                    FieldCondition(
                        key="provider_name",
                        match=MatchValue(value=self.airline.lower())
                    )
                )
            
            # Filter by region
            region = self._determine_region()
            if region:
                must_conditions.append(
                    FieldCondition(
                        key="region",
                        match=MatchValue(value=region.upper())
                    )
                )
            
            # Filter by disruption type
            if self.disruption_type:
                must_conditions.append(
                    FieldCondition(
                        key="disruption_type",
                        match=MatchValue(value=self.disruption_type.lower())
                    )
                )
            
            # Filter by provider type
            must_conditions.append(
                FieldCondition(
                    key="type",
                    match=MatchValue(value=self.provider_type)
                )
            )
            
            # ✅ Search WITH filters
            if must_conditions:
                search_filter = Filter(must=must_conditions)
                
                search_results = qdrant_client.search(
                    collection_name=collection_name,
                    query_vector=query_embedding,
                    query_filter=search_filter,  # ✅ ADD FILTER
                    limit=self.k,
                    with_payload=True
                )
            else:
                # No filters - search everything
                search_results = qdrant_client.search(
                    collection_name=collection_name,
                    query_vector=query_embedding,
                    limit=self.k,
                    with_payload=True
                )
            
            # Convert to LangChain Documents
            documents = []
            for result in search_results:
                doc = Document(
                    page_content=result.payload["content"],
                    metadata={
                        "type": result.payload["type"],
                        "provider_name": result.payload["provider_name"],
                        "region": result.payload["region"],
                        "disruption_type": result.payload.get("disruption_type"),
                        "source_url": result.payload.get("source_url"),
                        "source_title": result.payload.get("source_title"),
                        "relevance_score": result.score,
                        "policy_version": result.payload.get("policy_version")
                    }
                )
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"❌ Semantic search failed: {e}")
            # Fallback: return chunks without ranking
            return [
                Document(
                    page_content=chunk["content"],
                    metadata={
                        "type": chunk["type"],
                        "provider_name": chunk["provider_name"],
                        "region": chunk["region"],
                        "source_url": chunk.get("source_url")
                    }
                )
                for chunk in policy_chunks[:self.k]
            ]

    
    def _determine_region(self) -> Optional[str]:
        """
        Determine applicable region based on origin/destination
        
        Rules:
        - EU flights (within EU or departing from EU) → EU
        - US flights → US
        - UK flights → UK
        - Otherwise → origin country
        """
        eu_countries = {
            "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
            "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
            "PL", "PT", "RO", "SK", "SI", "ES", "SE"
        }
        
        origin = self.origin_country.upper() if self.origin_country else None
        destination = self.destination_country.upper() if self.destination_country else None
        
        # EU261 applies if flight departs from EU
        if origin in eu_countries:
            return "EU"
        
        # Or if it's an EU airline arriving in EU
        if destination in eu_countries:
            return "EU"
        
        # US rules
        if origin == "US" or destination == "US":
            return "US"
        
        # UK rules
        if origin == "UK" or destination == "UK":
            return "UK"
        
        # Default to origin country
        return origin


def create_travel_guide_retriever(
    city: str, 
    themes: List[str] = None, 
    k: int = 5,
    use_cache: bool = True
) -> TravelGuideRetriever:
    """
    Factory function to create a travel guide retriever
    
    Args:
        city: City name
        themes: List of themes (default: ["attractions", "food", "culture"])
        k: Number of results to return
        use_cache: Whether to use cached data
        
    Returns:
        TravelGuideRetriever instance
    """
    if themes is None:
        themes = ["attractions", "food", "culture"]
    
    return TravelGuideRetriever(
        city=city,
        themes=themes,
        k=k,
        use_cache=use_cache
    )


def create_rights_retriever(
    airline: Optional[str] = None,
    origin_country: Optional[str] = None,
    destination_country: Optional[str] = None,
    disruption_type: Optional[str] = None,
    provider_type: str = "airline",
    k: int = 5,
    use_cache: bool = True
) -> RightsRetriever:
    """
    Factory function to create a rights retriever
    
    Args:
        airline: Airline name (e.g., "American Airlines")
        origin_country: Origin country code (e.g., "US", "FR")
        destination_country: Destination country code
        disruption_type: Type of disruption (delay, cancellation)
        provider_type: Type of provider (airline, hotel, insurance)
        k: Number of results to return
        use_cache: Whether to use cached policies
        
    Returns:
        RightsRetriever instance
    """
    return RightsRetriever(
        airline=airline,
        origin_country=origin_country,
        destination_country=destination_country,
        disruption_type=disruption_type,
        provider_type=provider_type,
        k=k,
        use_cache=use_cache
    )