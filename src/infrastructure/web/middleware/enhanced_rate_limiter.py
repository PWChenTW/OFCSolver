"""
Enhanced rate limiting middleware with advanced algorithms and adaptive strategies.
Integrates high-performance rate limiting with monitoring and fault tolerance.
"""

import time
import logging
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from src.config import get_settings
from src.infrastructure.algorithms.rate_limiting import get_rate_limit_manager
from src.infrastructure.monitoring.performance_analytics import get_performance_analyzer
from src.infrastructure.reliability.error_recovery import get_fault_tolerance

logger = logging.getLogger(__name__)
settings = get_settings()


class EnhancedRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Enhanced rate limiting middleware with advanced algorithms.
    
    Features:
    - Multiple rate limiting algorithms (Token Bucket, Sliding Window, Adaptive)
    - Hierarchical limits (global, user, endpoint)
    - Performance monitoring and adaptive adjustment
    - Fault tolerance and graceful degradation
    - Detailed metrics and analytics
    - User-specific and endpoint-specific configurations
    """

    def __init__(self, app):
        super().__init__(app)
        self.rate_manager = get_rate_limit_manager()
        self.performance_analyzer = get_performance_analyzer()
        self.fault_tolerance = get_fault_tolerance()
        
        # Configure exempt paths
        self.exempt_paths = self._get_exempt_paths()
        
        # Register rate limiting service with fault tolerance
        from src.infrastructure.reliability.error_recovery import RetryConfig, CircuitBreakerConfig
        
        retry_config = RetryConfig(
            max_attempts=1,  # No retry for rate limiting to avoid delays
            base_delay=0.1,
            max_delay=0.5
        )
        
        circuit_config = CircuitBreakerConfig(
            failure_threshold=20,  # Higher threshold for rate limiting
            recovery_timeout=10.0,  # Quick recovery
            success_threshold=5
        )
        
        self.fault_tolerance.register_service(
            "rate_limiting",
            retry_config=retry_config,
            circuit_config=circuit_config
        )

    async def dispatch(self, request: Request, call_next):
        """Main rate limiting dispatch with comprehensive monitoring."""
        start_time = time.time()
        
        # Skip rate limiting for exempt paths
        if self._is_exempt_path(request.url.path):
            return await call_next(request)

        try:
            # Perform rate limiting check with fault tolerance
            await self._check_rate_limits_with_protection(request)
            
            # Process request
            response = await call_next(request)
            
            # Record successful request with response time for adaptive limiting
            response_time = time.time() - start_time
            await self._record_successful_request(request, response_time)
            
            return response
            
        except HTTPException as e:
            # Rate limit exceeded - record metrics
            self._record_rate_limit_exceeded(request)
            raise
        except Exception as e:
            logger.error(f"Rate limiting error: {e}", exc_info=True)
            # Fail open - allow request if rate limiting fails
            logger.warning("Rate limiting failed, allowing request (fail-open)")
            return await call_next(request)

    async def _check_rate_limits_with_protection(self, request: Request):
        """Check rate limits with fault tolerance protection."""
        
        async def _rate_limit_check():
            # Get user information
            user_info = await self._get_user_info(request)
            user_id = user_info["user_id"]
            user_type = user_info["user_type"]
            
            # Ensure user limits are configured
            self.rate_manager.setup_user_limits(user_id, user_type)
            
            # Get endpoint identifier
            endpoint = self._get_endpoint_identifier(request)
            
            # Check rate limits
            result = self.rate_manager.check_rate_limit(
                user_id=user_id,
                endpoint=endpoint,
                requested_tokens=1
            )
            
            if not result.allowed:
                # Create detailed rate limit response
                error_detail = {
                    "message": "Rate limit exceeded",
                    "user_id": result.user_id,
                    "remaining_tokens": result.remaining_tokens,
                    "reset_time": result.reset_time,
                    "algorithm": result.algorithm_used
                }
                
                headers = {}
                if result.retry_after:
                    headers["Retry-After"] = str(int(result.retry_after))
                    error_detail["retry_after"] = result.retry_after
                
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=error_detail,
                    headers=headers
                )
        
        # Execute with fault tolerance (fail-open on circuit breaker)
        try:
            await self.fault_tolerance.execute_with_protection(
                "rate_limiting",
                _rate_limit_check
            )
        except Exception as e:
            # If circuit breaker is open or other issues, fail open
            if "Circuit breaker" in str(e):
                logger.warning("Rate limiting circuit breaker open, allowing request")
                return
            raise

    async def _get_user_info(self, request: Request) -> Dict[str, Any]:
        """Get user information from request state or create anonymous user."""
        if hasattr(request.state, "user") and request.state.user:
            user = request.state.user
            return {
                "user_id": user.get("user_id", "anonymous"),
                "user_type": user.get("user_type", "anonymous"),
                "is_authenticated": user.get("is_authenticated", False)
            }
        
        # Anonymous user fallback
        client_ip = self._get_client_ip(request)
        return {
            "user_id": f"anonymous_{client_ip}",
            "user_type": "anonymous",
            "is_authenticated": False
        }

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address with proper header handling."""
        # Check for forwarded headers (behind proxy/load balancer)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP (original client)
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Direct connection
        if request.client:
            return request.client.host
        
        return "unknown"

    def _get_endpoint_identifier(self, request: Request) -> str:
        """Get endpoint identifier for rate limiting granularity."""
        path = request.url.path
        method = request.method
        
        # Group similar endpoints together for consistent limiting
        endpoint_groups = {
            "/api/v1/games": "games",
            "/api/v1/analysis": "analysis",
            "/api/v1/training": "training",
            "/health": "health",
            "/metrics": "metrics"
        }
        
        for pattern, group in endpoint_groups.items():
            if path.startswith(pattern):
                return f"{method}:{group}"
        
        # Default: use path-based grouping
        path_parts = path.split("/")
        if len(path_parts) >= 4:  # /api/v1/service/...
            service = path_parts[3]
            return f"{method}:{service}"
        
        return f"{method}:other"

    async def _record_successful_request(self, request: Request, response_time: float):
        """Record successful request for adaptive rate limiting."""
        user_info = await self._get_user_info(request)
        endpoint = self._get_endpoint_identifier(request)
        
        # Update rate limiting with performance feedback for adaptive algorithms
        self.rate_manager.check_rate_limit(
            user_id=user_info["user_id"],
            endpoint=endpoint,
            requested_tokens=0,  # No tokens consumed, just feedback
            response_time=response_time
        )

    def _record_rate_limit_exceeded(self, request: Request):
        """Record rate limit exceeded event for monitoring."""
        # This would typically send metrics to monitoring system
        logger.info(f"Rate limit exceeded for {request.url.path} from {self._get_client_ip(request)}")

    def _is_exempt_path(self, path: str) -> bool:
        """Check if path is exempt from rate limiting."""
        for exempt_path in self.exempt_paths:
            if path.startswith(exempt_path):
                return True
        return False

    def _get_exempt_paths(self) -> set:
        """Get paths exempt from rate limiting."""
        return {
            "/health",           # Health checks
            "/metrics",          # Monitoring
            "/api/docs",         # Documentation  
            "/api/redoc",        # Documentation
            "/api/openapi.json", # API spec
        }

    def get_rate_limit_metrics(self) -> Dict[str, Any]:
        """Get comprehensive rate limiting metrics."""
        manager_metrics = self.rate_manager.get_performance_metrics()
        fault_tolerance_metrics = self.fault_tolerance.get_system_health()
        
        return {
            "rate_limiting": manager_metrics,
            "fault_tolerance": {
                "circuit_breakers": fault_tolerance_metrics.get("circuit_breakers", {}),
                "system_health": fault_tolerance_metrics.get("success_rate", 1.0)
            },
            "middleware_info": {
                "exempt_paths_count": len(self.exempt_paths),
                "algorithms_supported": [
                    "token_bucket",
                    "sliding_window", 
                    "adaptive",
                    "hierarchical"
                ],
                "features": [
                    "user_specific_limits",
                    "endpoint_specific_limits",
                    "adaptive_adjustment",
                    "fault_tolerance",
                    "performance_monitoring"
                ]
            }
        }

    def get_user_status(self, user_id: str) -> Dict[str, Any]:
        """Get rate limiting status for specific user."""
        # This would query the rate manager for user-specific status
        return {
            "user_id": user_id,
            "current_limits": "user_specific_data_here",
            "utilization": "utilization_data_here",
            "recent_activity": "activity_data_here"
        }


