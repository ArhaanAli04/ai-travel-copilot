from google import genai
from google.genai import types
import numpy as np
from typing import List, Dict, Literal
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
        # Use latest model with configurable dimensions
        self.model_name = "gemini-embedding-001"
        self.dimension = 768  # Optimized for storage (vs default 3072)
        self.batch_size = 100  # Process embeddings in batches
        self.rate_limit_delay = 0.1  # Delay between API calls (seconds)
    
    def embed_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """
        Generate embeddings for text chunks (LEGACY - for existing RAG system)
        
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
                
                # Generate embeddings with RETRIEVAL_DOCUMENT task type
                embeddings = self.generate_embeddings(
                    texts,
                    task_type="RETRIEVAL_DOCUMENT"
                )
                
                # Add embeddings to chunks
                for chunk, embedding in zip(batch, embeddings):
                    chunk["embedding"] = embedding
                    embedded_chunks.append(chunk)
                
                # Rate limiting
                if i + self.batch_size < len(chunks):
                    time.sleep(self.rate_limit_delay)
                
                logger.info(f"✅ Embedded batch {i//self.batch_size + 1}/{(len(chunks)-1)//self.batch_size + 1}")
                
            except Exception as e:
                logger.error(f"❌ Failed to embed batch {i//self.batch_size + 1}: {e}")
                # Skip this batch and continue
                continue
        
        logger.info(f"✅ Generated {len(embedded_chunks)} embeddings")
        return embedded_chunks
    
    def generate_embeddings(
        self,
        texts: List[str],
        task_type: Literal["RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY"] = "RETRIEVAL_DOCUMENT"
    ) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using Gemini API (NEW - optimized)
        
        Args:
            texts: List of text strings to embed
            task_type: "RETRIEVAL_DOCUMENT" for storing, "RETRIEVAL_QUERY" for searching
        
        Returns:
            List of normalized embedding vectors (768 dimensions each)
        """
        if not texts:
            return []
        
        embeddings_list = []
        
        try:
            # Call Gemini embedding API with optimized config
            result = self.client.models.embed_content(
                model=self.model_name,
                contents=texts,
                config=types.EmbedContentConfig(
                    output_dimensionality=self.dimension,  # 768 dims for storage savings
                    task_type=task_type
                )
            )
            
            # Extract and normalize embeddings
            for embedding in result.embeddings:
                normalized = self.normalize_embedding(embedding.values)
                embeddings_list.append(normalized)
            
            return embeddings_list
        
        except Exception as e:
            logger.error(f"❌ Error generating embeddings: {e}")
            raise
    
    def generate_single_embedding(
        self,
        text: str,
        task_type: Literal["RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY"] = "RETRIEVAL_DOCUMENT"
    ) -> List[float]:
        """
        Generate embedding for a single text (NEW - convenience method)
        
        Args:
            text: Text string to embed
            task_type: "RETRIEVAL_DOCUMENT" for storing, "RETRIEVAL_QUERY" for searching
        
        Returns:
            Normalized embedding vector (768 dimensions)
        """
        embeddings = self.generate_embeddings([text], task_type)
        return embeddings[0] if embeddings else []
    
    def normalize_embedding(self, embedding: List[float]) -> List[float]:
        """
        Normalize embedding vector to unit length (NEW - for Qdrant)
        
        Args:
            embedding: Raw embedding vector
        
        Returns:
            Normalized embedding vector as list
        """
        embedding_np = np.array(embedding, dtype=np.float32)
        norm = np.linalg.norm(embedding_np)
        
        if norm == 0:
            return embedding  # Avoid division by zero
        
        normalized = embedding_np / norm
        return normalized.tolist()
    
    def _embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts (LEGACY - internal method)
        
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
                # Call Gemini embedding API with optimized dimensions
                result = self.client.models.embed_content(
                    model=self.model_name,
                    contents=text,
                    config=types.EmbedContentConfig(
                        output_dimensionality=self.dimension,
                        task_type="RETRIEVAL_DOCUMENT"
                    )
                )
                
                # Extract embedding values
                embedding = result.embeddings[0].values
                embeddings_list.append(embedding)
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to embed single text: {e}")
                # Fallback: zero vector with 768 dimensions
                embeddings_list.append([0.0] * self.dimension)
        
        # Convert to numpy array
        embeddings = np.array(embeddings_list, dtype=np.float32)
        
        # L2-normalize for cosine similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)  # Avoid division by zero
        embeddings = embeddings / norms
        
        return embeddings
    
    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a search query (UPDATED - uses new method)
        
        Args:
            query: Search query text
            
        Returns:
            Embedding vector as list (768 dimensions)
        """
        try:
            return self.generate_single_embedding(query, task_type="RETRIEVAL_QUERY")
        except Exception as e:
            logger.error(f"❌ Failed to embed query: {e}")
            raise
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts (UPDATED - uses new method)
        
        Args:
            texts: List of text strings
            
        Returns:
            List of embedding vectors (each as a list of floats, 768 dimensions)
        """
        try:
            logger.info(f"🔄 Generating embeddings for {len(texts)} texts...")
            
            embeddings_list = []
            
            # Process in batches to avoid rate limits
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i:i + self.batch_size]
                
                # Generate embeddings for this batch
                batch_embeddings = self.generate_embeddings(
                    batch,
                    task_type="RETRIEVAL_DOCUMENT"
                )
                
                embeddings_list.extend(batch_embeddings)
                
                # Rate limiting
                if i + self.batch_size < len(texts):
                    time.sleep(self.rate_limit_delay)
                
                logger.info(f"✅ Embedded batch {i//self.batch_size + 1}/{(len(texts)-1)//self.batch_size + 1}")
            
            logger.info(f"✅ Generated {len(embeddings_list)} embeddings")
            return embeddings_list
            
        except Exception as e:
            logger.error(f"❌ Failed to embed batch: {e}")
            raise
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings from this model"""
        return self.dimension  # Now returns 768 instead of 3072


# Global instance
embedding_service = EmbeddingService()
