"""Command validators for ensuring command integrity."""
from typing import Optional, Set
import re

from ..commands.base import Command, CommandValidator
from ..commands.game_commands import (
    CreateGameCommand,
    PlaceCardCommand,
    SetFantasyLandCommand
)
from ..commands.analysis_commands import (
    RequestAnalysisCommand,
    BatchAnalysisCommand
)
from ..commands.training_commands import (
    StartTrainingSessionCommand,
    SubmitTrainingMoveCommand
)
from ...domain.repositories.game_repository import GameRepository
from ...domain.repositories.player_repository import PlayerRepository
from ...domain.exceptions.validation_exceptions import ValidationException
from ...domain.value_objects.card import Card, Rank, Suit


class CreateGameCommandValidator(CommandValidator):
    """Validator for CreateGameCommand."""
    
    def __init__(self, player_repository: PlayerRepository):
        self.player_repository = player_repository
    
    async def validate(self, command: CreateGameCommand) -> None:
        """Validate create game command."""
        # Validate player count
        if len(command.player_ids) < 2:
            raise ValidationException("At least 2 players are required")
        
        if len(command.player_ids) > 4:
            raise ValidationException("Maximum 4 players allowed")
        
        # Check for duplicate players
        if len(set(command.player_ids)) != len(command.player_ids):
            raise ValidationException("Duplicate player IDs found")
        
        # Validate each player exists
        for player_id in command.player_ids:
            player = await self.player_repository.get_by_id(player_id)
            if not player:
                raise ValidationException(f"Player not found: {player_id}")
        
        # Validate game variant
        valid_variants = ["standard", "pineapple", "progressive_pineapple"]
        if command.game_variant not in valid_variants:
            raise ValidationException(
                f"Invalid game variant: {command.game_variant}. "
                f"Must be one of: {', '.join(valid_variants)}"
            )
        
        # Validate rules
        if not command.rules:
            raise ValidationException("Game rules must be specified")


class PlaceCardCommandValidator(CommandValidator):
    """Validator for PlaceCardCommand."""
    
    def __init__(self, game_repository: GameRepository):
        self.game_repository = game_repository
    
    async def validate(self, command: PlaceCardCommand) -> None:
        """Validate place card command."""
        # Validate game exists
        game = await self.game_repository.get_by_id(command.game_id)
        if not game:
            raise ValidationException("Game not found")
        
        # Validate player is in the game
        player_ids = [p.id for p in game.players]
        if command.player_id not in player_ids:
            raise ValidationException("Player is not in this game")
        
        # Validate it's the player's turn
        current_player = game.get_current_player()
        if current_player.id != command.player_id:
            raise ValidationException("It's not this player's turn")
        
        # Validate card
        if not self._is_valid_card(command.card):
            raise ValidationException(f"Invalid card: {command.card}")
        
        # Validate card is available
        if not game.is_card_available(command.card):
            raise ValidationException("Card is not available in the deck")
        
        # Validate position
        valid_rows = ["top", "middle", "bottom"]
        if command.position.row not in valid_rows:
            raise ValidationException(
                f"Invalid row: {command.position.row}. "
                f"Must be one of: {', '.join(valid_rows)}"
            )
        
        # Validate position index
        player = game.get_player(command.player_id)
        current_row_cards = len(player.get_row_cards(command.position.row))
        max_cards = {"top": 3, "middle": 5, "bottom": 5}
        
        if current_row_cards >= max_cards[command.position.row]:
            raise ValidationException(
                f"{command.position.row.capitalize()} row is already full"
            )
    
    def _is_valid_card(self, card: Card) -> bool:
        """Check if card is valid."""
        return (
            card.rank in Rank and
            card.suit in Suit and
            not card.is_joker  # Standard OFC doesn't use jokers
        )


class SetFantasyLandCommandValidator(CommandValidator):
    """Validator for SetFantasyLandCommand."""
    
    def __init__(self, game_repository: GameRepository):
        self.game_repository = game_repository
    
    async def validate(self, command: SetFantasyLandCommand) -> None:
        """Validate fantasy land arrangement command."""
        # Validate game exists
        game = await self.game_repository.get_by_id(command.game_id)
        if not game:
            raise ValidationException("Game not found")
        
        # Validate player is in fantasy land
        player = game.get_player(command.player_id)
        if not player:
            raise ValidationException("Player not found in game")
        
        if not player.is_in_fantasy_land:
            raise ValidationException("Player is not in fantasy land")
        
        # Validate card counts
        if len(command.top_cards) != 3:
            raise ValidationException("Top row must have exactly 3 cards")
        
        if len(command.middle_cards) != 5:
            raise ValidationException("Middle row must have exactly 5 cards")
        
        if len(command.bottom_cards) != 5:
            raise ValidationException("Bottom row must have exactly 5 cards")
        
        # Check for duplicate cards
        all_cards = command.top_cards + command.middle_cards + command.bottom_cards
        if len(set(all_cards)) != len(all_cards):
            raise ValidationException("Duplicate cards found in arrangement")
        
        # Validate all cards are from player's fantasy land cards
        player_fl_cards = set(player.fantasy_land_cards)
        submitted_cards = set(all_cards)
        
        if submitted_cards != player_fl_cards:
            raise ValidationException(
                "Submitted cards don't match player's fantasy land cards"
            )


