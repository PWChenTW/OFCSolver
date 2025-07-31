"""Difficulty Value Object - Placeholder"""
from dataclasses import dataclass
from ..base import ValueObject

@dataclass(frozen=True)
class Difficulty(ValueObject):
    """Difficulty placeholder."""
    level: int
    name: str = "Unknown"