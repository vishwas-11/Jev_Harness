"""Factory for instantiating production classification engines based on settings.

NO RUNTIME MOCK FALLBACK:
If API credentials are not configured, this factory raises explicit configuration errors.
It never silently falls back to a fake or mock decision engine.
"""

from __future__ import annotations

import logging

from ..config import Settings, get_settings
from .interfaces import BaseClassifier
from .jev.adapter import JevClassifier, JevConfigurationError
from .llm.adapter import LLMClassifier, LLMConfigurationError

logger = logging.getLogger(__name__)


def get_jev_classifier(settings: Settings | None = None) -> JevClassifier:
    """Return production Jev classifier or raise JevConfigurationError if key is missing."""
    cfg = settings or get_settings()

    if not cfg.has_jev_credentials:
        raise JevConfigurationError(
            "Vercel AI Gateway API key is missing. "
            "Please configure AI_GATEWAY_API_KEY in backend/.env to run Jev classifications."
        )

    return JevClassifier(
        api_key=cfg.effective_jev_api_key or "",
        base_url=cfg.ai_gateway_base_url,
        model=cfg.jev_model,
        timeout=cfg.jev_timeout,
    )


def get_llm_classifier(settings: Settings | None = None) -> LLMClassifier:
    """Return production LLM classifier or raise LLMConfigurationError if key is missing."""
    cfg = settings or get_settings()

    if not cfg.has_llm_credentials:
        raise LLMConfigurationError(
            "OpenAI API key is missing. "
            "Please configure OPENAI_API_KEY in backend/.env to run LLM baseline classifications."
        )

    return LLMClassifier(
        api_key=cfg.effective_openai_api_key or "",
        model=cfg.llm_model,
        timeout=cfg.llm_timeout,
    )


def get_classifier(
    strategy: str = "jev",
    settings: Settings | None = None,
) -> BaseClassifier:
    """Return the specified classification engine (jev or llm).

    Fails loudly with structured configuration errors when credentials are unavailable.
    """
    strat = strategy.lower().strip()
    if strat == "jev":
        return get_jev_classifier(settings=settings)
    elif strat in ["llm", "openai"]:
        return get_llm_classifier(settings=settings)
    else:
        raise ValueError(f"Unsupported classification strategy '{strategy}'. Supported: 'jev', 'llm'.")
