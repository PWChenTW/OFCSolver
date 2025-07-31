"""Confidence Interval Value Object - Placeholder"""
from dataclasses import dataclass
from ..base import ValueObject

@dataclass(frozen=True)
class ConfidenceInterval(ValueObject):
    """Confidence interval placeholder."""
    lower_bound: float
    upper_bound: float
    confidence_level: float = 0.95
    
    def to_dict(self) -> dict:
        return {
            'lower_bound': self.lower_bound,
            'upper_bound': self.upper_bound,
            'confidence_level': self.confidence_level
        }