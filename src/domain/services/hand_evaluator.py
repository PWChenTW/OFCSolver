"""
Hand Evaluator Domain Service

Service for evaluating poker hand rankings and strengths
according to OFC rules and royalty calculations.
"""

from typing import Dict, List, Tuple
from functools import lru_cache

from ..base import DomainService
from ..value_objects import Card, HandRanking
from ..value_objects.hand_ranking import HandType


class HandEvaluator(DomainService):
    """
    Domain service for poker hand evaluation.

    Evaluates poker hands according to standard rules with
    OFC-specific considerations for royalties and hand comparisons.
    """

    def __init__(self):
        """Initialize hand evaluator."""
        self._evaluation_cache: Dict[str, HandRanking] = {}

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

        # Create cache key from sorted cards
        cache_key = self._create_cache_key(cards)

        # Check cache first
        if cache_key in self._evaluation_cache:
            cached_result = self._evaluation_cache[cache_key]
            # Return a copy with the original card order
            return HandRanking(
                hand_type=cached_result.hand_type,
                strength_value=cached_result.strength_value,
                kickers=cached_result.kickers,
                royalty_bonus=cached_result.royalty_bonus,
                cards=cards.copy(),
            )

        # Determine hand type and strength
        hand_type, strength_value, kickers = self._analyze_hand(cards)

        # Calculate royalty bonus
        royalty_bonus = self._calculate_royalty_bonus(cards, hand_type)

        result = HandRanking(
            hand_type=hand_type,
            strength_value=strength_value,
            kickers=kickers,
            royalty_bonus=royalty_bonus,
            cards=cards.copy(),
        )

        # Cache the result
        self._evaluation_cache[cache_key] = result

        return result

    def compare_hands(self, hand1: HandRanking, hand2: HandRanking) -> int:
        """
        Compare two hands.

        Args:
            hand1: First hand to compare
            hand2: Second hand to compare

        Returns:
            1 if hand1 wins, -1 if hand2 wins, 0 if tie
        """
        return hand1.compare_to(hand2)

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

        # Check progression: bottom > middle > top (strict ordering, no equal hands)
        bottom_beats_middle = self.compare_hands(bottom_hand, middle_hand) > 0
        middle_beats_top = self.compare_hands(middle_hand, top_hand) > 0

        return bottom_beats_middle and middle_beats_top

    def is_fouled_hand(
        self, top_cards: List[Card], middle_cards: List[Card], bottom_cards: List[Card]
    ) -> bool:
        """
        Check if an OFC hand is fouled.

        A hand is fouled if the rows don't follow proper strength progression:
        bottom > middle > top.

        Args:
            top_cards: Top row cards (3 cards)
            middle_cards: Middle row cards (5 cards)
            bottom_cards: Bottom row cards (5 cards)

        Returns:
            True if hand is fouled, False if valid
        """
        return not self.validate_ofc_progression(top_cards, middle_cards, bottom_cards)

    def _analyze_hand(self, cards: List[Card]) -> Tuple[HandType, int, List[int]]:
        """
        Analyze hand to determine type, strength, and kickers.

        Returns:
            Tuple of (hand_type, strength_value, kickers)
        """
        # Sort cards by rank (descending)
        sorted_cards = sorted(cards, key=lambda c: c.rank.numeric_value, reverse=True)
        ranks = [card.rank.numeric_value for card in sorted_cards]
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

        elif (count_groups[0][1] == 3 and len(count_groups) > 1 and
              count_groups[1][1] == 2):  # Full house
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

        elif (count_groups[0][1] == 2 and len(count_groups) > 1 and
              count_groups[1][1] == 2):  # Two pair
            high_pair = max(count_groups[0][0], count_groups[1][0])
            low_pair = min(count_groups[0][0], count_groups[1][0])
            kicker = count_groups[2][0] if len(count_groups) > 2 else 0
            kickers = [low_pair, kicker] if kicker else [low_pair]
            return HandType.TWO_PAIR, high_pair, kickers

        elif count_groups[0][1] == 2:  # Pair
            pair_rank = count_groups[0][0]
            kickers = [rank for rank, count in count_groups[1:]]
            return HandType.PAIR, pair_rank, kickers

        else:  # High card
            return HandType.HIGH_CARD, ranks[0], ranks[1:]

    @staticmethod
    @lru_cache(maxsize=1024)
    def _check_straight_cached(ranks_tuple: Tuple[int, ...]) -> Tuple[bool, int]:
        """
        Check if ranks form a straight (cached version).

        Returns:
            Tuple of (is_straight, high_card_rank)
        """
        if len(ranks_tuple) != 5:
            return False, 0

        # Sort ranks
        sorted_ranks = sorted(set(ranks_tuple))

        # Check for regular straight
        if len(sorted_ranks) == 5:
            if sorted_ranks[-1] - sorted_ranks[0] == 4:
                return True, sorted_ranks[-1]

        # Check for A-2-3-4-5 straight (wheel)
        if sorted_ranks == [2, 3, 4, 5, 14]:
            return True, 5  # 5 is high in wheel

        return False, 0

    def _check_straight(self, ranks: List[int]) -> Tuple[bool, int]:
        """
        Check if ranks form a straight.

        Returns:
            Tuple of (is_straight, high_card_rank)
        """
        # Convert to tuple for caching
        return self._check_straight_cached(tuple(ranks))

    def _create_cache_key(self, cards: List[Card]) -> str:
        """
        Create a cache key from cards.

        Cards are sorted to ensure same hands produce same keys.
        """
        sorted_cards = sorted(
            cards, key=lambda c: (c.rank.numeric_value, c.suit.value)
        )
        return ''.join(str(card) for card in sorted_cards)

    def clear_cache(self) -> None:
        """Clear the evaluation cache."""
        self._evaluation_cache.clear()

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
                card.rank.numeric_value
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
            HandType.STRAIGHT.value: 2,
            HandType.FLUSH.value: 4,
            HandType.FULL_HOUSE.value: 6,
            HandType.FOUR_OF_A_KIND.value: 10,
            HandType.STRAIGHT_FLUSH.value: 15,
            HandType.ROYAL_FLUSH.value: 25,
        }
        return royalty_table.get(hand_type.value, 0)
