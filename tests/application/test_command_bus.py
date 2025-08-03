"""Integration tests for command bus."""
import pytest
from unittest.mock import Mock, AsyncMock
from uuid import uuid4

from src.application.services.command_bus import (
    CommandBus,
    CommandBusBuilder,
    LoggingMiddleware,
    MetricsMiddleware,
    CommandMiddleware
)
from src.application.commands.base import Command, CommandHandler, CommandResult
from src.application.commands.game_commands import CreateGameCommand
from src.application.validators.command_validators import (
    CommandValidatorRegistry,
    CreateGameCommandValidator
)
from src.domain.value_objects.game_rules import GameRules
from src.domain.exceptions.validation_exceptions import ValidationException


class TestCommand(Command):
    """Test command for testing."""
    def __init__(self, value: str):
        super().__init__()
        self.value = value


class TestCommandHandler(CommandHandler[CommandResult]):
    """Test handler for testing."""
    
    async def handle(self, command: TestCommand) -> CommandResult:
        """Handle test command."""
        if command.value == "error":
            raise Exception("Test error")
        return CommandResult.ok(
            data={"value": command.value},
            command_id=command.command_id
        )


class TestCommandBus:
    """Test CommandBus functionality."""
    
    @pytest.fixture
    def command_bus(self):
        """Create command bus instance."""
        return CommandBus(enable_validation=True, enable_transactions=True)
    
    @pytest.fixture
    def test_handler(self):
        """Create test handler."""
        return TestCommandHandler()
    
    @pytest.mark.asyncio
    async def test_execute_command_success(
        self,
        command_bus,
        test_handler
    ):
        """Test successful command execution."""
        # Arrange
        command_bus.register_handler(TestCommand, test_handler)
        command = TestCommand(value="test_value")
        
        # Act
        result = await command_bus.execute(command)
        
        # Assert
        assert result.success is True
        assert result.data["value"] == "test_value"
        assert result.command_id == command.command_id
    
    @pytest.mark.asyncio
    async def test_execute_command_no_handler(self, command_bus):
        """Test command execution with no registered handler."""
        # Arrange
        command = TestCommand(value="test")
        
        # Act
        result = await command_bus.execute(command)
        
        # Assert
        assert result.success is False
        assert "No handler registered" in result.error
    
    @pytest.mark.asyncio
    async def test_execute_command_handler_error(
        self,
        command_bus,
        test_handler
    ):
        """Test command execution when handler throws error."""
        # Arrange
        command_bus.register_handler(TestCommand, test_handler)
        command = TestCommand(value="error")
        
        # Act
        result = await command_bus.execute(command)
        
        # Assert
        assert result.success is False
        assert "Test error" in result.error
    
    @pytest.mark.asyncio
    async def test_command_validation(self, command_bus):
        """Test command validation."""
        # Arrange
        validator = AsyncMock()
        validator.validate = AsyncMock(
            side_effect=ValidationException("Invalid command")
        )
        
        registry = CommandValidatorRegistry()
        registry.register(TestCommand, validator)
        
        command_bus._validator_registry = registry
        command_bus.register_handler(TestCommand, TestCommandHandler())
        
        command = TestCommand(value="test")
        
        # Act
        result = await command_bus.execute(command)
        
        # Assert
        assert result.success is False
        assert "Invalid command" in result.error
    
    @pytest.mark.asyncio
    async def test_middleware_execution(self, command_bus, test_handler):
        """Test middleware is executed in correct order."""
        # Arrange
        call_order = []
        
        class TestMiddleware1(CommandMiddleware):
            async def before_command(self, command):
                call_order.append("before1")
                return command
            
            async def after_command(self, command, result):
                call_order.append("after1")
                return result
        
        class TestMiddleware2(CommandMiddleware):
            async def before_command(self, command):
                call_order.append("before2")
                return command
            
            async def after_command(self, command, result):
                call_order.append("after2")
                return result
        
        command_bus.register_handler(TestCommand, test_handler)
        command_bus.register_middleware(TestMiddleware1())
        command_bus.register_middleware(TestMiddleware2())
        
        command = TestCommand(value="test")
        
        # Act
        await command_bus.execute(command)
        
        # Assert
        assert call_order == ["before1", "before2", "after2", "after1"]


class TestCommandBusBuilder:
    """Test CommandBusBuilder functionality."""
    
    @pytest.mark.asyncio
    async def test_builder_with_logging(self):
        """Test builder with logging middleware."""
        # Arrange
        builder = CommandBusBuilder()
        bus = (
            builder
            .with_handler(TestCommand, TestCommandHandler())
            .with_logging()
            .build()
        )
        
        command = TestCommand(value="test")
        
        # Act
        result = await bus.execute(command)
        
        # Assert
        assert result.success is True
        assert len(bus._middleware) == 1
        assert isinstance(bus._middleware[0], LoggingMiddleware)
    
    @pytest.mark.asyncio
    async def test_builder_with_metrics(self):
        """Test builder with metrics middleware."""
        # Arrange
        metrics_collector = Mock()
        metrics_collector.increment = Mock()
        metrics_collector.histogram = Mock()
        
        builder = CommandBusBuilder()
        bus = (
            builder
            .with_handler(TestCommand, TestCommandHandler())
            .with_metrics(metrics_collector)
            .build()
        )
        
        command = TestCommand(value="test")
        
        # Act
        result = await bus.execute(command)
        
        # Assert
        assert result.success is True
        metrics_collector.increment.assert_called()
        metrics_collector.histogram.assert_called()
    
    @pytest.mark.asyncio
    async def test_builder_with_validator(self):
        """Test builder with command validator."""
        # Arrange
        validator = AsyncMock()
        validator.validate = AsyncMock()
        
        builder = CommandBusBuilder()
        bus = (
            builder
            .with_handler(TestCommand, TestCommandHandler())
            .with_validator(TestCommand, validator)
            .build()
        )
        
        command = TestCommand(value="test")
        
        # Act
        result = await bus.execute(command)
        
        # Assert
        assert result.success is True
        validator.validate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_builder_complete_setup(self):
        """Test complete command bus setup with builder."""
        # Arrange
        # Mock dependencies
        player_repo = AsyncMock()
        game_repo = AsyncMock()
        
        players = [
            Mock(id="player1", name="Player 1"),
            Mock(id="player2", name="Player 2")
        ]
        player_repo.get_by_id = AsyncMock(
            side_effect=lambda pid: next((p for p in players if p.id == pid), None)
        )
        game_repo.save = AsyncMock()
        
        # Create real handler and validator
        from src.application.handlers.game_command_handlers import (
            CreateGameCommandHandler
        )
        
        handler = CreateGameCommandHandler(
            game_repository=game_repo,
            player_repository=player_repo
        )
        
        validator = CreateGameCommandValidator(player_repository=player_repo)
        
        # Build command bus
        builder = CommandBusBuilder()
        bus = (
            builder
            .with_handler(CreateGameCommand, handler)
            .with_validator(CreateGameCommand, validator)
            .with_logging()
            .build()
        )
        
        # Create command
        command = CreateGameCommand(
            player_ids=["player1", "player2"],
            rules=GameRules(),
            game_variant="standard"
        )
        
        # Act
        result = await bus.execute(command)
        
        # Assert
        assert result.success is True
        assert "game_id" in result.data
        game_repo.save.assert_called_once()