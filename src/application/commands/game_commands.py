"""Game-related commands for the OFC Solver system."""
from dataclasses import dataclass
from typing import List, Dict, Optional
from uuid import UUID

from .base import Command
from ...domain.value_objects.card import Card
from ...domain.value_objects.card_position import CardPosition
from ...domain.value_objects.game_rules import GameRules


@dataclass
class CreateGameCommand(Command):
    """Command to create a new OFC game."""
    player_ids: List[str]
    rules: GameRules
    game_variant: str = "standard"  # standard, pineapple, etc.
    
    def __post_init__(self):
        super().__init__()  # Initialize command fields
        if len(self.player_ids) < 2:
            raise ValueError("At least 2 players required")
        if len(self.player_ids) > 4:
            raise ValueError("Maximum 4 players allowed")


@dataclass
class PlaceCardCommand(Command):
    """Command to place a card in a player's layout."""
    game_id: UUID
    player_id: str
    card: Card
    position: CardPosition
    
    def __post_init__(self):
        super().__init__()  # Initialize command fields
        if not self.game_id:
            raise ValueError("Game ID is required")
        if not self.player_id:
            raise ValueError("Player ID is required")


@dataclass
class StartFantasyLandCommand(Command):
    """Command to start fantasy land for a player."""
    game_id: UUID
    player_id: str
    cards_to_deal: int = 14  # Standard fantasy land cards
    
    def __post_init__(self):
        super().__init__()  # Initialize command fields
        if self.cards_to_deal not in [13, 14, 15]:
            raise ValueError("Fantasy land cards must be 13, 14, or 15")


@dataclass
class CompleteRoundCommand(Command):
    """Command to complete a round and calculate scores."""
    game_id: UUID
    
    def __post_init__(self):
        super().__init__()  # Initialize command fields
        if not self.game_id:
            raise ValueError("Game ID is required")


@dataclass
class ForfeitGameCommand(Command):
    """Command for a player to forfeit the game."""
    game_id: UUID
    player_id: str
    
    def __post_init__(self):
        super().__init__()  # Initialize command fields
        if not self.game_id:
            raise ValueError("Game ID is required")
        if not self.player_id:
            raise ValueError("Player ID is required")


@dataclass
class SetFantasyLandCommand(Command):
    """Command to set fantasy land arrangement for a player."""
    game_id: UUID
    player_id: str
    top_cards: List[Card]
    middle_cards: List[Card]
    bottom_cards: List[Card]
    
    def __post_init__(self):
        super().__init__()  # Initialize command fields
        if len(self.top_cards) != 3:
            raise ValueError("Top row must have exactly 3 cards")
        if len(self.middle_cards) != 5:
            raise ValueError("Middle row must have exactly 5 cards")
        if len(self.bottom_cards) != 5:
            raise ValueError("Bottom row must have exactly 5 cards")


@dataclass
class DiscardCardCommand(Command):
    """Command to discard a card (for Pineapple variant)."""
    game_id: UUID
    player_id: str
    card: Card
    
    def __post_init__(self):
        super().__init__()  # Initialize command fields
        if not self.game_id:
            raise ValueError("Game ID is required")
        if not self.player_id:
            raise ValueError("Player ID is required")