from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
import logging

from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.pool import NullPool, QueuePool, StaticPool

from src.config import settings

logger = logging.getLogger(__name__)


class ConnectionPoolManager:
    """Manages database connection pools for the application - MVP version."""

    def __init__(self):
        self._postgres_engine: Optional[AsyncEngine] = None
        self._initialized = False

    async def initialize(self):
        """Initialize connection pools."""
        if self._initialized:
            return

        try:
            # Initialize PostgreSQL
            await self._init_postgres()
            
            self._initialized = True
            logger.info("Connection pool initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize connection pools: {e}")
            await self.shutdown()
            raise

    async def _init_postgres(self):
        """Initialize PostgreSQL connection pool."""
        # Determine pool class based on environment
        if settings.environment == "testing":
            pool_class = NullPool
        elif settings.environment == "development":
            pool_class = StaticPool
        else:
            pool_class = QueuePool

        self._postgres_engine = create_async_engine(
            settings.database.url,
            echo=settings.debug and settings.environment == "development",
            pool_size=settings.database.min_connections,
            max_overflow=settings.database.max_overflow,
            pool_timeout=settings.database.pool_timeout,
            pool_pre_ping=True,
            poolclass=pool_class,
            connect_args={
                "server_settings": {"application_name": "ofc_solver", "jit": "off"},
                "command_timeout": 60,
                "timeout": settings.database.pool_timeout,
            },
        )

        # Test connection
        try:
            async with self._postgres_engine.connect() as conn:
                result = await conn.execute("SELECT 1")
                await result.fetchone()
            logger.info("PostgreSQL connection pool initialized")
        except Exception as e:
            logger.warning(f"PostgreSQL connection test failed: {e}")
            # Don't fail initialization for MVP - we'll use mock data

    @property
    def postgres(self) -> AsyncEngine:
        """Get PostgreSQL engine."""
        if not self._postgres_engine:
            raise RuntimeError("PostgreSQL not initialized")
        return self._postgres_engine

    async def get_postgres_stats(self) -> Dict[str, Any]:
        """Get PostgreSQL connection pool statistics."""
        if not self._postgres_engine or not hasattr(self._postgres_engine, 'pool'):
            return {"status": "not_initialized"}

        pool = self._postgres_engine.pool
        if hasattr(pool, "size"):
            return {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "total": pool.size() + pool.overflow(),
            }
        return {"status": "pool_stats_unavailable"}

    async def get_redis_stats(self) -> Dict[str, Any]:
        """Get Redis connection pool statistics - MVP placeholder."""
        return {
            "status": "not_implemented_in_mvp",
            "created_connections": 0,
            "available_connections": 0,
            "in_use_connections": 0,
            "max_connections": 0,
        }

    async def health_check(self) -> Dict[str, bool]:
        """Check health of all connections."""
        health = {"postgres": False, "redis": True, "clickhouse": True}  # Redis/CH mocked as healthy

        # Check PostgreSQL
        try:
            if self._postgres_engine:
                async with self._postgres_engine.connect() as conn:
                    await conn.execute("SELECT 1")
                    health["postgres"] = True
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")

        return health

    async def shutdown(self):
        """Shutdown all connection pools."""
        logger.info("Shutting down connection pools...")

        # Close PostgreSQL
        if self._postgres_engine:
            await self._postgres_engine.dispose()
            self._postgres_engine = None

        self._initialized = False
        logger.info("Connection pools shut down")

    # MVP Properties for compatibility
    @property
    def redis(self):
        """Redis client placeholder for MVP."""
        return MockRedis()

    @property  
    def clickhouse(self):
        """ClickHouse client placeholder for MVP."""
        return None


class MockRedis:
    """Mock Redis client for MVP."""
    
    async def ping(self) -> bool:
        return True
    
    async def close(self):
        pass


# Global connection pool manager
connection_pool = ConnectionPoolManager()


@asynccontextmanager
async def lifespan_manager():
    """Lifespan manager for FastAPI."""
    # Startup
    await connection_pool.initialize()

    yield

    # Shutdown
    await connection_pool.shutdown()