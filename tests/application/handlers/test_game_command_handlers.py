"""Integration tests for game command handlers."""
import pytest
from unittest.mock import Mock, AsyncMock
from uuid import uuid4

from src.application.commands.game_commands import (
    CreateGameCommand,
    PlaceCardCommand,
    CompleteRoundCommand,
    SetFantasyLandCommand
)
from src.application.handlers.game_command_handlers import (
    CreateGameCommandHandler,
    PlaceCardCommandHandler,
    CompleteRoundCommandHandler,
    SetFantasyLandCommandHandler
)
from src.domain.entities.game.game import Game
from src.domain.entities.game.player import Player
from src.domain.value_objects.card import Card, Rank, Suit
from src.domain.value_objects.card_position import CardPosition
from src.domain.value_objects.game_rules import GameRules
from src.domain.exceptions.game_exceptions import InvalidCardPlacementError


class TestCreateGameCommandHandler:
    """Test CreateGameCommand handler."""
    
    @pytest.fixture
    def mock_game_repository(self):
        """Create mock game repository."""
        repo = AsyncMock()
        repo.save = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_player_repository(self):
        """Create mock player repository."""
        repo = AsyncMock()
        # Create mock players
        players = [
            Mock(id="player1", name="Player 1"),
            Mock(id="player2", name="Player 2")
        ]
        repo.get_by_id = AsyncMock(side_effect=lambda pid: 
            next((p for p in players if p.id == pid), None)
        )
        return repo
    
    @pytest.fixture
    def handler(self, mock_game_repository, mock_player_repository):
        """Create handler instance."""
        return CreateGameCommandHandler(
            game_repository=mock_game_repository,
            player_repository=mock_player_repository
        )
    
    @pytest.mark.asyncio
    async def test_create_game_success(self, handler, mock_game_repository):
        """Test successful game creation."""
        # Arrange
        command = CreateGameCommand(
            player_ids=["player1", "player2"],
            rules=GameRules(),
            game_variant="standard"
        )
        
        # Act
        result = await handler.handle(command)
        
        # Assert
        assert result.success is True
        assert "game_id" in result.data
        assert mock_game_repository.save.called
    
    @pytest.mark.asyncio
    async def test_create_game_player_not_found(self, handler):
        """Test game creation fails when player not found."""
        # Arrange
        command = CreateGameCommand(
            player_ids=["player1", "invalid_player"],
            rules=GameRules(),
            game_variant="standard"
        )
        
        # Act
        result = await handler.handle(command)
        
        # Assert
        assert result.success is False
        assert "Player not found" in result.error
    
    @pytest.mark.asyncio
    async def test_create_game_validates_player_count(self, handler):
        """Test game creation validates player count."""
        # Arrange - too few players
        command = CreateGameCommand(
            player_ids=["player1"],
            rules=GameRules(),
            game_variant="standard"
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="At least 2 players required"):
            command = CreateGameCommand(
                player_ids=["player1"],
                rules=GameRules(),
                game_variant="standard"
            )


