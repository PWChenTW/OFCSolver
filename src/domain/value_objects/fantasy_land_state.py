"""
Fantasy Land State Value Object

Represents player's Fantasy Land status in Pineapple OFC.
Following MVP principles - minimal but complete.
"""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from ..base import ValueObject


@dataclass(frozen=True)
class FantasyLandState(ValueObject):
    """
    Immutable value object representing a player's Fantasy Land state.
    
    MVP implementation focusing on essential state tracking only.
    """
    
    player_id: UUID
    is_active: bool
    entry_round: Optional[int] = None  # Round when entered FL
    consecutive_count: int = 0  # How many times stayed in FL
    
    def enter_fantasy_land(self, current_round: int) -> "FantasyLandState":
        """Create new state for entering Fantasy Land."""
        if self.is_active:
            # Already in FL, this is staying
            return FantasyLandState(
                player_id=self.player_id,
                is_active=True,
                entry_round=self.entry_round,  # Keep original entry
                consecutive_count=self.consecutive_count + 1,
            )
        else:
            # First time entering
            return FantasyLandState(
                player_id=self.player_id,
                is_active=True,
                entry_round=current_round,
                consecutive_count=1,
            )
    
    def exit_fantasy_land(self) -> "FantasyLandState":
        """Create new state for exiting Fantasy Land."""
        return FantasyLandState(
            player_id=self.player_id,
            is_active=False,
            entry_round=None,
            consecutive_count=0,
        )
    
    @classmethod
    def create_initial(cls, player_id: UUID) -> "FantasyLandState":
        """Create initial state (not in Fantasy Land)."""
        return cls(
            player_id=player_id,
            is_active=False,
            entry_round=None,
            consecutive_count=0,
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "player_id": str(self.player_id),
            "is_active": self.is_active,
            "entry_round": self.entry_round,
            "consecutive_count": self.consecutive_count,
        }