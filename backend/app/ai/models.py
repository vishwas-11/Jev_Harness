"""Domain models for AI classification decisions, primitives, traces, and timing."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class EmailInput(BaseModel):
    """Raw input email to be classified."""

    subject: str = Field(default="", description="Email subject line.")
    body: str = Field(default="", description="Email plain text or markdown body.")
    id: str | None = Field(default=None, description="Optional external or dataset record ID.")

    model_config = ConfigDict(extra="ignore")

    def to_state(self) -> dict[str, str]:
        """Convert email into structured state."""
        return {
            "subject": self.subject.strip(),
            "body": self.body.strip(),
        }


class ChoiceDecision(BaseModel):
    """Result of a categorical choice decision (Jev Choice or LLM enum)."""

    question_id: str
    choice: str
    confidence: float = Field(ge=0.0, le=1.0, description="Model confidence or distribution probability in the chosen label.")
    probabilities: dict[str, float] = Field(
        default_factory=dict,
        description="Probability distribution across all allowed categories (from Jev or LLM output).",
    )


class BooleanDecision(BaseModel):
    """Result of a binary/boolean decision (Jev Noul or LLM bool).

    In Jev/TypeSafe, a Noul evaluates the probability that a statement is 'true'.
    The boolean `value` is True when probability >= 0.5.
    `confidence` represents distance from maximal uncertainty (0.5), computed as max(p, 1 - p).
    """

    question_id: str
    value: bool
    probability: float = Field(ge=0.0, le=1.0, description="Probability that the answer is yes/true.")
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Decision confidence computed as max(p, 1 - p).",
    )


class ScoreDecision(BaseModel):
    """Result of an ordinal score decision (Jev Score expected value or LLM rubric score).

    Evaluated against an ordered zero-indexed rubric (0 to 4).
    `score` is the expected value or rubric level.
    `legend` contains the rubric descriptions for each level.
    """

    question_id: str
    score: float = Field(ge=0.0, description="Ordinal score (expected value or discrete level).")
    max_score: float = Field(default=4.0, description="Maximum scale level.")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in the score estimate.")
    legend: dict[int, str] = Field(default_factory=dict, description="Rubric criteria descriptions.")
    probabilities: dict[int, float] = Field(
        default_factory=dict,
        description="Probability distribution over each rubric index.",
    )


class LatencyBreakdown(BaseModel):
    """Detailed timing instrumentation for classification pipeline phases."""

    state_prep_ms: float = Field(default=0.0, description="Time spent formatting input state and questions/prompts.")
    jev_request_ms: float = Field(default=0.0, description="Time spent in the HTTP network round-trip to Jev.")
    llm_request_ms: float = Field(default=0.0, description="Time spent awaiting LLM provider completion.")
    normalization_ms: float = Field(default=0.0, description="Time spent normalizing provider output into domain models.")
    validation_ms: float = Field(default=0.0, description="Time spent validating structured output schemas.")
    total_ms: float = Field(default=0.0, description="End-to-end classification latency.")


class DecisionTrace(BaseModel):
    """Audit and explainability trace for the decision."""

    request_id: str | None = Field(default=None, description="Provider or gateway request correlation ID.")
    model: str = Field(description="Model identifier, e.g. typesafe-ai/jev or gpt-4o-mini.")
    provider: str = Field(default="vercel-ai-gateway", description="Routing provider (e.g. vercel-ai-gateway, openai).")
    strategy: str = Field(default="jev", description="Classification strategy ('jev' or 'llm').")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    latency: LatencyBreakdown
    usage: dict[str, int | None] = Field(
        default_factory=lambda: {"input_tokens": None, "output_tokens": None, "total_tokens": None},
        description="Token or decision unit usage.",
    )
    finish_reason: str | None = Field(default=None, description="LLM finish reason if applicable.")
    validation_status: str = Field(default="VALID", description="Structured output validation status.")
    raw_decisions: dict[str, Any] = Field(
        default_factory=dict,
        description="Sanitized summary of raw provider answers.",
    )


class ClassificationResult(BaseModel):
    """Normalized multi-dimensional decision result common across Jev and LLM."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    strategy: str = Field(default="jev", description="Engine strategy: 'jev' or 'llm'.")
    subject: str
    body_snippet: str
    intent: ChoiceDecision
    department: ChoiceDecision
    urgency: ChoiceDecision
    sentiment: ChoiceDecision
    spam: BooleanDecision
    requires_human: BooleanDecision
    priority: ScoreDecision
    aggregate_confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Mean confidence across dimensions.",
    )
    latency: LatencyBreakdown
    trace: DecisionTrace
    is_mock: bool = Field(default=False, description="True only if produced by test fake in test suite.")