class TestPlaceCardCommandHandler:
    """Test PlaceCardCommand handler."""
    
    @pytest.fixture
    def mock_game(self):
        """Create mock game."""
        game = Mock(spec=Game)
        game.id = uuid4()
        game.place_card = Mock()
        game.is_round_complete = Mock(return_value=False)
        game.add_event = Mock()
        return game
    
    @pytest.fixture
    def mock_game_repository(self, mock_game):
        """Create mock game repository."""
        repo = AsyncMock()
        repo.get_by_id = AsyncMock(return_value=mock_game)
        repo.save = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_game_validator(self):
        """Create mock game validator."""
        validator = AsyncMock()
        validation_result = Mock()
        validation_result.is_valid = True
        validation_result.error_message = None
        validator.validate_card_placement = AsyncMock(return_value=validation_result)
        return validator
    
    @pytest.fixture
    def handler(self, mock_game_repository, mock_game_validator):
        """Create handler instance."""
        return PlaceCardCommandHandler(
            game_repository=mock_game_repository,
            game_validator=mock_game_validator
        )
    
    @pytest.mark.asyncio
    async def test_place_card_success(self, handler, mock_game):
        """Test successful card placement."""
        # Arrange
        command = PlaceCardCommand(
            game_id=mock_game.id,
            player_id="player1",
            card=Card(rank=Rank.ACE, suit=Suit.SPADES),
            position=CardPosition(row="bottom", index=0)
        )
        
        # Act
        result = await handler.handle(command)
        
        # Assert
        assert result.success is True
        assert result.data["game_id"] == str(mock_game.id)
        assert mock_game.place_card.called
    
    @pytest.mark.asyncio
    async def test_place_card_game_not_found(self, handler, mock_game_repository):
        """Test card placement fails when game not found."""
        # Arrange
        mock_game_repository.get_by_id = AsyncMock(return_value=None)
        command = PlaceCardCommand(
            game_id=uuid4(),
            player_id="player1",
            card=Card(rank=Rank.ACE, suit=Suit.SPADES),
            position=CardPosition(row="bottom", index=0)
        )
        
        # Act
        result = await handler.handle(command)
        
        # Assert
        assert result.success is False
        assert "Game not found" in result.error
    
    @pytest.mark.asyncio
    async def test_place_card_invalid_placement(self, handler, mock_game_validator):
        """Test card placement fails validation."""
        # Arrange
        validation_result = Mock()
        validation_result.is_valid = False
        validation_result.error_message = "Invalid card placement"
        mock_game_validator.validate_card_placement = AsyncMock(
            return_value=validation_result
        )
        
        command = PlaceCardCommand(
            game_id=uuid4(),
            player_id="player1",
            card=Card(rank=Rank.ACE, suit=Suit.SPADES),
            position=CardPosition(row="bottom", index=0)
        )
        
        # Act
        result = await handler.handle(command)
        
        # Assert
        assert result.success is False
        assert "Invalid card placement" in result.error


class TestCompleteRoundCommandHandler:
    """Test CompleteRoundCommand handler."""
    
    @pytest.fixture
    def mock_game(self):
        """Create mock game."""
        game = Mock(spec=Game)
        game.id = uuid4()
        game.is_round_complete = Mock(return_value=True)
        game.complete_round = Mock(return_value={"player1": 10, "player2": -10})
        game.is_complete = Mock(return_value=False)
        game.current_round = 2
        game.add_event = Mock()
        return game
    
    @pytest.fixture
    def mock_game_repository(self, mock_game):
        """Create mock game repository."""
        repo = AsyncMock()
        repo.get_by_id = AsyncMock(return_value=mock_game)
        repo.save = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_game_validator(self):
        """Create mock game validator."""
        return AsyncMock()
    
    @pytest.fixture
    def handler(self, mock_game_repository, mock_game_validator):
        """Create handler instance."""
        return CompleteRoundCommandHandler(
            game_repository=mock_game_repository,
            game_validator=mock_game_validator
        )
    
    @pytest.mark.asyncio
    async def test_complete_round_success(self, handler, mock_game):
        """Test successful round completion."""
        # Arrange
        command = CompleteRoundCommand(game_id=mock_game.id)
        
        # Act
        result = await handler.handle(command)
        
        # Assert
        assert result.success is True
        assert result.data["round_scores"] == {"player1": 10, "player2": -10}
        assert result.data["current_round"] == 2
        assert mock_game.complete_round.called
    
    @pytest.mark.asyncio
    async def test_complete_round_not_ready(self, handler, mock_game):
        """Test round completion fails when round not complete."""
        # Arrange
        mock_game.is_round_complete = Mock(return_value=False)
        command = CompleteRoundCommand(game_id=mock_game.id)
        
        # Act
        result = await handler.handle(command)
        
        # Assert
        assert result.success is False
        assert "Round is not complete" in result.error


