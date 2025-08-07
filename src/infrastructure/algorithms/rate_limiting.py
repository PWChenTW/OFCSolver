"""
Advanced rate limiting algorithms with high performance and accuracy.
Implements multiple algorithms: Token Bucket, Sliding Window, and Adaptive Rate Limiting.
"""

import time
import asyncio
import threading
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from collections import deque
from enum import Enum
import heapq
import logging

logger = logging.getLogger(__name__)


class RateLimitAlgorithm(Enum):
    """Rate limiting algorithm types."""
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"
    ADAPTIVE = "adaptive"


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    requests_per_minute: int = 60
    burst_size: int = 10
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.TOKEN_BUCKET
    window_size_seconds: int = 60
    adaptive_threshold: float = 0.8  # Trigger adaptive limiting at 80% usage


@dataclass
class RateLimitResult:
    """Result of rate limit check."""
    allowed: bool
    remaining_tokens: int
    reset_time: float
    retry_after: Optional[float] = None
    algorithm_used: Optional[str] = None
    user_id: Optional[str] = None


class TokenBucketLimiter:
    """
    High-performance token bucket rate limiter.
    Most accurate algorithm for burst handling and steady-state limiting.
    """

    def __init__(self, requests_per_minute: int, burst_size: int):
        self.capacity = burst_size
        self.tokens = float(burst_size)
        self.refill_rate = requests_per_minute / 60.0  # tokens per second
        self.last_refill = time.time()
        self._lock = threading.RLock()

    def check_limit(self, requested_tokens: int = 1) -> RateLimitResult:
        """Check if request is within rate limit."""
        with self._lock:
            current_time = time.time()
            
            # Refill tokens based on elapsed time
            elapsed = current_time - self.last_refill
            tokens_to_add = elapsed * self.refill_rate
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_refill = current_time
            
            # Check if we have enough tokens
            if self.tokens >= requested_tokens:
                self.tokens -= requested_tokens
                return RateLimitResult(
                    allowed=True,
                    remaining_tokens=int(self.tokens),
                    reset_time=current_time + (self.capacity - self.tokens) / self.refill_rate,
                    algorithm_used="token_bucket"
                )
            else:
                # Calculate retry after time
                tokens_needed = requested_tokens - self.tokens
                retry_after = tokens_needed / self.refill_rate
                
                return RateLimitResult(
                    allowed=False,
                    remaining_tokens=int(self.tokens),
                    reset_time=current_time + retry_after,
                    retry_after=retry_after,
                    algorithm_used="token_bucket"
                )

    def get_status(self) -> Dict[str, Any]:
        """Get current limiter status."""
        with self._lock:
            current_time = time.time()
            elapsed = current_time - self.last_refill
            available_tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            
            return {
                "algorithm": "token_bucket",
                "capacity": self.capacity,
                "available_tokens": available_tokens,
                "refill_rate": self.refill_rate,
                "utilization": 1.0 - (available_tokens / self.capacity)
            }


class SlidingWindowLimiter:
    """
    Sliding window rate limiter with precise timing.
    More memory efficient than log-based sliding window.
    """

    def __init__(self, requests_per_minute: int, window_size_seconds: int = 60):
        self.limit = requests_per_minute
        self.window_size = window_size_seconds
        self.requests: deque = deque()  # Timestamps of requests
        self._lock = threading.RLock()

    def check_limit(self, requested_tokens: int = 1) -> RateLimitResult:
        """Check if request is within rate limit."""
        with self._lock:
            current_time = time.time()
            window_start = current_time - self.window_size
            
            # Remove old requests outside the window
            while self.requests and self.requests[0] < window_start:
                self.requests.popleft()
            
            # Check if adding new requests would exceed limit
            if len(self.requests) + requested_tokens <= self.limit:
                # Add timestamps for each token
                for _ in range(requested_tokens):
                    self.requests.append(current_time)
                
                return RateLimitResult(
                    allowed=True,
                    remaining_tokens=self.limit - len(self.requests),
                    reset_time=self.requests[0] + self.window_size if self.requests else current_time,
                    algorithm_used="sliding_window"
                )
            else:
                # Calculate when the oldest request will expire
                if self.requests:
                    retry_after = (self.requests[0] + self.window_size) - current_time
                else:
                    retry_after = 0
                
                return RateLimitResult(
                    allowed=False,
                    remaining_tokens=max(0, self.limit - len(self.requests)),
                    reset_time=self.requests[0] + self.window_size if self.requests else current_time,
                    retry_after=max(0, retry_after),
                    algorithm_used="sliding_window"
                )

    def get_status(self) -> Dict[str, Any]:
        """Get current limiter status."""
        with self._lock:
            current_time = time.time()
            window_start = current_time - self.window_size
            
            # Count active requests
            active_requests = sum(1 for req_time in self.requests if req_time >= window_start)
            
            return {
                "algorithm": "sliding_window",
                "limit": self.limit,
                "active_requests": active_requests,
                "remaining": max(0, self.limit - active_requests),
                "utilization": active_requests / self.limit,
                "window_size": self.window_size
            }


