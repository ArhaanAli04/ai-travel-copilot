from google import genai
import numpy as np
from typing import List, Dict
from app.core.config import settings
import logging
import time

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings using Google Gemini API"""
    
    def __init__(self):
        """Initialize Gemini client with API key"""
        if not settings.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY not set in environment")
        
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = "gemini-embedding-001"  # Latest Gemini embedding model
        self.batch_size = 100  # Process embeddings in batches
        self.rate_limit_delay = 0.1  # Delay between API calls (seconds)
    
    def embed_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """
        Generate embeddings for text chunks
        
        Args:
            chunks: List of chunk dictionaries with 'content' field
            
        Returns:
            Same chunks with added 'embedding' field (as list, not numpy)
        """
        logger.info(f"🔄 Generating embeddings for {len(chunks)} chunks...")
        
        embedded_chunks = []
        
        # Process in batches to avoid rate limits
        for i in range(0, len(chunks), self.batch_size):
            batch = chunks[i:i + self.batch_size]
            
            try:
                # Extract text content
                texts = [chunk["content"] for chunk in batch]
                
                # Generate embeddings
                embeddings = self._embed_texts(texts)
                
                # Add embeddings to chunks (convert numpy to list for JSON serialization)
                for chunk, embedding in zip(batch, embeddings):
                    chunk["embedding"] = embedding.tolist() if isinstance(embedding, np.ndarray) else embedding
                    embedded_chunks.append(chunk)
                
                # Rate limiting
                if i + self.batch_size < len(chunks):
                    time.sleep(self.rate_limit_delay)
                
                logger.info(f" Embedded batch {i//self.batch_size + 1}/{(len(chunks)-1)//self.batch_size + 1}")
                
            except Exception as e:
                logger.error(f"❌ Failed to embed batch {i//self.batch_size + 1}: {e}")
                # Skip this batch and continue
                continue
        
        logger.info(f" Generated {len(embedded_chunks)} embeddings")
        return embedded_chunks
    
    def _embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts using Gemini API
        
        Args:
            texts: List of text strings
            
        Returns:
            2D numpy array of shape (len(texts), embedding_dim)
        """
        if not texts:
            return np.array([])
        
        embeddings_list = []
        
        for text in texts:
            try:
                # Call Gemini embedding API
                result = self.client.models.embed_content(
                    model=self.model_name,
                    contents=text
                )
                
                # Extract embedding values
                embedding = result.embeddings[0].values
                embeddings_list.append(embedding)
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to embed single text: {e}")
                # Fallback: zero vector with Gemini embedding dimension (768)
                embeddings_list.append([0.0] * 3072)
        
        # Convert to numpy array
        embeddings = np.array(embeddings_list, dtype=np.float32)
        
        # L2-normalize for cosine similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)  # Avoid division by zero
        embeddings = embeddings / norms
        
        return embeddings
    
    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a search query
        
        Args:
            query: Search query text
            
        Returns:
            Embedding vector as list
        """
        try:
            result = self.client.models.embed_content(
                model=self.model_name,
                contents=query
            )
            
            # Extract and normalize embedding
            embedding = np.array(result.embeddings[0].values, dtype=np.float32)
            
            # L2-normalize
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            return embedding.tolist()
        
        except Exception as e:
            logger.error(f"❌ Failed to embed query: {e}")
            raise
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings from this model"""
        return 3072  # Gemini embedding dimension


# Global instance
embedding_service = EmbeddingService()
