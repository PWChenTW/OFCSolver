"""
Exercise Entity - Placeholder

This module will contain the Exercise entity for managing
individual practice problems within training scenarios.
"""

from ...base import DomainEntity

ExerciseId = str


class Exercise(DomainEntity):
    """
    Training exercise entity - placeholder implementation.
    
    TODO: Implement exercise logic including:
    - Problem definition
    - Solution validation
    - Scoring system
    - Hints and feedback
    """
    
    def __init__(self, exercise_id: ExerciseId):
        super().__init__(exercise_id)
        # TODO: Implement exercise logic
        pass