class AdaptiveLimiter:
    """
    Adaptive rate limiter that adjusts limits based on system performance.
    Uses system metrics to dynamically modify rate limits.
    """

    def __init__(self, base_config: RateLimitConfig):
        self.base_limit = base_config.requests_per_minute
        self.current_limit = base_config.requests_per_minute
        self.burst_size = base_config.burst_size
        self.adaptive_threshold = base_config.adaptive_threshold
        
        # Use token bucket as underlying mechanism
        self.limiter = TokenBucketLimiter(self.current_limit, self.burst_size)
        
        # Performance tracking
        self.performance_window = deque(maxlen=100)
        self.last_adjustment = time.time()
        self.adjustment_interval = 30  # Adjust every 30 seconds
        
        self._lock = threading.RLock()

    def check_limit(self, requested_tokens: int = 1, response_time: Optional[float] = None) -> RateLimitResult:
        """Check rate limit with adaptive adjustment."""
        with self._lock:
            # Record performance metrics
            if response_time is not None:
                self.performance_window.append({
                    'response_time': response_time,
                    'timestamp': time.time()
                })
            
            # Adjust limits if needed
            self._adjust_limits_if_needed()
            
            # Use underlying limiter
            result = self.limiter.check_limit(requested_tokens)
            result.algorithm_used = "adaptive"
            
            return result

    def _adjust_limits_if_needed(self):
        """Adjust rate limits based on system performance."""
        current_time = time.time()
        
        if current_time - self.last_adjustment < self.adjustment_interval:
            return
        
        if len(self.performance_window) < 10:
            return  # Need more data
        
        # Calculate recent performance metrics
        recent_responses = [
            item for item in self.performance_window
            if current_time - item['timestamp'] < 60  # Last minute
        ]
        
        if not recent_responses:
            return
        
        avg_response_time = sum(item['response_time'] for item in recent_responses) / len(recent_responses)
        
        # Adjust limits based on performance
        if avg_response_time > 5.0:  # Slow responses
            # Reduce limit to protect system
            new_limit = max(self.base_limit * 0.5, self.current_limit * 0.8)
            logger.warning(f"Reducing rate limit to {new_limit} due to slow responses ({avg_response_time:.2f}s)")
        elif avg_response_time < 1.0:  # Fast responses
            # Gradually increase limit
            new_limit = min(self.base_limit * 1.5, self.current_limit * 1.1)
            if new_limit > self.current_limit:
                logger.info(f"Increasing rate limit to {new_limit} due to good performance ({avg_response_time:.2f}s)")
        else:
            # Gradually return to base limit
            if self.current_limit > self.base_limit:
                new_limit = max(self.base_limit, self.current_limit * 0.95)
            elif self.current_limit < self.base_limit:
                new_limit = min(self.base_limit, self.current_limit * 1.05)
            else:
                new_limit = self.current_limit
        
        # Update limiter if limit changed significantly
        if abs(new_limit - self.current_limit) > self.current_limit * 0.1:
            self.current_limit = int(new_limit)
            self.limiter = TokenBucketLimiter(self.current_limit, self.burst_size)
            self.last_adjustment = current_time

    def get_status(self) -> Dict[str, Any]:
        """Get adaptive limiter status."""
        with self._lock:
            base_status = self.limiter.get_status()
            
            # Add adaptive-specific metrics
            recent_responses = [
                item for item in self.performance_window
                if time.time() - item['timestamp'] < 60
            ]
            
            avg_response_time = 0
            if recent_responses:
                avg_response_time = sum(item['response_time'] for item in recent_responses) / len(recent_responses)
            
            base_status.update({
                "algorithm": "adaptive",
                "base_limit": self.base_limit,
                "current_limit": self.current_limit,
                "adjustment_factor": self.current_limit / self.base_limit,
                "avg_response_time": avg_response_time,
                "performance_samples": len(self.performance_window)
            })
            
            return base_status


