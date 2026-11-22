import re
from typing import List
from app.schemas.document import ProcessedDocument
from app.schemas.rag import DocumentChunk


class DocumentChunker:
    """Splits processed documents into contextually coherent passages with metadata tracking."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, doc: ProcessedDocument) -> List[DocumentChunk]:
        """Splits a single document into bounded chunks preserving sentence and paragraph boundaries."""
        if not doc.content or not doc.content.strip():
            return []

        text = doc.content.strip()
        chunks: List[DocumentChunk] = []

        # If document is shorter than chunk size, return it as a single chunk
        if len(text) <= self.chunk_size:
            chunk = DocumentChunk(
                chunk_id=f"{doc.domain}_0",
                document_url=doc.url,
                document_title=doc.title,
                domain=doc.domain,
                text=text,
                chunk_index=0,
                character_length=len(text),
                metadata={
                    "content_type": doc.content_type,
                    "author": doc.author,
                    "publication_date": doc.publication_date,
                },
            )
            return [chunk]

        # Break text into paragraphs
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        current_chunk_text = ""
        chunk_idx = 0

        for para in paragraphs:
            # If adding this paragraph exceeds chunk size and we already have content, finalize current chunk
            if len(current_chunk_text) + len(para) > self.chunk_size and len(current_chunk_text) >= min(self.chunk_size // 2, 50):
                chunk = DocumentChunk(
                    chunk_id=f"{doc.domain}_{chunk_idx}",
                    document_url=doc.url,
                    document_title=doc.title,
                    domain=doc.domain,
                    text=current_chunk_text.strip(),
                    chunk_index=chunk_idx,
                    character_length=len(current_chunk_text.strip()),
                    metadata={
                        "content_type": doc.content_type,
                        "publication_date": doc.publication_date,
                    },
                )
                chunks.append(chunk)
                chunk_idx += 1

                # Start new chunk with overlap
                overlap_text = current_chunk_text[-self.chunk_overlap:] if len(current_chunk_text) > self.chunk_overlap else ""
                current_chunk_text = f"{overlap_text} {para}".strip()
            else:
                if current_chunk_text:
                    current_chunk_text += f"\n\n{para}"
                else:
                    current_chunk_text = para

        # Append trailing chunk
        if current_chunk_text and len(current_chunk_text.strip()) >= 50:
            chunk = DocumentChunk(
                chunk_id=f"{doc.domain}_{chunk_idx}",
                document_url=doc.url,
                document_title=doc.title,
                domain=doc.domain,
                text=current_chunk_text.strip(),
                chunk_index=chunk_idx,
                character_length=len(current_chunk_text.strip()),
                metadata={
                    "content_type": doc.content_type,
                    "publication_date": doc.publication_date,
                },
            )
            chunks.append(chunk)

        return chunks

    def chunk_documents(self, documents: List[ProcessedDocument]) -> List[DocumentChunk]:
        """Chunks a collection of processed documents."""
        all_chunks: List[DocumentChunk] = []
        for doc in documents:
            if doc.is_usable:
                all_chunks.extend(self.chunk_document(doc))
        return all_chunks


document_chunker = DocumentChunker()
