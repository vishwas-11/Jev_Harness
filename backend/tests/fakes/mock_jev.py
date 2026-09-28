"""Test-only fake Jev classifier for unit testing and offline simulation."""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime
from uuid import uuid4

from app.ai.interfaces import BaseClassifier
from app.ai.models import (
    BooleanDecision,
    ChoiceDecision,
    ClassificationResult,
    DecisionTrace,
    EmailInput,
    LatencyBreakdown,
    ScoreDecision,
)
from app.ai.schemas import DEFAULT_CLASSIFICATION_DEFINITION, ClassificationDefinition


class FakeTestJevClassifier(BaseClassifier):
    """Test-only fake Jev classifier for offline unit tests."""

    def __init__(
        self,
        definition: ClassificationDefinition = DEFAULT_CLASSIFICATION_DEFINITION,
        simulated_delay_ms: float = 0.0,
    ) -> None:
        self.definition = definition
        self.simulated_delay_ms = simulated_delay_ms

    async def classify_email(self, email: EmailInput) -> ClassificationResult:
        start_total = time.perf_counter()

        t0 = time.perf_counter()
        text = f"{email.subject} {email.body}".lower()
        state_prep_ms = (time.perf_counter() - t0) * 1000.0

        t1 = time.perf_counter()
        if self.simulated_delay_ms > 0:
            await asyncio.sleep(self.simulated_delay_ms / 1000.0)
        jev_request_ms = (time.perf_counter() - t1) * 1000.0

        t2 = time.perf_counter()

        if any(k in text for k in ["refund", "chargeback"]):
            intent = "refund"
            dept = "billing"
            urgency = "high"
            sentiment = "frustrated"
            priority = 3.2
            needs_human = True
        elif any(k in text for k in ["password", "login", "account"]):
            intent = "account_issue"
            dept = "account_management"
            urgency = "medium"
            sentiment = "frustrated"
            priority = 2.0
            needs_human = False
        elif any(k in text for k in ["crash", "bug", "500", "error"]):
            intent = "technical_issue"
            dept = "support"
            urgency = "critical"
            sentiment = "neutral"
            priority = 3.8
            needs_human = True
        elif any(k in text for k in ["free money", "lottery", "casino"]):
            intent = "other"
            dept = "other"
            urgency = "low"
            sentiment = "neutral"
            priority = 0.1
            needs_human = False
        else:
            intent = "general_question"
            dept = "support"
            urgency = "low"
            sentiment = "positive"
            priority = 1.0
            needs_human = False

        spam_val = "free money" in text or "lottery" in text
        conf = 0.92

        normalization_ms = (time.perf_counter() - t2) * 1000.0
        total_ms = (time.perf_counter() - start_total) * 1000.0

        latency = LatencyBreakdown(
            state_prep_ms=round(state_prep_ms, 2),
            jev_request_ms=round(jev_request_ms, 2),
            normalization_ms=round(normalization_ms, 2),
            total_ms=round(total_ms, 2),
        )

        legend = {i: desc for i, desc in enumerate(self.definition.priority.rubric)}

        return ClassificationResult(
            id=str(uuid4()),
            strategy="jev",
            subject=email.subject,
            body_snippet=email.body[:140],
            intent=ChoiceDecision(question_id="intent", choice=intent, confidence=conf, probabilities={intent: conf, "other": round(1.0 - conf, 4)}),
            department=ChoiceDecision(question_id="department", choice=dept, confidence=conf, probabilities={dept: conf, "other": round(1.0 - conf, 4)}),
            urgency=ChoiceDecision(question_id="urgency", choice=urgency, confidence=conf, probabilities={urgency: conf, "medium": round(1.0 - conf, 4)}),
            sentiment=ChoiceDecision(question_id="sentiment", choice=sentiment, confidence=conf, probabilities={sentiment: conf, "neutral": round(1.0 - conf, 4)}),
            spam=BooleanDecision(question_id="spam", value=spam_val, probability=0.98 if spam_val else 0.02, confidence=0.96),
            requires_human=BooleanDecision(question_id="requires_human", value=needs_human, probability=0.88 if needs_human else 0.12, confidence=0.88),
            priority=ScoreDecision(question_id="priority", score=priority, max_score=4.0, confidence=conf, legend=legend),
            aggregate_confidence=conf,
            latency=latency,
            trace=DecisionTrace(
                request_id=f"fake_{uuid4().hex[:8]}",
                model="typesafe-ai/jev (test-fake)",
                provider="test-fake",
                strategy="jev",
                timestamp=datetime.now(UTC),
                latency=latency,
            ),
            is_mock=True,
        )

    async def classify_batch(
        self, emails: list[EmailInput], max_concurrency: int = 5
    ) -> list[ClassificationResult]:
        return await asyncio.gather(*[self.classify_email(e) for e in emails])