class DistributedLimiter:
    """
    Distributed rate limiter for multi-instance deployments.
    Uses Redis for coordination between instances (mock implementation for MVP).
    """

    def __init__(self, config: RateLimitConfig, instance_id: str):
        self.config = config
        self.instance_id = instance_id
        
        # Local limiter for fast path
        self.local_limiter = TokenBucketLimiter(
            config.requests_per_minute,
            config.burst_size
        )
        
        # Distributed state (would use Redis in production)
        self.distributed_state = {}
        self.last_sync = time.time()
        self.sync_interval = 5  # Sync every 5 seconds

    def check_limit(self, user_id: str, requested_tokens: int = 1) -> RateLimitResult:
        """Check rate limit across distributed instances."""
        # Fast path: check local limiter first
        local_result = self.local_limiter.check_limit(requested_tokens)
        
        if not local_result.allowed:
            return local_result
        
        # Distributed check (simplified for MVP)
        # In production, this would coordinate with Redis
        distributed_key = f"rate_limit:{user_id}"
        
        # Simulate distributed check
        if self._should_sync():
            self._sync_distributed_state()
        
        # For MVP, assume distributed check passes
        local_result.algorithm_used = "distributed"
        return local_result

    def _should_sync(self) -> bool:
        """Check if we should sync with distributed state."""
        return time.time() - self.last_sync > self.sync_interval

    def _sync_distributed_state(self):
        """Sync local state with distributed store."""
        # Mock implementation - would use Redis in production
        self.last_sync = time.time()


class HierarchicalLimiter:
    """
    Hierarchical rate limiter with multiple tiers (global, user, endpoint).
    Provides fine-grained control over rate limiting.
    """

    def __init__(self):
        self.limiters: Dict[str, Dict[str, Any]] = {
            "global": {},
            "user": {},
            "endpoint": {},
            "user_endpoint": {}
        }
        self._lock = threading.RLock()

    def add_limiter(self, tier: str, key: str, config: RateLimitConfig):
        """Add a rate limiter at specific tier and key."""
        with self._lock:
            if tier not in self.limiters:
                self.limiters[tier] = {}
            
            # Create appropriate limiter based on algorithm
            if config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
                limiter = TokenBucketLimiter(config.requests_per_minute, config.burst_size)
            elif config.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
                limiter = SlidingWindowLimiter(config.requests_per_minute, config.window_size_seconds)
            elif config.algorithm == RateLimitAlgorithm.ADAPTIVE:
                limiter = AdaptiveLimiter(config)
            else:
                limiter = TokenBucketLimiter(config.requests_per_minute, config.burst_size)
            
            self.limiters[tier][key] = {
                "limiter": limiter,
                "config": config
            }

    def check_limits(
        self, 
        user_id: str, 
        endpoint: str, 
        requested_tokens: int = 1,
        response_time: Optional[float] = None
    ) -> RateLimitResult:
        """
        Check all applicable rate limits in hierarchy.
        Returns first limit violation or success if all pass.
        """
        with self._lock:
            # Check in order of precedence
            checks = [
                ("global", "all"),
                ("user", user_id),
                ("endpoint", endpoint),
                ("user_endpoint", f"{user_id}:{endpoint}")
            ]
            
            for tier, key in checks:
                if tier in self.limiters and key in self.limiters[tier]:
                    limiter_info = self.limiters[tier][key]
                    limiter = limiter_info["limiter"]
                    
                    # Use adaptive check if supported
                    if hasattr(limiter, 'check_limit') and response_time is not None:
                        if isinstance(limiter, AdaptiveLimiter):
                            result = limiter.check_limit(requested_tokens, response_time)
                        else:
                            result = limiter.check_limit(requested_tokens)
                    else:
                        result = limiter.check_limit(requested_tokens)
                    
                    if not result.allowed:
                        result.user_id = user_id
                        return result
            
            # All checks passed
            return RateLimitResult(
                allowed=True,
                remaining_tokens=float('inf'),
                reset_time=time.time() + 60,
                algorithm_used="hierarchical",
                user_id=user_id
            )

    def get_all_status(self) -> Dict[str, Any]:
        """Get status of all limiters in hierarchy."""
        with self._lock:
            status = {}
            
            for tier, limiters in self.limiters.items():
                status[tier] = {}
                for key, limiter_info in limiters.items():
                    limiter = limiter_info["limiter"]
                    if hasattr(limiter, 'get_status'):
                        status[tier][key] = limiter.get_status()
            
            return status


