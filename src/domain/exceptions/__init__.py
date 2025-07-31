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
    DomainError,
    BusinessRuleViolationError,
    InvalidOperationError,
    ResourceNotFoundError
)

from .game_exceptions import (
    GameStateError,
    InvalidCardPlacementError,
    PlayerNotFoundError,
    GameNotFoundError,
    InvalidGameConfigurationError
)

from .strategy_exceptions import (
    AnalysisError,
    CalculationTimeoutError,
    InvalidPositionError,
    StrategyNotFoundError,
    InsufficientDataError
)

from .training_exceptions import (
    TrainingSessionError,
    ScenarioNotFoundError,
    InvalidDifficultyError,
    ExerciseError
)

from .validation_exceptions import (
    ValidationError,
    InvalidCardError,
    InvalidMoveError,
    HandValidationError
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