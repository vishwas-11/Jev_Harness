"""LLM classifier adapter using LangChain ChatOpenAI with strict structured outputs."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AuthenticationError,
    RateLimitError,
)
from pydantic import ValidationError

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
from .prompts import build_llm_system_prompt, build_llm_user_prompt
from .schemas import LLMSupportClassification

logger = logging.getLogger(__name__)


class LLMClassificationError(Exception):
    """Base exception for LLM classification failures."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class LLMConfigurationError(LLMClassificationError):
    """Raised when OpenAI configuration or API key is missing (HTTP 400)."""

    def __init__(self, message: str = "OPENAI_API_KEY is not configured in backend/.env.") -> None:
        super().__init__(message, status_code=400)


class LLMAuthenticationError(LLMClassificationError):
    """Raised when OpenAI authentication fails (HTTP 401)."""

    def __init__(self, message: str = "OpenAI authentication failed. Check OPENAI_API_KEY.") -> None:
        super().__init__(message, status_code=401)


class LLMRateLimitError(LLMClassificationError):
    """Raised when OpenAI rate limit is exceeded (HTTP 429)."""

    def __init__(self, message: str = "OpenAI rate limit exceeded.") -> None:
        super().__init__(message, status_code=429)


class LLMTimeoutError(LLMClassificationError):
    """Raised when LLM request times out (HTTP 504)."""

    def __init__(self, message: str = "LLM classification request timed out.") -> None:
        super().__init__(message, status_code=504)


class LLMValidationError(LLMClassificationError):
    """Raised when structured output schema validation fails (HTTP 502)."""

    def __init__(self, message: str = "LLM structured output failed validation.") -> None:
        super().__init__(message, status_code=502)


class LLMProviderError(LLMClassificationError):
    """Raised on upstream OpenAI failure (HTTP 502)."""

    def __init__(self, message: str = "Upstream OpenAI API error.", status_code: int = 502) -> None:
        super().__init__(message, status_code=status_code)


