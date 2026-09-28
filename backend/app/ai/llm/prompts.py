"""Prompt templates constructing semantic parity for LLM classification."""

from __future__ import annotations

from ..schemas import ClassificationDefinition, DEFAULT_CLASSIFICATION_DEFINITION


def build_llm_system_prompt(
    definition: ClassificationDefinition = DEFAULT_CLASSIFICATION_DEFINITION,
) -> str:
    """Build system instructions ensuring 100% semantic parity with Jev's questions.

    The exact same categories, criteria, true/false definitions, and rubric tiers
    are injected into the LLM system prompt.
    """
    intent_lines = "\n".join(
        f"  - `{k}`: {v}" for k, v in definition.intent.options.items()
    )
    dept_lines = "\n".join(
        f"  - `{k}`: {v}" for k, v in definition.department.options.items()
    )
    urgency_lines = "\n".join(
        f"  - `{k}`: {v}" for k, v in definition.urgency.options.items()
    )
    sentiment_lines = "\n".join(
        f"  - `{k}`: {v}" for k, v in definition.sentiment.options.items()
    )
    rubric_lines = "\n".join(
        f"  Level {i}: {desc}" for i, desc in enumerate(definition.priority.rubric)
    )

    return f"""You are an expert customer support email decision classifier.
Your task is to analyze the provided customer email and classify it across 7 standardized dimensions.

Follow the exact criteria and taxonomy defined below:

1. Intent ({definition.intent.instructions})
Allowed choices:
{intent_lines}

2. Department ({definition.department.instructions})
Allowed choices:
{dept_lines}

3. Urgency ({definition.urgency.instructions})
Allowed choices:
{urgency_lines}

4. Sentiment ({definition.sentiment.instructions})
Allowed choices:
{sentiment_lines}

5. Spam ({definition.spam.instructions})
- True criteria: {definition.spam.true_criteria}
- False criteria: {definition.spam.false_criteria}

6. Human Review ({definition.requires_human.instructions})
- True criteria: {definition.requires_human.true_criteria}
- False criteria: {definition.requires_human.false_criteria}

7. Priority ({definition.priority.instructions})
Rubric levels:
{rubric_lines}

Evaluate the email state objectively based only on the criteria provided above.
Return the structured classification matching the required schema.
"""


def build_llm_user_prompt(subject: str, body: str) -> str:
    """Format email state as a clean input message without prompt pollution."""
    return f"""Email Subject:
{subject.strip() or "(No Subject)"}

Email Body:
{body.strip() or "(No Body Content)"}
"""
