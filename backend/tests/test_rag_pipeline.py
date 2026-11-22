import numpy as np
import pytest
from app.schemas.document import ProcessedDocument
from app.schemas.rag import DocumentChunk, RetrievedPassage, RAGContext
from app.services.chunker import document_chunker, DocumentChunker
from app.services.embedding_service import embedding_service
from app.services.vector_store import VectorStore
from app.services.retriever import evidence_retriever
from app.services.context_builder import context_builder
from app.services.rag_service import rag_service
from app.services.factcheck_service import factcheck_service
from app.schemas.factcheck import FactCheckRequest, VerdictEnum


def test_document_chunker_boundaries():
    text = (
        "Paragraph 1 contains scientific details about geodesy.\n\n"
        "Paragraph 2 discusses satellite measurements and orbital photography.\n\n"
        "Paragraph 3 reviews laser ranging observations of planetary bodies."
    )
    doc = ProcessedDocument(
        url="https://nasa.gov/geodesy",
        title="Geodesy",
        domain="nasa.gov",
        content=text,
        cleaned_length=len(text),
    )

    chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
    chunks = chunker.chunk_document(doc)

    assert len(chunks) >= 2
    for c in chunks:
        assert c.document_url == "https://nasa.gov/geodesy"
        assert c.domain == "nasa.gov"
        assert len(c.text) > 0


def test_embedding_service_normalization():
    texts = ["Earth is an oblate spheroid.", "Planetary curvature."]
    embeddings = embedding_service.embed_texts(texts)

    assert isinstance(embeddings, np.ndarray)
    assert embeddings.shape[0] == 2
    assert embeddings.shape[1] == embedding_service.dimension

    # Verify unit L2 norm
    for vec in embeddings:
        norm = np.linalg.norm(vec)
        assert pytest.approx(norm, 0.01) == 1.0


def test_vector_store_exact_similarity():
    store = VectorStore(dimension=embedding_service.dimension)
    chunk1 = DocumentChunk(
        chunk_id="nasa_1",
        document_url="https://nasa.gov/page1",
        document_title="NASA Geodesy",
        domain="nasa.gov",
        text="Earth curvature and oblate spheroid shape.",
    )
    chunk2 = DocumentChunk(
        chunk_id="snopes_1",
        document_url="https://snopes.com/factcheck",
        document_title="Flat Earth Fact Check",
        domain="snopes.com",
        text="Claims of flat earth are debunked by satellite observations.",
    )

    embeds = embedding_service.embed_texts([chunk1.text, chunk2.text])
    store.add_chunks([chunk1, chunk2], embeds)

    query_embed = embedding_service.embed_query("Earth curvature shape")
    matches = store.search(query_embed, top_k=2)

    assert len(matches) == 2
    top_chunk, top_score = matches[0]
    assert top_score >= 0.0
    assert top_chunk.chunk_id in {"nasa_1", "snopes_1"}


def test_context_builder_guardrails():
    chunk = DocumentChunk(
        chunk_id="test_1",
        document_url="https://nature.com/article1",
        document_title="Planetary Physics",
        domain="nature.com",
        text="Laser measurements verify curvature.",
    )
    passage = RetrievedPassage(chunk=chunk, score=0.92, perspective="refuting")
    context = context_builder.build_context("The Earth is flat.", [passage])

    assert "<user_claim>" in context.formatted_context
    assert "<retrieved_evidence>" in context.formatted_context
    assert "CRITICAL SECURITY GUARDRAIL" in context.formatted_context
    assert "https://nature.com/article1" in context.formatted_context
    assert context.unique_sources == ["https://nature.com/article1"]


@pytest.mark.anyio
async def test_rag_service_contradictory_evidence_assessment():
    chunk = DocumentChunk(
        chunk_id="snopes_1",
        document_url="https://snopes.com/factcheck/flat-earth",
        document_title="Flat Earth Debunked",
        domain="snopes.com",
        text="Satellite imagery and planetary geodesy confirm Earth is spherical. Flat Earth claims are completely debunked and false.",
    )
    passage = RetrievedPassage(chunk=chunk, score=0.95, perspective="refuting")
    context = context_builder.build_context("The Earth is flat.", [passage])

    assessment = await rag_service.assess_evidence(context)
    assert assessment.preliminary_verdict == "False"
    assert "https://snopes.com/factcheck/flat-earth" in assessment.contradictory_citations
    assert assessment.is_insufficient_evidence is False


@pytest.mark.anyio
async def test_rag_service_insufficient_evidence_handling():
    chunk = DocumentChunk(
        chunk_id="random_1",
        document_url="https://example.com/cooking",
        document_title="Baking Sourdough Bread",
        domain="example.com",
        text="Mix flour and water and let the yeast ferment for 12 hours.",
    )
    passage = RetrievedPassage(chunk=chunk, score=0.10, perspective="neutral")
    context = context_builder.build_context("Aliens landed in Texas yesterday.", [passage])

    assessment = await rag_service.assess_evidence(context)
    assert assessment.preliminary_verdict == "Unverified"
    assert assessment.is_insufficient_evidence is True


@pytest.mark.anyio
async def test_full_rag_pipeline_orchestration():
    req = FactCheckRequest(claim="The Earth is flat.")
    response = await factcheck_service.verify_claim(req)

    assert response.claim == "The Earth is flat."
    assert response.verdict == VerdictEnum.FALSE
    assert len(response.evidence) > 0
    assert len(response.sources) > 0
    assert response.processing_metadata["passages_retrieved"] > 0
    # Verify citations are traceable
    for ev in response.evidence:
        assert ev.url.startswith("http")
        assert len(ev.text) > 0
        assert ev.relationship.value in ["supports", "contradicts", "contextual", "neutral", "insufficient"]
