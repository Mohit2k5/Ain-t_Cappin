import hashlib
import numpy as np
from typing import List, Optional
from app.core.logging import logger


class EmbeddingService:
    """Produces normalized vector embeddings using Sentence Transformers with a deterministic fallback."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", dimension: int = 384):
        self.model_name = model_name
        self.dimension = dimension
        self.model = None
        self._initialize_model()

    def _initialize_model(self):
        """Attempts to load SentenceTransformer model or falls back gracefully."""
        try:
            from sentence_transformers import SentenceTransformer
            # Set a fast local load or initialize
            self.model = SentenceTransformer(self.model_name)
            logger.info("SentenceTransformer '%s' loaded successfully.", self.model_name)
        except Exception as e:
            logger.info(
                "Could not initialize local SentenceTransformer model (%s). Using deterministic semantic vectorizer fallback.",
                str(e),
            )
            self.model = None

    def _deterministic_embed(self, text: str) -> np.ndarray:
        """Generates a normalized deterministic semantic vector for offline/fallback environments.
        
        Uses character n-grams and hashing to produce consistent 384-dim semantic embeddings.
        """
        vec = np.zeros(self.dimension, dtype=np.float32)
        words = text.lower().split()
        if not words:
            return vec

        for word in words:
            # Word hash
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dimension
            val = ((h >> 8) % 1000) / 1000.0
            vec[idx] += float(val)

            # Character 3-grams for semantic fuzzy matching
            for i in range(max(1, len(word) - 2)):
                tri = word[i:i+3]
                th = int(hashlib.sha256(tri.encode("utf-8")).hexdigest(), 16)
                tidx = th % self.dimension
                vec[tidx] += 0.5

        # L2 normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Generates normalized embeddings for a list of document chunk strings."""
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)

        if self.model:
            try:
                embeddings = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
                return embeddings.astype(np.float32)
            except Exception as e:
                logger.warning("Inference with SentenceTransformer failed: %s; using fallback.", str(e))

        # Fallback
        vecs = [self._deterministic_embed(t) for t in texts]
        return np.array(vecs, dtype=np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        """Generates a normalized 1xD embedding for a search/verification query."""
        res = self.embed_texts([query])
        return res


embedding_service = EmbeddingService()
