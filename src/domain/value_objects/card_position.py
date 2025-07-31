"""
Card Position Value Object

Represents the position where a card can be placed in OFC layout.
"""

from enum import Enum

from ..base import ValueObject


class CardPosition(Enum):
    """Positions where cards can be placed in OFC layout."""
    TOP = "top"        # Top row (3 cards)
    MIDDLE = "middle"  # Middle row (5 cards) 
    BOTTOM = "bottom"  # Bottom row (5 cards)
    
    def __str__(self) -> str:
        return self.value
    
    @property
    def max_cards(self) -> int:
        """Get maximum number of cards for this position."""
        return {
            CardPosition.TOP: 3,
            CardPosition.MIDDLE: 5,
            CardPosition.BOTTOM: 5
        }[self]
    
    @property
    def display_name(self) -> str:
        """Get display name for UI."""
        return {
            CardPosition.TOP: "Top Row",
            CardPosition.MIDDLE: "Middle Row", 
            CardPosition.BOTTOM: "Bottom Row"
        }[self]
    
    @classmethod
    def all_positions(cls) -> list['CardPosition']:
        """Get all positions in order."""
        return [cls.TOP, cls.MIDDLE, cls.BOTTOM]
    
    @classmethod
    def from_string(cls, position_str: str) -> 'CardPosition':
        """Create position from string."""
        position_str = position_str.lower().strip()
        for position in cls:
            if position.value == position_str:
                return position
        raise ValueError(f"Invalid position: {position_str}")