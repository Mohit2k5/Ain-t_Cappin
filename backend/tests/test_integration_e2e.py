import pytest
import httpx
from app.main import app
from app.schemas.factcheck import VerdictEnum, ConfidenceBand, EvidenceRelationship


ALL_CATEGORIES_TEST_DATA = [
    ("NASA confirmed new evidence of liquid water on Mars.", "Science"),
    ("Drinking lemon water and baking soda cures cancer.", "Health"),
    ("The President signed new federal legislation into law.", "Politics"),
    ("The Roman Empire collapsed in the 5th century AD.", "History"),
    ("OpenAI launched a new generative artificial intelligence model.", "Technology"),
    ("The Federal Reserve increased interest rates to combat inflation.", "Finance"),
    ("A severe earthquake struck the coastline today.", "Current events"),
    ("The Eiffel Tower is located in Paris, France.", "General factual claims"),
]


@pytest.mark.anyio
@pytest.mark.parametrize("claim,expected_category", ALL_CATEGORIES_TEST_DATA)
async def test_all_8_categories_e2e_pipeline(claim, expected_category):
    """Verify that all 8 taxonomy categories successfully execute end-to-end through the RAG pipeline."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/fact-check", json={"claim": claim})
        assert response.status_code == 200
        data = response.json()

        # Schema conformity
        assert data["claim"] == claim
        assert data["verdict"] in [v.value for v in VerdictEnum]
        assert len(data["explanation"]) >= 10
        assert isinstance(data["evidence"], list)
        assert isinstance(data["sources"], list)

        # Confidence conformity
        assert data["confidence"]["level"] in [c.value for c in ConfidenceBand]
        assert 0.0 <= data["confidence"]["score"] <= 100.0

        # Self-consistency agreement conformity
        assert 0.0 <= data["assessment_agreement"]["percentage"] <= 100.0
        assert data["assessment_agreement"]["agreeing"] <= data["assessment_agreement"]["total"]

        # Telemetry & category classification
        assert data["processing_metadata"]["category"] == expected_category
        assert data["processing_metadata"]["total_chunks_indexed"] >= 0


@pytest.mark.anyio
async def test_fact_check_with_context():
    """Verify handling of claims with additional context."""
    payload = {
        "claim": "The Great Wall of China is visible from the Moon with the naked eye.",
        "language": "en",
        "context": "Reported in a popular viral TikTok video claim.",
    }
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/fact-check", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["verdict"] in ["False", "Misleading", "Unverified"]
        assert len(data["explanation"]) > 20


@pytest.mark.anyio
async def test_fact_check_upper_boundary_claim_length():
    """Verify claim near max boundary length (900-1000 chars) succeeds."""
    long_claim = "Scientists at international universities have extensively tested " + ("and verified " * 70) + "the claim."
    long_claim = long_claim[:950]  # within 1000
    assert 900 <= len(long_claim) <= 1000

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/fact-check", json={"claim": long_claim})
        assert response.status_code == 200
        data = response.json()
        assert "verdict" in data


@pytest.mark.anyio
async def test_fact_check_exceeds_max_boundary_fails():
    """Verify claim over 1000 characters is rejected with 422."""
    excessive_claim = "A" * 1005
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/fact-check", json={"claim": excessive_claim})
        assert response.status_code == 422
        data = response.json()
        assert data["status_code"] == 422


@pytest.mark.anyio
async def test_cors_preflight_and_response_headers():
    """Verify CORS headers for Vite frontend origins."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        headers = {
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        }
        res = await client.options("/api/v1/fact-check", headers=headers)
        assert res.status_code == 200
        assert res.headers.get("access-control-allow-origin") in ["http://localhost:5173", "*"]
