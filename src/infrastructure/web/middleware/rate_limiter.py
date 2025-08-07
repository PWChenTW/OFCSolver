"""
Rate limiting middleware for API request throttling.
MVP implementation with memory-based rate limiting and user-specific limits.
"""

import time
import logging
from typing import Dict, Any, Optional
from collections import defaultdict, deque
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from src.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware with user-specific limits.
    
    MVP Features:
    - In-memory rate limiting (simple sliding window)
    - Different limits for authenticated vs anonymous users
    - Per-endpoint rate limiting
    - Graceful degradation under high load
    """

    def __init__(self, app):
        super().__init__(app)
        # In-memory storage for request tracking
        # Format: {user_id: {endpoint: deque(timestamps)}}
        self.request_history: Dict[str, Dict[str, deque]] = defaultdict(
            lambda: defaultdict(deque)
        )
        self.cleanup_interval = 300  # Clean up every 5 minutes
        self.last_cleanup = time.time()

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path.startswith("/health"):
            return await call_next(request)

        # Get user information for rate limiting
        user_info = await self._get_user_info(request)
        
        # Check rate limits
        try:
            await self._check_rate_limits(request, user_info)
        except HTTPException:
            raise

        # Process request
        response = await call_next(request)
        
        # Record successful request
        await self._record_request(request, user_info)
        
        # Periodic cleanup
        await self._periodic_cleanup()
        
        return response

    async def _get_user_info(self, request: Request) -> Dict[str, Any]:
        """Get user information from request state or create anonymous user."""
        if hasattr(request.state, "user"):
            return request.state.user
        
        # Anonymous user fallback
        return {
            "user_id": f"anonymous_{request.client.host}" if request.client else "anonymous_unknown",
            "is_authenticated": False,
            "rate_limit": 30,  # Lower limit for anonymous users
            "user_type": "anonymous"
        }

    async def _check_rate_limits(self, request: Request, user_info: Dict[str, Any]):
        """Check if request should be rate limited."""
        
        user_id = user_info["user_id"]
        endpoint = self._get_endpoint_key(request)
        current_time = time.time()
        
        # Get rate limit for user
        rate_limit = self._get_rate_limit(user_info, endpoint)
        time_window = 60  # 1 minute window
        
        # Get request history for this user/endpoint
        request_times = self.request_history[user_id][endpoint]
        
        # Remove old requests outside the time window
        while request_times and request_times[0] < current_time - time_window:
            request_times.popleft()
        
        # Check if limit exceeded
        if len(request_times) >= rate_limit:
            # Calculate time until next request allowed
            oldest_request = request_times[0]
            retry_after = int(oldest_request + time_window - current_time) + 1
            
            logger.warning(
                f"Rate limit exceeded for user {user_id} on endpoint {endpoint}. "
                f"Requests: {len(request_times)}/{rate_limit}"
            )
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)}
            )

    async def _record_request(self, request: Request, user_info: Dict[str, Any]):
        """Record successful request for rate limiting."""
        user_id = user_info["user_id"]
        endpoint = self._get_endpoint_key(request)
        current_time = time.time()
        
        # Add current request to history
        self.request_history[user_id][endpoint].append(current_time)

    def _get_endpoint_key(self, request: Request) -> str:
        """Get endpoint key for rate limiting granularity."""
        
        # MVP: Use path pattern for grouping
        path = request.url.path
        method = request.method
        
        # Group similar endpoints together
        endpoint_patterns = {
            "/api/v1/games": "games",
            "/api/v1/analysis": "analysis", 
            "/api/v1/training": "training",
        }
        
        for pattern, key in endpoint_patterns.items():
            if path.startswith(pattern):
                return f"{method}:{key}"
        
        # Default: use full path
        return f"{method}:{path}"

    def _get_rate_limit(self, user_info: Dict[str, Any], endpoint: str) -> int:
        """Get rate limit for user and endpoint."""
        
        # Base rate limit from user info
        base_limit = user_info.get("rate_limit", 60)
        
        # Endpoint-specific adjustments
        endpoint_multipliers = {
            "POST:analysis": 0.5,  # Analysis is resource-intensive
            "GET:games": 2.0,      # Game queries are lighter
            "POST:games": 1.0,     # Game creation is moderate
            "GET:training": 1.5,   # Training queries are moderate
            "POST:training": 0.8,  # Training creation is heavier
        }
        
        multiplier = endpoint_multipliers.get(endpoint, 1.0)
        return max(1, int(base_limit * multiplier))

    async def _periodic_cleanup(self):
        """Periodically clean up old request history."""
        current_time = time.time()
        
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        # Clean up old entries
        cutoff_time = current_time - 3600  # Keep 1 hour of history
        
        users_to_remove = []
        for user_id, endpoints in self.request_history.items():
            endpoints_to_remove = []
            
            for endpoint, request_times in endpoints.items():
                # Remove old requests
                while request_times and request_times[0] < cutoff_time:
                    request_times.popleft()
                
                # Mark empty endpoint histories for removal
                if not request_times:
                    endpoints_to_remove.append(endpoint)
            
            # Remove empty endpoints
            for endpoint in endpoints_to_remove:
                del endpoints[endpoint]
            
            # Mark empty user histories for removal
            if not endpoints:
                users_to_remove.append(user_id)
        
        # Remove empty user histories
        for user_id in users_to_remove:
            del self.request_history[user_id]
        
        self.last_cleanup = current_time
        
        if users_to_remove or any(endpoints_to_remove for endpoints_to_remove in [[]]):
            logger.info(f"Rate limit cleanup: removed {len(users_to_remove)} inactive users")


# Helper functions for rate limiting configuration

def get_user_rate_limit(user_type: str) -> int:
    """Get default rate limit based on user type."""
    rate_limits = {
        "anonymous": 30,
        "demo": 100,
        "basic": 200,
        "premium": 500,
        "enterprise": 1000,
        "test": 2000,
    }
    return rate_limits.get(user_type, 60)


def get_endpoint_priority(endpoint: str) -> float:
    """Get endpoint priority for rate limiting (lower = higher priority)."""
    priorities = {
        "health": 0.1,
        "analysis": 1.0,
        "games": 0.5,
        "training": 0.7,
    }
    
    for pattern, priority in priorities.items():
        if pattern in endpoint:
            return priority
    
    return 1.0  # Default priority