"""Factory for instantiating classification engines based on settings."""

from __future__ import annotations

import logging
from functools import lru_cache

from ..config import Settings, get_settings
from .interfaces import BaseClassifier
from .jev.adapter import JevClassifier
from .jev.mock import MockJevClassifier

logger = logging.getLogger(__name__)


def get_classifier(
    settings: Settings | None = None,
    force_mock: bool = False,
) -> BaseClassifier:
    """Return configured classification engine.

    If credentials are missing or force_mock is requested, returns MockJevClassifier
    so development, testing, and UI evaluation function seamlessly without live billing.
    """
    cfg = settings or get_settings()

    if force_mock or not cfg.has_jev_credentials:
        if not force_mock:
            logger.info(
                "No Jev credentials found (AI_GATEWAY_API_KEY / TYPESAFE_API_KEY). "
                "Operating in mock development sandbox mode."
            )
        return MockJevClassifier()

    return JevClassifier(
        api_key=cfg.effective_jev_api_key or "",
        base_url=cfg.ai_gateway_base_url,
        model=cfg.jev_model,
        timeout=cfg.jev_timeout,
    )
