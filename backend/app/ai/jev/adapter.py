"""Jev classifier adapter routing typed multi-question evaluation through Vercel AI Gateway."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from langchain_typesafe import (
    ClassifierRequest,
    ClassifierResponse,
    TypeSafeClassifier,
)
from langchain_typesafe.client import (
    TypeSafeAPIConnectionError,
    TypeSafeAPIError,
    TypeSafeAPIResponseValidationError,
    TypeSafeAPITimeoutError,
    TypeSafeAuthenticationError,
    TypeSafeRateLimitError,
)

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
from .questions import build_jev_questions

logger = logging.getLogger(__name__)


class JevClassificationError(Exception):
    """Base exception for Jev classification failures."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class JevAuthenticationError(JevClassificationError):
    """Raised when AI Gateway authentication fails (HTTP 401/403)."""

    def __init__(self, message: str = "Vercel AI Gateway authentication failed.") -> None:
        super().__init__(message, status_code=401)


class JevRateLimitError(JevClassificationError):
    """Raised when Jev or Gateway rate limit is exceeded (HTTP 429)."""

    def __init__(self, message: str = "Rate limit exceeded on AI Gateway.") -> None:
        super().__init__(message, status_code=429)


class JevTimeoutError(JevClassificationError):
    """Raised when request times out."""

    def __init__(self, message: str = "Jev classification request timed out.") -> None:
        super().__init__(message, status_code=504)


class JevProviderError(JevClassificationError):
    """Raised on upstream provider failure or invalid payload."""

    def __init__(self, message: str = "Upstream Jev evaluation failed.", status_code: int = 502) -> None:
        super().__init__(message, status_code=status_code)


