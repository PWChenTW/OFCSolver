"""
Domain Exceptions Package

Contains all domain-specific exceptions that represent
business rule violations and domain errors.

Exception Categories:
- Game exceptions: Invalid moves, game state errors
- Strategy exceptions: Analysis failures, calculation errors
- Training exceptions: Session errors, scenario problems
- Validation exceptions: Rule violations, data validation
"""

from .base_exceptions import (
    BusinessRuleViolationError,
    DomainError,
    InvalidOperationError,
    ResourceNotFoundError,
)
from .game_exceptions import (
    GameNotFoundError,
    GameStateError,
    InvalidCardPlacementError,
    InvalidGameConfigurationError,
    PlayerNotFoundError,
)
from .strategy_exceptions import (
    AnalysisError,
    CalculationTimeoutError,
    InsufficientDataError,
    InvalidPositionError,
    StrategyCalculationError,
    StrategyNotFoundError,
)
from .training_exceptions import (
    ExerciseError,
    InvalidDifficultyError,
    ScenarioNotFoundError,
    TrainingSessionError,
)
from .validation_exceptions import (
    HandValidationError,
    InvalidCardError,
    InvalidMoveError,
    ValidationError,
)

__all__ = [
    # Base exceptions
    "DomainError",
    "BusinessRuleViolationError",
    "InvalidOperationError",
    "ResourceNotFoundError",
    # Game exceptions
    "GameStateError",
    "InvalidCardPlacementError",
    "PlayerNotFoundError",
    "GameNotFoundError",
    "InvalidGameConfigurationError",
    # Strategy exceptions
    "AnalysisError",
    "CalculationTimeoutError",
    "InvalidPositionError",
    "StrategyNotFoundError",
    "InsufficientDataError",
    "StrategyCalculationError",
    # Training exceptions
    "TrainingSessionError",
    "ScenarioNotFoundError",
    "InvalidDifficultyError",
    "ExerciseError",
    # Validation exceptions
    "ValidationError",
    "InvalidCardError",
    "InvalidMoveError",
    "HandValidationError",
]
