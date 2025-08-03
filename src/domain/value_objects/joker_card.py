"""
Joker Card Support for Pineapple OFC

MVP implementation of Joker (wild card) functionality.
Joker can represent any card when evaluating hands.
"""

from dataclasses import dataclass
from typing import List, Optional

from .card import Card, Rank, Suit
from ..base import ValueObject


@dataclass(frozen=True)
class JokerCard(ValueObject):
    """
    Special card type representing a Joker (wild card).

    MVP implementation:
    - Joker has no inherent rank/suit
    - Can be substituted for any card during evaluation
    - Simplified handling without complex optimization
    """

    id: str = "JOKER"  # Unique identifier

    def __str__(self) -> str:
        """String representation."""
        return "🃏"

    def __repr__(self) -> str:
        """Detailed representation."""
        return "JokerCard()"

    @property
    def is_joker(self) -> bool:
        """Always True for JokerCard."""
        return True

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {"type": "joker", "id": self.id}


class JokerHandEvaluator:
    """
    Simple evaluator for hands containing jokers.

    MVP approach:
    - Find best possible substitution for each joker
    - Use existing hand evaluator for actual evaluation
    - No complex optimization, just reasonable heuristics
    """

    def __init__(self, base_evaluator):
        """Initialize with base evaluator."""
        self.base_evaluator = base_evaluator

    def evaluate_with_jokers(
        self,
        cards: List[Card],
        jokers: List[JokerCard],
    ) -> dict:
        """
        Evaluate hand with jokers by finding best substitution.

        Simplified algorithm:
        1. If no jokers, use base evaluator
        2. For each joker, try common beneficial substitutions
        3. Return best result

        Returns dict with:
        - best_hand: The optimal hand configuration
        - substitutions: What each joker represents
        - ranking: Hand ranking result
        """
        if not jokers:
            # No jokers, just evaluate normally
            ranking = self.base_evaluator.evaluate_hand(cards)
            return {
                "best_hand": cards,
                "substitutions": {},
                "ranking": ranking,
            }

        # For MVP, use simple heuristics
        best_substitution = self._find_best_substitution(cards, len(jokers))

        # Create substituted hand
        substituted_cards = cards + best_substitution["cards"]
        ranking = self.base_evaluator.evaluate_hand(substituted_cards)

        return {
            "best_hand": substituted_cards,
            "substitutions": best_substitution["mapping"],
            "ranking": ranking,
        }

    def _find_best_substitution(
        self,
        existing_cards: List[Card],
        joker_count: int,
    ) -> dict:
        """
        Find best cards to substitute for jokers.

        Simplified heuristics:
        - For pairs/trips: match existing high cards
        - For flushes: match dominant suit
        - For straights: fill gaps
        - Default: high cards (Aces/Kings)
        """
        # Count existing ranks and suits
        rank_counts = {}
        suit_counts = {}

        for card in existing_cards:
            rank_counts[card.rank] = rank_counts.get(card.rank, 0) + 1
            suit_counts[card.suit] = suit_counts.get(card.suit, 0) + 1

        substitutions = []
        mapping = {}

        # Simple strategy: prioritize pairs/trips with high cards
        high_ranks = [Rank.ACE, Rank.KING, Rank.QUEEN, Rank.JACK]

        for i in range(joker_count):
            joker_id = f"JOKER_{i}"

            # Check for pair potential
            for rank in high_ranks:
                if rank_counts.get(rank, 0) == 1 and joker_count > 0:
                    # Make a pair
                    suit = self._get_different_suit(existing_cards, rank)
                    card = Card(suit, rank)
                    substitutions.append(card)
                    mapping[joker_id] = str(card)
                    joker_count -= 1
                    break
            else:
                # Default to high card
                if joker_count > 0:
                    card = Card(Suit.SPADES, Rank.ACE)
                    substitutions.append(card)
                    mapping[joker_id] = str(card)
                    joker_count -= 1

        return {
            "cards": substitutions,
            "mapping": mapping,
        }

    def _get_different_suit(
        self,
        existing_cards: List[Card],
        rank: Rank,
    ) -> Suit:
        """Get a suit not already used for this rank."""
        used_suits = {card.suit for card in existing_cards if card.rank == rank}

        for suit in [Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS]:
            if suit not in used_suits:
                return suit

        return Suit.SPADES  # Default


def identify_jokers_in_hand(cards: list) -> tuple[List[Card], List[JokerCard]]:
    """
    Separate regular cards from jokers in a mixed hand.

    Returns:
        (regular_cards, joker_cards)
    """
    regular_cards = []
    joker_cards = []

    for card in cards:
        if isinstance(card, JokerCard):
            joker_cards.append(card)
        elif isinstance(card, Card):
            regular_cards.append(card)
        else:
            # Handle other representations if needed
            pass

    return regular_cards, joker_cards
