"""Game Rules Value Object - Placeholder"""
from dataclasses import dataclass
from ..base import ValueObject

@dataclass(frozen=True)
class GameRules(ValueObject):
    """Game rules placeholder."""
    variant: str = "standard"
    
    def to_dict(self) -> dict:
        return {'variant': self.variant}