"""Score Value Object - Placeholder"""

from dataclasses import dataclass

from ..base import ValueObject


@dataclass(frozen=True)
class Score(ValueObject):
    """Score placeholder."""

    points: int
    royalties: int = 0
    penalties: int = 0

    @property
    def total_points(self) -> int:
        return self.points + self.royalties - self.penalties
