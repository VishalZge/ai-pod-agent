"""
Embedding Service
Uses Gemini embeddings for similarity matching to detect duplicate/similar designs.
"""

import json
import time
from typing import List, Dict, Any, Tuple
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from services.gemini_service import GeminiService
from utils.logger import api_logger, app_logger
from utils.config import Config


class EmbeddingService:
    """Service for generating and comparing embeddings."""

    def __init__(self):
        """Initialize embedding service."""
        self.gemini = GeminiService()
        self.similarity_threshold = Config.SIMILARITY_THRESHOLD
        self.embedding_cache = {}  # Simple in-memory cache

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        try:
            # Check cache first
            if text in self.embedding_cache:
                return self.embedding_cache[text]

            start_time = time.time()
            embedding = self.gemini.generate_embeddings(text)
            response_time = time.time() - start_time

            # Cache result
            self.embedding_cache[text] = embedding

            api_logger.info(
                json.dumps(
                    {
                        "service": "embedding",
                        "endpoint": "embed_text",
                        "status": 200,
                        "response_time_ms": response_time * 1000,
                        "vector_dim": len(embedding),
                    }
                )
            )

            return embedding

        except Exception as e:
            app_logger.error(f"Text embedding failed: {str(e)}")
            raise

    def calculate_similarity(
        self,
        text1: str,
        text2: str,
    ) -> float:
        """
        Calculate similarity between two texts (0-1).

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0-1)
        """
        try:
            embedding1 = self.embed_text(text1)
            embedding2 = self.embed_text(text2)

            # Convert to numpy arrays
            vec1 = np.array(embedding1).reshape(1, -1)
            vec2 = np.array(embedding2).reshape(1, -1)

            # Calculate cosine similarity
            similarity = cosine_similarity(vec1, vec2)[0][0]

            return float(similarity)

        except Exception as e:
            app_logger.error(f"Similarity calculation failed: {str(e)}")
            raise

    def find_similar_designs(
        self,
        design_description: str,
        existing_designs: List[Dict[str, Any]],
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Find similar designs from existing designs.

        Args:
            design_description: New design description
            existing_designs: List of existing design dicts with 'description' key

        Returns:
            List of (design_dict, similarity_score) tuples, sorted by similarity
        """
        try:
            similar_designs = []

            # Get embedding for new design
            new_embedding = self.embed_text(design_description)

            # Compare with existing designs
            for design in existing_designs:
                if "description" not in design:
                    continue

                existing_embedding = self.embed_text(design["description"])

                # Calculate similarity
                vec1 = np.array(new_embedding).reshape(1, -1)
                vec2 = np.array(existing_embedding).reshape(1, -1)
                similarity = cosine_similarity(vec1, vec2)[0][0]

                if similarity > self.similarity_threshold:
                    similar_designs.append((design, float(similarity)))

            # Sort by similarity (highest first)
            similar_designs.sort(key=lambda x: x[1], reverse=True)

            return similar_designs

        except Exception as e:
            app_logger.error(f"Similar design search failed: {str(e)}")
            return []

    def is_duplicate(
        self,
        design_description: str,
        existing_designs: List[Dict[str, Any]],
    ) -> Tuple[bool, float]:
        """
        Check if design is a duplicate of existing designs.

        Args:
            design_description: New design description
            existing_designs: List of existing designs

        Returns:
            (is_duplicate, max_similarity_score)
        """
        try:
            similar = self.find_similar_designs(design_description, existing_designs)

            if similar:
                max_similarity = similar[0][1]
                is_dup = max_similarity >= self.similarity_threshold
                return is_dup, max_similarity

            return False, 0.0

        except Exception as e:
            app_logger.error(f"Duplicate check failed: {str(e)}")
            return False, 0.0

    def batch_embed(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings
        """
        embeddings = []
        for text in texts:
            try:
                embedding = self.embed_text(text)
                embeddings.append(embedding)
            except Exception as e:
                app_logger.error(f"Batch embed failed for text: {str(e)}")
                embeddings.append([])

        return embeddings

    def clear_cache(self) -> None:
        """Clear embedding cache."""
        self.embedding_cache.clear()
        app_logger.info("Embedding cache cleared")

    def get_cache_size(self) -> int:
        """Get current cache size."""
        return len(self.embedding_cache)
