"""FastAPI routes for test classifications, batch playground, and schema inspection."""

from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..ai import (
    ClassificationDefinition,
    ClassificationResult,
    DEFAULT_CLASSIFICATION_DEFINITION,
    EmailInput,
    get_classifier,
)
from ..ai.jev.adapter import JevClassificationError
from ..ai.llm.adapter import LLMClassificationError
from ..config import Settings, get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/classifications", tags=["classifications"])


class TestClassificationRequest(BaseModel):
    """Request payload for single-email test classification."""

    subject: str = Field(default="", description="Email subject line.")
    body: str = Field(default="", description="Email body content.")
    strategy: str = Field(
        default="jev",
        description="Decision engine strategy: 'jev' (TypeSafe via Vercel AI Gateway) or 'llm' (OpenAI baseline).",
    )


class BatchClassificationItem(BaseModel):
    id: str | None = None
    subject: str = ""
    body: str = ""


class TestBatchRequest(BaseModel):
    """Request payload for small batch test classifications."""

    records: list[BatchClassificationItem] = Field(
        ...,
        min_length=1,
        max_length=25,
        description="Bounded list of up to 25 records for playground batch evaluation.",
    )
    strategy: str = Field(default="jev", description="'jev' or 'llm'")
    max_concurrency: int = Field(default=5, ge=1, le=10)


class TestBatchResponse(BaseModel):
    """Response containing batch classification results and summary metrics."""

    strategy: str
    results: list[ClassificationResult]
    total_count: int
    total_latency_ms: float
    avg_latency_ms: float


class ProviderStatusResponse(BaseModel):
    """Provider configuration status without revealing secrets."""

    jev_configured: bool
    jev_model: str
    gateway_url: str
    llm_configured: bool
    llm_model: str
    gmail_configured: bool


@router.get("/schema", response_model=ClassificationDefinition)
async def get_classification_schema() -> ClassificationDefinition:
    """Return the active classification definition, questions, categories, and rubric."""
    return DEFAULT_CLASSIFICATION_DEFINITION


@router.get("/provider-status", response_model=ProviderStatusResponse)
async def get_provider_status(settings: Settings = Depends(get_settings)) -> ProviderStatusResponse:
    """Return Jev, LLM, and Gmail integration status for the control plane."""
    return ProviderStatusResponse(
        jev_configured=settings.has_jev_credentials,
        jev_model=settings.jev_model,
        gateway_url=settings.ai_gateway_base_url,
        llm_configured=settings.has_llm_credentials,
        llm_model=settings.llm_model,
        gmail_configured=settings.has_gmail_credentials,
    )


@router.post("/test", response_model=ClassificationResult)
async def test_classify(
    req: TestClassificationRequest,
    settings: Settings = Depends(get_settings),
) -> ClassificationResult:
    """Evaluate a single email using Jev or LLM decision engine.

    Fails loudly with structured HTTP errors if API credentials are not configured
    or if the upstream provider fails. Never falls back to a mock classifier.
    """
    if not req.subject.strip() and not req.body.strip():
        raise HTTPException(
            status_code=422,
            detail="Subject or body must contain text to classify.",
        )

    try:
        classifier = get_classifier(strategy=req.strategy, settings=settings)
    except (JevClassificationError, LLMClassificationError) as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        result = await classifier.classify_email(
            EmailInput(subject=req.subject, body=req.body)
        )
        return result
    except (JevClassificationError, LLMClassificationError) as exc:
        logger.warning("%s classification failed: %s", req.strategy.upper(), exc.message)
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:
        logger.exception("Unexpected classification error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during {req.strategy} classification: {exc}",
        ) from exc


@router.post("/test-batch", response_model=TestBatchResponse)
async def test_batch_classify(
    req: TestBatchRequest,
    settings: Settings = Depends(get_settings),
) -> TestBatchResponse:
    """Evaluate a small batch of records using Jev or LLM decision engine."""
    try:
        classifier = get_classifier(strategy=req.strategy, settings=settings)
    except (JevClassificationError, LLMClassificationError) as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    inputs = [
        EmailInput(subject=r.subject, body=r.body, id=r.id)
        for r in req.records
    ]

    t0 = time.perf_counter()
    try:
        results = await classifier.classify_batch(
            inputs, max_concurrency=req.max_concurrency
        )
    except (JevClassificationError, LLMClassificationError) as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:
        logger.exception("Unexpected batch classification error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during batch {req.strategy} classification: {exc}",
        ) from exc

    total_time_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    avg_time_ms = round(total_time_ms / max(1, len(results)), 2)

    return TestBatchResponse(
        strategy=req.strategy,
        results=results,
        total_count=len(results),
        total_latency_ms=total_time_ms,
        avg_latency_ms=avg_time_ms,
    )
