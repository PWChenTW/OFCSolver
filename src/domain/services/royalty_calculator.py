"""Royalty Calculator Service - Placeholder"""

from typing import List

from ..base import DomainService
from ..value_objects import Card


class RoyaltyCalculator(DomainService):
    """Royalty calculator placeholder."""

    def __init__(self) -> None:
        pass

    def calculate_total_royalties(
        self, top_row: List[Card], middle_row: List[Card], bottom_row: List[Card]
    ) -> int:
        """Calculate total royalties - placeholder."""
        return 0
