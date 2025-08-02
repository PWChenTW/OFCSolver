"""
Game Domain Events

Events related to game management and gameplay.
"""

from dataclasses import dataclass
from typing import Dict, Optional

from ..base import DomainEvent
from ..value_objects import Card, CardPosition, Score


@dataclass(frozen=True)
class GameCompletedEvent(DomainEvent):
    """Event fired when a game is completed."""

    game_id: str
    final_scores: Dict[str, Score]
    winner_id: Optional[str] = None
    game_duration_seconds: Optional[int] = None


@dataclass(frozen=True)
class CardPlacedEvent(DomainEvent):
    """Event fired when a card is placed."""

    game_id: str
    player_id: str
    card: Card
    position: CardPosition
    round_number: int
    placement_sequence: int = 0


@dataclass(frozen=True)
class RoundStartedEvent(DomainEvent):
    """Event fired when a new round starts."""

    game_id: str
    round_number: int
    active_player_id: str
    remaining_cards: int = 0


@dataclass(frozen=True)
class PlayerJoinedEvent(DomainEvent):
    """Event fired when a player joins a game."""

    game_id: str
    player_id: str
    player_name: str
    player_count: int


@dataclass(frozen=True)
class PlayerLeftEvent(DomainEvent):
    """Event fired when a player leaves a game."""

    game_id: str
    player_id: str
    reason: str = "Unknown"
    remaining_players: int = 0
