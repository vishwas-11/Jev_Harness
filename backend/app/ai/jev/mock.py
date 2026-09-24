"""High-fidelity Mock Jev classifier for tests and local development without active credentials."""

from __future__ import annotations

import asyncio
import re
import time
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from ..interfaces import BaseClassifier
from ..models import (
    BooleanDecision,
    ChoiceDecision,
    ClassificationResult,
    DecisionTrace,
    EmailInput,
    LatencyBreakdown,
    ScoreDecision,
)
from ..schemas import DEFAULT_CLASSIFICATION_DEFINITION, ClassificationDefinition


class MockJevClassifier(BaseClassifier):
    """Deterministic, heuristic Mock Jev classifier.

    Simulates the exact typed responses of Jev routed through Vercel AI Gateway:
    - Multi-question evaluation in a single mock call
    - Valid probability distributions that sum to 1.0
    - Exact rubric mapping and expected-value scoring
    - Realistic latency simulation (~30-50ms)
    - Decision traces matching live gateway telemetry
    """

    def __init__(
        self,
        definition: ClassificationDefinition = DEFAULT_CLASSIFICATION_DEFINITION,
        simulated_delay_ms: float = 35.0,
    ) -> None:
        self.definition = definition
        self.simulated_delay_ms = simulated_delay_ms

    async def classify_email(self, email: EmailInput) -> ClassificationResult:
        start_total = time.perf_counter()

        # Phase 1: State preparation
        t0 = time.perf_counter()
        text = f"{email.subject} {email.body}".lower()
        state_prep_ms = (time.perf_counter() - t0) * 1000.0

        # Phase 2: Simulated Jev request latency
        t1 = time.perf_counter()
        if self.simulated_delay_ms > 0:
            await asyncio.sleep(self.simulated_delay_ms / 1000.0)
        jev_request_ms = (time.perf_counter() - t1) * 1000.0

        # Phase 3: Response normalization & heuristic decision derivation
        t2 = time.perf_counter()

        intent_choice, intent_probs, intent_conf = self._decide_intent(text)
        dept_choice, dept_probs, dept_conf = self._decide_department(intent_choice, text)
        urgency_choice, urgency_probs, urgency_conf = self._decide_urgency(text)
        sentiment_choice, sentiment_probs, sentiment_conf = self._decide_sentiment(text)
        spam_val, spam_prob, spam_conf = self._decide_spam(text)
        human_val, human_prob, human_conf = self._decide_human_review(
            text, intent_choice, urgency_choice, sentiment_choice
        )
        score_val, score_probs, score_conf = self._decide_priority(
            urgency_choice, sentiment_choice, human_val, spam_val
        )

        legend = {i: desc for i, desc in enumerate(self.definition.priority.rubric)}

        intent_decision = ChoiceDecision(
            question_id="intent",
            choice=intent_choice,
            confidence=intent_conf,
            probabilities=intent_probs,
        )
        dept_decision = ChoiceDecision(
            question_id="department",
            choice=dept_choice,
            confidence=dept_conf,
            probabilities=dept_probs,
        )
        urgency_decision = ChoiceDecision(
            question_id="urgency",
            choice=urgency_choice,
            confidence=urgency_conf,
            probabilities=urgency_probs,
        )
        sentiment_decision = ChoiceDecision(
            question_id="sentiment",
            choice=sentiment_choice,
            confidence=sentiment_conf,
            probabilities=sentiment_probs,
        )
        spam_decision = BooleanDecision(
            question_id="spam",
            value=spam_val,
            probability=spam_prob,
            confidence=spam_conf,
        )
        human_decision = BooleanDecision(
            question_id="requires_human",
            value=human_val,
            probability=human_prob,
            confidence=human_conf,
        )
        priority_decision = ScoreDecision(
            question_id="priority",
            score=score_val,
            max_score=float(len(self.definition.priority.rubric) - 1),
            confidence=score_conf,
            legend=legend,
            probabilities=score_probs,
        )

        all_confidences = [
            intent_conf,
            dept_conf,
            urgency_conf,
            sentiment_conf,
            spam_conf,
            human_conf,
            score_conf,
        ]
        aggregate_confidence = round(sum(all_confidences) / len(all_confidences), 4)

        normalization_ms = (time.perf_counter() - t2) * 1000.0
        total_ms = (time.perf_counter() - start_total) * 1000.0

        latency = LatencyBreakdown(
            state_prep_ms=round(state_prep_ms, 2),
            jev_request_ms=round(jev_request_ms, 2),
            normalization_ms=round(normalization_ms, 2),
            total_ms=round(total_ms, 2),
        )

        raw_decisions = {
            "intent": {"choice": intent_choice, "confidence": intent_conf},
            "department": {"choice": dept_choice, "confidence": dept_conf},
            "urgency": {"choice": urgency_choice, "confidence": urgency_conf},
            "sentiment": {"choice": sentiment_choice, "confidence": sentiment_conf},
            "spam": {"noul": spam_prob},
            "requires_human": {"noul": human_prob},
            "priority": {"score": score_val, "confidence": score_conf},
        }

        body_snippet = email.body[:140] + ("..." if len(email.body) > 140 else "")

        trace = DecisionTrace(
            request_id=f"mock_req_{uuid4().hex[:12]}",
            model="typesafe-ai/jev (mock-engine)",
            provider="local-mock-adapter",
            timestamp=datetime.now(UTC),
            latency=latency,
            usage={"input_tokens": max(15, len(text.split())), "output_tokens": 7},
            raw_decisions=raw_decisions,
        )

        return ClassificationResult(
            id=str(uuid4()),
            subject=email.subject,
            body_snippet=body_snippet,
            intent=intent_decision,
            department=dept_decision,
            urgency=urgency_decision,
            sentiment=sentiment_decision,
            spam=spam_decision,
            requires_human=human_decision,
            priority=priority_decision,
            aggregate_confidence=aggregate_confidence,
            latency=latency,
            trace=trace,
            is_mock=True,
        )

    async def classify_batch(
        self, emails: list[EmailInput], max_concurrency: int = 5
    ) -> list[ClassificationResult]:
        semaphore = asyncio.Semaphore(max(1, max_concurrency))

        async def _bounded_classify(email: EmailInput) -> ClassificationResult:
            async with semaphore:
                return await self.classify_email(email)

        return await asyncio.gather(*[_bounded_classify(e) for e in emails])

    def _decide_intent(self, text: str) -> tuple[str, dict[str, float], float]:
        if any(k in text for k in ["refund", "money back", "reimburse", "chargeback"]):
            choice = "refund"
        elif any(k in text for k in ["invoice", "bill", "charged", "card", "payment", "subscription", "pricing"]):
            choice = "billing_issue"
        elif any(k in text for k in ["login", "password", "2fa", "account", "locked", "reset"]):
            choice = "account_issue"
        elif any(k in text for k in ["bug", "error", "crash", "broken", "failed", "api", "500", "exception", "down"]):
            choice = "technical_issue"
        elif any(k in text for k in ["demo", "enterprise license", "quote", "sales", "purchase", "seats"]):
            choice = "sales"
        elif any(k in text for k in ["unacceptable", "furious", "terrible", "complaint", "awful", "manager"]):
            choice = "complaint"
        elif any(k in text for k in ["how to", "where is", "documentation", "guide", "question"]):
            choice = "general_question"
        else:
            choice = "other"

        options = list(self.definition.intent.options.keys())
        probs = self._build_categorical_distribution(options, choice, primary_prob=0.91)
        return choice, probs, probs[choice]

    def _decide_department(self, intent: str, text: str) -> tuple[str, dict[str, float], float]:
        mapping = {
            "refund": "billing",
            "billing_issue": "billing",
            "technical_issue": "support",
            "account_issue": "support",
            "sales": "sales",
            "complaint": "support",
            "general_question": "support",
            "other": "other",
        }
        if "security" in text or "breach" in text or "vulnerability" in text:
            choice = "security"
        elif "downtime" in text or "server" in text or "latency" in text:
            choice = "operations"
        else:
            choice = mapping.get(intent, "support")

        options = list(self.definition.department.options.keys())
        probs = self._build_categorical_distribution(options, choice, primary_prob=0.89)
        return choice, probs, probs[choice]

    def _decide_urgency(self, text: str) -> tuple[str, dict[str, float], float]:
        if any(k in text for k in ["outage", "emergency", "immediately", "asap", "down", "critical", "sue"]):
            choice = "critical"
        elif any(k in text for k in ["urgent", "today", "blocking", "furious", "production", "broken"]):
            choice = "high"
        elif any(k in text for k in ["help", "issue", "problem", "waiting", "soon"]):
            choice = "medium"
        else:
            choice = "low"

        options = list(self.definition.urgency.options.keys())
        probs = self._build_categorical_distribution(options, choice, primary_prob=0.86)
        return choice, probs, probs[choice]

    def _decide_sentiment(self, text: str) -> tuple[str, dict[str, float], float]:
        if any(k in text for k in ["furious", "angry", "hate", "scam", "lawyer", "disaster", "threat"]):
            choice = "angry"
        elif any(k in text for k in ["frustrated", "annoyed", "unacceptable", "disappointed", "waiting days"]):
            choice = "frustrated"
        elif any(k in text for k in ["thanks", "great", "awesome", "appreciate", "love", "helpful"]):
            choice = "positive"
        elif any(k in text for k in ["unfortunate", "sadly", "sorry", "cannot", "failed"]):
            choice = "negative"
        else:
            choice = "neutral"

        options = list(self.definition.sentiment.options.keys())
        probs = self._build_categorical_distribution(options, choice, primary_prob=0.92)
        return choice, probs, probs[choice]

    def _decide_spam(self, text: str) -> tuple[bool, float, float]:
        is_spam_candidate = any(
            k in text
            for k in [
                "viagra", "casino", "lottery", "crypto profit", "wire transfer",
                "rich quickly", "seo services", "unlimited leads", "free gift card",
            ]
        )
        if is_spam_candidate:
            prob = 0.98
            val = True
        else:
            prob = 0.03
            val = False
        conf = round(max(prob, 1.0 - prob), 4)
        return val, prob, conf

    def _decide_human_review(
        self, text: str, intent: str, urgency: str, sentiment: str
    ) -> tuple[bool, float, float]:
        needs_human = (
            urgency == "critical"
            or sentiment == "angry"
            or intent in ["complaint", "refund"]
            or any(k in text for k in ["lawyer", "attorney", "regulator", "legal action", "executive"])
        )
        if needs_human:
            prob = 0.88
            val = True
        else:
            prob = 0.12
            val = False
        conf = round(max(prob, 1.0 - prob), 4)
        return val, prob, conf

    def _decide_priority(
        self, urgency: str, sentiment: str, human_val: bool, spam_val: bool
    ) -> tuple[float, dict[int, float], float]:
        if spam_val:
            expected_score = 0.15
            probs = {0: 0.88, 1: 0.08, 2: 0.03, 3: 0.01, 4: 0.0}
            conf = 0.94
        elif urgency == "critical":
            expected_score = 3.85
            probs = {0: 0.0, 1: 0.01, 2: 0.05, 3: 0.15, 4: 0.79}
            conf = 0.92
        elif urgency == "high" or sentiment == "angry":
            expected_score = 3.10
            probs = {0: 0.01, 1: 0.04, 2: 0.15, 3: 0.70, 4: 0.10}
            conf = 0.88
        elif human_val or urgency == "medium":
            expected_score = 2.15
            probs = {0: 0.02, 1: 0.15, 2: 0.65, 3: 0.15, 4: 0.03}
            conf = 0.85
        else:
            expected_score = 1.10
            probs = {0: 0.10, 1: 0.75, 2: 0.12, 3: 0.03, 4: 0.0}
            conf = 0.87

        return expected_score, probs, conf

    def _build_categorical_distribution(
        self, options: list[str], selected: str, primary_prob: float = 0.90
    ) -> dict[str, float]:
        remainder = round((1.0 - primary_prob) / max(1, len(options) - 1), 4)
        distribution: dict[str, float] = {}
        for opt in options:
            if opt == selected:
                distribution[opt] = primary_prob
            else:
                distribution[opt] = remainder
        total = sum(distribution.values())
        return {k: round(v / total, 4) for k, v in distribution.items()}
