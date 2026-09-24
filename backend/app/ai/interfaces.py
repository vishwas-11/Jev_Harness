"""Abstract interfaces for classification engines."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .models import ClassificationResult, EmailInput


class BaseClassifier(ABC):
    """Abstract base class for all classification engines.

    Allows the application, benchmark harness, and evaluation pipelines
    to interact with Jev, future LLM baselines, and test mocks through
    an identical interface without coupling to provider SDK specifics.
    """

    @abstractmethod
    async def classify_email(self, email: EmailInput) -> ClassificationResult:
        """Classify a single email into structured typed dimensions."""
        raise NotImplementedError

    @abstractmethod
    async def classify_batch(
        self, emails: list[EmailInput], max_concurrency: int = 5
    ) -> list[ClassificationResult]:
        """Classify a bounded batch of emails with controlled concurrency."""
        raise NotImplementedError
