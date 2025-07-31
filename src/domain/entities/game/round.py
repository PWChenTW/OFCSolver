"""
Round Entity for Game Management

The Round entity represents a single round within an OFC game,
tracking player actions and round state.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from ...base import DomainEntity
from ...value_objects import Card, CardPosition
from .player import PlayerId

RoundId = str


class RoundStatus(Enum):
    """Status of a game round."""

    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class CardPlacement:
    """Represents a card placement within a round."""

    player_id: PlayerId
    card: Card
    position: CardPosition
    timestamp: datetime
    sequence_number: int


class Round(DomainEntity):
    """
    Represents a single round in an OFC game.

    Tracks player actions, card placements, and round progression.
    Each round involves all players placing one card each.
    """

    def __init__(
        self,
        round_id: RoundId,
        round_number: int,
        game_id: str,
        player_ids: List[PlayerId],
        starting_player_id: PlayerId,
    ):
        super().__init__(round_id)

        self._round_number = round_number
        self._game_id = game_id
        self._player_ids = player_ids.copy()
        self._starting_player_id = starting_player_id
        self._status = RoundStatus.ACTIVE
        self._started_at = datetime.utcnow()
        self._completed_at: Optional[datetime] = None

        # Track card placements in order
        self._placements: List[CardPlacement] = []
        self._current_player_index = player_ids.index(starting_player_id)

        # Track which players have acted this round
        self._players_acted: Dict[PlayerId, bool] = {
            player_id: False for player_id in player_ids
        }

    @property
    def round_number(self) -> int:
        """Get round number."""
        return self._round_number

    @property
    def game_id(self) -> str:
        """Get game ID this round belongs to."""
        return self._game_id

    @property
    def status(self) -> RoundStatus:
        """Get round status."""
        return self._status

    @property
    def started_at(self) -> datetime:
        """Get round start time."""
        return self._started_at

    @property
    def completed_at(self) -> Optional[datetime]:
        """Get round completion time."""
        return self._completed_at

    @property
    def player_ids(self) -> List[PlayerId]:
        """Get list of player IDs in this round."""
        return self._player_ids.copy()

    @property
    def starting_player_id(self) -> PlayerId:
        """Get ID of player who started this round."""
        return self._starting_player_id

    @property
    def placements(self) -> List[CardPlacement]:
        """Get all card placements in this round."""
        return self._placements.copy()

    @property
    def is_completed(self) -> bool:
        """Check if round is completed."""
        return self._status == RoundStatus.COMPLETED

    @property
    def is_active(self) -> bool:
        """Check if round is active."""
        return self._status == RoundStatus.ACTIVE

    def get_current_player_id(self) -> Optional[PlayerId]:
        """Get ID of player whose turn it is."""
        if not self.is_active:
            return None
        return self._player_ids[self._current_player_index]

    def has_player_acted(self, player_id: PlayerId) -> bool:
        """Check if player has acted this round."""
        return self._players_acted.get(player_id, False)

    def get_players_remaining(self) -> List[PlayerId]:
        """Get list of players who haven't acted yet."""
        return [
            player_id
            for player_id in self._player_ids
            if not self._players_acted[player_id]
        ]

    def get_placement_count(self) -> int:
        """Get number of placements made this round."""
        return len(self._placements)

    def get_placements_by_player(self, player_id: PlayerId) -> List[CardPlacement]:
        """Get placements made by specific player."""
        return [p for p in self._placements if p.player_id == player_id]

    def record_placement(
        self, player_id: PlayerId, card: Card, position: CardPosition
    ) -> None:
        """
        Record a card placement in this round.

        Args:
            player_id: ID of player making placement
            card: Card being placed
            position: Position where card is placed

        Raises:
            ValueError: If placement is invalid
        """
        if not self.is_active:
            raise ValueError("Cannot record placement in inactive round")

        if player_id != self.get_current_player_id():
            raise ValueError(f"It's not player {player_id}'s turn")

        if self.has_player_acted(player_id):
            raise ValueError(f"Player {player_id} has already acted this round")

        # Create placement record
        placement = CardPlacement(
            player_id=player_id,
            card=card,
            position=position,
            timestamp=datetime.utcnow(),
            sequence_number=len(self._placements) + 1,
        )

        # Record placement
        self._placements.append(placement)
        self._players_acted[player_id] = True

        # Advance to next player
        self._advance_turn()

        # Check if round is complete
        if self._is_round_complete():
            self._complete_round()

        self._increment_version()

    def cancel_round(self, reason: str = "Unknown") -> None:
        """Cancel this round."""
        if not self.is_active:
            raise ValueError("Cannot cancel inactive round")

        self._status = RoundStatus.CANCELLED
        self._completed_at = datetime.utcnow()
        self._increment_version()

    def get_round_summary(self) -> Dict:
        """Get summary of round events."""
        return {
            "round_id": str(self.id),
            "round_number": self._round_number,
            "game_id": self._game_id,
            "status": self._status.value,
            "started_at": self._started_at.isoformat(),
            "completed_at": (
                self._completed_at.isoformat() if self._completed_at else None
            ),
            "total_placements": len(self._placements),
            "players_acted": sum(self._players_acted.values()),
            "players_remaining": len(self.get_players_remaining()),
            "placements": [
                {
                    "player_id": p.player_id,
                    "card": str(p.card),
                    "position": p.position.value,
                    "sequence": p.sequence_number,
                    "timestamp": p.timestamp.isoformat(),
                }
                for p in self._placements
            ],
        }

    def get_turn_order(self) -> List[PlayerId]:
        """Get the turn order for this round."""
        # Reorder players starting from the starting player
        start_index = self._player_ids.index(self._starting_player_id)
        return self._player_ids[start_index:] + self._player_ids[:start_index]

    def get_elapsed_time(self) -> float:
        """Get elapsed time in seconds since round start."""
        end_time = self._completed_at or datetime.utcnow()
        return (end_time - self._started_at).total_seconds()

    def _advance_turn(self) -> None:
        """Advance to next player's turn."""
        if not self.is_active:
            return

        # Find next player who hasn't acted
        for _ in range(len(self._player_ids)):
            self._current_player_index = (self._current_player_index + 1) % len(
                self._player_ids
            )
            next_player_id = self._player_ids[self._current_player_index]

            if not self._players_acted[next_player_id]:
                break

    def _is_round_complete(self) -> bool:
        """Check if all players have acted."""
        return all(self._players_acted.values())

    def _complete_round(self) -> None:
        """Complete the round."""
        self._status = RoundStatus.COMPLETED
        self._completed_at = datetime.utcnow()

    def __repr__(self) -> str:
        """String representation of round."""
        return (
            f"Round(id={self.id}, number={self._round_number}, "
            f"game={self._game_id}, status={self._status.value}, "
            f"placements={len(self._placements)}/{len(self._player_ids)})"
        )
