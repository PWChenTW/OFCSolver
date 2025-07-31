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
from .card import Card, Suit, Rank
from .hand import Hand
from .deck import Deck
from .game_rules import GameRules
from .card_position import CardPosition
from .move import Move
from .score import Score

# Strategy-related value objects  
from .strategy import Strategy
from .expected_value import ExpectedValue
from .probability import Probability
from .confidence_interval import ConfidenceInterval

# Performance and analysis value objects
from .hand_ranking import HandRanking
from .difficulty import Difficulty
from .performance import Performance
from .feedback import Feedback

__all__ = [
    # Game value objects
    "Card",
    "Suit", 
    "Rank",
    "Hand",
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
    "Difficulty",
    "Performance", 
    "Feedback",
]