from typing import List, Dict, Union
import re
import logging
from app.schemas.guide import WebSearchResult
logger = logging.getLogger(__name__)


class ChunkingService:
    """Service for intelligently chunking text for embeddings"""
    
    def __init__(self, max_chunk_size: int = 500, chunk_overlap: int = 100):
        """
        Initialize chunking service
        
        Args:
            max_chunk_size: Maximum tokens per chunk
            chunk_overlap: Number of overlapping tokens between chunks
        """
        self.max_chunk_size = max_chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_web_results(
        self, 
        web_results: List[Union[WebSearchResult, Dict]], 
        city: str, 
        theme: str
    ) -> List[Dict]:
        """
        Chunk web search results into embeddable pieces
        
        Args:
            web_results: List of WebSearchResult objects
            city: City name for metadata
            theme: Theme for metadata
            
        Returns:
            List of chunk dictionaries with content and metadata
        """
        chunks = []
        
        for result in web_results:
            # ✅ HANDLE BOTH WebSearchResult OBJECTS AND DICTS
            if isinstance(result, dict):
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                url = result.get("url", "")
            else:
                # WebSearchResult object
                title = result.title
                snippet = result.snippet
                url = result.url
            
            # Combine title and snippet for richer context
            full_text = f"{title}\n\n{snippet}"
            
            # Clean the text
            cleaned_text = self._clean_text(full_text)
            
            # Split into sentences
            sentences = self._split_into_sentences(cleaned_text)
            
            # Create chunks from sentences
            text_chunks = self._create_chunks_from_sentences(sentences)
            
            # Add metadata to each chunk
            for idx, chunk_text in enumerate(text_chunks):
                if chunk_text.strip():  # Skip empty chunks
                    chunks.append({
                        "content": chunk_text.strip(),
                        "city": city,
                        "theme": theme,
                        "source_url": url,
                        "source_title": title,
                        "chunk_index": idx,
                        "total_chunks_from_source": len(text_chunks)
                    })
        
        logger.info(f" Created {len(chunks)} chunks from {len(web_results)} web results")
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s.,!?;:()\-\'\"]+', '', text)
        
        # Remove URLs
        text = re.sub(r'http\S+|www.\S+', '', text)
        
        return text.strip()
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting (handles most cases)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _create_chunks_from_sentences(self, sentences: List[str]) -> List[str]:
        """
        Create overlapping chunks from sentences
        
        Ensures chunks don't exceed max_chunk_size while maintaining context
        """
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence.split())
            
            # If single sentence is too large, split it
            if sentence_size > self.max_chunk_size:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
                    current_size = 0
                
                # Split large sentence into smaller parts
                words = sentence.split()
                for i in range(0, len(words), self.max_chunk_size):
                    chunk_words = words[i:i + self.max_chunk_size]
                    chunks.append(' '.join(chunk_words))
                continue
            
            # Check if adding sentence exceeds limit
            if current_size + sentence_size > self.max_chunk_size:
                # Save current chunk
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                
                # Start new chunk with overlap
                overlap_sentences = self._get_overlap_sentences(current_chunk)
                current_chunk = overlap_sentences + [sentence]
                current_size = sum(len(s.split()) for s in current_chunk)
            else:
                current_chunk.append(sentence)
                current_size += sentence_size
        
        # Add final chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _get_overlap_sentences(self, sentences: List[str]) -> List[str]:
        """Get sentences for overlap between chunks"""
        if not sentences:
            return []
        
        # Calculate how many sentences to include in overlap
        total_words = sum(len(s.split()) for s in sentences)
        overlap_target = self.chunk_overlap
        
        overlap_sentences = []
        overlap_size = 0
        
        # Take sentences from the end until we reach overlap size
        for sentence in reversed(sentences):
            sentence_size = len(sentence.split())
            if overlap_size + sentence_size <= overlap_target:
                overlap_sentences.insert(0, sentence)
                overlap_size += sentence_size
            else:
                break
        
        return overlap_sentences


# Global instance
chunking_service = ChunkingService()
