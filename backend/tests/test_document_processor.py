import io
import pytest
from app.services.document_processor import DocumentProcessor, document_processor
from app.schemas.claim import SearchResultItem
from app.schemas.document import ProcessedDocument
from app.services.factcheck_service import factcheck_service
from app.schemas.factcheck import FactCheckRequest
import pypdf


def test_clean_text():
    raw = (
        "  Title of Article\n\n"
        "Accept All Cookies and read our Privacy Policy.\n\n"
        "This is substantive evidence content verifying scientific observations.\n"
        "Another paragraph with “smart quotes” and\xa0non-breaking spaces.  "
    )
    cleaned = DocumentProcessor.clean_text(raw)
    assert "Accept All Cookies" not in cleaned
    assert "substantive evidence content" in cleaned
    assert '"smart quotes"' in cleaned
    assert "\xa0" not in cleaned


def test_extract_html_removes_scripts_and_extracts_article():
    html_content = b"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>NASA - Earth Geodesy</title>
        <meta property="og:title" content="Earth's Oblate Spheroid Shape" />
        <meta name="author" content="Dr. Jane Doe" />
        <meta property="article:published_time" content="2023-10-15T12:00:00Z" />
        <script>alert('malicious script');</script>
        <style>body { background: black; }</style>
    </head>
    <body>
        <header><nav><a href="/">Home</a><a href="/about">About</a></nav></header>
        <article>
            <h1>Planetary Geodesy</h1>
            <p>Satellite laser ranging and GPS constellations provide empirical proof of Earth's curvature.</p>
            <p>The equatorial diameter exceeds the polar diameter by approximately 43 kilometers.</p>
        </article>
        <footer><p>All Rights Reserved &copy; 2023</p></footer>
    </body>
    </html>
    """
    cleaned, title, author, pub_date = DocumentProcessor.extract_html(html_content)

    assert title == "Earth's Oblate Spheroid Shape"
    assert author == "Dr. Jane Doe"
    assert pub_date == "2023-10-15"
    assert "alert" not in cleaned
    assert "Planetary Geodesy" in cleaned or "Satellite laser ranging" in cleaned
    assert "empirical proof of Earth's curvature" in cleaned
    assert "All Rights Reserved" not in cleaned


def test_extract_pdf_in_memory():
    # Build a simple PDF in memory using pypdf writer
    writer = pypdf.PdfWriter()
    page = writer.add_blank_page(width=200, height=200)
    # Add metadata
    writer.add_metadata({
        "/Title": "Empirical Geodesy Report",
        "/Author": "Planetary Science Institute",
    })

    pdf_buffer = io.BytesIO()
    writer.write(pdf_buffer)
    pdf_bytes = pdf_buffer.getvalue()

    cleaned, title, author, pub_date = DocumentProcessor.extract_pdf(pdf_bytes)
    assert title == "Empirical Geodesy Report"
    assert author == "Planetary Science Institute"


@pytest.mark.anyio
async def test_fetch_document_fallback_to_snippet_on_error():
    candidate = SearchResultItem(
        title="Scientific Observation of Curvature",
        url="https://nonexistent-domain-123456789.org/evidence.html",
        domain="nonexistent-domain-123456789.org",
        snippet="Empirical measurements from high-altitude weather balloons verify the horizon drops below eye level.",
        publication_date="2024-01-01",
    )

    processor = DocumentProcessor(timeout_seconds=2.0)
    doc = await processor.fetch_document(candidate)

    assert doc.url == candidate.url
    assert doc.content_type == "snippet_fallback"
    assert doc.is_usable is True
    assert "Empirical measurements" in doc.content
    assert doc.extraction_error is not None


@pytest.mark.anyio
async def test_process_candidates_batch():
    candidates = [
        SearchResultItem(
            title="Candidate 1",
            url="https://test1-invalid.org/doc1",
            domain="test1-invalid.org",
            snippet="Detailed factual passage explaining the scientific consensus.",
        ),
        SearchResultItem(
            title="Candidate 2",
            url="https://test2-invalid.org/doc2",
            domain="test2-invalid.org",
            snippet="Another authoritative report providing data points and measurements.",
        ),
    ]

    docs = await document_processor.process_candidates(candidates)
    assert len(docs) == 2
    assert all(d.is_usable for d in docs)
    assert all(d.cleaned_length > 0 for d in docs)


@pytest.mark.anyio
async def test_fact_check_service_pipeline_phase_3():
    req = FactCheckRequest(claim="The Earth is flat.")
    response = await factcheck_service.verify_claim(req)

    assert response.claim == "The Earth is flat."
    assert "documents_processed" in response.processing_metadata
    assert response.processing_metadata["documents_processed"] > 0
    assert response.processing_metadata["total_text_length"] > 0
    assert len(response.sources) > 0
