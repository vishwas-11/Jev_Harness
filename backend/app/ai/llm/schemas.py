"""Pydantic schemas for LLM structured output classification."""

from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

IntentType = Literal[
    "billing_issue",
    "technical_issue",
    "account_issue",
    "sales",
    "refund",
    "general_question",
    "complaint",
    "other",
]

DepartmentType = Literal[
    "billing",
    "support",
    "sales",
    "account_management",
    "security",
    "operations",
    "other",
]

UrgencyType = Literal[
    "low",
    "medium",
    "high",
    "critical",
]

SentimentType = Literal[
    "positive",
    "neutral",
    "frustrated",
    "angry",
    "negative",
]


class LLMSupportClassification(BaseModel):
    """Structured output schema enforced on OpenAI LLM baseline.

    Uses native JSON schema enforcement (strict=True) to eliminate
    unstructured prose and parsing failures.
    """

    model_config = ConfigDict(extra="forbid")

    intent: IntentType = Field(
        description="The primary customer intent of the email."
    )
    department: DepartmentType = Field(
        description="The internal department that should handle this request."
    )
    urgency: UrgencyType = Field(
        description="The operational urgency level of the request."
    )
    sentiment: SentimentType = Field(
        description="The dominant customer sentiment expressed."
    )
    spam: bool = Field(
        description="True if the message is unsolicited advertising, phishing, or promotional spam."
    )
    requires_human: bool = Field(
        description="True if the inquiry requires human review, discretion, or escalation rather than automation."
    )
    priority: int = Field(
        ge=0,
        le=4,
        description="Operational priority score: 0 (P5 - Trivial) to 4 (P1 - Critical) following the rubric.",
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Model self-estimated confidence in this classification decision.",
    )
    rationale: str = Field(
        description="Concise 1-sentence rationale for the intent and urgency decision."
    )
