"""
Game Domain Events

Events related to game management and gameplay.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

from ..base import DomainEvent
from ..value_objects import Card, CardPosition, Score


@dataclass(frozen=True)
class GameCompletedEvent:
    """Event fired when a game is completed."""

    game_id: str
    final_scores: Dict[str, Score]
    winner_id: Optional[str] = None
    game_duration_seconds: Optional[int] = None
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    event_version: int = 1
    aggregate_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif hasattr(value, "to_dict"):
                result[key] = value.to_dict()
            else:
                result[key] = value
        return result


@dataclass(frozen=True)
class CardPlacedEvent:
    """Event fired when a card is placed."""

    game_id: str
    player_id: str
    card: Card
    position: CardPosition
    round_number: int
    placement_sequence: int = 0
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    event_version: int = 1
    aggregate_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif hasattr(value, "to_dict"):
                result[key] = value.to_dict()
            else:
                result[key] = value
        return result


@dataclass(frozen=True)
class RoundStartedEvent:
    """Event fired when a new round starts."""

    game_id: str
    round_number: int
    active_player_id: str
    remaining_cards: int = 0
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    event_version: int = 1
    aggregate_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif hasattr(value, "to_dict"):
                result[key] = value.to_dict()
            else:
                result[key] = value
        return result


@dataclass(frozen=True)
class PlayerJoinedEvent:
    """Event fired when a player joins a game."""

    game_id: str
    player_id: str
    player_name: str
    player_count: int
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    event_version: int = 1
    aggregate_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif hasattr(value, "to_dict"):
                result[key] = value.to_dict()
            else:
                result[key] = value
        return result


@dataclass(frozen=True)
class PlayerLeftEvent:
    """Event fired when a player leaves a game."""

    game_id: str
    player_id: str
    reason: str = "Unknown"
    remaining_players: int = 0
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    event_version: int = 1
    aggregate_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif hasattr(value, "to_dict"):
                result[key] = value.to_dict()
            else:
                result[key] = value
        return result
