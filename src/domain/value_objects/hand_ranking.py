"""Hand Ranking Value Object - Placeholder"""

from dataclasses import dataclass
from typing import List

from ..base import ValueObject
from ..services.hand_evaluator import HandType
from .card import Card


@dataclass(frozen=True)
class HandRanking(ValueObject):
    """Hand ranking placeholder."""

    hand_type: HandType
    strength_value: int
    kickers: List[int]
    royalty_bonus: int
    cards: List[Card]