class JevClassifier(BaseClassifier):
    """Production Jev adapter connecting to TypeSafe Jev via Vercel AI Gateway.

    Evaluates state and multiple typed questions (Choice, Noul, Score)
    in a single network request.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://ai-gateway.vercel.sh/typesafe",
        model: str = "typesafe-ai/jev",
        timeout: float = 30.0,
        definition: ClassificationDefinition = DEFAULT_CLASSIFICATION_DEFINITION,
    ) -> None:
        if not api_key:
            raise ValueError("Jev API key or AI Gateway API key is required.")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.definition = definition

        # Initialize LangChain TypeSafeClassifier
        self._classifier = TypeSafeClassifier(
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
        )

    async def classify_email(self, email: EmailInput) -> ClassificationResult:
        start_total = time.perf_counter()

        # Phase 1: State & question preparation
        t0 = time.perf_counter()
        state = email.to_state()
        questions = build_jev_questions(self.definition)
        state_prep_ms = (time.perf_counter() - t0) * 1000.0

        request: ClassifierRequest = {
            "state": state,
            "questions": questions,
        }

        # Phase 2: Single multi-question request via AI Gateway
        t1 = time.perf_counter()
        try:
            response: ClassifierResponse = await self._classifier.ainvoke(request)
        except TypeSafeAuthenticationError as exc:
            logger.error("AI Gateway authentication error: %s", exc)
            raise JevAuthenticationError("AI Gateway or TypeSafe authentication failed.") from exc
        except TypeSafeRateLimitError as exc:
            logger.warning("AI Gateway rate limit exceeded: %s", exc)
            raise JevRateLimitError("Rate limit exceeded on Vercel AI Gateway.") from exc
        except TypeSafeAPITimeoutError as exc:
            logger.error("AI Gateway request timed out: %s", exc)
            raise JevTimeoutError("Jev request timed out.") from exc
        except (TypeSafeAPIResponseValidationError, ValueError) as exc:
            logger.error("Response validation failed from Jev: %s", exc)
            raise JevProviderError("Invalid response received from Jev.") from exc
        except (TypeSafeAPIConnectionError, TypeSafeAPIError) as exc:
            logger.error("Upstream error connecting to Jev: %s", exc)
            raise JevProviderError("Failed to communicate with Jev via AI Gateway.") from exc
        except Exception as exc:
            logger.exception("Unexpected error during Jev classification: %s", exc)
            raise JevProviderError("Internal error during Jev classification.") from exc

        jev_request_ms = (time.perf_counter() - t1) * 1000.0

        # Phase 3: Response normalization
        t2 = time.perf_counter()
        result = self._normalize_response(
            email=email,
            response=response,
            state_prep_ms=state_prep_ms,
            jev_request_ms=jev_request_ms,
            t2=t2,
            start_total=start_total,
        )
        return result

    async def classify_batch(
        self, emails: list[EmailInput], max_concurrency: int = 5
    ) -> list[ClassificationResult]:
        semaphore = asyncio.Semaphore(max(1, max_concurrency))

        async def _bounded_classify(e: EmailInput) -> ClassificationResult:
            async with semaphore:
                return await self.classify_email(e)

        return await asyncio.gather(*[_bounded_classify(e) for e in emails])

    def _normalize_response(
        self,
        email: EmailInput,
        response: ClassifierResponse,
        state_prep_ms: float,
        jev_request_ms: float,
        t2: float,
        start_total: float,
    ) -> ClassificationResult:
        choices = response.choices
        nouls = response.nouls
        scores = response.scores

        # 1. Intent (Choice)
        intent_ans = choices.get("intent")
        if not intent_ans:
            raise JevProviderError("Missing 'intent' answer in Jev response.")
        intent_decision = ChoiceDecision(
            question_id="intent",
            choice=intent_ans.choice,
            confidence=round(intent_ans.confidence, 4),
            probabilities={k: round(v, 4) for k, v in intent_ans.probabilities.items()},
        )

        # 2. Department (Choice)
        dept_ans = choices.get("department")
        if not dept_ans:
            raise JevProviderError("Missing 'department' answer in Jev response.")
        dept_decision = ChoiceDecision(
            question_id="department",
            choice=dept_ans.choice,
            confidence=round(dept_ans.confidence, 4),
            probabilities={k: round(v, 4) for k, v in dept_ans.probabilities.items()},
        )

        # 3. Urgency (Choice)
        urgency_ans = choices.get("urgency")
        if not urgency_ans:
            raise JevProviderError("Missing 'urgency' answer in Jev response.")
        urgency_decision = ChoiceDecision(
            question_id="urgency",
            choice=urgency_ans.choice,
            confidence=round(urgency_ans.confidence, 4),
            probabilities={k: round(v, 4) for k, v in urgency_ans.probabilities.items()},
        )

        # 4. Sentiment (Choice)
        sentiment_ans = choices.get("sentiment")
        if not sentiment_ans:
            raise JevProviderError("Missing 'sentiment' answer in Jev response.")
        sentiment_decision = ChoiceDecision(
            question_id="sentiment",
            choice=sentiment_ans.choice,
            confidence=round(sentiment_ans.confidence, 4),
            probabilities={k: round(v, 4) for k, v in sentiment_ans.probabilities.items()},
        )

        # 5. Spam (Noul)
        spam_ans = nouls.get("spam")
        if not spam_ans:
            raise JevProviderError("Missing 'spam' answer in Jev response.")
        spam_p = round(spam_ans.noul, 4)
        spam_decision = BooleanDecision(
            question_id="spam",
            value=(spam_p >= 0.5),
            probability=spam_p,
            confidence=round(max(spam_p, 1.0 - spam_p), 4),
        )

        # 6. Requires Human Review (Noul)
        human_ans = nouls.get("requires_human")
        if not human_ans:
            raise JevProviderError("Missing 'requires_human' answer in Jev response.")
        human_p = round(human_ans.noul, 4)
        human_decision = BooleanDecision(
            question_id="requires_human",
            value=(human_p >= 0.5),
            probability=human_p,
            confidence=round(max(human_p, 1.0 - human_p), 4),
        )

        # 7. Priority (Score)
        priority_ans = scores.get("priority")
        if not priority_ans:
            raise JevProviderError("Missing 'priority' answer in Jev response.")
        legend = {int(k): str(v) for k, v in priority_ans.legend.items()}
        priority_decision = ScoreDecision(
            question_id="priority",
            score=round(priority_ans.score, 2),
            max_score=float(len(self.definition.priority.rubric) - 1),
            confidence=round(priority_ans.confidence, 4),
            legend=legend,
            probabilities={int(k): round(v, 4) for k, v in priority_ans.probabilities.items()},
        )

        all_confidences = [
            intent_decision.confidence,
            dept_decision.confidence,
            urgency_decision.confidence,
            sentiment_decision.confidence,
            spam_decision.confidence,
            human_decision.confidence,
            priority_decision.confidence,
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

        raw_summary: dict[str, Any] = {
            "intent": {"choice": intent_decision.choice, "confidence": intent_decision.confidence},
            "department": {"choice": dept_decision.choice, "confidence": dept_decision.confidence},
            "urgency": {"choice": urgency_decision.choice, "confidence": urgency_decision.confidence},
            "sentiment": {"choice": sentiment_decision.choice, "confidence": sentiment_decision.confidence},
            "spam": {"noul": spam_decision.probability},
            "requires_human": {"noul": human_decision.probability},
            "priority": {"score": priority_decision.score, "confidence": priority_decision.confidence},
        }

        body_snippet = email.body[:140] + ("..." if len(email.body) > 140 else "")

        trace = DecisionTrace(
            request_id=response.request_id or f"jev_{uuid4().hex[:12]}",
            model=response.model or self.model,
            provider="vercel-ai-gateway",
            timestamp=datetime.now(UTC),
            latency=latency,
            usage={
                "input_tokens": response.usage.input_tokens if response.usage else None,
                "output_tokens": response.usage.output_tokens if response.usage else None,
            },
            raw_decisions=raw_summary,
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
            is_mock=False,
        )
