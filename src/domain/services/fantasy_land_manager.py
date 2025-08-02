"""
Fantasy Land Manager Domain Service

Service for managing Fantasy Land rules and qualifications in OFC.
Fantasy Land is a special state where a player receives all cards at
once and can set them optimally.
"""

from typing import List, Optional

from ..base import DomainService
from ..value_objects import Card, HandRanking
from ..value_objects.hand_ranking import HandType


class FantasyLandManager(DomainService):
    """
    Domain service for Fantasy Land management.

    Fantasy Land is a special OFC state earned by achieving certain hands:
    - Top row: QQ or better
    - Middle row: Three of a kind or better
    - Bottom row: Straight or better

    In Fantasy Land, players receive all remaining cards at once.
    """

    def __init__(self) -> None:
        """Initialize Fantasy Land manager."""
        pass

    def qualifies_for_fantasy_land(
        self,
        top_hand: Optional[HandRanking] = None,
        middle_hand: Optional[HandRanking] = None,
        bottom_hand: Optional[HandRanking] = None,
    ) -> bool:
        """
        Check if hand qualifies for Fantasy Land.

        Args:
            top_hand: Evaluated top row hand
            middle_hand: Evaluated middle row hand
            bottom_hand: Evaluated bottom row hand

        Returns:
            True if any row qualifies for Fantasy Land
        """
        # Check top row (QQ or better)
        if top_hand and self._qualifies_top_row(top_hand):
            return True

        # Check middle row (Three of a kind or better)
        if middle_hand and self._qualifies_middle_row(middle_hand):
            return True

        # Check bottom row (Straight or better)
        if bottom_hand and self._qualifies_bottom_row(bottom_hand):
            return True

        return False

    def can_stay_in_fantasy_land(
        self,
        top_hand: Optional[HandRanking] = None,
        middle_hand: Optional[HandRanking] = None,
        bottom_hand: Optional[HandRanking] = None,
    ) -> bool:
        """
        Check if player can stay in Fantasy Land for another round.

        Staying requires stronger hands than initial qualification:
        - Top row: Three of a kind
        - Middle row: Full house or better
        - Bottom row: Four of a kind or better

        Args:
            top_hand: Evaluated top row hand
            middle_hand: Evaluated middle row hand
            bottom_hand: Evaluated bottom row hand

        Returns:
            True if any row qualifies to stay in Fantasy Land
        """
        # Check top row (Three of a kind)
        if top_hand and top_hand.hand_type == HandType.THREE_OF_A_KIND:
            return True

        # Check middle row (Full house or better)
        if middle_hand and middle_hand.hand_type.value >= HandType.FULL_HOUSE.value:
            return True

        # Check bottom row (Four of a kind or better)
        if bottom_hand and bottom_hand.hand_type.value >= HandType.FOUR_OF_A_KIND.value:
            return True

        return False

    def get_fantasy_land_card_count(self, variant: str = "standard") -> int:
        """
        Get number of cards dealt in Fantasy Land.

        Args:
            variant: OFC variant being played

        Returns:
            Number of cards to deal
        """
        # Standard OFC: 13 cards in Fantasy Land
        if variant == "standard":
            return 13
        # Pineapple OFC: 14 cards in Fantasy Land
        elif variant == "pineapple":
            return 14
        # 2-7 Pineapple: 14 cards
        elif variant == "2-7-pineapple":
            return 14
        else:
            return 13  # Default to standard

    def validate_fantasy_land_setting(
        self, cards: List[Card], variant: str = "standard"
    ) -> bool:
        """
        Validate that Fantasy Land card setting is legal.

        Args:
            cards: Cards being set in Fantasy Land
            variant: OFC variant being played

        Returns:
            True if setting is valid
        """
        expected_count = self.get_fantasy_land_card_count(variant)

        # Check correct number of cards
        if len(cards) != expected_count:
            return False

        # Check for duplicates
        if len(set(cards)) != len(cards):
            return False

        return True

    def _qualifies_top_row(self, hand: HandRanking) -> bool:
        """Check if top row qualifies for Fantasy Land (QQ+)."""
        if hand.hand_type != HandType.PAIR:
            # Three of a kind always qualifies
            return hand.hand_type == HandType.THREE_OF_A_KIND

        # For pairs, need QQ or better
        return hand.strength_value >= 12  # Q = 12

    def _qualifies_middle_row(self, hand: HandRanking) -> bool:
        """Check if middle row qualifies for Fantasy Land (trips+)."""
        return hand.hand_type.value >= HandType.THREE_OF_A_KIND.value

    def _qualifies_bottom_row(self, hand: HandRanking) -> bool:
        """Check if bottom row qualifies for Fantasy Land (straight+)."""
        return hand.hand_type.value >= HandType.STRAIGHT.value

    def get_qualification_requirements(self) -> dict:
        """Get Fantasy Land qualification requirements."""
        return {
            "initial_qualification": {
                "top": "QQ or better (pair of queens or higher)",
                "middle": "Three of a kind or better",
                "bottom": "Straight or better",
            },
            "stay_requirements": {
                "top": "Three of a kind",
                "middle": "Full house or better",
                "bottom": "Four of a kind or better",
            },
            "card_count": {
                "standard": 13,
                "pineapple": 14,
                "2-7-pineapple": 14,
            },
        }

    def calculate_fantasy_land_probability(
        self, cards_seen: List[Card], position: str = "top"
    ) -> float:
        """
        Calculate probability of making Fantasy Land from current position.

        Args:
            cards_seen: Cards already visible
            position: Which row to calculate for

        Returns:
            Probability between 0 and 1
        """
        # This is a simplified calculation
        # Full implementation would consider remaining cards and outs

        remaining_cards = 52 - len(cards_seen)

        if position == "top":
            # Rough estimate for QQ+ in 3 cards
            return min(0.15 * (remaining_cards / 40), 0.20)
        elif position == "middle":
            # Rough estimate for trips+ in 5 cards
            return min(0.10 * (remaining_cards / 40), 0.15)
        elif position == "bottom":
            # Rough estimate for straight+ in 5 cards
            return min(0.25 * (remaining_cards / 40), 0.35)
        else:
            return 0.0
