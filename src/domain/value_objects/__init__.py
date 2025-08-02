"""
Domain Value Objects Package

Contains all immutable value objects for the OFC Solver system.
Value objects are compared by their values and have no identity.

Key Value Objects:
- Card: Individual playing card
- Hand: Collection of cards in OFC layout
- Strategy: Optimal play recommendation
- ExpectedValue: EV calculation result
- GameRules: OFC game configuration
- Move: Card placement action
"""

# Game-related value objects
from .card import Card, Rank, Suit
from .card_position import CardPosition
from .confidence_interval import ConfidenceInterval
from .deck import Deck
from .difficulty import Difficulty
from .expected_value import ExpectedValue
from .feedback import Feedback
from .game_rules import GameRules
from .hand import Hand, HandValidationError, InvalidCardPlacementError

# Performance and analysis value objects
from .hand_ranking import HandRanking, HandType
from .move import Move
from .performance import Performance
from .probability import Probability
from .score import Score

# Strategy-related value objects
from .strategy import Strategy

__all__ = [
    # Game value objects
    "Card",
    "Suit",
    "Rank",
    "Hand",
    "HandValidationError", 
    "InvalidCardPlacementError",
    "Deck",
    "GameRules",
    "CardPosition",
    "Move",
    "Score",
    # Strategy value objects
    "Strategy",
    "ExpectedValue",
    "Probability",
    "ConfidenceInterval",
    # Analysis value objects
    "HandRanking",
    "HandType",
    "Difficulty",
    "Performance",
    "Feedback",
]