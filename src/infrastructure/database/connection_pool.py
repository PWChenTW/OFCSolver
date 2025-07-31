from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
import logging

from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.pool import NullPool, QueuePool, StaticPool
import redis.asyncio as redis

from src.config import settings
from src.infrastructure.cache.redis_cache import RedisCache
from src.infrastructure.analytics.clickhouse_client import ClickHouseClient

logger = logging.getLogger(__name__)


class ConnectionPoolManager:
    """Manages all database connection pools for the application."""

    def __init__(self):
        self._postgres_engine: Optional[AsyncEngine] = None
        self._redis_pool: Optional[redis.ConnectionPool] = None
        self._redis_client: Optional[RedisCache] = None
        self._clickhouse_client: Optional[ClickHouseClient] = None
        self._initialized = False

    async def initialize(self):
        """Initialize all connection pools."""
        if self._initialized:
            return

        try:
            # Initialize PostgreSQL
            await self._init_postgres()

            # Initialize Redis
            await self._init_redis()

            # Initialize ClickHouse
            await self._init_clickhouse()

            self._initialized = True
            logger.info("All connection pools initialized successfully")

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
        async with self._postgres_engine.connect() as conn:
            result = await conn.execute("SELECT 1")
            await result.fetchone()

        logger.info("PostgreSQL connection pool initialized")

    async def _init_redis(self):
        """Initialize Redis connection pool."""
        self._redis_pool = redis.ConnectionPool(
            host=settings.redis.host,
            port=settings.redis.port,
            db=settings.redis.database,
            password=settings.redis.password,
            max_connections=settings.redis.max_connections,
            decode_responses=False,
            socket_timeout=settings.redis.socket_timeout,
            socket_connect_timeout=settings.redis.socket_timeout,
            retry_on_timeout=settings.redis.retry_on_timeout,
            health_check_interval=30,
        )

        # Create Redis client wrapper
        self._redis_client = RedisCache(connection_pool=self._redis_pool)

        # Test connection
        if not await self._redis_client.ping():
            raise ConnectionError("Failed to connect to Redis")

        logger.info("Redis connection pool initialized")

    async def _init_clickhouse(self):
        """Initialize ClickHouse client."""
        # Determine host based on environment
        ch_host = "clickhouse" if settings.environment == "development" else "localhost"

        self._clickhouse_client = ClickHouseClient(
            host=ch_host,
            port=9000,
            database="ofc_analytics",
            user="default",
            password="",
            connect_timeout=10,
            send_receive_timeout=300,
            sync_request_timeout=5,
            compress_block_size=1048576,
            settings={
                "max_block_size": 65536,
                "max_threads": 4,
                "max_memory_usage": 10000000000,  # 10GB
            },
        )

        # Test connection
        if not await self._clickhouse_client.ping():
            logger.warning("ClickHouse is not available, analytics will be disabled")
            # Don't fail if ClickHouse is not available
            # self._clickhouse_client = None

        logger.info("ClickHouse client initialized")

    @property
    def postgres(self) -> AsyncEngine:
        """Get PostgreSQL engine."""
        if not self._postgres_engine:
            raise RuntimeError("PostgreSQL not initialized")
        return self._postgres_engine

    @property
    def redis(self) -> RedisCache:
        """Get Redis client."""
        if not self._redis_client:
            raise RuntimeError("Redis not initialized")
        return self._redis_client

    @property
    def clickhouse(self) -> Optional[ClickHouseClient]:
        """Get ClickHouse client."""
        return self._clickhouse_client

    async def get_postgres_stats(self) -> Dict[str, Any]:
        """Get PostgreSQL connection pool statistics."""
        if not self._postgres_engine:
            return {}

        pool = self._postgres_engine.pool
        if hasattr(pool, "size"):
            return {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "total": pool.size() + pool.overflow(),
            }
        return {}

    async def get_redis_stats(self) -> Dict[str, Any]:
        """Get Redis connection pool statistics."""
        if not self._redis_pool:
            return {}

        return {
            "created_connections": self._redis_pool.created_connections,
            "available_connections": len(self._redis_pool._available_connections),
            "in_use_connections": len(self._redis_pool._in_use_connections),
            "max_connections": self._redis_pool.max_connections,
        }

    async def health_check(self) -> Dict[str, bool]:
        """Check health of all connections."""
        health = {"postgres": False, "redis": False, "clickhouse": False}

        # Check PostgreSQL
        try:
            async with self._postgres_engine.connect() as conn:
                await conn.execute("SELECT 1")
                health["postgres"] = True
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")

        # Check Redis
        try:
            health["redis"] = await self._redis_client.ping()
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")

        # Check ClickHouse
        try:
            if self._clickhouse_client:
                health["clickhouse"] = await self._clickhouse_client.ping()
        except Exception as e:
            logger.error(f"ClickHouse health check failed: {e}")

        return health

    async def shutdown(self):
        """Shutdown all connection pools."""
        logger.info("Shutting down connection pools...")

        # Close PostgreSQL
        if self._postgres_engine:
            await self._postgres_engine.dispose()
            self._postgres_engine = None

        # Close Redis
        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None

        if self._redis_pool:
            await self._redis_pool.disconnect()
            self._redis_pool = None

        # Close ClickHouse
        if self._clickhouse_client:
            await self._clickhouse_client.close()
            self._clickhouse_client = None

        self._initialized = False
        logger.info("All connection pools shut down")


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