class LLMClassifier(BaseClassifier):
    """Production LLM baseline classifier evaluating emails with native structured output."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        timeout: float = 30.0,
        definition: ClassificationDefinition = DEFAULT_CLASSIFICATION_DEFINITION,
    ) -> None:
        if not api_key or not api_key.strip():
            raise LLMConfigurationError(
                "OPENAI_API_KEY is not configured. Add your key to backend/.env."
            )
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.definition = definition

        # Initialize ChatOpenAI
        self._llm = ChatOpenAI(
            model=self.model,
            api_key=self.api_key,
            timeout=self.timeout,
            temperature=0.0,
        )

        # Enforce strict structured output JSON schema
        self._structured_llm = self._llm.with_structured_output(
            LLMSupportClassification,
            method="json_schema",
            strict=True,
        )

    async def classify_email(self, email: EmailInput) -> ClassificationResult:
        start_total = time.perf_counter()

        # Phase 1: State & prompt preparation
        t0 = time.perf_counter()
        system_text = build_llm_system_prompt(self.definition)
        user_text = build_llm_user_prompt(email.subject, email.body)
        messages = [
            SystemMessage(content=system_text),
            HumanMessage(content=user_text),
        ]
        state_prep_ms = (time.perf_counter() - t0) * 1000.0

        # Phase 2: Await LLM structured completion
        t1 = time.perf_counter()
        try:
            parsed: LLMSupportClassification = await self._structured_llm.ainvoke(messages)
        except AuthenticationError as exc:
            logger.error("OpenAI authentication error: %s", exc)
            raise LLMAuthenticationError("OpenAI authentication failed. Check OPENAI_API_KEY.") from exc
        except RateLimitError as exc:
            logger.warning("OpenAI rate limit error: %s", exc)
            raise LLMRateLimitError("OpenAI rate limit exceeded.") from exc
        except APITimeoutError as exc:
            logger.error("OpenAI request timed out: %s", exc)
            raise LLMTimeoutError("LLM request timed out.") from exc
        except (ValidationError, TypeError) as exc:
            logger.error("LLM structured output validation error: %s", exc)
            raise LLMValidationError(f"Invalid structured response from LLM: {exc}") from exc
        except (APIConnectionError, APIError) as exc:
            logger.error("OpenAI API error: %s", exc)
            raise LLMProviderError(f"OpenAI error: {exc}") from exc
        except Exception as exc:
            logger.exception("Unexpected error during LLM classification: %s", exc)
            raise LLMProviderError("Internal error during LLM classification.") from exc

        llm_request_ms = (time.perf_counter() - t1) * 1000.0

        # Phase 3: Response normalization & schema verification
        t2 = time.perf_counter()
        result = self._normalize_response(
            email=email,
            parsed=parsed,
            state_prep_ms=state_prep_ms,
            llm_request_ms=llm_request_ms,
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
        parsed: LLMSupportClassification,
        state_prep_ms: float,
        llm_request_ms: float,
        t2: float,
        start_total: float,
    ) -> ClassificationResult:
        # Confidence resolution
        conf = round(parsed.confidence, 4)

        intent_decision = ChoiceDecision(
            question_id="intent",
            choice=parsed.intent,
            confidence=conf,
            probabilities={parsed.intent: conf},
        )
        dept_decision = ChoiceDecision(
            question_id="department",
            choice=parsed.department,
            confidence=conf,
            probabilities={parsed.department: conf},
        )
        urgency_decision = ChoiceDecision(
            question_id="urgency",
            choice=parsed.urgency,
            confidence=conf,
            probabilities={parsed.urgency: conf},
        )
        sentiment_decision = ChoiceDecision(
            question_id="sentiment",
            choice=parsed.sentiment,
            confidence=conf,
            probabilities={parsed.sentiment: conf},
        )
        spam_prob = 0.95 if parsed.spam else 0.05
        spam_decision = BooleanDecision(
            question_id="spam",
            value=parsed.spam,
            probability=spam_prob,
            confidence=round(max(spam_prob, 1.0 - spam_prob), 4),
        )
        human_prob = 0.90 if parsed.requires_human else 0.10
        human_decision = BooleanDecision(
            question_id="requires_human",
            value=parsed.requires_human,
            probability=human_prob,
            confidence=round(max(human_prob, 1.0 - human_prob), 4),
        )

        legend = {i: desc for i, desc in enumerate(self.definition.priority.rubric)}
        priority_decision = ScoreDecision(
            question_id="priority",
            score=float(parsed.priority),
            max_score=4.0,
            confidence=conf,
            legend=legend,
            probabilities={parsed.priority: conf},
        )

        normalization_ms = (time.perf_counter() - t2) * 1000.0
        total_ms = (time.perf_counter() - start_total) * 1000.0

        latency = LatencyBreakdown(
            state_prep_ms=round(state_prep_ms, 2),
            llm_request_ms=round(llm_request_ms, 2),
            validation_ms=round(normalization_ms / 2, 2),
            normalization_ms=round(normalization_ms, 2),
            total_ms=round(total_ms, 2),
        )

        body_snippet = email.body[:140] + ("..." if len(email.body) > 140 else "")

        raw_summary: dict[str, Any] = {
            "intent": parsed.intent,
            "department": parsed.department,
            "urgency": parsed.urgency,
            "sentiment": parsed.sentiment,
            "spam": parsed.spam,
            "requires_human": parsed.requires_human,
            "priority": parsed.priority,
            "rationale": parsed.rationale,
        }

        trace = DecisionTrace(
            request_id=f"openai_{uuid4().hex[:12]}",
            model=self.model,
            provider="openai",
            strategy="llm",
            timestamp=datetime.now(UTC),
            latency=latency,
            usage={
                "input_tokens": None,
                "output_tokens": None,
                "total_tokens": None,
            },
            validation_status="VALID",
            raw_decisions=raw_summary,
        )

        return ClassificationResult(
            id=str(uuid4()),
            strategy="llm",
            subject=email.subject,
            body_snippet=body_snippet,
            intent=intent_decision,
            department=dept_decision,
            urgency=urgency_decision,
            sentiment=sentiment_decision,
            spam=spam_decision,
            requires_human=human_decision,
            priority=priority_decision,
            aggregate_confidence=conf,
            latency=latency,
            trace=trace,
            is_mock=False,
        )
