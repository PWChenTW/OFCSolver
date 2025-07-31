"""
Hand Value Object - Placeholder

This module will contain the Hand value object representing
a collection of cards in OFC layout format.
"""

from dataclasses import dataclass
from typing import List

from ..base import ValueObject
from .card import Card
from .card_position import CardPosition


@dataclass(frozen=True)
class Hand(ValueObject):
    """
    Hand value object - placeholder implementation.

    TODO: Implement full hand logic including:
    - Three-row layout (top, middle, bottom)
    - Hand cards not yet placed
    - Validation methods
    - Layout completion checking
    """

    top_row: List[Card]
    middle_row: List[Card]
    bottom_row: List[Card]
    hand_cards: List[Card]

    def is_complete(self) -> bool:
        """Check if hand layout is complete."""
        return (
            len(self.top_row) == 3
            and len(self.middle_row) == 5
            and len(self.bottom_row) == 5
        )

    def get_available_positions(self) -> List[CardPosition]:
        """Get positions where cards can still be placed."""
        positions = []
        if len(self.top_row) < 3:
            positions.append(CardPosition.TOP)
        if len(self.middle_row) < 5:
            positions.append(CardPosition.MIDDLE)
        if len(self.bottom_row) < 5:
            positions.append(CardPosition.BOTTOM)
        return positions

    def place_card(self, card: Card, position: CardPosition) -> "Hand":
        """Create new hand with card placed."""
        # TODO: Implement card placement logic
        pass

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "top_row": [str(card) for card in self.top_row],
            "middle_row": [str(card) for card in self.middle_row],
            "bottom_row": [str(card) for card in self.bottom_row],
            "hand_cards": [str(card) for card in self.hand_cards],
        }

    def to_string(self) -> str:
        """Convert to string representation."""
        top_str = " ".join(str(c) for c in self.top_row)
        middle_str = " ".join(str(c) for c in self.middle_row)
        bottom_str = " ".join(str(c) for c in self.bottom_row)
        return f"T:{top_str} M:{middle_str} B:{bottom_str}"

    def normalize_for_comparison(self) -> dict:
        """Normalize for position comparison."""
        return {
            "top": sorted(str(c) for c in self.top_row),
            "middle": sorted(str(c) for c in self.middle_row),
            "bottom": sorted(str(c) for c in self.bottom_row),
        }
