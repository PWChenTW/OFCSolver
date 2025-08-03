"""Command bus for orchestrating command handling."""
import logging
from typing import Dict, Type, Any, Optional
from datetime import datetime

from ..commands.base import Command, CommandHandler, CommandResult
from ..validators.command_validators import CommandValidatorRegistry
from ..decorators.transactional import UnitOfWork
from ...domain.exceptions.validation_exceptions import ValidationException


logger = logging.getLogger(__name__)


class CommandBus:
    """
    Central command bus for routing commands to handlers.
    
    Provides:
    - Command routing
    - Validation
    - Transaction management
    - Error handling
    - Logging and auditing
    """
    
    def __init__(
        self,
        validator_registry: CommandValidatorRegistry = None,
        enable_validation: bool = True,
        enable_transactions: bool = True
    ):
        self._handlers: Dict[Type[Command], CommandHandler] = {}
        self._validator_registry = validator_registry or CommandValidatorRegistry()
        self._enable_validation = enable_validation
        self._enable_transactions = enable_transactions
        self._middleware = []
    
    def register_handler(
        self,
        command_type: Type[Command],
        handler: CommandHandler
    ) -> None:
        """Register a handler for a command type."""
        self._handlers[command_type] = handler
        logger.info(f"Registered handler for {command_type.__name__}")
    
    def register_middleware(self, middleware: 'CommandMiddleware') -> None:
        """Register middleware for command processing."""
        self._middleware.append(middleware)
    
    async def execute(self, command: Command) -> CommandResult:
        """
        Execute a command through the bus.
        
        Steps:
        1. Run pre-processing middleware
        2. Validate command
        3. Get handler
        4. Execute with transaction (if enabled)
        5. Run post-processing middleware
        6. Return result
        """
        start_time = datetime.utcnow()
        
        try:
            # Run pre-processing middleware
            for middleware in self._middleware:
                command = await middleware.before_command(command)
            
            # Validate command
            if self._enable_validation:
                await self._validate_command(command)
            
            # Get handler
            handler = self._get_handler(type(command))
            if not handler:
                return CommandResult.fail(
                    f"No handler registered for {type(command).__name__}",
                    command.command_id
                )
            
            # Execute command
            if self._enable_transactions and hasattr(handler, 'handle_with_transaction'):
                result = await handler.handle_with_transaction(command)
            else:
                result = await handler.handle(command)
            
            # Run post-processing middleware
            for middleware in reversed(self._middleware):
                result = await middleware.after_command(command, result)
            
            # Log execution
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            logger.info(
                f"Command {type(command).__name__} executed successfully "
                f"in {execution_time:.3f}s"
            )
            
            return result
            
        except ValidationException as e:
            logger.warning(f"Command validation failed: {str(e)}")
            return CommandResult.fail(
                f"Validation error: {str(e)}",
                command.command_id
            )
        except Exception as e:
            logger.error(
                f"Command execution failed for {type(command).__name__}: {str(e)}"
            )
            return CommandResult.fail(
                f"Execution error: {str(e)}",
                command.command_id
            )
    
    async def _validate_command(self, command: Command) -> None:
        """Validate command using registered validators."""
        await self._validator_registry.validate(command)
    
    def _get_handler(self, command_type: Type[Command]) -> Optional[CommandHandler]:
        """Get handler for command type."""
        return self._handlers.get(command_type)


class CommandMiddleware:
    """Base class for command middleware."""
    
    async def before_command(self, command: Command) -> Command:
        """Process command before execution."""
        return command
    
    async def after_command(
        self,
        command: Command,
        result: CommandResult
    ) -> CommandResult:
        """Process result after execution."""
        return result


