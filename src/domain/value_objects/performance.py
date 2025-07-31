"""Performance Value Object - Placeholder"""

from dataclasses import dataclass

from ..base import ValueObject


@dataclass(frozen=True)
class Performance(ValueObject):
    """Performance placeholder."""

    score: float
    accuracy: float = 0.0
