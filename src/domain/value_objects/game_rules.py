"""
Game Rules Value Object

Represents the rules configuration for an OFC game.
"""

from dataclasses import dataclass
from typing import Optional

from ..base import ValueObject


@dataclass(frozen=True)
class GameRules(ValueObject):
    """
    OFC game rules configuration.

    Defines the variant and specific rules for a game session.
    """

    variant: str = "standard"  # standard, pineapple, 2-7-pineapple
    player_count: int = 2
    fantasy_land_enabled: bool = True
    scoring_system: str = "traditional"  # traditional, progressive
    time_limit_seconds: Optional[int] = None
    allow_scooping: bool = True  # Allow early folding
    royalty_multiplier: float = 1.0

    def __post_init__(self):
        """Validate rules configuration."""
        if self.variant not in ["standard", "pineapple", "2-7-pineapple"]:
            raise ValueError(f"Invalid variant: {self.variant}")

        if self.player_count < 2 or self.player_count > 4:
            raise ValueError(f"Player count must be 2-4, got {self.player_count}")

        if self.royalty_multiplier < 0:
            raise ValueError("Royalty multiplier cannot be negative")

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "variant": self.variant,
            "player_count": self.player_count,
            "fantasy_land_enabled": self.fantasy_land_enabled,
            "scoring_system": self.scoring_system,
            "time_limit_seconds": self.time_limit_seconds,
            "allow_scooping": self.allow_scooping,
            "royalty_multiplier": self.royalty_multiplier,
        }

    @property
    def initial_cards_count(self) -> int:
        """Get number of cards dealt initially."""
        if self.variant == "standard":
            return 5
        elif self.variant in ["pineapple", "2-7-pineapple"]:
            return 5  # Same initial deal
        else:
            return 5

    @property
    def cards_per_turn(self) -> int:
        """Get number of cards dealt per turn."""
        if self.variant == "standard":
            return 1
        elif self.variant in ["pineapple", "2-7-pineapple"]:
            return 3  # Deal 3, play 2, discard 1
        else:
            return 1

    @property
    def max_hand_size(self) -> int:
        """Get maximum hand size."""
        return 13  # Always 13 in OFC

    @property
    def supports_fantasy_land(self) -> bool:
        """Check if variant supports fantasy land."""
        return self.fantasy_land_enabled and self.variant in [
            "standard",
            "pineapple",
            "2-7-pineapple",
        ]

    @classmethod
    def standard_rules(cls) -> "GameRules":
        """Create standard OFC rules."""
        return cls(variant="standard")

    @classmethod
    def pineapple_rules(cls) -> "GameRules":
        """Create Pineapple OFC rules."""
        return cls(variant="pineapple")

    @classmethod
    def tournament_rules(cls, variant: str = "standard") -> "GameRules":
        """Create tournament-style rules."""
        return cls(
            variant=variant,
            time_limit_seconds=300,  # 5 minutes per player
            allow_scooping=False,
            royalty_multiplier=1.5,  # Higher stakes
        )
