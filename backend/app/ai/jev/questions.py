"""Question builder mapping classification definitions to LangChain TypeSafe primitives."""

from __future__ import annotations

from typing import Any

from langchain_typesafe import Choice, Noul, NoulCriteria, Score

from ..schemas import ClassificationDefinition, DEFAULT_CLASSIFICATION_DEFINITION


def build_jev_questions(
    definition: ClassificationDefinition = DEFAULT_CLASSIFICATION_DEFINITION,
) -> dict[str, Choice | Noul | Score]:
    """Build the dictionary of typed Jev questions for a single-request multi-question evaluation.

    Each question maps to the appropriate TypeSafe decision primitive:
    - Intent      -> Choice (categorical taxonomy)
    - Department  -> Choice (categorical routing)
    - Urgency     -> Choice (discrete urgency bucket)
    - Sentiment   -> Choice (affective customer tone)
    - Spam        -> Noul (binary boolean probability)
    - Human Review-> Noul (binary operational threshold)
    - Priority    -> Score (expected value across an ordered rubric)
    """
    return {
        "intent": Choice(
            instructions=definition.intent.instructions,
            criteria=definition.intent.options,
        ),
        "department": Choice(
            instructions=definition.department.instructions,
            criteria=definition.department.options,
        ),
        "urgency": Choice(
            instructions=definition.urgency.instructions,
            criteria=definition.urgency.options,
        ),
        "sentiment": Choice(
            instructions=definition.sentiment.instructions,
            criteria=definition.sentiment.options,
        ),
        "spam": Noul(
            instructions=definition.spam.instructions,
            criteria=NoulCriteria(
                true=definition.spam.true_criteria,
                false=definition.spam.false_criteria,
            ),
        ),
        "requires_human": Noul(
            instructions=definition.requires_human.instructions,
            criteria=NoulCriteria(
                true=definition.requires_human.true_criteria,
                false=definition.requires_human.false_criteria,
            ),
        ),
        "priority": Score(
            instructions=definition.priority.instructions,
            criteria=definition.priority.rubric,
        ),
    }
