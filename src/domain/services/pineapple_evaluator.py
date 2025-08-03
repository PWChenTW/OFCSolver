"""
Pineapple OFC Hand Evaluator

Extends the base hand evaluator with Pineapple OFC specific royalty calculations.
"""

from typing import List

from .hand_evaluator import HandEvaluator
from ..value_objects import Card, HandRanking
from ..value_objects.hand_ranking import HandType


class PineappleHandEvaluator(HandEvaluator):
    """
    Hand evaluator specific to Pineapple OFC rules.

    Main differences from standard OFC:
    - Different royalty bonuses for middle row
    - Fantasy Land qualification at QQ+ (front row)
    """

    def _calculate_top_row_royalties(
        self, cards: List[Card], hand_type: HandType
    ) -> int:
        """
        Calculate top row (3-card) royalty bonuses for Pineapple OFC.

        Based on OFC_GAME_RULES.md:
        - 66: 1 point
        - 77: 2 points
        - ...
        - AA: 9 points
        - 222: 10 points
        - 333: 11 points
        - ...
        - AAA: 22 points
        """
        if hand_type == HandType.THREE_OF_A_KIND:
            # Get the rank of the trips
            rank_counts = {}
            for card in cards:
                rank = card.rank.numeric_value
                rank_counts[rank] = rank_counts.get(rank, 0) + 1

            trips_rank = max(rank for rank, count in rank_counts.items() if count == 3)
            # 222 = 10, 333 = 11, ..., AAA = 22
            return 10 + (trips_rank - 2)

        elif hand_type == HandType.PAIR:
            # Get the pair rank
            rank_counts = {}
            for card in cards:
                rank = card.rank.numeric_value
                rank_counts[rank] = rank_counts.get(rank, 0) + 1

            pair_rank = max(rank for rank, count in rank_counts.items() if count == 2)
            # Only 66+ get royalties in Pineapple
            if pair_rank >= 6:
                return pair_rank - 5  # 66=1, 77=2, ..., AA=9

        return 0

    def _calculate_bottom_middle_royalties(
        self, cards: List[Card], hand_type: HandType
    ) -> int:
        """
        Calculate middle/bottom row (5-card) royalty bonuses for Pineapple OFC.

        Middle row (higher bonuses than bottom):
        - Three of a kind: 2 points
        - Straight: 4 points
        - Flush: 8 points (vs 4 in standard)
        - Full house: 12 points (vs 6 in standard)
        - Four of a kind: 20 points (vs 10 in standard)
        - Straight flush: 30 points (vs 15 in standard)
        - Royal flush: 50 points (vs 25 in standard)

        Bottom row (standard bonuses):
        - Straight: 2 points
        - Flush: 4 points
        - Full house: 6 points
        - Four of a kind: 10 points
        - Straight flush: 15 points
        - Royal flush: 25 points
        """
        # Need to know if this is middle or bottom row
        # For now, we'll use a heuristic based on the context
        # In a real implementation, this would be passed as a parameter

        # Standard bottom row royalties (same as base class)
        bottom_royalties = {
            HandType.STRAIGHT.value: 2,
            HandType.FLUSH.value: 4,
            HandType.FULL_HOUSE.value: 6,
            HandType.FOUR_OF_A_KIND.value: 10,
            HandType.STRAIGHT_FLUSH.value: 15,
            HandType.ROYAL_FLUSH.value: 25,
        }

        # Enhanced middle row royalties for Pineapple
        middle_royalties = {
            HandType.THREE_OF_A_KIND.value: 2,
            HandType.STRAIGHT.value: 4,
            HandType.FLUSH.value: 8,
            HandType.FULL_HOUSE.value: 12,
            HandType.FOUR_OF_A_KIND.value: 20,
            HandType.STRAIGHT_FLUSH.value: 30,
            HandType.ROYAL_FLUSH.value: 50,
        }

        # For now, return bottom royalties as default
        # In actual implementation, we'd need row position context
        return bottom_royalties.get(hand_type.value, 0)

    def evaluate_hand_with_position(
        self, cards: List[Card], row_position: str
    ) -> HandRanking:
        """
        Evaluate hand with specific row position for accurate royalty calculation.

        Args:
            cards: List of cards to evaluate
            row_position: "top", "middle", or "bottom"

        Returns:
            HandRanking with position-specific royalty bonus
        """
        # First get base evaluation
        base_ranking = self.evaluate_hand(cards)

        # Calculate position-specific royalty
        if row_position == "top" and len(cards) == 3:
            royalty = self._calculate_top_row_royalties(cards, base_ranking.hand_type)
        elif row_position == "middle" and len(cards) == 5:
            royalty = self._calculate_middle_row_royalties_pineapple(
                cards, base_ranking.hand_type
            )
        elif row_position == "bottom" and len(cards) == 5:
            royalty = self._calculate_bottom_row_royalties_pineapple(
                cards, base_ranking.hand_type
            )
        else:
            royalty = 0

        # Return new ranking with correct royalty
        return HandRanking(
            hand_type=base_ranking.hand_type,
            strength_value=base_ranking.strength_value,
            kickers=base_ranking.kickers,
            royalty_bonus=royalty,
            cards=base_ranking.cards,
        )

    def _calculate_middle_row_royalties_pineapple(
        self, cards: List[Card], hand_type: HandType
    ) -> int:
        """Calculate middle row specific royalties for Pineapple."""
        middle_royalties = {
            HandType.THREE_OF_A_KIND.value: 2,
            HandType.STRAIGHT.value: 4,
            HandType.FLUSH.value: 8,
            HandType.FULL_HOUSE.value: 12,
            HandType.FOUR_OF_A_KIND.value: 20,
            HandType.STRAIGHT_FLUSH.value: 30,
            HandType.ROYAL_FLUSH.value: 50,
        }
        return middle_royalties.get(hand_type.value, 0)

    def _calculate_bottom_row_royalties_pineapple(
        self, cards: List[Card], hand_type: HandType
    ) -> int:
        """Calculate bottom row specific royalties for Pineapple."""
        bottom_royalties = {
            HandType.STRAIGHT.value: 2,
            HandType.FLUSH.value: 4,
            HandType.FULL_HOUSE.value: 6,
            HandType.FOUR_OF_A_KIND.value: 10,
            HandType.STRAIGHT_FLUSH.value: 15,
            HandType.ROYAL_FLUSH.value: 25,
        }
        return bottom_royalties.get(hand_type.value, 0)

    def is_fantasy_land_qualifying(self, top_cards: List[Card]) -> bool:
        """
        Check if top row qualifies for Fantasy Land in Pineapple OFC.

        In Pineapple: QQ+ or trips qualifies (easier than standard OFC's AA+)
        """
        if len(top_cards) != 3:
            return False

        top_hand = self.evaluate_hand(top_cards)

        # Trips always qualify
        if top_hand.hand_type == HandType.THREE_OF_A_KIND:
            return True

        # Check for QQ+
        if top_hand.hand_type == HandType.PAIR:
            # Get pair rank
            rank_counts = {}
            for card in top_cards:
                rank = card.rank.numeric_value
                rank_counts[rank] = rank_counts.get(rank, 0) + 1

            pair_rank = max(rank for rank, count in rank_counts.items() if count == 2)
            return pair_rank >= 12  # Q=12, K=13, A=14

        return False