class RequestAnalysisCommandValidator(CommandValidator):
    """Validator for RequestAnalysisCommand."""
    
    async def validate(self, command: RequestAnalysisCommand) -> None:
        """Validate analysis request command."""
        # Validate analysis type
        valid_types = ["optimal", "monte_carlo", "heuristic"]
        if command.analysis_type not in valid_types:
            raise ValidationException(
                f"Invalid analysis type: {command.analysis_type}. "
                f"Must be one of: {', '.join(valid_types)}"
            )
        
        # Validate calculation depth
        if command.calculation_depth < 1 or command.calculation_depth > 10:
            raise ValidationException(
                "Calculation depth must be between 1 and 10"
            )
        
        # Validate timeout
        if command.max_calculation_time_seconds < 1:
            raise ValidationException(
                "Maximum calculation time must be at least 1 second"
            )
        
        if command.max_calculation_time_seconds > 600:
            raise ValidationException(
                "Maximum calculation time cannot exceed 600 seconds (10 minutes)"
            )
        
        # Validate position
        if not command.position:
            raise ValidationException("Position is required")
        
        # Validate position has valid data
        if not command.position.players_hands:
            raise ValidationException("Position must have player hands")
        
        # Validate priority
        if command.priority < -10 or command.priority > 10:
            raise ValidationException("Priority must be between -10 and 10")


class BatchAnalysisCommandValidator(CommandValidator):
    """Validator for BatchAnalysisCommand."""
    
    async def validate(self, command: BatchAnalysisCommand) -> None:
        """Validate batch analysis command."""
        # Validate positions count
        if not command.positions:
            raise ValidationException("At least one position is required")
        
        if len(command.positions) > 100:
            raise ValidationException(
                "Maximum 100 positions allowed in a batch"
            )
        
        # Validate analysis type
        valid_types = ["optimal", "monte_carlo", "heuristic"]
        if command.analysis_type not in valid_types:
            raise ValidationException(
                f"Invalid analysis type: {command.analysis_type}"
            )
        
        # Validate max parallel
        if command.max_parallel < 1 or command.max_parallel > 10:
            raise ValidationException(
                "Max parallel must be between 1 and 10"
            )
        
        # Validate each position
        for i, position in enumerate(command.positions):
            if not position.players_hands:
                raise ValidationException(
                    f"Position {i} must have player hands"
                )


class SubmitTrainingMoveCommandValidator(CommandValidator):
    """Validator for SubmitTrainingMoveCommand."""
    
    async def validate(self, command: SubmitTrainingMoveCommand) -> None:
        """Validate training move submission."""
        # Validate IDs
        if not command.session_id:
            raise ValidationException("Session ID is required")
        
        if not command.scenario_id:
            raise ValidationException("Scenario ID is required")
        
        # Validate time taken
        if command.time_taken_seconds < 0:
            raise ValidationException("Time taken cannot be negative")
        
        if command.time_taken_seconds > 3600:  # 1 hour
            raise ValidationException(
                "Time taken seems unrealistic (> 1 hour)"
            )
        
        # Validate card
        if not command.card:
            raise ValidationException("Card is required")
        
        # Validate position
        if not command.position:
            raise ValidationException("Position is required")
        
        valid_rows = ["top", "middle", "bottom"]
        if command.position.row not in valid_rows:
            raise ValidationException(f"Invalid row: {command.position.row}")


class CommandValidatorRegistry:
    """Registry for command validators."""
    
    def __init__(self):
        self._validators: dict[type[Command], CommandValidator] = {}
    
    def register(
        self,
        command_type: type[Command],
        validator: CommandValidator
    ) -> None:
        """Register a validator for a command type."""
        self._validators[command_type] = validator
    
    def get_validator(
        self,
        command_type: type[Command]
    ) -> Optional[CommandValidator]:
        """Get validator for a command type."""
        return self._validators.get(command_type)
    
    async def validate(self, command: Command) -> None:
        """Validate a command using registered validator."""
        validator = self.get_validator(type(command))
        if validator:
            await validator.validate(command)