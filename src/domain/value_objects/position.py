"""
Position Value Object

Represents a position on the OFC board where a card can be placed.
"""

from dataclasses import dataclass
from enum import Enum

from ..base import ValueObject


class Row(Enum):
    """OFC board rows."""

    TOP = "top"  # Front row - 3 cards
    MIDDLE = "middle"  # Middle row - 5 cards
    BOTTOM = "bottom"  # Back row - 5 cards


@dataclass(frozen=True)
class Position(ValueObject):
    """
    Represents a specific position on the OFC board.

    Each position is identified by row and index within that row.
    """

    row: Row
    index: int  # 0-based index within the row

    def __post_init__(self):
        """Validate position."""
        max_index = self._get_max_index()
        if self.index < 0 or self.index >= max_index:
            raise ValueError(
                f"Invalid index {self.index} for row {self.row.value}. "
                f"Must be 0-{max_index-1}"
            )

    def _get_max_index(self) -> int:
        """Get maximum index for the row."""
        if self.row == Row.TOP:
            return 3
        else:  # MIDDLE or BOTTOM
            return 5

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "row": self.row.value,
            "index": self.index,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Position":
        """Create from dictionary representation."""
        return cls(
            row=Row(data["row"]),
            index=data["index"],
        )

    def __str__(self) -> str:
        """String representation."""
        return f"{self.row.value}[{self.index}]"

    @property
    def is_top_row(self) -> bool:
        """Check if position is in top row."""
        return self.row == Row.TOP

    @property
    def is_middle_row(self) -> bool:
        """Check if position is in middle row."""
        return self.row == Row.MIDDLE

    @property
    def is_bottom_row(self) -> bool:
        """Check if position is in bottom row."""
        return self.row == Row.BOTTOM
