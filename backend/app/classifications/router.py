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
from ..config import Settings, get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/classifications", tags=["classifications"])


class TestClassificationRequest(BaseModel):
    """Request payload for single-email test classification."""

    subject: str = Field(default="", description="Email subject line.")
    body: str = Field(default="", description="Email body content.")
    force_mock: bool = Field(
        default=False,
        description="Force the local mock engine even if API credentials are configured.",
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
    force_mock: bool = False
    max_concurrency: int = Field(default=5, ge=1, le=10)


class TestBatchResponse(BaseModel):
    """Response containing batch classification results and summary metrics."""

    results: list[ClassificationResult]
    total_count: int
    total_latency_ms: float
    avg_latency_ms: float


class ProviderStatusResponse(BaseModel):
    """Provider configuration status without revealing secrets."""

    configured: bool
    mode: str
    provider: str
    gateway_url: str
    model: str


@router.get("/schema", response_model=ClassificationDefinition)
async def get_classification_schema() -> ClassificationDefinition:
    """Return the active classification definition, questions, categories, and rubric."""
    return DEFAULT_CLASSIFICATION_DEFINITION


@router.get("/provider-status", response_model=ProviderStatusResponse)
async def get_provider_status(settings: Settings = Depends(get_settings)) -> ProviderStatusResponse:
    """Return Jev and AI Gateway integration status for the control plane."""
    has_creds = settings.has_jev_credentials
    return ProviderStatusResponse(
        configured=has_creds,
        mode="live" if has_creds else "sandbox",
        provider="Vercel AI Gateway" if has_creds else "Mock Sandbox Engine",
        gateway_url=settings.ai_gateway_base_url,
        model=settings.jev_model,
    )


@router.post("/test", response_model=ClassificationResult)
async def test_classify(
    req: TestClassificationRequest,
    settings: Settings = Depends(get_settings),
) -> ClassificationResult:
    """Evaluate a single email using Jev decision primitives."""
    if not req.subject.strip() and not req.body.strip():
        raise HTTPException(
            status_code=422,
            detail="Subject or body must contain text to classify.",
        )

    classifier = get_classifier(settings=settings, force_mock=req.force_mock)

    try:
        result = await classifier.classify_email(
            EmailInput(subject=req.subject, body=req.body)
        )
        return result
    except JevClassificationError as exc:
        logger.warning("Classification failed: %s", exc.message)
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:
        logger.exception("Unexpected classification error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during classification.",
        ) from exc


@router.post("/test-batch", response_model=TestBatchResponse)
async def test_batch_classify(
    req: TestBatchRequest,
    settings: Settings = Depends(get_settings),
) -> TestBatchResponse:
    """Evaluate a small batch of records using Jev decision primitives."""
    classifier = get_classifier(settings=settings, force_mock=req.force_mock)

    inputs = [
        EmailInput(subject=r.subject, body=r.body, id=r.id)
        for r in req.records
    ]

    t0 = time.perf_counter()
    try:
        results = await classifier.classify_batch(
            inputs, max_concurrency=req.max_concurrency
        )
    except JevClassificationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:
        logger.exception("Unexpected batch classification error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during batch classification.",
        ) from exc

    total_time_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    avg_time_ms = round(total_time_ms / max(1, len(results)), 2)

    return TestBatchResponse(
        results=results,
        total_count=len(results),
        total_latency_ms=total_time_ms,
        avg_latency_ms=avg_time_ms,
    )