class LoggingMiddleware(CommandMiddleware):
    """Middleware for logging command execution."""
    
    def __init__(self, audit_logger: Optional[Any] = None):
        self.audit_logger = audit_logger or logger
    
    async def before_command(self, command: Command) -> Command:
        """Log command execution start."""
        self.audit_logger.info(
            f"Executing command: {type(command).__name__} "
            f"[ID: {command.command_id}]"
        )
        return command
    
    async def after_command(
        self,
        command: Command,
        result: CommandResult
    ) -> CommandResult:
        """Log command execution result."""
        status = "SUCCESS" if result.success else "FAILED"
        self.audit_logger.info(
            f"Command result: {type(command).__name__} "
            f"[ID: {command.command_id}] - {status}"
        )
        return result


class MetricsMiddleware(CommandMiddleware):
    """Middleware for collecting command metrics."""
    
    def __init__(self, metrics_collector: Any):
        self.metrics = metrics_collector
        self._start_times = {}
    
    async def before_command(self, command: Command) -> Command:
        """Record command start time."""
        self._start_times[command.command_id] = datetime.utcnow()
        self.metrics.increment(
            'commands_total',
            tags={'command_type': type(command).__name__}
        )
        return command
    
    async def after_command(
        self,
        command: Command,
        result: CommandResult
    ) -> CommandResult:
        """Record command execution metrics."""
        if command.command_id in self._start_times:
            duration = (
                datetime.utcnow() - self._start_times[command.command_id]
            ).total_seconds()
            
            self.metrics.histogram(
                'command_duration_seconds',
                duration,
                tags={'command_type': type(command).__name__}
            )
            
            status_tag = 'success' if result.success else 'failure'
            self.metrics.increment(
                'commands_by_status',
                tags={
                    'command_type': type(command).__name__,
                    'status': status_tag
                }
            )
            
            del self._start_times[command.command_id]
        
        return result


class AuthorizationMiddleware(CommandMiddleware):
    """Middleware for command authorization."""
    
    def __init__(self, authorization_service: Any):
        self.auth_service = authorization_service
    
    async def before_command(self, command: Command) -> Command:
        """Check if user is authorized to execute command."""
        if command.user_id:
            is_authorized = await self.auth_service.can_execute(
                user_id=command.user_id,
                command_type=type(command).__name__
            )
            
            if not is_authorized:
                raise ValidationException(
                    f"User {command.user_id} is not authorized to execute "
                    f"{type(command).__name__}"
                )
        
        return command


class CommandBusBuilder:
    """Builder for creating configured command bus instances."""
    
    def __init__(self):
        self._bus = CommandBus()
        self._handlers = {}
        self._validators = {}
    
    def with_handler(
        self,
        command_type: Type[Command],
        handler: CommandHandler
    ) -> 'CommandBusBuilder':
        """Add a command handler."""
        self._handlers[command_type] = handler
        return self
    
    def with_validator(
        self,
        command_type: Type[Command],
        validator: Any
    ) -> 'CommandBusBuilder':
        """Add a command validator."""
        self._validators[command_type] = validator
        return self
    
    def with_middleware(self, middleware: CommandMiddleware) -> 'CommandBusBuilder':
        """Add middleware."""
        self._bus.register_middleware(middleware)
        return self
    
    def with_logging(self) -> 'CommandBusBuilder':
        """Add logging middleware."""
        self._bus.register_middleware(LoggingMiddleware())
        return self
    
    def with_metrics(self, metrics_collector: Any) -> 'CommandBusBuilder':
        """Add metrics middleware."""
        self._bus.register_middleware(MetricsMiddleware(metrics_collector))
        return self
    
    def with_authorization(self, auth_service: Any) -> 'CommandBusBuilder':
        """Add authorization middleware."""
        self._bus.register_middleware(AuthorizationMiddleware(auth_service))
        return self
    
    def build(self) -> CommandBus:
        """Build the configured command bus."""
        # Register all handlers
        for command_type, handler in self._handlers.items():
            self._bus.register_handler(command_type, handler)
        
        # Register all validators
        validator_registry = CommandValidatorRegistry()
        for command_type, validator in self._validators.items():
            validator_registry.register(command_type, validator)
        
        self._bus._validator_registry = validator_registry
        
        return self._bus