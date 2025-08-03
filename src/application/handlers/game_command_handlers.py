"""Command handlers for game-related operations."""
import logging
from typing import Optional
from uuid import UUID

from ..commands.base import CommandHandler, CommandResult
from ..commands.game_commands import (
    CreateGameCommand,
    PlaceCardCommand,
    StartFantasyLandCommand,
    CompleteRoundCommand,
    ForfeitGameCommand,
    SetFantasyLandCommand,
    DiscardCardCommand
)
from ...domain.entities.game.game import Game
from ...domain.entities.game.player import Player
from ...domain.repositories.game_repository import GameRepository
from ...domain.repositories.player_repository import PlayerRepository
from ...domain.services.game_validator import GameValidator
from ...domain.services.fantasy_land_manager import FantasyLandManager
from ...domain.events.game_events import (
    GameCreatedEvent,
    CardPlacedEvent,
    RoundCompletedEvent,
    GameForfeitedEvent
)
from ...domain.exceptions.game_exceptions import (
    InvalidGameStateError,
    InvalidCardPlacementError,
    PlayerNotFoundError
)


logger = logging.getLogger(__name__)


class CreateGameCommandHandler(CommandHandler[CommandResult]):
    """Handler for creating new OFC games."""
    
    def __init__(
        self,
        game_repository: GameRepository,
        player_repository: PlayerRepository
    ):
        self.game_repository = game_repository
        self.player_repository = player_repository
    
    async def handle(self, command: CreateGameCommand) -> CommandResult:
        """Create a new OFC game."""
        try:
            # Validate players exist
            players = []
            for player_id in command.player_ids:
                player = await self.player_repository.get_by_id(player_id)
                if not player:
                    return CommandResult.fail(
                        f"Player not found: {player_id}",
                        command.command_id
                    )
                players.append(player)
            
            # Create the game
            game = Game.create(
                players=players,
                rules=command.rules,
                variant=command.game_variant
            )
            
            # Save the game
            await self.game_repository.save(game)
            
            # Publish domain event
            game.add_event(GameCreatedEvent(
                game_id=game.id,
                player_ids=command.player_ids,
                variant=command.game_variant,
                timestamp=command.timestamp
            ))
            
            logger.info(f"Game created: {game.id}")
            
            return CommandResult.ok(
                data={"game_id": str(game.id)},
                command_id=command.command_id
            )
            
        except Exception as e:
            logger.error(f"Failed to create game: {str(e)}")
            return CommandResult.fail(
                error=str(e),
                command_id=command.command_id
            )


class PlaceCardCommandHandler(CommandHandler[CommandResult]):
    """Handler for placing cards in OFC game."""
    
    def __init__(
        self,
        game_repository: GameRepository,
        game_validator: GameValidator
    ):
        self.game_repository = game_repository
        self.game_validator = game_validator
    
    async def handle(self, command: PlaceCardCommand) -> CommandResult:
        """Place a card in player's layout."""
        try:
            # Load the game
            game = await self.game_repository.get_by_id(command.game_id)
            if not game:
                return CommandResult.fail(
                    "Game not found",
                    command.command_id
                )
            
            # Validate the placement
            validation_result = await self.game_validator.validate_card_placement(
                game=game,
                player_id=command.player_id,
                card=command.card,
                position=command.position
            )
            
            if not validation_result.is_valid:
                return CommandResult.fail(
                    validation_result.error_message,
                    command.command_id
                )
            
            # Place the card
            game.place_card(
                player_id=command.player_id,
                card=command.card,
                position=command.position
            )
            
            # Save the updated game
            await self.game_repository.save(game)
            
            # Publish domain event
            game.add_event(CardPlacedEvent(
                game_id=game.id,
                player_id=command.player_id,
                card=command.card,
                position=command.position,
                timestamp=command.timestamp
            ))
            
            logger.info(
                f"Card placed in game {game.id}: "
                f"Player {command.player_id} placed {command.card} at {command.position}"
            )
            
            return CommandResult.ok(
                data={
                    "game_id": str(game.id),
                    "is_round_complete": game.is_round_complete()
                },
                command_id=command.command_id
            )
            
        except InvalidCardPlacementError as e:
            return CommandResult.fail(
                error=str(e),
                command_id=command.command_id
            )
        except Exception as e:
            logger.error(f"Failed to place card: {str(e)}")
            return CommandResult.fail(
                error=str(e),
                command_id=command.command_id
            )


