"""
Domain Entities Package

Contains all domain entities and aggregate roots for the OFC Solver system.
Entities have distinct identity and encapsulate business behavior.

Subpackages:
- game/: Game management entities (Game, Player, Position)
- strategy/: Strategy analysis entities (AnalysisSession, StrategyNode)  
- training/: Training system entities (TrainingSession, Scenario)
- analytics/: Analytics entities (AnalyticsProfile, HandHistory)
"""

# Import key entities for easy access
from .game import Game, Player, Position, Round
from .strategy import AnalysisSession, StrategyNode, Calculation
from .training import TrainingSession, Scenario, Exercise
from .analytics import AnalyticsProfile, HandHistory, PerformanceReport

__all__ = [
    # Game entities
    "Game",
    "Player", 
    "Position",
    "Round",
    
    # Strategy entities
    "AnalysisSession",
    "StrategyNode",
    "Calculation",
    
    # Training entities
    "TrainingSession",
    "Scenario",
    "Exercise",
    
    # Analytics entities
    "AnalyticsProfile",
    "HandHistory",
    "PerformanceReport",
]