class TestSetFantasyLandCommandHandler:
    """Test SetFantasyLandCommand handler."""
    
    @pytest.fixture
    def mock_player(self):
        """Create mock player in fantasy land."""
        player = Mock(spec=Player)
        player.id = "player1"
        player.is_in_fantasy_land = True
        player.fantasy_land_cards = [
            Card(rank=Rank.ACE, suit=Suit.SPADES),
            Card(rank=Rank.ACE, suit=Suit.HEARTS),
            Card(rank=Rank.ACE, suit=Suit.DIAMONDS),
            Card(rank=Rank.KING, suit=Suit.SPADES),
            Card(rank=Rank.KING, suit=Suit.HEARTS),
            Card(rank=Rank.QUEEN, suit=Suit.SPADES),
            Card(rank=Rank.QUEEN, suit=Suit.HEARTS),
            Card(rank=Rank.JACK, suit=Suit.SPADES),
            Card(rank=Rank.TEN, suit=Suit.SPADES),
            Card(rank=Rank.NINE, suit=Suit.SPADES),
            Card(rank=Rank.EIGHT, suit=Suit.SPADES),
            Card(rank=Rank.SEVEN, suit=Suit.SPADES),
            Card(rank=Rank.SIX, suit=Suit.SPADES),
        ]
        return player
    
    @pytest.fixture
    def mock_game(self, mock_player):
        """Create mock game."""
        game = Mock(spec=Game)
        game.id = uuid4()
        game.get_player = Mock(return_value=mock_player)
        return game
    
    @pytest.fixture
    def mock_game_repository(self, mock_game):
        """Create mock game repository."""
        repo = AsyncMock()
        repo.get_by_id = AsyncMock(return_value=mock_game)
        repo.save = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_game_validator(self):
        """Create mock game validator."""
        validator = AsyncMock()
        validator.validate_ofc_layout = AsyncMock(return_value=True)
        return validator
    
    @pytest.fixture
    def mock_fantasy_land_manager(self):
        """Create mock fantasy land manager."""
        manager = AsyncMock()
        manager.set_fantasy_land_arrangement = AsyncMock()
        return manager
    
    @pytest.fixture
    def handler(
        self,
        mock_game_repository,
        mock_game_validator,
        mock_fantasy_land_manager
    ):
        """Create handler instance."""
        return SetFantasyLandCommandHandler(
            game_repository=mock_game_repository,
            game_validator=mock_game_validator,
            fantasy_land_manager=mock_fantasy_land_manager
        )
    
    @pytest.mark.asyncio
    async def test_set_fantasy_land_success(self, handler, mock_game, mock_player):
        """Test successful fantasy land arrangement."""
        # Arrange
        fl_cards = mock_player.fantasy_land_cards
        command = SetFantasyLandCommand(
            game_id=mock_game.id,
            player_id="player1",
            top_cards=fl_cards[:3],
            middle_cards=fl_cards[3:8],
            bottom_cards=fl_cards[8:13]
        )
        
        # Act
        result = await handler.handle(command)
        
        # Assert
        assert result.success is True
        assert result.data["arrangement_set"] is True
    
    @pytest.mark.asyncio
    async def test_set_fantasy_land_invalid_layout(
        self,
        handler,
        mock_game,
        mock_player,
        mock_game_validator
    ):
        """Test fantasy land arrangement with invalid layout."""
        # Arrange
        mock_game_validator.validate_ofc_layout = AsyncMock(return_value=False)
        fl_cards = mock_player.fantasy_land_cards
        
        command = SetFantasyLandCommand(
            game_id=mock_game.id,
            player_id="player1",
            top_cards=fl_cards[:3],
            middle_cards=fl_cards[3:8],
            bottom_cards=fl_cards[8:13]
        )
        
        # Act
        result = await handler.handle(command)
        
        # Assert
        assert result.success is False
        assert "Invalid card arrangement" in result.error