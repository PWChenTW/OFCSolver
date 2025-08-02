"""
Repository Interfaces Package

Contains abstract repository interfaces for domain entities.
Repositories provide persistence abstraction following the
Repository pattern from DDD.

Repository Categories:
- Game repositories: Game, Player, Position management
- Strategy repositories: Analysis sessions, calculations
- Training repositories: Training data and progress
- Analytics repositories: Performance and historical data
"""

# Strategy repositories
from .analysis_repository import AnalysisRepository

# Analytics repositories
from .analytics_repository import AnalyticsRepository
from .calculation_repository import CalculationRepository

# Game repositories
from .game_repository import GameRepository
from .hand_history_repository import HandHistoryRepository
from .player_repository import PlayerRepository
from .position_repository import PositionRepository
from .scenario_repository import ScenarioRepository
from .strategy_repository import StrategyRepository

# Training repositories
from .training_repository import TrainingRepository

__all__ = [
    # Game repositories
    "GameRepository",
    "PlayerRepository",
    "PositionRepository",
    # Strategy repositories
    "AnalysisRepository",
    "StrategyRepository",
    "CalculationRepository",
    # Training repositories
    "TrainingRepository",
    "ScenarioRepository",
    # Analytics repositories
    "AnalyticsRepository",
    "HandHistoryRepository",
]
