import pytest
import httpx
from app.main import app


@pytest.mark.anyio
async def test_health_check():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "aint-cappin-backend"


@pytest.mark.anyio
async def test_fact_check_starter_endpoint():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/fact-check",
            json={"claim": "The Earth is flat."},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["claim"] == "The Earth is flat."
        assert "verdict" in data
        assert "confidence" in data
