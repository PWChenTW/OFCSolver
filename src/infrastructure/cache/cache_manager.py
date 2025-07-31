from typing import Optional, Dict, List, Any, Callable
from datetime import timedelta
import hashlib
import json
from functools import wraps
import logging

from .redis_cache import RedisCache

logger = logging.getLogger(__name__)


class CacheKeyBuilder:
    """Helper class to build consistent cache keys."""
    
    PREFIXES = {
        'game': 'game',
        'position': 'pos',
        'analysis': 'analysis',
        'strategy': 'strategy',
        'training': 'training',
        'user': 'user',
        'leaderboard': 'lb',
        'stats': 'stats'
    }
    
    @staticmethod
    def build(prefix: str, *parts: Any) -> str:
        """Build a cache key from prefix and parts.
        
        Args:
            prefix: Key prefix from PREFIXES
            *parts: Parts to include in the key
            
        Returns:
            Formatted cache key
        """
        prefix_value = CacheKeyBuilder.PREFIXES.get(prefix, prefix)
        key_parts = [prefix_value] + [str(part) for part in parts]
        return ':'.join(key_parts)
        
    @staticmethod
    def hash_position(position_data: Dict[str, Any]) -> str:
        """Create a hash for a game position.
        
        Args:
            position_data: Position data dictionary
            
        Returns:
            MD5 hash of the position
        """
        # Sort keys for consistent hashing
        sorted_data = json.dumps(position_data, sort_keys=True)
        return hashlib.md5(sorted_data.encode()).hexdigest()


