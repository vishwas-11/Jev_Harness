"""Integration tests for the classifications API endpoints (Phase 4)."""

from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.fakes.mock_jev import FakeTestJevClassifier


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
        assert "jev_configured" in data
        assert "llm_configured" in data
        assert "gmail_configured" in data
        assert "jev_model" in data
        assert "llm_model" in data
        assert "gateway_url" in data


@pytest.mark.asyncio
async def test_post_test_classification_unconfigured_fails_loudly():
    """Verify that calling test classification without credentials fails with 400 and NO silent mock."""
    from app.config import Settings, get_settings

    app.dependency_overrides[get_settings] = lambda: Settings(
        ai_gateway_api_key="", openai_api_key=""
    )
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Default Jev strategy
            response = await client.post(
                "/api/classifications/test",
                json={
                    "subject": "Need help with refund",
                    "body": "I was double charged.",
                    "strategy": "jev",
                },
            )
            assert response.status_code == 400
            assert "AI_GATEWAY_API_KEY" in response.json()["detail"]

            # LLM strategy
            response_llm = await client.post(
                "/api/classifications/test",
                json={
                    "subject": "Need help with refund",
                    "body": "I was double charged.",
                    "strategy": "llm",
                },
            )
            assert response_llm.status_code == 400
            assert "OPENAI_API_KEY" in response_llm.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_settings, None)


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
async def test_post_test_classification_with_injected_classifier():
    fake_classifier = FakeTestJevClassifier()
    with patch("app.classifications.router.get_classifier", return_value=fake_classifier):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/classifications/test",
                json={
                    "subject": "Unable to log in to my account",
                    "body": "I forgot my password and the reset link is giving a 404 error.",
                    "strategy": "jev",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert "id" in data
            assert data["strategy"] == "jev"
            assert data["intent"]["choice"] == "account_issue"
            assert data["spam"]["value"] is False
            assert "latency" in data
            assert "trace" in data


@pytest.mark.asyncio
async def test_post_test_batch_classification_with_injected_classifier():
    fake_classifier = FakeTestJevClassifier()
    with patch("app.classifications.router.get_classifier", return_value=fake_classifier):
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
                    "strategy": "jev",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["strategy"] == "jev"
            assert data["total_count"] == 2
            assert len(data["results"]) == 2
            assert data["total_latency_ms"] >= 0.0
            assert data["avg_latency_ms"] >= 0.0
