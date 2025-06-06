"""
Embedding Service
Generates vector embeddings using sentence-transformers for semantic search
"""

import asyncio
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Union
from functools import lru_cache
import hashlib
import pickle
import os
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("sentence-transformers not available. Embedding service will not work.")

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EmbeddingService:
    """Service for generating vector embeddings from text"""
    
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.embedding_model
        self.model = None
        self.cache_dir = Path("./cache/embeddings")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the sentence transformer model"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.error("sentence-transformers not available. Cannot initialize embedding model.")
            raise ImportError("sentence-transformers package required for embedding service")
        
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            
            # Get model dimension
            self.embedding_dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"Model loaded successfully. Embedding dimension: {self.embedding_dimension}")
            
        except Exception as e:
            logger.error(f"Failed to load embedding model {self.model_name}: {e}")
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Input text to embed
            
        Returns:
            List of float values representing the embedding vector
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return [0.0] * self.embedding_dimension
        
        try:
            # Check cache first
            cached_embedding = self._get_cached_embedding(text)
            if cached_embedding is not None:
                return cached_embedding
            
            # Generate new embedding
            embedding = self.model.encode(text, convert_to_numpy=True)
            embedding_list = embedding.tolist()
            
            # Cache the result
            self._cache_embedding(text, embedding_list)
            
            return embedding_list
            
        except Exception as e:
            logger.error(f"Failed to generate embedding for text: {e}")
            # Return zero vector as fallback
            return [0.0] * self.embedding_dimension
    
    async def embed_text_async(self, text: str) -> List[float]:
        """
        Async wrapper for embedding generation
        Runs the embedding in a thread pool to avoid blocking
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.embed_text, text)
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently
        
        Args:
            texts: List of input texts
            batch_size: Number of texts to process in each batch
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        try:
            embeddings = []
            
            # Process in batches
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                
                # Check cache for batch items
                batch_embeddings = []
                texts_to_embed = []
                indices_to_embed = []
                
                for idx, text in enumerate(batch_texts):
                    cached = self._get_cached_embedding(text)
                    if cached is not None:
                        batch_embeddings.append((i + idx, cached))
                    else:
                        texts_to_embed.append(text)
                        indices_to_embed.append(i + idx)
                
                # Generate embeddings for non-cached texts
                if texts_to_embed:
                    new_embeddings = self.model.encode(
                        texts_to_embed, 
                        convert_to_numpy=True,
                        batch_size=min(batch_size, len(texts_to_embed)),
                        show_progress_bar=len(texts_to_embed) > 10
                    )
                    
                    # Cache new embeddings and add to results
                    for idx, (text, embedding) in enumerate(zip(texts_to_embed, new_embeddings)):
                        embedding_list = embedding.tolist()
                        self._cache_embedding(text, embedding_list)
                        batch_embeddings.append((indices_to_embed[idx], embedding_list))
                
                # Sort by original index and extract embeddings
                batch_embeddings.sort(key=lambda x: x[0])
                embeddings.extend([emb for _, emb in batch_embeddings])
            
            logger.info(f"Generated embeddings for {len(texts)} texts")
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            # Return zero vectors as fallback
            return [[0.0] * self.embedding_dimension for _ in texts]
    
    async def embed_batch_async(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Async wrapper for batch embedding generation
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.embed_batch, texts, batch_size)
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Compute cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score between -1 and 1
        """
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Compute cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Failed to compute similarity: {e}")
            return 0.0
    
    def find_most_similar(
        self, 
        query_embedding: List[float], 
        candidate_embeddings: List[List[float]], 
        top_k: int = 5
    ) -> List[tuple]:
        """
        Find the most similar embeddings to a query
        
        Args:
            query_embedding: Query embedding vector
            candidate_embeddings: List of candidate embedding vectors
            top_k: Number of top results to return
            
        Returns:
            List of (index, similarity_score) tuples, sorted by similarity
        """
        try:
            similarities = []
            
            for idx, candidate in enumerate(candidate_embeddings):
                similarity = self.compute_similarity(query_embedding, candidate)
                similarities.append((idx, similarity))
            
            # Sort by similarity (descending) and return top_k
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Failed to find similar embeddings: {e}")
            return []
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        # Use hash of text + model name for cache key
        content = f"{self.model_name}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _get_cached_embedding(self, text: str) -> Optional[List[float]]:
        """Retrieve cached embedding for text"""
        try:
            cache_key = self._get_cache_key(text)
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            
            return None
            
        except Exception as e:
            logger.debug(f"Cache retrieval failed: {e}")
            return None
    
    def _cache_embedding(self, text: str, embedding: List[float]):
        """Cache embedding for text"""
        try:
            cache_key = self._get_cache_key(text)
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            
            with open(cache_file, 'wb') as f:
                pickle.dump(embedding, f)
                
        except Exception as e:
            logger.debug(f"Cache storage failed: {e}")
    
    def clear_cache(self):
        """Clear the embedding cache"""
        try:
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink()
            logger.info("Embedding cache cleared")
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            cache_files = list(self.cache_dir.glob("*.pkl"))
            total_size = sum(f.stat().st_size for f in cache_files)
            
            return {
                "cached_embeddings": len(cache_files),
                "total_cache_size_mb": round(total_size / (1024 * 1024), 2),
                "model_name": self.model_name,
                "embedding_dimension": self.embedding_dimension
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}
    
    @property
    def is_ready(self) -> bool:
        """Check if the embedding service is ready to use"""
        return self.model is not None and SENTENCE_TRANSFORMERS_AVAILABLE
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        if not self.is_ready:
            return {"error": "Model not loaded"}
        
        return {
            "model_name": self.model_name,
            "embedding_dimension": self.embedding_dimension,
            "max_sequence_length": getattr(self.model, 'max_seq_length', 'unknown'),
            "model_type": type(self.model).__name__
        } 