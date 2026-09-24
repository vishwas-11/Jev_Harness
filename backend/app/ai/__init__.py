"""AI package for decision models, schema definitions, and classification interfaces."""

from .factory import get_classifier
from .interfaces import BaseClassifier
from .models import (
    BooleanDecision,
    ChoiceDecision,
    ClassificationResult,
    DecisionTrace,
    EmailInput,
    LatencyBreakdown,
    ScoreDecision,
)
from .schemas import (
    BooleanDimension,
    ChoiceDimension,
    ClassificationDefinition,
    DEFAULT_CLASSIFICATION_DEFINITION,
    ScoreDimension,
)

__all__ = [
    "BaseClassifier",
    "BooleanDecision",
    "BooleanDimension",
    "ChoiceDecision",
    "ChoiceDimension",
    "ClassificationDefinition",
    "ClassificationResult",
    "DEFAULT_CLASSIFICATION_DEFINITION",
    "DecisionTrace",
    "EmailInput",
    "LatencyBreakdown",
    "ScoreDecision",
    "ScoreDimension",
    "get_classifier",
]
