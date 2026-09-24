"""Tests for JevClassifier adapter, MockJevClassifier, and normalization logic."""

from unittest.mock import AsyncMock, patch

import httpx2
import pytest
from langchain_typesafe import (
    ChoiceAnswer,
    ClassifierResponse,
    NoulAnswer,
    ScoreAnswer,
    TypeSafeClassifier,
    Usage,
)
from langchain_typesafe.client import (
    TypeSafeAPITimeoutError,
    TypeSafeAuthenticationError,
    TypeSafeRateLimitError,
)

from app.ai.jev.adapter import (
    JevAuthenticationError,
    JevClassifier,
    JevProviderError,
    JevRateLimitError,
    JevTimeoutError,
)
from app.ai.jev.mock import MockJevClassifier
from app.ai.models import EmailInput


@pytest.mark.asyncio
async def test_email_state_conversion():
    email = EmailInput(subject="Billing inquiry", body="Why was I charged twice?")
    state = email.to_state()
    assert state == {
        "subject": "Billing inquiry",
        "body": "Why was I charged twice?",
    }


@pytest.mark.asyncio
async def test_mock_jev_classifier_single_email():
    classifier = MockJevClassifier(simulated_delay_ms=0)
    email = EmailInput(
        subject="Refund request for duplicate charge",
        body="I was charged twice on my credit card. Please issue a refund immediately.",
    )
    result = await classifier.classify_email(email)

    assert result.is_mock is True
    assert result.intent.choice == "refund"
    assert result.department.choice == "billing"
    assert result.spam.value is False
    assert result.requires_human.value is True  # refund/charge issue warrants human review
    assert result.priority.score > 2.0
    assert 0.0 <= result.aggregate_confidence <= 1.0

    # Latency breakdown
    assert result.latency.total_ms >= 0.0
    assert result.latency.state_prep_ms >= 0.0
    assert result.latency.normalization_ms >= 0.0

    # Probability distributions
    assert sum(result.intent.probabilities.values()) == pytest.approx(1.0, rel=1e-2)
    assert sum(result.department.probabilities.values()) == pytest.approx(1.0, rel=1e-2)


@pytest.mark.asyncio
async def test_mock_jev_classifier_batch():
    classifier = MockJevClassifier(simulated_delay_ms=0)
    emails = [
        EmailInput(subject="Crash report", body="The app crashes with 500 internal server error."),
        EmailInput(subject="Win free money now", body="Congratulations! Click here to claim your lottery jackpot."),
    ]
    results = await classifier.classify_batch(emails, max_concurrency=2)
    assert len(results) == 2
    assert results[0].intent.choice == "technical_issue"
    assert results[1].spam.value is True


@pytest.mark.asyncio
async def test_jev_classifier_normalization_with_mocked_ainvoke():
    """Verify JevClassifier accurately unpacks and normalizes live LangChain TypeSafe responses."""
    classifier = JevClassifier(api_key="fake-test-key")

    mock_response = ClassifierResponse(
        model="typesafe-ai/jev",
        answers={
            "intent": ChoiceAnswer(
                type="choice",
                choice="refund",
                confidence=0.942,
                probabilities={"refund": 0.942, "billing_issue": 0.048, "other": 0.010},
            ),
            "department": ChoiceAnswer(
                type="choice",
                choice="billing",
                confidence=0.915,
                probabilities={"billing": 0.915, "support": 0.085},
            ),
            "urgency": ChoiceAnswer(
                type="choice",
                choice="high",
                confidence=0.880,
                probabilities={"high": 0.880, "medium": 0.120},
            ),
            "sentiment": ChoiceAnswer(
                type="choice",
                choice="frustrated",
                confidence=0.960,
                probabilities={"frustrated": 0.960, "neutral": 0.040},
            ),
            "spam": NoulAnswer(type="noul", noul=0.03),
            "requires_human": NoulAnswer(type="noul", noul=0.87),
            "priority": ScoreAnswer(
                type="score",
                score=3.42,
                legend={0: "P5", 1: "P4", 2: "P3", 3: "P2", 4: "P1"},
                probabilities={0: 0.0, 1: 0.02, 2: 0.10, 3: 0.44, 4: 0.44},
                confidence=0.910,
            ),
        },
        usage=Usage(input_tokens=142, output_tokens=7),
        request_id="req_test_gateway_999",
    )

    with patch.object(TypeSafeClassifier, "ainvoke", new=AsyncMock(return_value=mock_response)):
        email = EmailInput(
            subject="Refund not received",
            body="I asked for my refund 5 days ago and nobody answered.",
        )
        result = await classifier.classify_email(email)

        assert result.is_mock is False
        assert result.intent.choice == "refund"
        assert result.intent.confidence == 0.942
        assert result.department.choice == "billing"
        assert result.urgency.choice == "high"
        assert result.sentiment.choice == "frustrated"

        # Spam boolean decision (p=0.03 -> False)
        assert result.spam.value is False
        assert result.spam.probability == 0.03
        assert result.spam.confidence == 0.97  # max(0.03, 0.97)

        # Requires Human Review boolean decision (p=0.87 -> True)
        assert result.requires_human.value is True
        assert result.requires_human.probability == 0.87

        # Priority score decision
        assert result.priority.score == 3.42
        assert result.priority.confidence == 0.910

        # Trace telemetry
        assert result.trace.request_id == "req_test_gateway_999"
        assert result.trace.usage["input_tokens"] == 142
        assert result.trace.usage["output_tokens"] == 7


@pytest.mark.asyncio
async def test_jev_classifier_authentication_error():
    classifier = JevClassifier(api_key="bad-key")
    headers = httpx2.Headers({"content-type": "application/json"})
    with patch.object(
        TypeSafeClassifier,
        "ainvoke",
        new=AsyncMock(side_effect=TypeSafeAuthenticationError(401, {"error": "Unauthorized"}, headers)),
    ):
        with pytest.raises(JevAuthenticationError):
            await classifier.classify_email(EmailInput(subject="Hi", body="Test"))


@pytest.mark.asyncio
async def test_jev_classifier_rate_limit_error():
    classifier = JevClassifier(api_key="valid-key")
    headers = httpx2.Headers({"retry-after": "5"})
    with patch.object(
        TypeSafeClassifier,
        "ainvoke",
        new=AsyncMock(side_effect=TypeSafeRateLimitError(429, {"error": "Rate limit"}, headers)),
    ):
        with pytest.raises(JevRateLimitError):
            await classifier.classify_email(EmailInput(subject="Hi", body="Test"))


@pytest.mark.asyncio
async def test_jev_classifier_timeout_error():
    classifier = JevClassifier(api_key="valid-key")
    with patch.object(
        TypeSafeClassifier,
        "ainvoke",
        new=AsyncMock(side_effect=TypeSafeAPITimeoutError(timeout=30.0)),
    ):
        with pytest.raises(JevTimeoutError):
            await classifier.classify_email(EmailInput(subject="Hi", body="Test"))
