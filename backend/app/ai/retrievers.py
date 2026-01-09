from typing import List, Dict, Any
from langchain.schema import Document
from langchain.schema.retriever import BaseRetriever
from langchain.callbacks.manager import CallbackManagerForRetrieverRun

from app.core.qdrant import get_qdrant_client, get_collection_name
from app.services.embedding_service import embedding_service
from app.services.guide_service import guide_service
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
