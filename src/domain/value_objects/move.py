"""
Move Value Object

Represents a card placement move in OFC.
"""

from dataclasses import dataclass
from typing import Optional

from ..base import ValueObject
from .card import Card
from .card_position import CardPosition


@dataclass(frozen=True)
class Move(ValueObject):
    """
    Immutable move value object.
    
    Represents placing a specific card at a specific position.
    """
    card: Card
    position: CardPosition
    player_id: Optional[str] = None  # Optional for context
    
    def __str__(self) -> str:
        """String representation (e.g., 'As->top')."""
        return f"{self.card}->{self.position.value}"
    
    def __repr__(self) -> str:
        """Detailed representation."""
        return f"Move(card={self.card}, position={self.position.value})"
    
    @classmethod
    def from_string(cls, move_str: str, player_id: Optional[str] = None) -> 'Move':
        """
        Create move from string representation.
        
        Args:
            move_str: String like 'As->top', 'Kh->middle'
            player_id: Optional player ID
            
        Returns:
            Move instance
        """
        if '->' not in move_str:
            raise ValueError(f"Move string must contain '->', got: {move_str}")
        
        card_str, position_str = move_str.split('->', 1)
        card = Card.from_string(card_str.strip())
        position = CardPosition.from_string(position_str.strip())
        
        return cls(card=card, position=position, player_id=player_id)
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            'card': str(self.card),
            'position': self.position.value,
            'player_id': self.player_id
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Move':
        """Create move from dictionary."""
        return cls(
            card=Card.from_string(data['card']),
            position=CardPosition.from_string(data['position']),
            player_id=data.get('player_id')
        )
    
    def is_same_move(self, other: 'Move') -> bool:
        """Check if this is the same move (ignoring player_id)."""
        return self.card == other.card and self.position == other.position
    
    def with_player(self, player_id: str) -> 'Move':
        """Create new move with player ID."""
        return Move(
            card=self.card,
            position=self.position, 
            player_id=player_id
        )