class CacheManager:
    """High-level cache manager for OFC Solver System."""
    
    # Default TTL values
    TTL_SHORT = timedelta(minutes=5)
    TTL_MEDIUM = timedelta(hours=1)
    TTL_LONG = timedelta(hours=24)
    TTL_ANALYSIS = timedelta(days=7)
    
    def __init__(self, redis_cache: RedisCache):
        """Initialize cache manager.
        
        Args:
            redis_cache: Redis cache instance
        """
        self.cache = redis_cache
        self.key_builder = CacheKeyBuilder()
        
    # Game caching methods
    
    def get_game(self, game_id: str) -> Optional[Dict[str, Any]]:
        """Get game data from cache.
        
        Args:
            game_id: Game identifier
            
        Returns:
            Game data or None if not cached
        """
        key = self.key_builder.build('game', game_id)
        return self.cache.get(key)
        
    def set_game(self, game_id: str, game_data: Dict[str, Any], ttl: Optional[timedelta] = None) -> bool:
        """Cache game data.
        
        Args:
            game_id: Game identifier
            game_data: Game data to cache
            ttl: Time to live (defaults to MEDIUM)
            
        Returns:
            True if cached successfully
        """
        key = self.key_builder.build('game', game_id)
        ttl = ttl or self.TTL_MEDIUM
        return self.cache.set(key, game_data, expire=ttl)
        
    def delete_game(self, game_id: str) -> bool:
        """Delete game from cache.
        
        Args:
            game_id: Game identifier
            
        Returns:
            True if deleted
        """
        key = self.key_builder.build('game', game_id)
        return bool(self.cache.delete(key))
        
    # Position caching methods
    
    def get_position(self, position_hash: str) -> Optional[Dict[str, Any]]:
        """Get position data from cache.
        
        Args:
            position_hash: Position hash
            
        Returns:
            Position data or None if not cached
        """
        key = self.key_builder.build('position', position_hash)
        return self.cache.get(key)
        
    def set_position(self, position_data: Dict[str, Any], ttl: Optional[timedelta] = None) -> bool:
        """Cache position data.
        
        Args:
            position_data: Position data to cache
            ttl: Time to live (defaults to LONG)
            
        Returns:
            True if cached successfully
        """
        position_hash = self.key_builder.hash_position(position_data)
        key = self.key_builder.build('position', position_hash)
        ttl = ttl or self.TTL_LONG
        return self.cache.set(key, position_data, expire=ttl)
        
    # Analysis caching methods
    
    def get_analysis(self, position_hash: str, method: str) -> Optional[Dict[str, Any]]:
        """Get analysis result from cache.
        
        Args:
            position_hash: Position hash
            method: Analysis method used
            
        Returns:
            Analysis result or None if not cached
        """
        key = self.key_builder.build('analysis', position_hash, method)
        return self.cache.get(key)
        
    def set_analysis(
        self,
        position_hash: str,
        method: str,
        analysis_result: Dict[str, Any],
        ttl: Optional[timedelta] = None
    ) -> bool:
        """Cache analysis result.
        
        Args:
            position_hash: Position hash
            method: Analysis method used
            analysis_result: Analysis result to cache
            ttl: Time to live (defaults to ANALYSIS)
            
        Returns:
            True if cached successfully
        """
        key = self.key_builder.build('analysis', position_hash, method)
        ttl = ttl or self.TTL_ANALYSIS
        return self.cache.set(key, analysis_result, expire=ttl)
        
    # Strategy caching methods
    
    def get_strategy(self, position_hash: str) -> Optional[Dict[str, Any]]:
        """Get optimal strategy from cache.
        
        Args:
            position_hash: Position hash
            
        Returns:
            Strategy data or None if not cached
        """
        key = self.key_builder.build('strategy', position_hash)
        return self.cache.get(key)
        
    def set_strategy(
        self,
        position_hash: str,
        strategy_data: Dict[str, Any],
        ttl: Optional[timedelta] = None
    ) -> bool:
        """Cache optimal strategy.
        
        Args:
            position_hash: Position hash
            strategy_data: Strategy data to cache
            ttl: Time to live (defaults to ANALYSIS)
            
        Returns:
            True if cached successfully
        """
        key = self.key_builder.build('strategy', position_hash)
        ttl = ttl or self.TTL_ANALYSIS
        return self.cache.set(key, strategy_data, expire=ttl)
        
    # Training caching methods
    
    def get_training_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get training session from cache.
        
        Args:
            session_id: Training session ID
            
        Returns:
            Session data or None if not cached
        """
        key = self.key_builder.build('training', 'session', session_id)
        return self.cache.get(key)
        
    def set_training_session(
        self,
        session_id: str,
        session_data: Dict[str, Any],
        ttl: Optional[timedelta] = None
    ) -> bool:
        """Cache training session.
        
        Args:
            session_id: Training session ID
            session_data: Session data to cache
            ttl: Time to live (defaults to MEDIUM)
            
        Returns:
            True if cached successfully
        """
        key = self.key_builder.build('training', 'session', session_id)
        ttl = ttl or self.TTL_MEDIUM
        return self.cache.set(key, session_data, expire=ttl)
        
    def get_training_progress(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get training progress from cache.
        
        Args:
            session_id: Training session ID
            
        Returns:
            Progress data or None if not cached
        """
        key = self.key_builder.build('training', 'progress', session_id)
        return self.cache.get(key)
        
    def update_training_progress(
        self,
        session_id: str,
        completed_scenarios: int,
        accuracy: float
    ) -> bool:
        """Update training progress in cache.
        
        Args:
            session_id: Training session ID
            completed_scenarios: Number of completed scenarios
            accuracy: Current accuracy rate
            
        Returns:
            True if updated successfully
        """
        key = self.key_builder.build('training', 'progress', session_id)
        progress_data = {
            'completed_scenarios': completed_scenarios,
            'accuracy': accuracy,
            'last_updated': None  # Will be set by Redis
        }
        return self.cache.set(key, progress_data, expire=self.TTL_MEDIUM)
        
    # Statistics caching methods
    
    def increment_stat(self, stat_name: str, amount: int = 1) -> Optional[int]:
        """Increment a statistic counter.
        
        Args:
            stat_name: Name of the statistic
            amount: Amount to increment by
            
        Returns:
            New value or None on error
        """
        key = self.key_builder.build('stats', stat_name)
        return self.cache.incr(key, amount)
        
    def get_stat(self, stat_name: str) -> Optional[int]:
        """Get a statistic value.
        
        Args:
            stat_name: Name of the statistic
            
        Returns:
            Statistic value or None if not found
        """
        key = self.key_builder.build('stats', stat_name)
        value = self.cache.get(key)
        return int(value) if value is not None else None
        
    # Leaderboard methods
    
    def update_leaderboard(self, leaderboard_type: str, user_id: str, score: float) -> bool:
        """Update user score in leaderboard.
        
        Args:
            leaderboard_type: Type of leaderboard (daily, weekly, all-time)
            user_id: User identifier
            score: User's score
            
        Returns:
            True if updated successfully
        """
        key = self.key_builder.build('leaderboard', leaderboard_type)
        # Use Redis sorted set for leaderboards
        try:
            self.cache.redis_client.zadd(key, {user_id: score})
            return True
        except Exception as e:
            logger.error(f"Failed to update leaderboard: {e}")
            return False
            
    def get_leaderboard(
        self,
        leaderboard_type: str,
        start: int = 0,
        end: int = 9,
        with_scores: bool = True
    ) -> List[tuple]:
        """Get leaderboard entries.
        
        Args:
            leaderboard_type: Type of leaderboard
            start: Start rank (0-based)
            end: End rank (inclusive)
            with_scores: Include scores in result
            
        Returns:
            List of (user_id, score) tuples if with_scores, else list of user_ids
        """
        key = self.key_builder.build('leaderboard', leaderboard_type)
        try:
            return self.cache.redis_client.zrevrange(key, start, end, withscores=with_scores)
        except Exception as e:
            logger.error(f"Failed to get leaderboard: {e}")
            return []
            
    # Utility methods
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching a pattern.
        
        Args:
            pattern: Key pattern (e.g., "game:*")
            
        Returns:
            Number of keys deleted
        """
        try:
            keys = list(self.cache.redis_client.scan_iter(match=pattern))
            if keys:
                return self.cache.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Failed to invalidate pattern {pattern}: {e}")
            return 0
            
    def warm_cache(self, position_data: Dict[str, Any], analysis_result: Dict[str, Any]) -> bool:
        """Warm cache with position and analysis data.
        
        Args:
            position_data: Position data
            analysis_result: Analysis result
            
        Returns:
            True if all data cached successfully
        """
        position_hash = self.key_builder.hash_position(position_data)
        
        # Cache position
        position_cached = self.set_position(position_data)
        
        # Cache analysis
        method = analysis_result.get('calculation_method', 'unknown')
        analysis_cached = self.set_analysis(position_hash, method, analysis_result)
        
        # Cache strategy if available
        strategy_cached = True
        if 'optimal_strategy' in analysis_result:
            strategy_cached = self.set_strategy(position_hash, analysis_result['optimal_strategy'])
            
        return position_cached and analysis_cached and strategy_cached
        
    def health_check(self) -> bool:
        """Check if cache is healthy.
        
        Returns:
            True if cache is accessible
        """
        return self.cache.ping()


def cached(
    cache_manager: CacheManager,
    prefix: str,
    ttl: Optional[timedelta] = None,
    key_func: Optional[Callable] = None
):
    """Decorator for caching function results.
    
    Args:
        cache_manager: CacheManager instance
        prefix: Cache key prefix
        ttl: Time to live for cached results
        key_func: Custom function to generate cache key from arguments
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Simple key generation from function name and arguments
                key_parts = [func.__name__] + [str(arg) for arg in args]
                key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
                cache_key = CacheKeyBuilder.build(prefix, *key_parts)
                
            # Try to get from cache
            cached_result = cache_manager.cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_result
                
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            cache_manager.cache.set(cache_key, result, expire=ttl)
            logger.debug(f"Cached result for key: {cache_key}")
            
            return result
            
        return wrapper
    return decorator