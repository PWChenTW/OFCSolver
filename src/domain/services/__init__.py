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

# Game domain services
from .hand_evaluator import HandEvaluator
from .game_validator import GameValidator
from .royalty_calculator import RoyaltyCalculator
from .fantasy_land_manager import FantasyLandManager

# Strategy domain services
from .strategy_calculator import StrategyCalculator
from .game_tree_builder import GameTreeBuilder
from .monte_carlo_simulator import MonteCarloSimulator
from .optimal_play_finder import OptimalPlayFinder

# Training domain services
from .scenario_generator import ScenarioGenerator
from .performance_tracker import PerformanceTracker
from .adaptive_difficulty import AdaptiveDifficulty

__all__ = [
    # Game services
    "HandEvaluator",
    "GameValidator",
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