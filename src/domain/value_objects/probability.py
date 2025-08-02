"""
Probability Value Object - Placeholder
"""

from dataclasses import dataclass

from ..base import ValueObject


@dataclass(frozen=True)
class Probability(ValueObject):
    """Probability placeholder."""

    value: float

    def __post_init__(self) -> None:
        if not 0 <= self.value <= 1:
            raise ValueError("Probability must be between 0 and 1")
