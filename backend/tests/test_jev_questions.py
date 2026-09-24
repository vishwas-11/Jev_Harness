"""Tests for Jev question construction from classification schema."""

from langchain_typesafe import Choice, Noul, Score

from app.ai.jev.questions import build_jev_questions
from app.ai.schemas import DEFAULT_CLASSIFICATION_DEFINITION


def test_build_jev_questions_primitives():
    """Verify each question maps to the appropriate TypeSafe decision primitive."""
    questions = build_jev_questions(DEFAULT_CLASSIFICATION_DEFINITION)

    # 1. Intent -> Choice
    assert "intent" in questions
    assert isinstance(questions["intent"], Choice)
    assert questions["intent"].type == "choice"
    assert len(questions["intent"].criteria) == 8
    assert "billing_issue" in questions["intent"].criteria
    assert "technical_issue" in questions["intent"].criteria
    assert "other" in questions["intent"].criteria

    # 2. Department -> Choice
    assert "department" in questions
    assert isinstance(questions["department"], Choice)
    assert len(questions["department"].criteria) == 7
    assert "billing" in questions["department"].criteria
    assert "support" in questions["department"].criteria

    # 3. Urgency -> Choice
    assert "urgency" in questions
    assert isinstance(questions["urgency"], Choice)
    assert len(questions["urgency"].criteria) == 4
    assert set(questions["urgency"].criteria.keys()) == {"low", "medium", "high", "critical"}

    # 4. Sentiment -> Choice
    assert "sentiment" in questions
    assert isinstance(questions["sentiment"], Choice)
    assert len(questions["sentiment"].criteria) == 5
    assert set(questions["sentiment"].criteria.keys()) == {
        "positive", "neutral", "frustrated", "angry", "negative"
    }

    # 5. Spam -> Noul
    assert "spam" in questions
    assert isinstance(questions["spam"], Noul)
    assert questions["spam"].type == "noul"
    assert questions["spam"].criteria is not None
    assert questions["spam"].criteria.true is not None
    assert questions["spam"].criteria.false is not None

    # 6. Requires Human Review -> Noul
    assert "requires_human" in questions
    assert isinstance(questions["requires_human"], Noul)
    assert questions["requires_human"].criteria is not None
    assert questions["requires_human"].criteria.true is not None

    # 7. Priority -> Score
    assert "priority" in questions
    assert isinstance(questions["priority"], Score)
    assert questions["priority"].type == "score"
    assert isinstance(questions["priority"].criteria, list)
    assert len(questions["priority"].criteria) == 5
