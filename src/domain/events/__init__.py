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
    GameCompletedEvent,
    CardPlacedEvent, 
    RoundStartedEvent,
    PlayerJoinedEvent,
    PlayerLeftEvent
)

# Strategy events  
from .strategy_events import (
    AnalysisRequestedEvent,
    AnalysisCompletedEvent,
    StrategyCalculatedEvent,
    CalculationStartedEvent,
    CalculationCompletedEvent
)

# Training events
from .training_events import (
    TrainingScenarioCompletedEvent,
    TrainingSessionStartedEvent,
    ExerciseCompletedEvent
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