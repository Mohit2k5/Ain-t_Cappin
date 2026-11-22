import pytest
import httpx
from app.main import app


@pytest.mark.anyio
async def test_root_health_endpoint():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "aint-cappin-backend"
        assert "version" in data
        assert "environment" in data


@pytest.mark.anyio
async def test_api_health_endpoint():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.anyio
async def test_fact_check_valid_request():
    payload = {
        "claim": "Water boils at 100 degrees Celsius at sea level.",
        "language": "en",
    }
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/fact-check", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["claim"] == payload["claim"]
        assert data["verdict"] in [
            "True",
            "False",
            "Partially True",
            "Misleading",
            "Unverified",
            "Outdated",
        ]
        assert "confidence" in data
        assert "assessment_agreement" in data
        assert "evidence" in data
        assert "sources" in data
        assert "processing_metadata" in data
        assert "category" in data["processing_metadata"]


@pytest.mark.anyio
@pytest.mark.parametrize(
    "claim,expected_category",
    [
        ("NASA confirmed new evidence of liquid water on Mars.", "Science"),
        ("Drinking baking soda cures cancer.", "Health"),
        ("The Federal Reserve increased interest rates to slow inflation.", "Finance"),
    ],
)
async def test_fact_check_categories_end_to_end(claim, expected_category):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/fact-check", json={"claim": claim})
        assert response.status_code == 200
        data = response.json()
        assert data["processing_metadata"]["category"] == expected_category
        assert len(data["sources"]) > 0


@pytest.mark.anyio
async def test_fact_check_invalid_claim_too_short():
    payload = {"claim": "ab"}
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/fact-check", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
        assert data["status_code"] == 422


@pytest.mark.anyio
async def test_fact_check_invalid_claim_whitespace_only():
    payload = {"claim": "     "}
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/fact-check", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
        assert data["status_code"] == 422


@pytest.mark.anyio
async def test_cors_headers():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        headers = {
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        }
        response = await client.options("/api/v1/fact-check", headers=headers)
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
