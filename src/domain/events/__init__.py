"""
Domain Events Package

Contains all domain events for inter-context communication.
Domain events represent important business occurrences that
other parts of the system may need to react to.

Event Categories:
- Game events: Game state changes, card placements
- Strategy events: Analysis completion, calculation results
- Training events: Session progress, scenario completion
"""

# Game events
from .game_events import (
    CardPlacedEvent,
    GameCompletedEvent,
    PlayerJoinedEvent,
    PlayerLeftEvent,
    RoundStartedEvent,
)

# Strategy events
from .strategy_events import (
    AnalysisCompletedEvent,
    AnalysisRequestedEvent,
    CalculationCompletedEvent,
    CalculationStartedEvent,
    StrategyCalculatedEvent,
)

# Training events
from .training_events import (
    ExerciseCompletedEvent,
    TrainingScenarioCompletedEvent,
    TrainingSessionStartedEvent,
)

__all__ = [
    # Game events
    "GameCompletedEvent",
    "CardPlacedEvent",
    "RoundStartedEvent",
    "PlayerJoinedEvent",
    "PlayerLeftEvent",
    # Strategy events
    "AnalysisRequestedEvent",
    "AnalysisCompletedEvent",
    "StrategyCalculatedEvent",
    "CalculationStartedEvent",
    "CalculationCompletedEvent",
    # Training events
    "TrainingScenarioCompletedEvent",
    "TrainingSessionStartedEvent",
    "ExerciseCompletedEvent",
]