class StartFantasyLandCommandHandler(CommandHandler[CommandResult]):
    """Handler for starting fantasy land."""
    
    def __init__(
        self,
        game_repository: GameRepository,
        fantasy_land_manager: FantasyLandManager
    ):
        self.game_repository = game_repository
        self.fantasy_land_manager = fantasy_land_manager
    
    async def handle(self, command: StartFantasyLandCommand) -> CommandResult:
        """Start fantasy land for a player."""
        try:
            # Load the game
            game = await self.game_repository.get_by_id(command.game_id)
            if not game:
                return CommandResult.fail(
                    "Game not found",
                    command.command_id
                )
            
            # Check if player qualifies for fantasy land
            qualifies = await self.fantasy_land_manager.check_fantasy_land_qualification(
                game=game,
                player_id=command.player_id
            )
            
            if not qualifies:
                return CommandResult.fail(
                    "Player does not qualify for fantasy land",
                    command.command_id
                )
            
            # Start fantasy land
            cards = await self.fantasy_land_manager.deal_fantasy_land_cards(
                game=game,
                player_id=command.player_id,
                num_cards=command.cards_to_deal
            )
            
            # Save the updated game
            await self.game_repository.save(game)
            
            logger.info(
                f"Fantasy land started for player {command.player_id} "
                f"in game {game.id} with {command.cards_to_deal} cards"
            )
            
            return CommandResult.ok(
                data={
                    "game_id": str(game.id),
                    "cards_dealt": len(cards)
                },
                command_id=command.command_id
            )
            
        except Exception as e:
            logger.error(f"Failed to start fantasy land: {str(e)}")
            return CommandResult.fail(
                error=str(e),
                command_id=command.command_id
            )


class CompleteRoundCommandHandler(CommandHandler[CommandResult]):
    """Handler for completing a round and calculating scores."""
    
    def __init__(
        self,
        game_repository: GameRepository,
        game_validator: GameValidator
    ):
        self.game_repository = game_repository
        self.game_validator = game_validator
    
    async def handle(self, command: CompleteRoundCommand) -> CommandResult:
        """Complete the current round."""
        try:
            # Load the game
            game = await self.game_repository.get_by_id(command.game_id)
            if not game:
                return CommandResult.fail(
                    "Game not found",
                    command.command_id
                )
            
            # Validate round can be completed
            if not game.is_round_complete():
                return CommandResult.fail(
                    "Round is not complete - not all players have placed their cards",
                    command.command_id
                )
            
            # Calculate scores and complete the round
            round_scores = game.complete_round()
            
            # Save the updated game
            await self.game_repository.save(game)
            
            # Publish domain event
            game.add_event(RoundCompletedEvent(
                game_id=game.id,
                round_number=game.current_round - 1,  # Previous round just completed
                scores=round_scores,
                timestamp=command.timestamp
            ))
            
            logger.info(f"Round completed in game {game.id}")
            
            return CommandResult.ok(
                data={
                    "game_id": str(game.id),
                    "round_scores": round_scores,
                    "is_game_complete": game.is_complete(),
                    "current_round": game.current_round
                },
                command_id=command.command_id
            )
            
        except Exception as e:
            logger.error(f"Failed to complete round: {str(e)}")
            return CommandResult.fail(
                error=str(e),
                command_id=command.command_id
            )


class SetFantasyLandCommandHandler(CommandHandler[CommandResult]):
    """Handler for setting fantasy land card arrangement."""
    
    def __init__(
        self,
        game_repository: GameRepository,
        game_validator: GameValidator,
        fantasy_land_manager: FantasyLandManager
    ):
        self.game_repository = game_repository
        self.game_validator = game_validator
        self.fantasy_land_manager = fantasy_land_manager
    
    async def handle(self, command: SetFantasyLandCommand) -> CommandResult:
        """Set the fantasy land arrangement for a player."""
        try:
            # Load the game
            game = await self.game_repository.get_by_id(command.game_id)
            if not game:
                return CommandResult.fail(
                    "Game not found",
                    command.command_id
                )
            
            # Validate the player is in fantasy land
            player = game.get_player(command.player_id)
            if not player or not player.is_in_fantasy_land:
                return CommandResult.fail(
                    "Player is not in fantasy land",
                    command.command_id
                )
            
            # Validate the arrangement
            is_valid = await self.game_validator.validate_ofc_layout(
                top_cards=command.top_cards,
                middle_cards=command.middle_cards,
                bottom_cards=command.bottom_cards
            )
            
            if not is_valid:
                return CommandResult.fail(
                    "Invalid card arrangement - hands must be in ascending order",
                    command.command_id
                )
            
            # Set the fantasy land arrangement
            await self.fantasy_land_manager.set_fantasy_land_arrangement(
                game=game,
                player_id=command.player_id,
                top_cards=command.top_cards,
                middle_cards=command.middle_cards,
                bottom_cards=command.bottom_cards
            )
            
            # Save the updated game
            await self.game_repository.save(game)
            
            logger.info(
                f"Fantasy land arrangement set for player {command.player_id} "
                f"in game {game.id}"
            )
            
            return CommandResult.ok(
                data={
                    "game_id": str(game.id),
                    "arrangement_set": True
                },
                command_id=command.command_id
            )
            
        except Exception as e:
            logger.error(f"Failed to set fantasy land arrangement: {str(e)}")
            return CommandResult.fail(
                error=str(e),
                command_id=command.command_id
            )