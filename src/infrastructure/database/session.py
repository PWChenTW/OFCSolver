from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool, QueuePool

from src.config import settings


class DatabaseSession:
    """Database session manager."""
    
    def __init__(self):
        self._engine = None
        self._sessionmaker = None
        
    def init(self):
        """Initialize database engine and session maker."""
        # Create engine with appropriate pool settings
        if settings.environment == "testing":
            # Use NullPool for testing to avoid connection issues
            pool_class = NullPool
        else:
            pool_class = QueuePool
            
        self._engine = create_async_engine(
            settings.database.url,
            echo=settings.debug and settings.environment == "development",
            pool_size=settings.database.min_connections,
            max_overflow=settings.database.max_overflow,
            pool_timeout=settings.database.pool_timeout,
            pool_pre_ping=True,  # Enable connection health checks
            poolclass=pool_class,
        )
        
        self._sessionmaker = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,  # Don't expire objects after commit
            autocommit=False,
            autoflush=False,
        )
        
    async def close(self):
        """Close database connections."""
        if self._engine:
            await self._engine.dispose()
            
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session as async context manager."""
        if not self._sessionmaker:
            raise RuntimeError("Database session not initialized. Call init() first.")
            
        async with self._sessionmaker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
                
    async def get_db(self) -> AsyncGenerator[AsyncSession, None]:
        """Dependency for FastAPI to get database session."""
        async with self.get_session() as session:
            yield session


# Global database session instance
db_session = DatabaseSession()


# Dependency for FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for dependency injection."""
    async with db_session.get_session() as session:
        yield session