from typing import Any, Optional, Union
import json
import redis
from redis import Redis
from redis.connection import ConnectionPool
import pickle
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis cache implementation for OFC Solver System."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        decode_responses: bool = False,
        max_connections: int = 50,
        socket_timeout: int = 5,
        connection_pool: Optional[ConnectionPool] = None,
    ):
        """Initialize Redis cache client.

        Args:
            host: Redis server host
            port: Redis server port
            db: Redis database number
            password: Redis password if authentication is required
            decode_responses: Whether to decode responses to strings
            max_connections: Maximum number of connections in the pool
            socket_timeout: Socket timeout in seconds
            connection_pool: Existing connection pool to use
        """
        if connection_pool:
            self.redis_client = Redis(connection_pool=connection_pool)
        else:
            self.redis_client = Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=decode_responses,
                max_connections=max_connections,
                socket_timeout=socket_timeout,
            )

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        try:
            value = self.redis_client.get(key)
            if value is None:
                return None

            # Try to deserialize as JSON first
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # If JSON fails, try pickle
                try:
                    return pickle.loads(value)
                except (pickle.PickleError, TypeError):
                    # Return as string if both fail
                    return value.decode("utf-8") if isinstance(value, bytes) else value

        except redis.RedisError as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        expire: Optional[Union[int, timedelta]] = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            expire: Expiration time in seconds or timedelta
            nx: Only set if key doesn't exist
            xx: Only set if key exists

        Returns:
            True if set successfully, False otherwise
        """
        try:
            # Serialize value
            if isinstance(value, (str, int, float, bytes)):
                serialized_value = value
            else:
                # Try JSON first for better interoperability
                try:
                    serialized_value = json.dumps(value)
                except (TypeError, ValueError):
                    # Fall back to pickle for complex objects
                    serialized_value = pickle.dumps(value)

            result = self.redis_client.set(
                key, serialized_value, ex=expire, nx=nx, xx=xx
            )
            return bool(result)

        except redis.RedisError as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False

    def delete(self, *keys: str) -> int:
        """Delete one or more keys from cache.

        Args:
            *keys: Cache keys to delete

        Returns:
            Number of keys deleted
        """
        try:
            return self.redis_client.delete(*keys)
        except redis.RedisError as e:
            logger.error(f"Redis delete error for keys {keys}: {e}")
            return 0

    def exists(self, *keys: str) -> int:
        """Check if keys exist in cache.

        Args:
            *keys: Cache keys to check

        Returns:
            Number of keys that exist
        """
        try:
            return self.redis_client.exists(*keys)
        except redis.RedisError as e:
            logger.error(f"Redis exists error for keys {keys}: {e}")
            return 0

    def expire(self, key: str, time: Union[int, timedelta]) -> bool:
        """Set expiration time for a key.

        Args:
            key: Cache key
            time: Expiration time in seconds or timedelta

        Returns:
            True if expiration was set, False otherwise
        """
        try:
            return bool(self.redis_client.expire(key, time))
        except redis.RedisError as e:
            logger.error(f"Redis expire error for key {key}: {e}")
            return False

    def ttl(self, key: str) -> int:
        """Get time to live for a key.

        Args:
            key: Cache key

        Returns:
            TTL in seconds, -1 if key exists but has no TTL, -2 if key doesn't exist
        """
        try:
            return self.redis_client.ttl(key)
        except redis.RedisError as e:
            logger.error(f"Redis ttl error for key {key}: {e}")
            return -2

    def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment value by amount.

        Args:
            key: Cache key
            amount: Amount to increment by

        Returns:
            New value after increment or None on error
        """
        try:
            return self.redis_client.incr(key, amount)
        except redis.RedisError as e:
            logger.error(f"Redis incr error for key {key}: {e}")
            return None

    def decr(self, key: str, amount: int = 1) -> Optional[int]:
        """Decrement value by amount.

        Args:
            key: Cache key
            amount: Amount to decrement by

        Returns:
            New value after decrement or None on error
        """
        try:
            return self.redis_client.decr(key, amount)
        except redis.RedisError as e:
            logger.error(f"Redis decr error for key {key}: {e}")
            return None

    def hget(self, name: str, key: str) -> Optional[Any]:
        """Get value from hash.

        Args:
            name: Hash name
            key: Field key

        Returns:
            Field value or None if not found
        """
        try:
            value = self.redis_client.hget(name, key)
            if value is None:
                return None

            # Try to deserialize
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value.decode("utf-8") if isinstance(value, bytes) else value

        except redis.RedisError as e:
            logger.error(f"Redis hget error for hash {name}, key {key}: {e}")
            return None

    def hset(self, name: str, key: str, value: Any) -> bool:
        """Set value in hash.

        Args:
            name: Hash name
            key: Field key
            value: Field value

        Returns:
            True if field is new, False if field was updated
        """
        try:
            # Serialize value
            if isinstance(value, (str, int, float, bytes)):
                serialized_value = value
            else:
                serialized_value = json.dumps(value)

            result = self.redis_client.hset(name, key, serialized_value)
            return bool(result)

        except redis.RedisError as e:
            logger.error(f"Redis hset error for hash {name}, key {key}: {e}")
            return False

    def hgetall(self, name: str) -> dict:
        """Get all fields and values from hash.

        Args:
            name: Hash name

        Returns:
            Dictionary of field-value pairs
        """
        try:
            raw_data = self.redis_client.hgetall(name)
            result = {}

            for key, value in raw_data.items():
                # Decode key if bytes
                decoded_key = key.decode("utf-8") if isinstance(key, bytes) else key

                # Try to deserialize value
                try:
                    result[decoded_key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    result[decoded_key] = (
                        value.decode("utf-8") if isinstance(value, bytes) else value
                    )

            return result

        except redis.RedisError as e:
            logger.error(f"Redis hgetall error for hash {name}: {e}")
            return {}

    def lpush(self, key: str, *values: Any) -> Optional[int]:
        """Push values to the head of list.

        Args:
            key: List key
            *values: Values to push

        Returns:
            Length of list after push or None on error
        """
        try:
            serialized_values = []
            for value in values:
                if isinstance(value, (str, int, float, bytes)):
                    serialized_values.append(value)
                else:
                    serialized_values.append(json.dumps(value))

            return self.redis_client.lpush(key, *serialized_values)

        except redis.RedisError as e:
            logger.error(f"Redis lpush error for key {key}: {e}")
            return None

    def lrange(self, key: str, start: int, end: int) -> list:
        """Get range of elements from list.

        Args:
            key: List key
            start: Start index
            end: End index (-1 for last element)

        Returns:
            List of elements
        """
        try:
            raw_values = self.redis_client.lrange(key, start, end)
            result = []

            for value in raw_values:
                try:
                    result.append(json.loads(value))
                except (json.JSONDecodeError, TypeError):
                    result.append(
                        value.decode("utf-8") if isinstance(value, bytes) else value
                    )

            return result

        except redis.RedisError as e:
            logger.error(f"Redis lrange error for key {key}: {e}")
            return []

    def sadd(self, key: str, *values: Any) -> Optional[int]:
        """Add members to set.

        Args:
            key: Set key
            *values: Values to add

        Returns:
            Number of elements added or None on error
        """
        try:
            serialized_values = []
            for value in values:
                if isinstance(value, (str, int, float, bytes)):
                    serialized_values.append(value)
                else:
                    serialized_values.append(json.dumps(value))

            return self.redis_client.sadd(key, *serialized_values)

        except redis.RedisError as e:
            logger.error(f"Redis sadd error for key {key}: {e}")
            return None

    def smembers(self, key: str) -> set:
        """Get all members of set.

        Args:
            key: Set key

        Returns:
            Set of members
        """
        try:
            raw_values = self.redis_client.smembers(key)
            result = set()

            for value in raw_values:
                try:
                    result.add(json.loads(value))
                except (json.JSONDecodeError, TypeError):
                    result.add(
                        value.decode("utf-8") if isinstance(value, bytes) else value
                    )

            return result

        except redis.RedisError as e:
            logger.error(f"Redis smembers error for key {key}: {e}")
            return set()

    async def ping(self) -> bool:
        """Ping Redis server to check connection.

        Returns:
            True if connection is alive, False otherwise
        """
        try:
            return self.redis_client.ping()
        except redis.RedisError as e:
            logger.error(f"Redis ping error: {e}")
            return False

    def flushdb(self) -> bool:
        """Flush current database (use with caution).

        Returns:
            True if flushed successfully, False otherwise
        """
        try:
            return bool(self.redis_client.flushdb())
        except redis.RedisError as e:
            logger.error(f"Redis flushdb error: {e}")
            return False

    def close(self):
        """Close Redis connection."""
        try:
            self.redis_client.close()
        except redis.RedisError as e:
            logger.error(f"Redis close error: {e}")
