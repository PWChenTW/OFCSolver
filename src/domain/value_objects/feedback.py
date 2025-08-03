"""Feedback Value Object - Placeholder"""

from dataclasses import dataclass
from enum import Enum
from typing import List

from ..base import ValueObject


class FeedbackLevel(Enum):
    """Feedback quality levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    NEEDS_IMPROVEMENT = "needs_improvement"


@dataclass(frozen=True)
class Feedback(ValueObject):
    """Feedback placeholder."""

    level: FeedbackLevel
    message: str
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    category: str = "general"
