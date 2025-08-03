"""Analysis-related commands for the OFC Solver system."""
from dataclasses import dataclass
from typing import Optional, Dict, List
from uuid import UUID

from .base import Command
from ...domain.entities.game.position import Position


@dataclass
class RequestAnalysisCommand(Command):
    """Command to request strategy analysis for a position."""
    position: Position
    analysis_type: str = "optimal"  # optimal, monte_carlo, heuristic
    calculation_depth: int = 3
    max_calculation_time_seconds: int = 60
    force_recalculate: bool = False
    priority: int = 0  # Higher priority gets processed first
    
    def __post_init__(self):

        if self.analysis_type not in ["optimal", "monte_carlo", "heuristic"]:
            raise ValueError(f"Invalid analysis type: {self.analysis_type}")
        if self.calculation_depth < 1 or self.calculation_depth > 10:
            raise ValueError("Calculation depth must be between 1 and 10")
        if self.max_calculation_time_seconds < 1:
            raise ValueError("Max calculation time must be positive")


@dataclass
class CancelAnalysisCommand(Command):
    """Command to cancel an ongoing analysis."""
    analysis_session_id: UUID
    reason: Optional[str] = None
    
    def __post_init__(self):

        if not self.analysis_session_id:
            raise ValueError("Analysis session ID is required")


@dataclass
class GetAnalysisStatusCommand(Command):
    """Command to get the status of an analysis session."""
    analysis_session_id: UUID
    
    def __post_init__(self):

        if not self.analysis_session_id:
            raise ValueError("Analysis session ID is required")


@dataclass
class BatchAnalysisCommand(Command):
    """Command to request analysis for multiple positions."""
    positions: List[Position]
    analysis_type: str = "optimal"
    max_parallel: int = 4
    priority: int = 0
    
    def __post_init__(self):

        if not self.positions:
            raise ValueError("At least one position is required")
        if len(self.positions) > 100:
            raise ValueError("Maximum 100 positions allowed in batch")
        if self.max_parallel < 1 or self.max_parallel > 10:
            raise ValueError("Max parallel must be between 1 and 10")


@dataclass
class CompareStrategiesCommand(Command):
    """Command to compare different strategies for a position."""
    position: Position
    strategies_to_compare: List[str]  # e.g., ["optimal", "monte_carlo", "heuristic"]
    
    def __post_init__(self):

        if len(self.strategies_to_compare) < 2:
            raise ValueError("At least 2 strategies required for comparison")
        valid_strategies = {"optimal", "monte_carlo", "heuristic", "user_defined"}
        invalid = set(self.strategies_to_compare) - valid_strategies
        if invalid:
            raise ValueError(f"Invalid strategies: {invalid}")


@dataclass
class SaveAnalysisResultCommand(Command):
    """Command to save analysis results for future reference."""
    analysis_session_id: UUID
    name: str
    tags: List[str] = None
    description: Optional[str] = None
    
    def __post_init__(self):

        if not self.analysis_session_id:
            raise ValueError("Analysis session ID is required")
        if not self.name:
            raise ValueError("Name is required")
        if self.tags is None:
            self.tags = []