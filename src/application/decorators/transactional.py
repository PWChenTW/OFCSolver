"""Transaction management decorators for command handlers."""
import functools
import logging
from typing import TypeVar, Callable, Any
from contextlib import asynccontextmanager

try:
    from sqlalchemy.ext.asyncio import AsyncSession
    from ...infrastructure.database.session import get_async_session
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    AsyncSession = None
    get_async_session = None
    SQLALCHEMY_AVAILABLE = False


logger = logging.getLogger(__name__)

T = TypeVar('T')


def transactional(isolation_level: str = "READ_COMMITTED"):
    """
    Decorator for managing database transactions in command handlers.
    
    Args:
        isolation_level: Database isolation level (READ_COMMITTED, SERIALIZABLE, etc.)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs) -> T:
            # Get or create session
            session = getattr(self, '_session', None)
            owns_session = False
            
            if session is None and SQLALCHEMY_AVAILABLE:
                # Create new session if handler doesn't have one
                async with get_async_session() as new_session:
                    self._session = new_session
                    owns_session = True
                    
                    try:
                        # Set isolation level
                        await new_session.execute(
                            f"SET TRANSACTION ISOLATION LEVEL {isolation_level}"
                        )
                        
                        # Execute the handler
                        result = await func(self, *args, **kwargs)
                        
                        # Commit transaction
                        await new_session.commit()
                        
                        logger.debug(
                            f"Transaction committed for {func.__name__}"
                        )
                        
                        return result
                        
                    except Exception as e:
                        # Rollback on error
                        await new_session.rollback()
                        logger.error(
                            f"Transaction rolled back for {func.__name__}: {str(e)}"
                        )
                        raise
                    finally:
                        if owns_session:
                            self._session = None
            else:
                # Use existing session or run without transaction if SQLAlchemy unavailable
                return await func(self, *args, **kwargs)
        
        return wrapper
    return decorator


def read_only_transaction():
    """Decorator for read-only transactions with appropriate isolation."""
    return transactional(isolation_level="READ_COMMITTED")


def write_transaction():
    """Decorator for write transactions with stronger isolation."""
    return transactional(isolation_level="REPEATABLE_READ")


class UnitOfWork:
    """
    Unit of Work pattern implementation for managing transactions.
    
    Ensures all repositories within a handler use the same session.
    """
    
    def __init__(self, session=None):
        self._session = session
        self._owns_session = session is None
        self._repositories = {}
    
    async def __aenter__(self):
        if self._owns_session and SQLALCHEMY_AVAILABLE:
            self._session = await get_async_session().__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.rollback()
        else:
            await self.commit()
        
        if self._owns_session and self._session:
            await self._session.close()
    
    async def commit(self):
        """Commit the transaction."""
        if self._session:
            await self._session.commit()
            logger.debug("Unit of work committed")
    
    async def rollback(self):
        """Rollback the transaction."""
        if self._session:
            await self._session.rollback()
            logger.debug("Unit of work rolled back")
    
    @property
    def session(self):
        """Get the current session."""
        return self._session
    
    def register_repository(self, name: str, repository: Any) -> None:
        """Register a repository with this unit of work."""
        self._repositories[name] = repository
        # Inject session into repository
        if hasattr(repository, 'set_session'):
            repository.set_session(self._session)
    
    def get_repository(self, name: str) -> Any:
        """Get a registered repository."""
        return self._repositories.get(name)


@asynccontextmanager
async def transaction_scope(isolation_level: str = "READ_COMMITTED"):
    """
    Context manager for transaction scope.
    
    Usage:
        async with transaction_scope() as session:
            # Perform database operations
            await session.execute(...)
    """
    if not SQLALCHEMY_AVAILABLE:
        yield None
        return
        
    async with get_async_session() as session:
        try:
            # Set isolation level
            await session.execute(
                f"SET TRANSACTION ISOLATION LEVEL {isolation_level}"
            )
            
            yield session
            
            # Commit if no exception
            await session.commit()
            
        except Exception:
            # Rollback on exception
            await session.rollback()
            raise


class TransactionalCommandHandler:
    """
    Base class for command handlers with transaction support.
    
    Automatically manages transactions for handle() method.
    """
    
    def __init__(self, unit_of_work: UnitOfWork = None):
        self._uow = unit_of_work
    
    async def handle_with_transaction(self, command: Any) -> Any:
        """Handle command within a transaction."""
        if self._uow:
            # Use existing unit of work
            return await self.handle(command)
        else:
            # Create new unit of work
            async with UnitOfWork() as uow:
                self._uow = uow
                try:
                    return await self.handle(command)
                finally:
                    self._uow = None
    
    async def handle(self, command: Any) -> Any:
        """Override this method in subclasses."""
        raise NotImplementedError