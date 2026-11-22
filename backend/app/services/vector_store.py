import faiss
import numpy as np
from typing import List, Tuple
from app.core.logging import logger
from app.schemas.rag import DocumentChunk


class VectorStore:
    """In-memory FAISS vector index providing exact cosine similarity retrieval for document chunks."""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        # IndexFlatIP computes exact inner product (equivalent to cosine similarity on L2-normalized vectors)
        self.index = faiss.IndexFlatIP(self.dimension)
        self.chunks: List[DocumentChunk] = []

    def add_chunks(self, chunks: List[DocumentChunk], embeddings: np.ndarray) -> None:
        """Adds document chunks and their corresponding normalized vectors into the index."""
        if not chunks or embeddings.size == 0:
            return

        if embeddings.shape[1] != self.dimension:
            raise ValueError(
                f"Embedding dimension mismatch: expected {self.dimension}, got {embeddings.shape[1]}"
            )

        # Ensure float32 contiguous array
        vectors = np.ascontiguousarray(embeddings, dtype=np.float32)
        self.index.add(vectors)
        self.chunks.extend(chunks)
        logger.info("Added %d passages to in-memory FAISS index (total: %d).", len(chunks), len(self.chunks))

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Tuple[DocumentChunk, float]]:
        """Performs semantic similarity search and returns ranked top-k chunks with cosine scores."""
        if self.index.ntotal == 0 or len(self.chunks) == 0:
            return []

        k = min(top_k, self.index.ntotal)
        query_vector = np.ascontiguousarray(query_embedding, dtype=np.float32)

        # Search index
        scores, indices = self.index.search(query_vector, k)

        results: List[Tuple[DocumentChunk, float]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.chunks):
                continue
            # Cosine similarity clamp 0.0 to 1.0
            norm_score = float(max(0.0, min(1.0, (score + 1.0) / 2.0 if score < 0 else score)))
            results.append((self.chunks[idx], round(norm_score, 4)))

        return results

    @property
    def total_passages(self) -> int:
        return self.index.ntotal
