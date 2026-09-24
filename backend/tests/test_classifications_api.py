"""Integration tests for the classifications API endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_get_classification_schema():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/classifications/schema")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "1.0.0"
        assert "intent" in data
        assert "department" in data
        assert "urgency" in data
        assert "sentiment" in data
        assert "spam" in data
        assert "requires_human" in data
        assert "priority" in data
        assert len(data["intent"]["options"]) == 8
        assert len(data["priority"]["rubric"]) == 5


@pytest.mark.asyncio
async def test_get_provider_status():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/classifications/provider-status")
        assert response.status_code == 200
        data = response.json()
        assert "configured" in data
        assert "mode" in data
        assert "provider" in data
        assert "gateway_url" in data
        assert "model" in data


@pytest.mark.asyncio
async def test_post_test_classification_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/classifications/test",
            json={
                "subject": "Unable to log in to my account",
                "body": "I forgot my password and the reset link is giving a 404 error.",
                "force_mock": True,
            },
        )
        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "id" in data
        assert "intent" in data
        assert data["intent"]["choice"] == "account_issue"
        assert "department" in data
        assert "urgency" in data
        assert "sentiment" in data
        assert "spam" in data
        assert data["spam"]["value"] is False
        assert "requires_human" in data
        assert "priority" in data
        assert "latency" in data
        assert "trace" in data
        assert data["is_mock"] is True


@pytest.mark.asyncio
async def test_post_test_classification_empty_fails():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/classifications/test",
            json={"subject": "   ", "body": ""},
        )
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_post_test_batch_classification():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/classifications/test-batch",
            json={
                "records": [
                    {
                        "id": "rec-1",
                        "subject": "Billing overcharge",
                        "body": "Please refund the extra $50 fee on invoice 409.",
                    },
                    {
                        "id": "rec-2",
                        "subject": "System crash",
                        "body": "API returns 500 internal server error for all GET /v1/users calls.",
                    },
                ],
                "force_mock": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 2
        assert len(data["results"]) == 2
        assert data["total_latency_ms"] >= 0.0
        assert data["avg_latency_ms"] >= 0.0
