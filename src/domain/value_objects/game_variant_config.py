"""
Game Variant Configuration

Simple configuration object for different OFC rule variants.
Following YAGNI principle - only essential config options.
"""

from dataclasses import dataclass
from typing import Dict, Any
from ..base import ValueObject


@dataclass(frozen=True)
class GameVariantConfig(ValueObject):
    """
    Configuration for OFC game variant rules.

    MVP approach: Simple dataclass with rule parameters.
    No complex inheritance or strategy patterns.
    """

    # Basic variant info
    variant_name: str  # e.g., "pineapple_standard", "pineapple_pokerstars"

    # Card dealing
    initial_cards: int = 5
    cards_per_turn: int = 3  # For pineapple
    cards_to_place: int = 2  # For pineapple

    # Fantasy Land rules
    fl_entry_requirement: str = "QQ+"  # Simple string description
    fl_stay_requirement: str = "QQ+"  # Can be different per platform
    fl_cards_dealt: int = 14
    fl_cards_to_place: int = 13

    # Royalty scoring (points)
    royalty_top: Dict[str, int] = None
    royalty_middle: Dict[str, int] = None
    royalty_bottom: Dict[str, int] = None

    # Game rules
    allow_fouling: bool = True
    foul_penalty: int = 6
    scoop_bonus: int = 6

    def __post_init__(self):
        # Set default royalty scoring if not provided
        if self.royalty_top is None:
            object.__setattr__(
                self,
                "royalty_top",
                {
                    "66": 1,
                    "77": 2,
                    "88": 3,
                    "99": 4,
                    "TT": 5,
                    "JJ": 6,
                    "QQ": 7,
                    "KK": 8,
                    "AA": 9,
                    "222": 10,
                    "333": 11,
                    "444": 12,
                    "555": 13,
                    "666": 14,
                    "777": 15,
                    "888": 16,
                    "999": 17,
                    "TTT": 18,
                    "JJJ": 19,
                    "QQQ": 20,
                    "KKK": 21,
                    "AAA": 22,
                },
            )

        if self.royalty_middle is None:
            object.__setattr__(
                self,
                "royalty_middle",
                {
                    "trips": 2,
                    "straight": 4,
                    "flush": 8,  # Pineapple bonus
                    "full_house": 12,
                    "quads": 20,
                    "straight_flush": 30,
                    "royal_flush": 50,
                },
            )

        if self.royalty_bottom is None:
            object.__setattr__(
                self,
                "royalty_bottom",
                {
                    "straight": 2,
                    "flush": 4,
                    "full_house": 6,
                    "quads": 10,
                    "straight_flush": 15,
                    "royal_flush": 25,
                },
            )


# Pre-defined configurations for common variants
PINEAPPLE_STANDARD = GameVariantConfig(
    variant_name="pineapple_standard",
    fl_entry_requirement="QQ+",
    fl_stay_requirement="QQ+",
)

PINEAPPLE_POKERSTARS = GameVariantConfig(
    variant_name="pineapple_pokerstars",
    fl_entry_requirement="QQ+",
    fl_stay_requirement="trips_top_or_fh_middle_or_quads_bottom",
)

STANDARD_OFC = GameVariantConfig(
    variant_name="standard_ofc",
    cards_per_turn=1,
    cards_to_place=1,
    fl_entry_requirement="AA+",
    fl_stay_requirement="TT+",
)
