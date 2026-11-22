import asyncio
from typing import List, Set, Tuple
from app.core.logging import logger
from app.schemas.document import ProcessedDocument
from app.schemas.rag import DocumentChunk, RetrievedPassage
from app.services.chunker import document_chunker
from app.services.embedding_service import embedding_service
from app.services.vector_store import VectorStore


class EvidenceRetriever:
    """Orchestrates document chunking, vector indexing, and multi-perspective evidence retrieval."""

    def __init__(self, top_k_per_query: int = 4, max_total_evidence: int = 8):
        self.top_k = top_k_per_query
        self.max_total_evidence = max_total_evidence

    def retrieve_evidence(
        self,
        claim: str,
        documents: List[ProcessedDocument],
        search_queries: List[str] = None,
    ) -> List[RetrievedPassage]:
        """Indexes extracted documents in an in-memory FAISS store and retrieves multi-angle evidence."""
        if not documents:
            logger.info("No documents provided to retriever; returning empty evidence.")
            return []

        # 1. Chunk documents
        chunks = document_chunker.chunk_documents(documents)
        if not chunks:
            logger.warning("Document chunking produced 0 passages.")
            return []

        # 2. Generate embeddings
        chunk_texts = [c.text for c in chunks]
        embeddings = embedding_service.embed_texts(chunk_texts)

        # 3. Create FAISS index
        store = VectorStore(dimension=embedding_service.dimension)
        store.add_chunks(chunks, embeddings)

        # 4. Multi-perspective query embeddings
        retrieval_queries: List[Tuple[str, str]] = [
            (claim, "neutral"),
            (f"{claim} debunk refuted false fact check", "refuting"),
            (f"{claim} proven true verified evidence", "supporting"),
        ]

        if search_queries:
            for q in search_queries[:2]:
                retrieval_queries.append((q, "neutral"))

        seen_chunk_ids: Set[str] = set()
        retrieved_passages: List[RetrievedPassage] = []

        for query_str, perspective in retrieval_queries:
            q_emb = embedding_service.embed_query(query_str)
            matches = store.search(q_emb, top_k=self.top_k)

            for chunk, score in matches:
                # Deduplicate by chunk_id
                if chunk.chunk_id in seen_chunk_ids:
                    continue

                # Filter out irrelevant low-scoring matches (threshold > 0.15)
                if score < 0.15:
                    continue

                seen_chunk_ids.add(chunk.chunk_id)
                retrieved_passages.append(
                    RetrievedPassage(
                        chunk=chunk,
                        score=score,
                        perspective=perspective,
                    )
                )

        # Rank passages primarily by similarity score
        retrieved_passages.sort(key=lambda p: p.score, reverse=True)
        final_evidence = retrieved_passages[: self.max_total_evidence]
        logger.info(
            "Retrieved %d high-relevance evidence passages across %d unique sources.",
            len(final_evidence),
            len({p.chunk.document_url for p in final_evidence}),
        )
        return final_evidence


evidence_retriever = EvidenceRetriever()
