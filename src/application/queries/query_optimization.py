"""Query optimization utilities and decorators."""

import asyncio
import functools
import hashlib
import json
import time
from typing import Any, Callable, Dict, Optional, TypeVar, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

from src.infrastructure.cache.cache_manager import CacheManager
from src.infrastructure.monitoring.health_checker import HealthChecker


T = TypeVar('T')


@dataclass
class CacheConfig:
    """Configuration for query caching."""
    enabled: bool = True
    ttl_seconds: int = 300  # 5 minutes default
    key_prefix: str = "query"
    include_user_context: bool = True
    cache_null_results: bool = False


@dataclass
class QueryMetrics:
    """Metrics for query performance tracking."""
    query_name: str
    execution_time: float
    cache_hit: bool
    result_size: int
    timestamp: datetime


class QueryOptimizer:
    """Central query optimization manager."""
    
    def __init__(self, cache_manager: CacheManager, health_checker: HealthChecker):
        self.cache_manager = cache_manager
        self.health_checker = health_checker
        self._query_metrics: Dict[str, list] = {}
        self._slow_query_threshold = 1.0  # 1 second
    
    def cache_query(self, cache_config: Optional[CacheConfig] = None):
        """Decorator to cache query results."""
        config = cache_config or CacheConfig()
        
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @functools.wraps(func)
            async def wrapper(self, query: Any) -> T:
                if not config.enabled:
                    return await func(self, query)
                
                # Generate cache key
                cache_key = self._generate_cache_key(
                    config.key_prefix,
                    func.__name__,
                    query
                )
                
                # Try to get from cache
                start_time = time.time()
                cached_result = await self.cache_manager.get(cache_key)
                
                if cached_result is not None:
                    # Record cache hit
                    self._record_metrics(
                        func.__name__,
                        time.time() - start_time,
                        True,
                        len(str(cached_result))
                    )
                    return cached_result
                
                # Execute query
                result = await func(self, query)
                execution_time = time.time() - start_time
                
                # Cache result if appropriate
                if result is not None or config.cache_null_results:
                    await self.cache_manager.set(
                        cache_key,
                        result,
                        ttl=config.ttl_seconds
                    )
                
                # Record cache miss
                self._record_metrics(
                    func.__name__,
                    execution_time,
                    False,
                    len(str(result)) if result else 0
                )
                
                # Check for slow queries
                if execution_time > self._slow_query_threshold:
                    await self._handle_slow_query(
                        func.__name__,
                        query,
                        execution_time
                    )
                
                return result
            
            return wrapper
        
        return decorator
    
    def batch_queries(self, batch_size: int = 10, delay_ms: int = 50):
        """Decorator to batch multiple queries together."""
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            # Store pending queries
            pending_queries = []
            pending_futures = []
            batch_lock = asyncio.Lock()
            
            @functools.wraps(func)
            async def wrapper(self, query: Any) -> T:
                future = asyncio.Future()
                
                async with batch_lock:
                    pending_queries.append(query)
                    pending_futures.append(future)
                    
                    # If batch is full, process immediately
                    if len(pending_queries) >= batch_size:
                        await self._process_batch(
                            func,
                            self,
                            pending_queries[:],
                            pending_futures[:]
                        )
                        pending_queries.clear()
                        pending_futures.clear()
                    else:
                        # Schedule batch processing after delay
                        asyncio.create_task(
                            self._delayed_batch_process(
                                func,
                                self,
                                pending_queries,
                                pending_futures,
                                batch_lock,
                                delay_ms
                            )
                        )
                
                return await future
            
            return wrapper
        
        return decorator
    
    def prefetch_related(self, *related_queries: str):
        """Decorator to prefetch related data."""
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @functools.wraps(func)
            async def wrapper(self, query: Any) -> T:
                # Execute main query
                result = await func(self, query)
                
                # Prefetch related data in parallel
                if hasattr(self, '_prefetch_handlers'):
                    prefetch_tasks = []
                    
                    for related_query in related_queries:
                        handler = self._prefetch_handlers.get(related_query)
                        if handler:
                            prefetch_tasks.append(
                                handler(query, result)
                            )
                    
                    if prefetch_tasks:
                        await asyncio.gather(*prefetch_tasks)
                
                return result
            
            return wrapper
        
        return decorator
    
    def with_timeout(self, timeout_seconds: float):
        """Decorator to add timeout to queries."""
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @functools.wraps(func)
            async def wrapper(self, query: Any) -> T:
                try:
                    return await asyncio.wait_for(
                        func(self, query),
                        timeout=timeout_seconds
                    )
                except asyncio.TimeoutError:
                    await self._handle_timeout(
                        func.__name__,
                        query,
                        timeout_seconds
                    )
                    raise
            
            return wrapper
        
        return decorator
    
    def with_retry(self, max_retries: int = 3, backoff_factor: float = 2.0):
        """Decorator to add retry logic to queries."""
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @functools.wraps(func)
            async def wrapper(self, query: Any) -> T:
                last_exception = None
                
                for attempt in range(max_retries):
                    try:
                        return await func(self, query)
                    except Exception as e:
                        last_exception = e
                        
                        if attempt < max_retries - 1:
                            delay = backoff_factor ** attempt
                            await asyncio.sleep(delay)
                        else:
                            await self._handle_retry_exhausted(
                                func.__name__,
                                query,
                                attempt + 1,
                                e
                            )
                
                raise last_exception
            
            return wrapper
        
        return decorator
    
    def optimize_pagination(self):
        """Decorator to optimize paginated queries."""
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @functools.wraps(func)
            async def wrapper(self, query: Any) -> T:
                # Check if query has pagination
                if hasattr(query, 'pagination') and query.pagination:
                    pagination = query.pagination
                    
                    # Optimize based on page size and offset
                    if pagination.offset > 1000:
                        # Use cursor-based pagination for large offsets
                        return await self._cursor_based_query(
                            func,
                            self,
                            query
                        )
                    elif pagination.page_size > 100:
                        # Warn about large page sizes
                        await self._handle_large_page_size(
                            func.__name__,
                            pagination.page_size
                        )
                
                return await func(self, query)
            
            return wrapper
        
        return decorator
    
    # Helper methods
    def _generate_cache_key(self, prefix: str, func_name: str, query: Any) -> str:
        """Generate a cache key for the query."""
        # Convert query to dict for hashing
        query_dict = asdict(query) if hasattr(query, '__dataclass_fields__') else str(query)
        query_json = json.dumps(query_dict, sort_keys=True)
        
        # Generate hash
        query_hash = hashlib.md5(query_json.encode()).hexdigest()
        
        return f"{prefix}:{func_name}:{query_hash}"
    
    def _record_metrics(self, query_name: str, execution_time: float,
                       cache_hit: bool, result_size: int):
        """Record query performance metrics."""
        metrics = QueryMetrics(
            query_name=query_name,
            execution_time=execution_time,
            cache_hit=cache_hit,
            result_size=result_size,
            timestamp=datetime.now()
        )
        
        if query_name not in self._query_metrics:
            self._query_metrics[query_name] = []
        
        self._query_metrics[query_name].append(metrics)
        
        # Keep only last 1000 metrics per query
        if len(self._query_metrics[query_name]) > 1000:
            self._query_metrics[query_name] = self._query_metrics[query_name][-1000:]
    
    async def _handle_slow_query(self, query_name: str, query: Any, execution_time: float):
        """Handle slow query detection."""
        # Log slow query
        print(f"Slow query detected: {query_name} took {execution_time:.2f}s")
        
        # Could send to monitoring system
        await self.health_checker.report_slow_query(
            query_name,
            execution_time,
            str(query)
        )
    
    async def _process_batch(self, func: Callable, handler: Any,
                           queries: list, futures: list):
        """Process a batch of queries."""
        try:
            # Execute batch query
            results = await func(handler, queries)
            
            # Resolve futures with results
            for future, result in zip(futures, results):
                future.set_result(result)
        except Exception as e:
            # Reject all futures with the exception
            for future in futures:
                future.set_exception(e)
    
    async def _delayed_batch_process(self, func: Callable, handler: Any,
                                   queries: list, futures: list,
                                   lock: asyncio.Lock, delay_ms: int):
        """Process batch after delay."""
        await asyncio.sleep(delay_ms / 1000)
        
        async with lock:
            if queries:  # Check if not already processed
                await self._process_batch(func, handler, queries[:], futures[:])
                queries.clear()
                futures.clear()
    
    async def _cursor_based_query(self, func: Callable, handler: Any, query: Any) -> Any:
        """Execute query using cursor-based pagination."""
        # This would be implemented based on specific database capabilities
        # For now, fall back to regular query
        return await func(handler, query)
    
    async def _handle_large_page_size(self, query_name: str, page_size: int):
        """Handle large page size warning."""
        print(f"Warning: Large page size ({page_size}) in {query_name}")
    
    async def _handle_timeout(self, query_name: str, query: Any, timeout: float):
        """Handle query timeout."""
        print(f"Query timeout: {query_name} exceeded {timeout}s")
    
    async def _handle_retry_exhausted(self, query_name: str, query: Any,
                                    attempts: int, exception: Exception):
        """Handle exhausted retries."""
        print(f"Query failed after {attempts} attempts: {query_name}")
    
    def get_query_stats(self, query_name: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for queries."""
        if query_name:
            metrics = self._query_metrics.get(query_name, [])
        else:
            metrics = []
            for query_metrics in self._query_metrics.values():
                metrics.extend(query_metrics)
        
        if not metrics:
            return {}
        
        execution_times = [m.execution_time for m in metrics]
        cache_hits = sum(1 for m in metrics if m.cache_hit)
        
        return {
            'count': len(metrics),
            'cache_hit_rate': cache_hits / len(metrics) if metrics else 0,
            'avg_execution_time': sum(execution_times) / len(execution_times),
            'min_execution_time': min(execution_times),
            'max_execution_time': max(execution_times),
            'p95_execution_time': sorted(execution_times)[int(len(execution_times) * 0.95)],
            'avg_result_size': sum(m.result_size for m in metrics) / len(metrics)
        }


# Query optimization middleware
class QueryOptimizationMiddleware:
    """Middleware for automatic query optimization."""
    
    def __init__(self, optimizer: QueryOptimizer):
        self.optimizer = optimizer
    
    async def __call__(self, handler: Callable, query: Any) -> Any:
        """Apply optimization based on query characteristics."""
        # Check if query should be cached
        if self._should_cache(query):
            cache_config = self._get_cache_config(query)
            cached_handler = self.optimizer.cache_query(cache_config)(handler)
            return await cached_handler(query)
        
        # Check if query should have timeout
        if self._should_timeout(query):
            timeout = self._get_timeout(query)
            timeout_handler = self.optimizer.with_timeout(timeout)(handler)
            return await timeout_handler(query)
        
        # Regular execution
        return await handler(query)
    
    def _should_cache(self, query: Any) -> bool:
        """Determine if query should be cached."""
        # Cache read-only queries
        query_name = type(query).__name__
        return query_name.startswith('Get') or query_name.startswith('Find')
    
    def _get_cache_config(self, query: Any) -> CacheConfig:
        """Get cache configuration for query."""
        # Different TTL based on query type
        query_name = type(query).__name__
        
        if 'Stats' in query_name:
            return CacheConfig(ttl_seconds=600)  # 10 minutes for stats
        elif 'History' in query_name:
            return CacheConfig(ttl_seconds=300)  # 5 minutes for history
        else:
            return CacheConfig(ttl_seconds=60)   # 1 minute for others
    
    def _should_timeout(self, query: Any) -> bool:
        """Determine if query should have timeout."""
        # Timeout heavy queries
        query_name = type(query).__name__
        return 'Analysis' in query_name or 'Calculate' in query_name
    
    def _get_timeout(self, query: Any) -> float:
        """Get timeout for query."""
        query_name = type(query).__name__
        
        if 'Analysis' in query_name:
            return 30.0  # 30 seconds for analysis
        else:
            return 10.0  # 10 seconds default