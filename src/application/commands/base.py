"""Base command classes and interfaces for CQRS pattern."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Generic, TypeVar, Optional, Any
from uuid import UUID, uuid4


TResult = TypeVar('TResult')


class Command(ABC):
    """Base class for all commands."""
    
    def __init__(self, user_id: Optional[str] = None):
        self.user_id = user_id
        self.command_id = uuid4()
        self.timestamp = datetime.utcnow()


class CommandHandler(ABC, Generic[TResult]):
    """Base interface for command handlers."""
    
    @abstractmethod
    async def handle(self, command: Command) -> TResult:
        """Execute the command and return the result."""
        pass


class CommandValidator(ABC):
    """Base interface for command validators."""
    
    @abstractmethod
    async def validate(self, command: Command) -> None:
        """
        Validate the command.
        
        Raises:
            ValidationException: If validation fails
        """
        pass


@dataclass
class CommandResult:
    """Standard result for command execution."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    command_id: Optional[UUID] = None
    
    @classmethod
    def ok(cls, data: Any = None, command_id: UUID = None) -> 'CommandResult':
        """Create a successful result."""
        return cls(success=True, data=data, command_id=command_id)
    
    @classmethod
    def fail(cls, error: str, command_id: UUID = None) -> 'CommandResult':
        """Create a failed result."""
        return cls(success=False, error=error, command_id=command_id)