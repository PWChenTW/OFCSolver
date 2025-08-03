"""
Pineapple OFC Fantasy Land Manager

MVP implementation focusing on core Fantasy Land mechanics only.
Following YAGNI principle - only essential features.
"""

from typing import List, Optional, Tuple

from ..base import DomainService
from ..value_objects import Card
from ..value_objects.fantasy_land_state import FantasyLandState
from ..value_objects.hand_ranking import HandType
from .pineapple_evaluator import PineappleHandEvaluator


class PineappleFantasyLandManager(DomainService):
    """
    MVP Fantasy Land manager for Pineapple OFC.

    Core features only:
    - Entry: QQ+ in top row
    - Deal: 14 cards at once
    - Stay: Trips/FullHouse+/Quads+
    """

    def __init__(self, evaluator: Optional[PineappleHandEvaluator] = None):
        """Initialize with evaluator."""
        self.evaluator = evaluator or PineappleHandEvaluator()

    def check_entry_qualification(self, top_cards: List[Card]) -> bool:
        """
        Check if top row qualifies for Fantasy Land entry.

        Pineapple OFC: QQ+ in top row (simpler than standard).
        """
        if len(top_cards) != 3:
            return False

        return self.evaluator.is_fantasy_land_qualifying(top_cards)

    def check_stay_qualification(
        self,
        top_cards: List[Card],
        middle_cards: List[Card],
        bottom_cards: List[Card],
    ) -> bool:
        """
        Check if top row qualifies to stay in Fantasy Land.

        Pineapple OFC: Same as entry - QQ+ in top row.
        """
        # Only check top row for QQ+
        return self.check_entry_qualification(top_cards)

    def validate_fantasy_placement(
        self,
        placed_cards: List[Card],
        dealt_cards: List[Card],
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate Fantasy Land card placement (MVP version).

        Checks:
        - 13 cards placed from 14 dealt
        - All placed cards from dealt cards
        - No duplicates
        """
        if len(dealt_cards) != 14:
            return False, "Must deal exactly 14 cards in Fantasy Land"

        if len(placed_cards) != 13:
            return False, "Must place exactly 13 cards"

        placed_set = set(placed_cards)
        dealt_set = set(dealt_cards)

        if len(placed_set) != 13:
            return False, "Duplicate cards in placement"

        if not placed_set.issubset(dealt_set):
            return False, "Placed cards not from dealt cards"

        return True, None

    @staticmethod
    def get_cards_count() -> int:
        """Get number of cards dealt in Pineapple Fantasy Land."""
        return 14
