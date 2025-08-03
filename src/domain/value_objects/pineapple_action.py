"""
Pineapple OFC Action Value Object

Represents the 3-pick-2 action specific to Pineapple OFC variant.
"""

from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from .card import Card
from .position import Position


@dataclass(frozen=True)
class PineappleAction:
    """
    Represents a Pineapple OFC action where player receives 3 cards,
    places 2, and discards 1.
    """

    player_id: UUID
    street: int
    dealt_cards: List[Card]  # 3 cards dealt
    placements: List[tuple[Card, Position]]  # 2 cards to place
    discarded_card: Card  # 1 card to discard

    def __post_init__(self):
        """Validate the action."""
        if len(self.dealt_cards) != 3:
            raise ValueError(f"Must deal exactly 3 cards, got {len(self.dealt_cards)}")

        if len(self.placements) != 2:
            raise ValueError(f"Must place exactly 2 cards, got {len(self.placements)}")

        # Verify placed cards and discarded card are from dealt cards
        placed_cards = {card for card, _ in self.placements}
        all_action_cards = placed_cards | {self.discarded_card}
        dealt_set = set(self.dealt_cards)

        if all_action_cards != dealt_set:
            raise ValueError("Placed and discarded cards must match dealt cards")

        # Verify no duplicate positions
        positions = [pos for _, pos in self.placements]
        if len(positions) != len(set(positions)):
            raise ValueError("Cannot place cards in the same position")

    @property
    def placed_cards(self) -> List[Card]:
        """Get the cards that were placed."""
        return [card for card, _ in self.placements]

    @property
    def placement_positions(self) -> List[Position]:
        """Get the positions where cards were placed."""
        return [pos for _, pos in self.placements]


@dataclass(frozen=True)
class InitialPlacement:
    """
    Represents the initial placement of 5 cards in street 0.
    """

    player_id: UUID
    placements: List[tuple[Card, Position]]  # 5 cards to place

    def __post_init__(self):
        """Validate the initial placement."""
        if len(self.placements) != 5:
            raise ValueError(
                f"Initial placement must have exactly 5 cards, got {len(self.placements)}"
            )

        # Verify no duplicate positions
        positions = [pos for _, pos in self.placements]
        if len(positions) != len(set(positions)):
            raise ValueError("Cannot place cards in the same position")

        # Verify no duplicate cards
        cards = [card for card, _ in self.placements]
        if len(cards) != len(set(cards)):
            raise ValueError("Cannot place the same card multiple times")
