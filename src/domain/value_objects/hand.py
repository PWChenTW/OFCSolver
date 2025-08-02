"""
Hand Value Object

Represents a collection of cards in OFC (Open Face Chinese) layout.
Handles the three-row structure and validation specific to OFC rules.
"""

from dataclasses import dataclass
from typing import List, Optional, Set, Tuple

from ..base import DomainException, ValueObject
from .card import Card
from .card_position import CardPosition


class HandValidationError(DomainException):
    """Exception raised when hand validation fails."""
    pass


class InvalidCardPlacementError(DomainException):
    """Exception raised when trying to place a card in an invalid position."""
    pass


@dataclass(frozen=True)
class Hand(ValueObject):
    """
    Hand value object representing OFC layout.
    
    Contains three rows of cards:
    - Top row: 3 cards (weakest hand)
    - Middle row: 5 cards (medium strength)
    - Bottom row: 5 cards (strongest hand)
    
    Plus cards still in hand waiting to be placed.
    """
    
    top_row: List[Card]
    middle_row: List[Card]
    bottom_row: List[Card]
    hand_cards: List[Card]
    
    def __post_init__(self):
        """Validate hand state after initialization."""
        # Validate row sizes
        if len(self.top_row) > 3:
            raise HandValidationError(f"Top row cannot have more than 3 cards, got {len(self.top_row)}")
        if len(self.middle_row) > 5:
            raise HandValidationError(f"Middle row cannot have more than 5 cards, got {len(self.middle_row)}")
        if len(self.bottom_row) > 5:
            raise HandValidationError(f"Bottom row cannot have more than 5 cards, got {len(self.bottom_row)}")
        
        # Validate no duplicate cards across all positions
        all_cards = self.top_row + self.middle_row + self.bottom_row + self.hand_cards
        if len(all_cards) != len(set(all_cards)):
            raise HandValidationError("Hand contains duplicate cards")
        
        # Validate total card count doesn't exceed 13 (OFC limit)
        if len(all_cards) > 13:
            raise HandValidationError(f"Hand cannot contain more than 13 cards, got {len(all_cards)}")
    
    @classmethod
    def empty(cls) -> "Hand":
        """Create an empty hand."""
        return cls(top_row=[], middle_row=[], bottom_row=[], hand_cards=[])
    
    @classmethod
    def from_cards(cls, cards: List[Card]) -> "Hand":
        """Create hand with all cards in hand (not placed yet)."""
        if len(cards) > 13:
            raise HandValidationError(f"Cannot create hand with more than 13 cards, got {len(cards)}")
        
        return cls(top_row=[], middle_row=[], bottom_row=[], hand_cards=list(cards))
    
    @classmethod
    def from_layout(cls, top: List[Card], middle: List[Card], bottom: List[Card], 
                   hand: Optional[List[Card]] = None) -> "Hand":
        """Create hand from explicit layout."""
        return cls(
            top_row=list(top),
            middle_row=list(middle), 
            bottom_row=list(bottom),
            hand_cards=list(hand) if hand else []
        )
    
    def is_complete(self) -> bool:
        """Check if hand layout is complete (all 13 cards placed)."""
        return (
            len(self.top_row) == 3 and
            len(self.middle_row) == 5 and
            len(self.bottom_row) == 5 and
            len(self.hand_cards) == 0
        )
    
    def is_valid_for_completion(self) -> bool:
        """Check if current layout can potentially be completed validly."""
        total_cards = len(self.top_row) + len(self.middle_row) + len(self.bottom_row) + len(self.hand_cards)
        return total_cards <= 13
    
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
    
    def can_place_card(self, position: CardPosition) -> bool:
        """Check if a card can be placed in the given position."""
        if position == CardPosition.TOP:
            return len(self.top_row) < 3
        elif position == CardPosition.MIDDLE:
            return len(self.middle_row) < 5
        elif position == CardPosition.BOTTOM:
            return len(self.bottom_row) < 5
        return False
    
    def place_card(self, card: Card, position: CardPosition) -> "Hand":
        """
        Create new hand with card placed in specified position.
        
        Args:
            card: Card to place
            position: Where to place the card
            
        Returns:
            New Hand instance with card placed
            
        Raises:
            InvalidCardPlacementError: If placement is invalid
        """
        if card not in self.hand_cards:
            raise InvalidCardPlacementError(f"Card {card} is not available to place")
        
        if not self.can_place_card(position):
            raise InvalidCardPlacementError(f"Cannot place card in {position} - position full")
        
        # Create new card lists
        new_hand_cards = [c for c in self.hand_cards if c != card]
        new_top = list(self.top_row)
        new_middle = list(self.middle_row)
        new_bottom = list(self.bottom_row)
        
        # Place card in appropriate row
        if position == CardPosition.TOP:
            new_top.append(card)
        elif position == CardPosition.MIDDLE:
            new_middle.append(card)
        elif position == CardPosition.BOTTOM:
            new_bottom.append(card)
        
        return Hand.from_layout(new_top, new_middle, new_bottom, new_hand_cards)
    
    def place_cards(self, placements: List[Tuple[Card, CardPosition]]) -> "Hand":
        """
        Place multiple cards at once.
        
        Args:
            placements: List of (card, position) tuples
            
        Returns:
            New Hand instance with all cards placed
        """
        result = self
        for card, position in placements:
            result = result.place_card(card, position)
        return result
    
    def remove_card(self, card: Card) -> "Hand":
        """
        Remove a card from any position and return to hand.
        
        Args:
            card: Card to remove
            
        Returns:
            New Hand instance with card back in hand
            
        Raises:
            InvalidCardPlacementError: If card not found in any row
        """
        new_top = list(self.top_row)
        new_middle = list(self.middle_row)
        new_bottom = list(self.bottom_row)
        new_hand_cards = list(self.hand_cards)
        
        # Try to remove from each row
        if card in new_top:
            new_top.remove(card)
            new_hand_cards.append(card)
        elif card in new_middle:
            new_middle.remove(card)
            new_hand_cards.append(card)
        elif card in new_bottom:
            new_bottom.remove(card)
            new_hand_cards.append(card)
        else:
            raise InvalidCardPlacementError(f"Card {card} not found in any row")
        
        return Hand.from_layout(new_top, new_middle, new_bottom, new_hand_cards)
    
    def get_all_placed_cards(self) -> List[Card]:
        """Get all cards that have been placed in rows."""
        return self.top_row + self.middle_row + self.bottom_row
    
    def get_all_cards(self) -> List[Card]:
        """Get all cards in this hand (placed and unplaced)."""
        return self.get_all_placed_cards() + self.hand_cards
    
    def get_cards_by_position(self, position: CardPosition) -> List[Card]:
        """Get cards in a specific position."""
        if position == CardPosition.TOP:
            return list(self.top_row)
        elif position == CardPosition.MIDDLE:
            return list(self.middle_row)
        elif position == CardPosition.BOTTOM:
            return list(self.bottom_row)
        else:
            raise ValueError(f"Invalid position: {position}")
    
    def count_cards_in_position(self, position: CardPosition) -> int:
        """Count cards in a specific position."""
        return len(self.get_cards_by_position(position))
    
    def is_position_full(self, position: CardPosition) -> bool:
        """Check if a position is full."""
        return self.count_cards_in_position(position) >= position.max_cards
    
    def is_position_empty(self, position: CardPosition) -> bool:
        """Check if a position is empty."""
        return self.count_cards_in_position(position) == 0
    
    def get_completion_progress(self) -> dict:
        """Get completion progress for each position."""
        return {
            CardPosition.TOP: {
                "current": len(self.top_row),
                "max": 3,
                "complete": len(self.top_row) == 3
            },
            CardPosition.MIDDLE: {
                "current": len(self.middle_row),
                "max": 5,
                "complete": len(self.middle_row) == 5
            },
            CardPosition.BOTTOM: {
                "current": len(self.bottom_row),
                "max": 5,
                "complete": len(self.bottom_row) == 5
            }
        }
    
    def is_fouled(self, hand_evaluator=None) -> bool:
        """
        Check if hand is fouled (invalid according to OFC rules).
        
        A hand is fouled if:
        - Top row beats middle row, or
        - Middle row beats bottom row
        
        Args:
            hand_evaluator: Optional HandEvaluator instance for validation
                          If None, returns False (placeholder behavior)
        
        Returns:
            True if fouled, False if valid
        """
        # Must be complete to check for fouling
        if not self.is_complete():
            return False
        
        # If no evaluator provided, return False (placeholder)
        if hand_evaluator is None:
            return False
        
        # Use the evaluator to check OFC progression
        return not hand_evaluator.validate_ofc_progression(
            self.top_row, self.middle_row, self.bottom_row
        )
    
    def validate_ofc_rules(self, hand_evaluator=None) -> bool:
        """
        Validate that hand follows OFC rules.
        
        Args:
            hand_evaluator: Optional HandEvaluator instance for validation
        
        Returns:
            True if valid, False if fouled
        """
        return not self.is_fouled(hand_evaluator)
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "top_row": [str(card) for card in self.top_row],
            "middle_row": [str(card) for card in self.middle_row],
            "bottom_row": [str(card) for card in self.bottom_row],
            "hand_cards": [str(card) for card in self.hand_cards],
            "is_complete": self.is_complete(),
            "completion_progress": self.get_completion_progress()
        }
    
    def to_string(self) -> str:
        """Convert to string representation."""
        def format_row(cards: List[Card], label: str) -> str:
            if not cards:
                return f"{label}: (empty)"
            return f"{label}: {' '.join(str(c) for c in cards)}"
        
        lines = [
            format_row(self.top_row, "Top"),
            format_row(self.middle_row, "Mid"),
            format_row(self.bottom_row, "Bot")
        ]
        
        if self.hand_cards:
            lines.append(f"Hand: {' '.join(str(c) for c in self.hand_cards)}")
        
        return "\n".join(lines)
    
    def normalize_for_comparison(self) -> dict:
        """Normalize for position comparison (sorted cards)."""
        return {
            "top": sorted(str(c) for c in self.top_row),
            "middle": sorted(str(c) for c in self.middle_row),
            "bottom": sorted(str(c) for c in self.bottom_row),
            "hand": sorted(str(c) for c in self.hand_cards)
        }
    
    def __str__(self) -> str:
        """String representation for debugging."""
        return self.to_string()
    
    def __len__(self) -> int:
        """Total number of cards in hand."""
        return len(self.get_all_cards())