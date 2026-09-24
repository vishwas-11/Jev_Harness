"""Classification definitions, dimension specifications, and rubric taxonomies.

This schema is provider-agnostic so the same classification criteria can be reused
across Jev, future LLM baselines, and hybrid routing configurations.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class ChoiceDimension(BaseModel):
    """Specification for a categorical choice dimension."""

    instructions: str
    options: dict[str, str] = Field(
        description="Allowed categorical options mapped to their semantic criteria.",
    )


class BooleanDimension(BaseModel):
    """Specification for a binary (yes/no) dimension."""

    instructions: str
    true_criteria: str
    false_criteria: str


class ScoreDimension(BaseModel):
    """Specification for an ordinal score dimension evaluated across an ordered rubric."""

    instructions: str
    rubric: list[str] = Field(
        description="Zero-indexed rubric descriptions from lowest to highest level.",
    )


class ClassificationDefinition(BaseModel):
    """Complete specification of the 7 support email classification dimensions."""

    version: str = "1.0.0"
    intent: ChoiceDimension
    department: ChoiceDimension
    urgency: ChoiceDimension
    sentiment: ChoiceDimension
    spam: BooleanDimension
    requires_human: BooleanDimension
    priority: ScoreDimension


# Standard Default Support Taxonomy
DEFAULT_CLASSIFICATION_DEFINITION = ClassificationDefinition(
    version="1.0.0",
    intent=ChoiceDimension(
        instructions="What is the primary customer intent of this email?",
        options={
            "billing_issue": "Invoices, payment failures, subscription renewals, or billing disputes.",
            "technical_issue": "Software bugs, API errors, system crashes, connection problems, or service downtime.",
            "account_issue": "Login failures, password resets, 2FA issues, account lockouts, or profile updates.",
            "sales": "Enterprise pricing inquiries, product demonstrations, new feature requests, or license purchasing.",
            "refund": "Explicit requests for return of funds, payment reversals, or chargeback inquiries.",
            "general_question": "How-to questions, documentation guidance, roadmap inquiries, or general information requests.",
            "complaint": "Dissatisfaction with service quality, delayed response, executive escalations, or policy objections.",
            "other": "Emails that do not fit into any predefined category or lack coherent support context.",
        },
    ),
    department=ChoiceDimension(
        instructions="Which organizational department should be assigned to resolve this request?",
        options={
            "billing": "Handles payment processing, invoices, subscription changes, and refunds.",
            "support": "Handles day-to-day product troubleshooting, how-to inquiries, and customer assistance.",
            "sales": "Handles prospective customers, deal negotiations, quotes, and contract expansions.",
            "account_management": "Handles enterprise account renewals, executive relationships, and account reviews.",
            "security": "Handles vulnerability reports, authentication breaches, suspicious activity, and security compliance.",
            "operations": "Handles infrastructure incidents, maintenance notices, and platform availability.",
            "other": "Cross-departmental issues or unroutable inquiries requiring initial human triage.",
        },
    ),
    urgency=ChoiceDimension(
        instructions="How quickly must this customer communication be addressed?",
        options={
            "low": "Routine query with no business impact; can be addressed within standard SLA.",
            "medium": "Standard issue causing mild customer inconvenience without blocking critical operations.",
            "high": "Significant business friction, degradation of core functionality, or dissatisfied customer.",
            "critical": "Complete service outage, data loss threat, security breach, or high-value customer churn risk.",
        },
    ),
    sentiment=ChoiceDimension(
        instructions="What is the dominant emotional tone expressed by the customer in this message?",
        options={
            "positive": "Customer expresses gratitude, satisfaction, or polite praise.",
            "neutral": "Objective, matter-of-fact tone without emotional charge.",
            "frustrated": "Mild to moderate annoyance, impatience, or exasperation due to delay or friction.",
            "angry": "Strong hostility, aggressive phrasing, accusations, or threats of legal/regulatory action.",
            "negative": "Pessimistic, disappointed, or unhappy tone without active aggression.",
        },
    ),
    spam=BooleanDimension(
        instructions="Is this email unsolicited commercial advertising, promotional noise, or spam?",
        true_criteria="Unsolicited commercial advertising, phishing attempts, mass automated promotions, or irrelevant marketing blasts.",
        false_criteria="Genuine customer communication, support inquiry, business request, or authentic notification.",
    ),
    requires_human=BooleanDimension(
        instructions="Does this email require human discernment, specialized empathy, or escalation rather than automated handling?",
        true_criteria="High ambiguity, legal/regulatory threats, large financial impact, severe distress, or unhandled edge cases.",
        false_criteria="Standard, unambiguous inquiry that follows established operational playbooks and can be automated.",
    ),
    priority=ScoreDimension(
        instructions="Evaluate the operational triage priority of this support email from P5 (trivial) to P1 (critical).",
        rubric=[
            "P5 - Trivial: Non-actionable informational inquiry, spam candidate, or automated notification requiring zero immediate triage.",
            "P4 - Low: Informational request or minor question with no operational urgency; standard response window.",
            "P3 - Normal: Standard support or billing request with minor business impact; standard priority resolution.",
            "P2 - High: Escalated customer issue, billing dispute, or technical problem impacting business workflow; fast resolution needed.",
            "P1 - Critical: Urgent emergency, severe outage, security incident, refund demand, or executive escalation; immediate resolution required.",
        ],
    ),
)
