"""
Expected Value Value Object - Placeholder
"""

from dataclasses import dataclass

from ..base import ValueObject


@dataclass(frozen=True)
class ExpectedValue(ValueObject):
    """Expected value placeholder."""

    value: float

    def to_dict(self) -> dict:
        return {"value": self.value}
