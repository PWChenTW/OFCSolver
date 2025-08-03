"""
Strategy Value Object for OFC Solver System.

MVP implementation - represents optimal play recommendations and analysis results.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..base import ValueObject
from .expected_value import ExpectedValue
from .card import Card


@dataclass(frozen=True)
class ActionRecommendation(ValueObject):
    """
    Represents a recommended action in OFC.
    
    For Pineapple OFC: place 2 cards, discard 1.
    """
    cards_to_place: List[Card]
    card_to_discard: Card
    expected_value: float
    confidence: float = 0.0
    
    def __str__(self) -> str:
        """String representation."""
        place_str = ", ".join(str(c) for c in self.cards_to_place)
        return f"Place [{place_str}], Discard {self.card_to_discard} (EV: {self.expected_value:.2f})"


@dataclass(frozen=True)
class Strategy(ValueObject):
    """
    Complete strategy recommendation for a position.
    
    MVP version with essential information only.
    """
    # Primary recommendation
    recommended_actions: List[ActionRecommendation]
    expected_value: ExpectedValue
    confidence: float
    calculation_method: str
    
    # Optional metadata
    calculation_time_ms: int = 0
    tree_stats: Optional[Dict[str, Any]] = None
    alternative_actions: Optional[List[ActionRecommendation]] = None
    
    def __post_init__(self):
        """Validate strategy."""
        if self.confidence < 0.0 or self.confidence > 1.0:
            raise ValueError(f"Confidence must be between 0 and 1, got {self.confidence}")
    
    @property
    def primary_action(self) -> Optional[ActionRecommendation]:
        """Get the primary recommended action."""
        return self.recommended_actions[0] if self.recommended_actions else None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "expected_value": self.expected_value.value if self.expected_value else 0,
            "confidence": self.confidence,
            "calculation_method": self.calculation_method,
            "calculation_time_ms": self.calculation_time_ms,
        }
        
        if self.recommended_actions:
            result["recommended_actions"] = [
                {
                    "cards_to_place": [str(c) for c in action.cards_to_place],
                    "card_to_discard": str(action.card_to_discard),
                    "expected_value": action.expected_value,
                    "confidence": action.confidence
                }
                for action in self.recommended_actions
            ]
            
        if self.tree_stats:
            result["tree_stats"] = self.tree_stats
            
        if self.alternative_actions:
            result["alternative_actions"] = [
                {
                    "cards_to_place": [str(c) for c in action.cards_to_place],
                    "card_to_discard": str(action.card_to_discard),
                    "expected_value": action.expected_value,
                    "confidence": action.confidence
                }
                for action in self.alternative_actions
            ]
            
        return result
    
    def __str__(self) -> str:
        """String representation."""
        if self.primary_action:
            return (f"Strategy: {self.primary_action} | "
                   f"Method: {self.calculation_method} | "
                   f"Confidence: {self.confidence:.1%}")
        return f"Strategy: No actions | EV: {self.expected_value.value:.2f}"