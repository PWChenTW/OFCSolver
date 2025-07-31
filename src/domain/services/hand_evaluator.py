"""
Hand Evaluator Domain Service

Service for evaluating poker hand rankings and strengths
according to OFC rules and royalty calculations.
"""

from enum import Enum
from typing import List, Tuple

from ..base import DomainService
from ..value_objects import Card, HandRanking


class HandType(Enum):
    """Poker hand types in order of strength."""

    HIGH_CARD = (0, "High Card")
    PAIR = (1, "Pair")
    TWO_PAIR = (2, "Two Pair")
    THREE_OF_A_KIND = (3, "Three of a Kind")
    STRAIGHT = (4, "Straight")
    FLUSH = (5, "Flush")
    FULL_HOUSE = (6, "Full House")
    FOUR_OF_A_KIND = (7, "Four of a Kind")
    STRAIGHT_FLUSH = (8, "Straight Flush")
    ROYAL_FLUSH = (9, "Royal Flush")

    def __init__(self, value: int, display_name: str):
        self.value = value
        self.display_name = display_name

    def __lt__(self, other: "HandType") -> bool:
        return self.value < other.value


class HandEvaluator(DomainService):
    """
    Domain service for poker hand evaluation.

    Evaluates poker hands according to standard rules with
    OFC-specific considerations for royalties and hand comparisons.
    """

    def __init__(self):
        """Initialize hand evaluator."""
        pass

    def evaluate_hand(self, cards: List[Card]) -> HandRanking:
        """
        Evaluate poker hand strength.

        Args:
            cards: List of cards to evaluate

        Returns:
            HandRanking with type, strength, and royalty info

        Raises:
            ValueError: If invalid number of cards
        """
        if len(cards) < 3 or len(cards) > 5:
            raise ValueError(f"Hand must have 3-5 cards, got {len(cards)}")

        # Determine hand type and strength
        hand_type, strength_value, kickers = self._analyze_hand(cards)

        # Calculate royalty bonus
        royalty_bonus = self._calculate_royalty_bonus(cards, hand_type)

        return HandRanking(
            hand_type=hand_type,
            strength_value=strength_value,
            kickers=kickers,
            royalty_bonus=royalty_bonus,
            cards=cards.copy(),
        )

    def compare_hands(self, hand1: HandRanking, hand2: HandRanking) -> int:
        """
        Compare two hands.

        Args:
            hand1: First hand to compare
            hand2: Second hand to compare

        Returns:
            1 if hand1 wins, -1 if hand2 wins, 0 if tie
        """
        # Compare hand types first
        if hand1.hand_type.value != hand2.hand_type.value:
            return 1 if hand1.hand_type.value > hand2.hand_type.value else -1

        # Compare strength values for same hand type
        if hand1.strength_value != hand2.strength_value:
            return 1 if hand1.strength_value > hand2.strength_value else -1

        # Compare kickers
        for k1, k2 in zip(hand1.kickers, hand2.kickers):
            if k1 != k2:
                return 1 if k1 > k2 else -1

        return 0  # Tie

    def validate_ofc_progression(
        self, top_cards: List[Card], middle_cards: List[Card], bottom_cards: List[Card]
    ) -> bool:
        """
        Validate OFC hand progression (bottom > middle > top).

        Args:
            top_cards: Top row cards (3 cards)
            middle_cards: Middle row cards (5 cards)
            bottom_cards: Bottom row cards (5 cards)

        Returns:
            True if progression is valid, False if fouled
        """
        if len(top_cards) != 3 or len(middle_cards) != 5 or len(bottom_cards) != 5:
            return False

        # Evaluate each hand
        top_hand = self.evaluate_hand(top_cards)
        middle_hand = self.evaluate_hand(middle_cards)
        bottom_hand = self.evaluate_hand(bottom_cards)

        # Check progression: bottom > middle > top
        bottom_beats_middle = self.compare_hands(bottom_hand, middle_hand) > 0
        middle_beats_top = self.compare_hands(middle_hand, top_hand) > 0

        return bottom_beats_middle and middle_beats_top

    def _analyze_hand(self, cards: List[Card]) -> Tuple[HandType, int, List[int]]:
        """
        Analyze hand to determine type, strength, and kickers.

        Returns:
            Tuple of (hand_type, strength_value, kickers)
        """
        # Sort cards by rank (descending)
        sorted_cards = sorted(cards, key=lambda c: c.rank.value, reverse=True)
        ranks = [card.rank.value for card in sorted_cards]
        suits = [card.suit for card in sorted_cards]

        # Count rank frequencies
        rank_counts = {}
        for rank in ranks:
            rank_counts[rank] = rank_counts.get(rank, 0) + 1

        # Sort by count then rank
        count_groups = sorted(
            rank_counts.items(), key=lambda x: (x[1], x[0]), reverse=True
        )

        # Check for flush
        is_flush = len(set(suits)) == 1 and len(cards) == 5

        # Check for straight
        is_straight, straight_high = self._check_straight(ranks)

        # Determine hand type
        if is_straight and is_flush:
            if straight_high == 14:  # Ace high straight
                return HandType.ROYAL_FLUSH, 14, []
            else:
                return HandType.STRAIGHT_FLUSH, straight_high, []

        elif count_groups[0][1] == 4:  # Four of a kind
            quad_rank = count_groups[0][0]
            kicker = count_groups[1][0]
            return HandType.FOUR_OF_A_KIND, quad_rank, [kicker]

        elif count_groups[0][1] == 3 and count_groups[1][1] == 2:  # Full house
            trips_rank = count_groups[0][0]
            pair_rank = count_groups[1][0]
            return HandType.FULL_HOUSE, trips_rank, [pair_rank]

        elif is_flush:
            return HandType.FLUSH, ranks[0], ranks[1:]

        elif is_straight:
            return HandType.STRAIGHT, straight_high, []

        elif count_groups[0][1] == 3:  # Three of a kind
            trips_rank = count_groups[0][0]
            kickers = [rank for rank, count in count_groups[1:]]
            return HandType.THREE_OF_A_KIND, trips_rank, kickers

        elif count_groups[0][1] == 2 and count_groups[1][1] == 2:  # Two pair
            high_pair = max(count_groups[0][0], count_groups[1][0])
            low_pair = min(count_groups[0][0], count_groups[1][0])
            kicker = count_groups[2][0]
            return HandType.TWO_PAIR, high_pair, [low_pair, kicker]

        elif count_groups[0][1] == 2:  # Pair
            pair_rank = count_groups[0][0]
            kickers = [rank for rank, count in count_groups[1:]]
            return HandType.PAIR, pair_rank, kickers

        else:  # High card
            return HandType.HIGH_CARD, ranks[0], ranks[1:]

    def _check_straight(self, ranks: List[int]) -> Tuple[bool, int]:
        """
        Check if ranks form a straight.

        Returns:
            Tuple of (is_straight, high_card_rank)
        """
        if len(ranks) != 5:
            return False, 0

        # Sort ranks
        sorted_ranks = sorted(set(ranks))

        # Check for regular straight
        if len(sorted_ranks) == 5:
            if sorted_ranks[-1] - sorted_ranks[0] == 4:
                return True, sorted_ranks[-1]

        # Check for A-2-3-4-5 straight (wheel)
        if sorted_ranks == [2, 3, 4, 5, 14]:
            return True, 5  # 5 is high in wheel

        return False, 0

    def _calculate_royalty_bonus(self, cards: List[Card], hand_type: HandType) -> int:
        """
        Calculate OFC royalty bonus for hand.

        Args:
            cards: Cards in hand
            hand_type: Evaluated hand type

        Returns:
            Royalty bonus points
        """
        row_size = len(cards)

        if row_size == 3:  # Top row
            return self._calculate_top_row_royalties(cards, hand_type)
        elif row_size == 5:  # Middle/Bottom row
            return self._calculate_bottom_middle_royalties(cards, hand_type)

        return 0

    def _calculate_top_row_royalties(
        self, cards: List[Card], hand_type: HandType
    ) -> int:
        """Calculate top row (3-card) royalty bonuses."""
        if hand_type == HandType.THREE_OF_A_KIND:
            return 10
        elif hand_type == HandType.PAIR:
            pair_rank = max(
                card.rank.value
                for card in cards
                if sum(1 for c in cards if c.rank == card.rank) == 2
            )
            # Sixes or better get royalties
            if pair_rank >= 6:
                return pair_rank - 5
        return 0

    def _calculate_bottom_middle_royalties(
        self, cards: List[Card], hand_type: HandType
    ) -> int:
        """Calculate middle/bottom row (5-card) royalty bonuses."""
        royalty_table = {
            HandType.STRAIGHT: 2,
            HandType.FLUSH: 4,
            HandType.FULL_HOUSE: 6,
            HandType.FOUR_OF_A_KIND: 10,
            HandType.STRAIGHT_FLUSH: 15,
            HandType.ROYAL_FLUSH: 25,
        }
        return royalty_table.get(hand_type, 0)
