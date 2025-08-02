"""
Hand Ranking Value Object

Represents the evaluated strength and type of a poker hand
along with OFC-specific royalty bonuses.
"""

from dataclasses import dataclass
from typing import List

from ..base import ValueObject
from .card import Card


class HandType:
    """Poker hand types in order of strength."""

    def __init__(self, value: int, display_name: str):
        self.value = value
        self.display_name = display_name

    def __lt__(self, other: "HandType") -> bool:
        return self.value < other.value

    def __le__(self, other: "HandType") -> bool:
        return self.value <= other.value

    def __gt__(self, other: "HandType") -> bool:
        return self.value > other.value

    def __ge__(self, other: "HandType") -> bool:
        return self.value >= other.value

    def __eq__(self, other: "HandType") -> bool:
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)

    def __str__(self) -> str:
        return self.display_name

    def __repr__(self) -> str:
        return f"HandType({self.value}, '{self.display_name}')"


# Pre-defined hand types for convenient access
HandType.HIGH_CARD = HandType(0, "High Card")
HandType.PAIR = HandType(1, "Pair")
HandType.TWO_PAIR = HandType(2, "Two Pair")
HandType.THREE_OF_A_KIND = HandType(3, "Three of a Kind")
HandType.STRAIGHT = HandType(4, "Straight")
HandType.FLUSH = HandType(5, "Flush")
HandType.FULL_HOUSE = HandType(6, "Full House")
HandType.FOUR_OF_A_KIND = HandType(7, "Four of a Kind")
HandType.STRAIGHT_FLUSH = HandType(8, "Straight Flush")
HandType.ROYAL_FLUSH = HandType(9, "Royal Flush")


