import pytest
from app.services.search_service import (
    SearchService,
    MockSearchProvider,
    SearchResultItem,
)
from app.schemas.claim import ClaimCategory
from app.services.factcheck_service import factcheck_service
from app.schemas.factcheck import FactCheckRequest


def test_url_normalization():
    raw_url = "https://WWW.NASA.gov/earth/geodesy/?utm_source=twitter&utm_medium=social&fbclid=12345#overview"
    normalized = SearchService.normalize_url(raw_url)
    assert normalized == "https://www.nasa.gov/earth/geodesy"


def test_filter_and_deduplicate():
    items = [
        SearchResultItem(
            title="Doc 1",
            url="https://nasa.gov/page1?utm_source=test",
            domain="nasa.gov",
            snippet="Snippet 1",
        ),
        SearchResultItem(
            title="Doc 1 Duplicate",
            url="https://nasa.gov/page1",
            domain="nasa.gov",
            snippet="Snippet 1 duplicate",
        ),
        SearchResultItem(
            title="Image File",
            url="https://nasa.gov/earth.jpg",
            domain="nasa.gov",
            snippet="Image description",
        ),
        SearchResultItem(
            title="Doc 2",
            url="https://nature.com/article2",
            domain="nature.com",
            snippet="Snippet 2",
        ),
    ]

    filtered = SearchService.filter_and_deduplicate(items)
    assert len(filtered) == 2
    urls = [item.url for item in filtered]
    assert "https://nasa.gov/page1" in urls
    assert "https://nature.com/article2" in urls


@pytest.mark.anyio
async def test_mock_search_provider():
    provider = MockSearchProvider()
    results = await provider.search("Earth shape", max_results=2)
    assert len(results) == 2
    assert "nasa.gov" in results[0].url


@pytest.mark.anyio
async def test_search_service_execution():
    service = SearchService(provider=MockSearchProvider())
    queries = ["Earth shape scientific evidence", "NASA Earth geodesy measurements"]
    results = await service.execute_searches(queries, max_results_per_query=2)

    assert len(results) > 0
    # Verify quality assessments were attached
    for item in results:
        assert item.quality_assessment is not None
        assert item.quality_assessment.quality_score >= 0.0

    # Verify sorted by quality score descending
    scores = [item.quality_assessment.quality_score for item in results]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.anyio
async def test_fact_check_service_pipeline_phase_2():
    req = FactCheckRequest(claim="The Earth is flat.")
    response = await factcheck_service.verify_claim(req)

    assert response.claim == "The Earth is flat."
    assert response.processing_metadata["category"] == ClaimCategory.SCIENCE.value
    assert len(response.processing_metadata["queries_executed"]) >= 3
    assert len(response.sources) > 0
