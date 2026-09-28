"""LLM Baseline package for structured output email classification."""

from .adapter import (
    LLMAuthenticationError,
    LLMClassificationError,
    LLMClassifier,
    LLMConfigurationError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMValidationError,
)
from .prompts import build_llm_system_prompt, build_llm_user_prompt
from .schemas import LLMSupportClassification

__all__ = [
    "LLMAuthenticationError",
    "LLMClassificationError",
    "LLMClassifier",
    "LLMConfigurationError",
    "LLMProviderError",
    "LLMRateLimitError",
    "LLMSupportClassification",
    "LLMTimeoutError",
    "LLMValidationError",
    "build_llm_system_prompt",
    "build_llm_user_prompt",
]
