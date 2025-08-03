"""
Card Value Object

Represents an immutable playing card with suit and rank.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List

from ..base import ValueObject


class Suit(Enum):
    """Playing card suits."""

    SPADES = "s"
    HEARTS = "h"
    DIAMONDS = "d"
    CLUBS = "c"

    def __str__(self) -> str:
        return self.value

    @property
    def symbol(self) -> str:
        """Get Unicode symbol for suit."""
        symbols = {
            Suit.SPADES: "♠",
            Suit.HEARTS: "♥",
            Suit.DIAMONDS: "♦",
            Suit.CLUBS: "♣",
        }
        return symbols[self]

    @property
    def is_red(self) -> bool:
        """Check if suit is red."""
        return self in (Suit.HEARTS, Suit.DIAMONDS)

    @property
    def is_black(self) -> bool:
        """Check if suit is black."""
        return self in (Suit.SPADES, Suit.CLUBS)


class Rank(Enum):
    """Playing card ranks."""

    TWO = (2, "2")
    THREE = (3, "3")
    FOUR = (4, "4")
    FIVE = (5, "5")
    SIX = (6, "6")
    SEVEN = (7, "7")
    EIGHT = (8, "8")
    NINE = (9, "9")
    TEN = (10, "T")
    JACK = (11, "J")
    QUEEN = (12, "Q")
    KING = (13, "K")
    ACE = (14, "A")

    def __init__(self, numeric_value: int, symbol: str) -> None:
        self.numeric_value = numeric_value
        self.symbol = symbol

    def __str__(self) -> str:
        return self.symbol

    def __lt__(self, other: "Rank") -> bool:
        return self.numeric_value < other.numeric_value

    def __le__(self, other: "Rank") -> bool:
        return self.numeric_value <= other.numeric_value

    def __gt__(self, other: "Rank") -> bool:
        return self.numeric_value > other.numeric_value

    def __ge__(self, other: "Rank") -> bool:
        return self.numeric_value >= other.numeric_value

    @classmethod
    def from_symbol(cls, symbol: str) -> "Rank":
        """Get rank from symbol string."""
        for rank in cls:
            if rank.symbol == symbol.upper():
                return rank
        raise ValueError(f"Invalid rank symbol: {symbol}")

    @classmethod
    def all_ranks(cls) -> List["Rank"]:
        """Get all ranks in order."""
        return sorted(cls, key=lambda r: r.numeric_value)


@dataclass(frozen=True)
class Card(ValueObject):
    """
    Immutable playing card value object.

    Represents a single playing card with suit and rank.
    """

    suit: Suit
    rank: Rank

    def __post_init__(self):
        """Validate card creation parameters."""
        if not isinstance(self.suit, Suit):
            raise TypeError(f"suit must be a Suit enum, got {type(self.suit)}")
        if not isinstance(self.rank, Rank):
            raise TypeError(f"rank must be a Rank enum, got {type(self.rank)}")

    def __str__(self) -> str:
        """String representation (e.g., 'As', 'Kh', '2c')."""
        return f"{self.rank.symbol}{self.suit.value}"

    def __repr__(self) -> str:
        """Detailed representation."""
        return f"Card({self.rank.name}, {self.suit.name})"

    def __lt__(self, other: "Card") -> bool:
        """Less than comparison - compare by rank first, then suit."""
        if self.rank != other.rank:
            return self.rank < other.rank
        # For same rank, compare by suit (spades > hearts > diamonds > clubs)
        suit_order = {Suit.CLUBS: 1, Suit.DIAMONDS: 2, Suit.HEARTS: 3, Suit.SPADES: 4}
        return suit_order[self.suit] < suit_order[other.suit]

    def __le__(self, other: "Card") -> bool:
        """Less than or equal comparison."""
        return self < other or self == other

    def __gt__(self, other: "Card") -> bool:
        """Greater than comparison."""
        return not self <= other

    def __ge__(self, other: "Card") -> bool:
        """Greater than or equal comparison."""
        return not self < other

    @classmethod
    def from_string(cls, card_str: str) -> "Card":
        """
        Create card from string representation.

        Args:
            card_str: String like 'As', 'Kh', '2c'

        Returns:
            Card instance

        Raises:
            ValueError: If string format is invalid
        """
        if len(card_str) != 2:
            raise ValueError(f"Card string must be 2 characters, got: {card_str}")

        rank_symbol, suit_symbol = card_str[0], card_str[1].lower()

        try:
            rank = Rank.from_symbol(rank_symbol)
        except ValueError:
            raise ValueError(f"Invalid rank symbol: {rank_symbol}")

        try:
            suit = Suit(suit_symbol)
        except ValueError:
            raise ValueError(f"Invalid suit symbol: {suit_symbol}")

        return cls(suit=suit, rank=rank)

    @property
    def is_face_card(self) -> bool:
        """Check if card is a face card (J, Q, K)."""
        return self.rank in (Rank.JACK, Rank.QUEEN, Rank.KING)

    @property
    def is_ace(self) -> bool:
        """Check if card is an ace."""
        return self.rank == Rank.ACE

    @property
    def is_red(self) -> bool:
        """Check if card is red."""
        return self.suit.is_red

    @property
    def is_black(self) -> bool:
        """Check if card is black."""
        return self.suit.is_black

    @property
    def numeric_rank(self) -> int:
        """Get numeric rank value."""
        return self.rank.numeric_value

    def is_consecutive(self, other: "Card") -> bool:
        """Check if this card is consecutive with another."""
        return abs(self.rank.numeric_value - other.rank.numeric_value) == 1

    def is_same_suit(self, other: "Card") -> bool:
        """Check if this card has same suit as another."""
        return self.suit == other.suit

    def is_same_rank(self, other: "Card") -> bool:
        """Check if this card has same rank as another."""
        return self.rank == other.rank

    @staticmethod
    def create_deck() -> List["Card"]:
        """Create a full 52-card deck."""
        deck = []
        for suit in Suit:
            for rank in Rank:
                deck.append(Card(suit=suit, rank=rank))
        return deck

    @staticmethod
    def parse_cards(cards_str: str) -> List["Card"]:
        """
        Parse multiple cards from string.

        Args:
            cards_str: Space-separated card strings like 'As Kh 2c'

        Returns:
            List of Card instances
        """
        if not cards_str.strip():
            return []
        card_strings = cards_str.strip().split()
        return [Card.from_string(card_str) for card_str in card_strings]

    @staticmethod
    def cards_to_string(cards: List["Card"]) -> str:
        """Convert list of cards to string representation."""
        return " ".join(str(card) for card in cards)

    @staticmethod
    def group_by_suit(cards: List["Card"]) -> dict[Suit, List["Card"]]:
        """Group cards by suit."""
        groups = {suit: [] for suit in Suit}
        for card in cards:
            groups[card.suit].append(card)
        return groups

    @staticmethod
    def group_by_rank(cards: List["Card"]) -> dict[Rank, List["Card"]]:
        """Group cards by rank."""
        groups = {}
        for card in cards:
            if card.rank not in groups:
                groups[card.rank] = []
            groups[card.rank].append(card)
        return groups

    @staticmethod
    def sort_by_rank(cards: List["Card"], descending: bool = True) -> List["Card"]:
        """Sort cards by rank."""
        return sorted(cards, key=lambda c: c.rank.numeric_value, reverse=descending)

    @staticmethod
    def sort_by_suit(cards: List["Card"]) -> List["Card"]:
        """Sort cards by suit."""
        suit_order = {Suit.CLUBS: 1, Suit.DIAMONDS: 2, Suit.HEARTS: 3, Suit.SPADES: 4}
        return sorted(cards, key=lambda c: (suit_order[c.suit], c.rank.numeric_value))

    @staticmethod
    def validate_no_duplicates(cards: List["Card"]) -> bool:
        """Validate that there are no duplicate cards."""
        return len(cards) == len(set(cards))

    @staticmethod
    def get_missing_cards(cards: List["Card"]) -> List["Card"]:
        """Get cards missing from a full deck."""
        full_deck = set(Card.create_deck())
        provided_cards = set(cards)
        return list(full_deck - provided_cards)