class RateLimitManager:
    """
    Centralized rate limit management with performance monitoring.
    Provides unified interface for all rate limiting algorithms.
    """

    def __init__(self):
        self.hierarchical_limiter = HierarchicalLimiter()
        self.metrics = {
            "total_requests": 0,
            "allowed_requests": 0,
            "blocked_requests": 0,
            "algorithm_usage": {},
            "start_time": time.time()
        }
        self._lock = threading.RLock()

    def setup_user_limits(self, user_id: str, user_type: str):
        """Setup rate limits for a user based on their type."""
        # User-specific limits based on type
        user_configs = {
            "anonymous": RateLimitConfig(
                requests_per_minute=30,
                burst_size=5,
                algorithm=RateLimitAlgorithm.TOKEN_BUCKET
            ),
            "demo": RateLimitConfig(
                requests_per_minute=100,
                burst_size=20,
                algorithm=RateLimitAlgorithm.ADAPTIVE
            ),
            "basic": RateLimitConfig(
                requests_per_minute=200,
                burst_size=40,
                algorithm=RateLimitAlgorithm.ADAPTIVE
            ),
            "premium": RateLimitConfig(
                requests_per_minute=500,
                burst_size=100,
                algorithm=RateLimitAlgorithm.ADAPTIVE
            ),
            "test": RateLimitConfig(
                requests_per_minute=1000,
                burst_size=200,
                algorithm=RateLimitAlgorithm.SLIDING_WINDOW
            )
        }
        
        config = user_configs.get(user_type, user_configs["anonymous"])
        self.hierarchical_limiter.add_limiter("user", user_id, config)

    def setup_endpoint_limits(self, endpoint: str, limit_config: RateLimitConfig):
        """Setup rate limits for specific endpoints."""
        self.hierarchical_limiter.add_limiter("endpoint", endpoint, limit_config)

    def check_rate_limit(
        self,
        user_id: str,
        endpoint: str,
        requested_tokens: int = 1,
        response_time: Optional[float] = None
    ) -> RateLimitResult:
        """Check rate limits and update metrics."""
        with self._lock:
            self.metrics["total_requests"] += 1
            
            result = self.hierarchical_limiter.check_limits(
                user_id, endpoint, requested_tokens, response_time
            )
            
            # Update metrics
            if result.allowed:
                self.metrics["allowed_requests"] += 1
            else:
                self.metrics["blocked_requests"] += 1
            
            # Track algorithm usage
            algorithm = result.algorithm_used or "unknown"
            self.metrics["algorithm_usage"][algorithm] = self.metrics["algorithm_usage"].get(algorithm, 0) + 1
            
            return result

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        with self._lock:
            uptime = time.time() - self.metrics["start_time"]
            
            return {
                "uptime_seconds": uptime,
                "total_requests": self.metrics["total_requests"],
                "allowed_requests": self.metrics["allowed_requests"],
                "blocked_requests": self.metrics["blocked_requests"],
                "block_rate": (
                    self.metrics["blocked_requests"] / max(1, self.metrics["total_requests"])
                ),
                "requests_per_minute": self.metrics["total_requests"] / max(1, uptime / 60),
                "algorithm_usage": self.metrics["algorithm_usage"],
                "limiter_status": self.hierarchical_limiter.get_all_status()
            }


# Global rate limit manager
rate_limit_manager = RateLimitManager()

# Setup global limits
rate_limit_manager.hierarchical_limiter.add_limiter(
    "global", 
    "all", 
    RateLimitConfig(
        requests_per_minute=10000,  # Global system limit
        burst_size=1000,
        algorithm=RateLimitAlgorithm.SLIDING_WINDOW
    )
)

# Setup endpoint-specific limits
endpoint_configs = {
    "analysis": RateLimitConfig(
        requests_per_minute=100,  # Analysis is resource-intensive
        burst_size=10,
        algorithm=RateLimitAlgorithm.ADAPTIVE
    ),
    "games": RateLimitConfig(
        requests_per_minute=500,  # Game operations are lighter
        burst_size=50,
        algorithm=RateLimitAlgorithm.TOKEN_BUCKET
    ),
    "training": RateLimitConfig(
        requests_per_minute=200,
        burst_size=20,
        algorithm=RateLimitAlgorithm.ADAPTIVE
    )
}

for endpoint, config in endpoint_configs.items():
    rate_limit_manager.setup_endpoint_limits(endpoint, config)


def get_rate_limit_manager() -> RateLimitManager:
    """Get the rate limit manager instance."""
    return rate_limit_manager