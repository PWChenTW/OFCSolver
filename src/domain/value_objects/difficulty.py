"""Difficulty Value Object"""

from dataclasses import dataclass
from enum import Enum

from ..base import ValueObject


class DifficultyLevel(str, Enum):
    """Enumeration of difficulty levels."""
    
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


@dataclass(frozen=True)
class Difficulty(ValueObject):
    """Difficulty value object."""

    level: DifficultyLevel
    name: str = ""
    
    def __post_init__(self):
        if not self.name:
            level_names = {
                DifficultyLevel.EASY: "Easy",
                DifficultyLevel.MEDIUM: "Medium", 
                DifficultyLevel.HARD: "Hard",
                DifficultyLevel.EXPERT: "Expert"
            }
            object.__setattr__(self, 'name', level_names.get(self.level, "Unknown"))
