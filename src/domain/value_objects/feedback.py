"""Feedback Value Object - Placeholder"""

from dataclasses import dataclass

from ..base import ValueObject


@dataclass(frozen=True)
class Feedback(ValueObject):
    """Feedback placeholder."""

    message: str
    category: str = "general"
