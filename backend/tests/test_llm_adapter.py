"""Tests for LLMClassifier adapter, structured output schema, and error handling."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    InternalServerError,
    RateLimitError,
)

from app.ai.llm.adapter import (
    LLMAuthenticationError,
    LLMClassifier,
    LLMConfigurationError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from app.ai.llm.schemas import LLMSupportClassification
from app.ai.models import EmailInput


@pytest.mark.asyncio
async def test_llm_classifier_missing_key_fails():
    """Verify LLMClassifier strictly fails loudly if OPENAI_API_KEY is missing or empty."""
    with pytest.raises(LLMConfigurationError) as exc_info:
        LLMClassifier(api_key="")
    assert "OPENAI_API_KEY" in str(exc_info.value)
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_llm_classifier_structured_output_success():
    """Verify LLMClassifier correctly unpacks structured output from ChatOpenAI."""
    classifier = LLMClassifier(api_key="fake-openai-key", model="gpt-4o-mini")

    mock_parsed_obj = LLMSupportClassification(
        intent="refund",
        department="billing",
        urgency="high",
        sentiment="frustrated",
        spam=False,
        requires_human=True,
        priority=3,
        confidence=0.95,
        rationale="Customer requested refund for repeated charges.",
    )

    mock_runnable = MagicMock()
    mock_runnable.ainvoke = AsyncMock(return_value=mock_parsed_obj)

    with patch.object(classifier, "_structured_llm", mock_runnable):
        email = EmailInput(
            subject="Refund not received",
            body="I asked for my refund 5 days ago and nobody answered.",
        )
        result = await classifier.classify_email(email)

        assert result.strategy == "llm"
        assert result.is_mock is False
        assert result.intent.choice == "refund"
        assert result.department.choice == "billing"
        assert result.urgency.choice == "high"
        assert result.sentiment.choice == "frustrated"
        assert result.spam.value is False
        assert result.requires_human.value is True
        assert result.priority.score == 3.0

        # Latency breakdown
        assert result.latency.llm_request_ms is not None
        assert result.latency.llm_request_ms >= 0.0
        assert result.latency.validation_ms is not None
        assert result.latency.validation_ms >= 0.0
        assert result.latency.total_ms >= 0.0

        # Trace metadata
        assert result.trace.model == "gpt-4o-mini"
        assert result.trace.provider == "openai"
        assert result.trace.strategy == "llm"
        assert result.trace.validation_status == "VALID"


@pytest.mark.asyncio
async def test_llm_classifier_auth_error():
    classifier = LLMClassifier(api_key="bad-key", model="gpt-4o-mini")
    mock_runnable = MagicMock()
    mock_runnable.ainvoke = AsyncMock(
        side_effect=AuthenticationError(
            message="Incorrect API key provided",
            response=MagicMock(status_code=401),
            body={"error": {"message": "Invalid API Key"}},
        )
    )

    with patch.object(classifier, "_structured_llm", mock_runnable):
        with pytest.raises(LLMAuthenticationError) as exc_info:
            await classifier.classify_email(EmailInput(subject="Hi", body="Test"))
        assert exc_info.value.status_code == 401
        assert "authentication failed" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_llm_classifier_rate_limit_error():
    classifier = LLMClassifier(api_key="valid-key", model="gpt-4o-mini")
    mock_runnable = MagicMock()
    mock_runnable.ainvoke = AsyncMock(
        side_effect=RateLimitError(
            message="Rate limit exceeded",
            response=MagicMock(status_code=429),
            body={"error": {"message": "Rate limit exceeded"}},
        )
    )

    with patch.object(classifier, "_structured_llm", mock_runnable):
        with pytest.raises(LLMRateLimitError) as exc_info:
            await classifier.classify_email(EmailInput(subject="Hi", body="Test"))
        assert exc_info.value.status_code == 429


@pytest.mark.asyncio
async def test_llm_classifier_connection_timeout_error():
    classifier = LLMClassifier(api_key="valid-key", model="gpt-4o-mini")
    mock_runnable = MagicMock()
    mock_runnable.ainvoke = AsyncMock(
        side_effect=APITimeoutError(request=MagicMock())
    )

    with patch.object(classifier, "_structured_llm", mock_runnable):
        with pytest.raises(LLMTimeoutError) as exc_info:
            await classifier.classify_email(EmailInput(subject="Hi", body="Test"))
        assert exc_info.value.status_code == 504