@dataclass(frozen=True)
class HandRanking(ValueObject):
    """
    Hand ranking value object containing poker hand evaluation results.

    Represents the complete evaluation of a poker hand including:
    - Hand type (pair, flush, etc.)
    - Strength value for comparison within same type
    - Kicker cards for tie-breaking
    - OFC royalty bonus points
    - Original cards that formed the hand
    """

    hand_type: HandType
    strength_value: int
    kickers: List[int]
    royalty_bonus: int
    cards: List[Card]

    def __post_init__(self):
        """Validate hand ranking data."""
        if not isinstance(self.hand_type, HandType):
            raise TypeError("hand_type must be a HandType instance")

        if self.strength_value < 0:
            raise ValueError("strength_value must be non-negative")

        if self.royalty_bonus < 0:
            raise ValueError("royalty_bonus must be non-negative")

        if not self.cards:
            raise ValueError("cards list cannot be empty")

        if len(self.cards) < 3 or len(self.cards) > 5:
            raise ValueError(f"Hand must have 3-5 cards, got {len(self.cards)}")

    @property
    def is_made_hand(self) -> bool:
        """Check if this is a made hand (pair or better)."""
        return self.hand_type.value >= HandType.PAIR.value

    @property
    def is_premium_hand(self) -> bool:
        """Check if this is a premium hand (three of a kind or better)."""
        return self.hand_type.value >= HandType.THREE_OF_A_KIND.value

    @property
    def is_monster_hand(self) -> bool:
        """Check if this is a monster hand (straight or better)."""
        return self.hand_type.value >= HandType.STRAIGHT.value

    @property
    def has_royalty(self) -> bool:
        """Check if hand qualifies for royalty bonus."""
        return self.royalty_bonus > 0

    @property
    def total_value(self) -> int:
        """Get total value including royalty bonus."""
        return self.strength_value + self.royalty_bonus

    def compare_to(self, other: "HandRanking") -> int:
        """
        Compare this hand ranking to another.

        Args:
            other: Another HandRanking to compare against

        Returns:
            1 if this hand wins, -1 if other wins, 0 if tie
        """
        # Compare hand types first
        if self.hand_type.value != other.hand_type.value:
            return 1 if self.hand_type.value > other.hand_type.value else -1

        # Compare strength values for same hand type
        if self.strength_value != other.strength_value:
            return 1 if self.strength_value > other.strength_value else -1

        # Compare kickers
        for k1, k2 in zip(self.kickers, other.kickers):
            if k1 != k2:
                return 1 if k1 > k2 else -1

        return 0  # Tie

    def beats(self, other: "HandRanking") -> bool:
        """Check if this hand beats another hand."""
        return self.compare_to(other) > 0

    def loses_to(self, other: "HandRanking") -> bool:
        """Check if this hand loses to another hand."""
        return self.compare_to(other) < 0

    def ties_with(self, other: "HandRanking") -> bool:
        """Check if this hand ties with another hand."""
        return self.compare_to(other) == 0

    def get_hand_description(self) -> str:
        """Get a human-readable description of the hand."""
        if self.hand_type == HandType.HIGH_CARD:
            high_card = max(card.rank for card in self.cards)
            return f"{high_card} High"

        elif self.hand_type == HandType.PAIR:
            pair_rank = None
            rank_counts = {}
            for card in self.cards:
                rank_counts[card.rank] = rank_counts.get(card.rank, 0) + 1

            for rank, count in rank_counts.items():
                if count == 2:
                    pair_rank = rank
                    break

            return f"Pair of {pair_rank}s" if pair_rank else "Pair"

        elif self.hand_type == HandType.TWO_PAIR:
            pairs = []
            rank_counts = {}
            for card in self.cards:
                rank_counts[card.rank] = rank_counts.get(card.rank, 0) + 1

            for rank, count in rank_counts.items():
                if count == 2:
                    pairs.append(rank)

            if len(pairs) == 2:
                pairs.sort(key=lambda r: r.numeric_value, reverse=True)
                return f"{pairs[0]}s and {pairs[1]}s"
            return "Two Pair"

        elif self.hand_type == HandType.THREE_OF_A_KIND:
            trips_rank = None
            rank_counts = {}
            for card in self.cards:
                rank_counts[card.rank] = rank_counts.get(card.rank, 0) + 1

            for rank, count in rank_counts.items():
                if count == 3:
                    trips_rank = rank
                    break

            return f"Three {trips_rank}s" if trips_rank else "Three of a Kind"

        elif self.hand_type == HandType.STRAIGHT:
            high_card = max(card.rank for card in self.cards)
            if high_card.numeric_value == 5:  # Wheel straight
                return "Straight (5 High)"
            return f"Straight ({high_card} High)"

        elif self.hand_type == HandType.FLUSH:
            suit = self.cards[0].suit
            high_card = max(card.rank for card in self.cards)
            return f"{suit.symbol} Flush ({high_card} High)"

        elif self.hand_type == HandType.FULL_HOUSE:
            trips_rank = None
            pair_rank = None
            rank_counts = {}
            for card in self.cards:
                rank_counts[card.rank] = rank_counts.get(card.rank, 0) + 1

            for rank, count in rank_counts.items():
                if count == 3:
                    trips_rank = rank
                elif count == 2:
                    pair_rank = rank

            if trips_rank and pair_rank:
                return f"{trips_rank}s full of {pair_rank}s"
            return "Full House"

        elif self.hand_type == HandType.FOUR_OF_A_KIND:
            quads_rank = None
            rank_counts = {}
            for card in self.cards:
                rank_counts[card.rank] = rank_counts.get(card.rank, 0) + 1

            for rank, count in rank_counts.items():
                if count == 4:
                    quads_rank = rank
                    break

            return f"Four {quads_rank}s" if quads_rank else "Four of a Kind"

        elif self.hand_type == HandType.STRAIGHT_FLUSH:
            high_card = max(card.rank for card in self.cards)
            suit = self.cards[0].suit
            if high_card.numeric_value == 5:  # Wheel straight flush
                return f"{suit.symbol} Straight Flush (5 High)"
            return f"{suit.symbol} Straight Flush ({high_card} High)"

        elif self.hand_type == HandType.ROYAL_FLUSH:
            suit = self.cards[0].suit
            return f"{suit.symbol} Royal Flush"

        return str(self.hand_type)

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "hand_type": {
                "value": self.hand_type.value,
                "name": self.hand_type.display_name,
            },
            "strength_value": self.strength_value,
            "kickers": self.kickers,
            "royalty_bonus": self.royalty_bonus,
            "total_value": self.total_value,
            "cards": [str(card) for card in self.cards],
            "description": self.get_hand_description(),
            "has_royalty": self.has_royalty,
            "is_made_hand": self.is_made_hand,
            "is_premium_hand": self.is_premium_hand,
            "is_monster_hand": self.is_monster_hand,
        }

    def __str__(self) -> str:
        """String representation for display."""
        royalty_str = f" (+{self.royalty_bonus} royalty)" if self.has_royalty else ""
        return f"{self.get_hand_description()}{royalty_str}"

    def __lt__(self, other: "HandRanking") -> bool:
        """Less than comparison."""
        return self.compare_to(other) < 0

    def __le__(self, other: "HandRanking") -> bool:
        """Less than or equal comparison."""
        return self.compare_to(other) <= 0

    def __gt__(self, other: "HandRanking") -> bool:
        """Greater than comparison."""
        return self.compare_to(other) > 0

    def __ge__(self, other: "HandRanking") -> bool:
        """Greater than or equal comparison."""
        return self.compare_to(other) >= 0
