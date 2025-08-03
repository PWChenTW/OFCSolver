"""Training-related commands for the OFC Solver system."""
from dataclasses import dataclass
from typing import Optional, List, Dict
from uuid import UUID

from .base import Command
from ...domain.value_objects.difficulty import Difficulty
from ...domain.value_objects.card import Card
from ...domain.value_objects.card_position import CardPosition


@dataclass
class StartTrainingSessionCommand(Command):
    """Command to start a new training session."""
    difficulty: Difficulty
    scenario_type: str = "random"  # random, specific, progressive
    focus_areas: List[str] = None  # e.g., ["fantasy_land", "endgame", "middle_game"]
    time_limit_minutes: Optional[int] = None
    
    def __post_init__(self):
        super().__post_init__()
        if self.scenario_type not in ["random", "specific", "progressive"]:
            raise ValueError(f"Invalid scenario type: {self.scenario_type}")
        if self.focus_areas is None:
            self.focus_areas = []
        if self.time_limit_minutes and self.time_limit_minutes < 1:
            raise ValueError("Time limit must be positive")


@dataclass
class SubmitTrainingMoveCommand(Command):
    """Command to submit a move in a training scenario."""
    session_id: UUID
    scenario_id: UUID
    card: Card
    position: CardPosition
    time_taken_seconds: float
    
    def __post_init__(self):
        super().__post_init__()
        if not self.session_id:
            raise ValueError("Session ID is required")
        if not self.scenario_id:
            raise ValueError("Scenario ID is required")
        if self.time_taken_seconds < 0:
            raise ValueError("Time taken cannot be negative")


@dataclass
class RequestHintCommand(Command):
    """Command to request a hint for the current training scenario."""
    session_id: UUID
    scenario_id: UUID
    hint_level: int = 1  # 1=subtle, 2=moderate, 3=explicit
    
    def __post_init__(self):
        super().__post_init__()
        if not self.session_id:
            raise ValueError("Session ID is required")
        if not self.scenario_id:
            raise ValueError("Scenario ID is required")
        if self.hint_level not in [1, 2, 3]:
            raise ValueError("Hint level must be 1, 2, or 3")


@dataclass
class CompleteScenarioCommand(Command):
    """Command to complete a training scenario and get feedback."""
    session_id: UUID
    scenario_id: UUID
    
    def __post_init__(self):
        super().__post_init__()
        if not self.session_id:
            raise ValueError("Session ID is required")
        if not self.scenario_id:
            raise ValueError("Scenario ID is required")


@dataclass
class AdjustDifficultyCommand(Command):
    """Command to adjust difficulty during a training session."""
    session_id: UUID
    new_difficulty: Difficulty
    reason: Optional[str] = None  # e.g., "too_easy", "too_hard", "user_request"
    
    def __post_init__(self):
        super().__post_init__()
        if not self.session_id:
            raise ValueError("Session ID is required")


@dataclass
class GenerateCustomScenarioCommand(Command):
    """Command to generate a custom training scenario."""
    session_id: UUID
    scenario_params: Dict[str, any]  # Flexible parameters for scenario generation
    
    def __post_init__(self):
        super().__post_init__()
        if not self.session_id:
            raise ValueError("Session ID is required")
        if not self.scenario_params:
            raise ValueError("Scenario parameters are required")


@dataclass
class ReviewTrainingHistoryCommand(Command):
    """Command to review past training performance."""
    time_period_days: int = 30
    scenario_types: Optional[List[str]] = None
    minimum_scenarios: int = 1
    
    def __post_init__(self):
        super().__post_init__()
        if self.time_period_days < 1:
            raise ValueError("Time period must be positive")
        if self.minimum_scenarios < 1:
            raise ValueError("Minimum scenarios must be positive")


@dataclass
class EndTrainingSessionCommand(Command):
    """Command to end a training session."""
    session_id: UUID
    save_progress: bool = True
    
    def __post_init__(self):
        super().__post_init__()
        if not self.session_id:
            raise ValueError("Session ID is required")