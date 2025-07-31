"""
Training Domain Events

Events related to training sessions and exercises.
"""

from dataclasses import dataclass
from typing import Optional

from ..base import DomainEvent


@dataclass(frozen=True)
class TrainingSessionStartedEvent(DomainEvent):
    """Event fired when a training session starts."""
    session_id: str
    user_id: str
    scenario_type: str
    difficulty_level: int = 1


@dataclass(frozen=True)
class TrainingScenarioCompletedEvent(DomainEvent):
    """Event fired when a training scenario is completed."""
    session_id: str
    user_id: str
    scenario_id: str
    performance_score: float
    completion_time_ms: int
    mistakes_count: int = 0


@dataclass(frozen=True)
class ExerciseCompletedEvent(DomainEvent):
    """Event fired when an exercise is completed."""
    exercise_id: str
    user_id: str
    session_id: str
    is_correct: bool
    attempt_count: int = 1
    time_taken_ms: Optional[int] = None