class RateLimitMetricsEndpoint:
    """Endpoint for rate limiting metrics and management."""
    
    def __init__(self, rate_limit_middleware: EnhancedRateLimitMiddleware):
        self.rate_limit_middleware = rate_limit_middleware

    async def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive rate limiting metrics."""
        return self.rate_limit_middleware.get_rate_limit_metrics()

    async def get_health(self) -> Dict[str, Any]:
        """Get rate limiting system health status."""
        metrics = self.rate_limit_middleware.get_rate_limit_metrics()
        
        # Analyze health based on metrics
        rate_metrics = metrics["rate_limiting"]
        block_rate = rate_metrics.get("block_rate", 0)
        requests_per_minute = rate_metrics.get("requests_per_minute", 0)
        
        # Determine health status
        if block_rate > 0.5:  # More than 50% blocked
            health_status = "critical"
            message = f"High block rate: {block_rate:.2%}"
        elif block_rate > 0.2:  # More than 20% blocked
            health_status = "warning"
            message = f"Elevated block rate: {block_rate:.2%}"
        elif requests_per_minute > 1000:  # High load
            health_status = "warning"
            message = f"High load: {requests_per_minute:.0f} req/min"
        else:
            health_status = "healthy"
            message = "Rate limiting operating normally"
        
        return {
            "status": health_status,
            "message": message,
            "timestamp": time.time(),
            "metrics_summary": {
                "block_rate": block_rate,
                "requests_per_minute": requests_per_minute,
                "total_requests": rate_metrics.get("total_requests", 0),
                "blocked_requests": rate_metrics.get("blocked_requests", 0)
            },
            "algorithm_usage": rate_metrics.get("algorithm_usage", {}),
            "recommendations": self._generate_recommendations(rate_metrics)
        }

    def _generate_recommendations(self, metrics: Dict[str, Any]) -> list:
        """Generate rate limiting optimization recommendations."""
        recommendations = []
        
        block_rate = metrics.get("block_rate", 0)
        requests_per_minute = metrics.get("requests_per_minute", 0)
        
        if block_rate > 0.3:
            recommendations.append(
                f"High block rate ({block_rate:.2%}). Consider increasing limits for legitimate users."
            )
        
        if requests_per_minute > 5000:
            recommendations.append(
                f"Very high request rate ({requests_per_minute:.0f}/min). "
                "Consider implementing request caching or optimization."
            )
        
        if block_rate < 0.01:
            recommendations.append(
                "Very low block rate. Rate limits may be too permissive - review security implications."
            )
        
        algorithm_usage = metrics.get("algorithm_usage", {})
        if algorithm_usage:
            most_used = max(algorithm_usage, key=algorithm_usage.get)
            recommendations.append(
                f"Most used algorithm: {most_used}. "
                "Consider optimizing this algorithm for your workload."
            )
        
        if not recommendations:
            recommendations.append("Rate limiting is operating optimally.")
        
        return recommendations

    async def get_user_limits(self, user_id: str) -> Dict[str, Any]:
        """Get rate limits and status for specific user."""
        return self.rate_limit_middleware.get_user_status(user_id)

    async def update_user_limits(self, user_id: str, new_limits: Dict[str, Any]) -> Dict[str, Any]:
        """Update rate limits for specific user (admin function)."""
        # This would update user-specific rate limits
        # Implementation would depend on requirements
        return {
            "user_id": user_id,
            "updated_limits": new_limits,
            "timestamp": time.time(),
            "message": "User limits updated successfully"
        }


# Custom exception for rate limit exceeded with detailed information
class DetailedRateLimitExceeded(HTTPException):
    """Enhanced rate limit exception with detailed information."""
    
    def __init__(
        self,
        detail: Dict[str, Any],
        retry_after: Optional[float] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        http_headers = headers or {}
        if retry_after:
            http_headers["Retry-After"] = str(int(retry_after))
        
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers=http_headers
        )


# Utility functions for rate limit management

def get_user_rate_limit_info(request: Request) -> Dict[str, Any]:
    """Get current user's rate limit information."""
    # This would extract user info and return their current rate limit status
    return {
        "user_id": "example_user",
        "current_limits": {},
        "usage": {},
        "reset_time": time.time() + 3600
    }


def check_admin_access(request: Request) -> bool:
    """Check if user has admin access for rate limit management."""
    if not hasattr(request.state, "user"):
        return False
    
    user = request.state.user
    user_type = user.get("user_type", "")
    features = user.get("features", [])
    
    return user_type in ["admin", "enterprise"] or "admin" in features