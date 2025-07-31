"""Training Domain Exceptions - Placeholder"""
from .base_exceptions import DomainError

class TrainingSessionError(DomainError):
    """Training session error placeholder."""
    pass

class ScenarioNotFoundError(DomainError):
    """Scenario not found placeholder."""
    pass

class InvalidDifficultyError(DomainError):
    """Invalid difficulty placeholder."""
    pass

class ExerciseError(DomainError):
    """Exercise error placeholder."""
    pass