"""
Training Domain Events

Events related to training sessions and exercises.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any

from ..base import DomainEvent


@dataclass(frozen=True)
class TrainingSessionStartedEvent:
    """Event fired when a training session starts."""

    session_id: str
    user_id: str
    difficulty: Any  # Difficulty object
    timestamp: datetime
    scenario_type: str = ""
    difficulty_level: int = 1


@dataclass(frozen=True)
class ScenarioCompletedEvent:
    """Event fired when a training scenario is completed."""

    session_id: str
    scenario_id: str
    performance: Any  # Performance object
    timestamp: datetime
    user_id: str = ""
    performance_score: float = 0.0
    completion_time_ms: int = 0
    mistakes_count: int = 0


@dataclass(frozen=True)
class TrainingScenarioCompletedEvent:
    """Event fired when a training scenario is completed."""

    session_id: str
    user_id: str
    scenario_id: str
    performance_score: float
    completion_time_ms: int
    mistakes_count: int = 0


@dataclass(frozen=True)
class TrainingSessionEndedEvent:
    """Event fired when a training session ends."""

    session_id: str
    user_id: str
    total_scenarios: int
    overall_performance: Any  # Performance object
    timestamp: datetime


@dataclass(frozen=True)
class ExerciseCompletedEvent:
    """Event fired when an exercise is completed."""

    exercise_id: str
    user_id: str
    session_id: str
    is_correct: bool
    attempt_count: int = 1
    time_taken_ms: Optional[int] = None
