"""
Domain Services Package

Contains domain services that encapsulate business logic
that doesn't naturally fit within a single entity or value object.

Service Categories:
- Game services: Hand evaluation, game validation, royalty calculation
- Strategy services: Strategy calculation, game tree building, simulation
- Training services: Scenario generation, performance tracking
- Analysis services: Position analysis, pattern recognition
"""

from .adaptive_difficulty import AdaptiveDifficulty
from .fantasy_land_manager import FantasyLandManager
from .game_tree_builder import GameTreeBuilder
from .game_validator import GameValidator
from .pineapple_game_validator import PineappleGameValidator

# Game domain services
from .hand_evaluator import HandEvaluator
from .pineapple_evaluator import PineappleHandEvaluator
from .pineapple_fantasy_land import PineappleFantasyLandManager
from .fantasy_land_strategy import FantasyLandStrategyAnalyzer
from .monte_carlo_simulator import MonteCarloSimulator
from .optimal_play_finder import OptimalPlayFinder
from .performance_tracker import PerformanceTracker
from .royalty_calculator import RoyaltyCalculator

# Training domain services
from .scenario_generator import ScenarioGenerator

# Strategy domain services
from .strategy_calculator import StrategyCalculator

__all__ = [
    # Game services
    "HandEvaluator",
    "PineappleHandEvaluator",
    "PineappleFantasyLandManager",
    "FantasyLandStrategyAnalyzer",
    "GameValidator",
    "PineappleGameValidator",
    "RoyaltyCalculator",
    "FantasyLandManager",
    # Strategy services
    "StrategyCalculator",
    "GameTreeBuilder",
    "MonteCarloSimulator",
    "OptimalPlayFinder",
    # Training services
    "ScenarioGenerator",
    "PerformanceTracker",
    "AdaptiveDifficulty",
]
