"""
Enhanced authentication middleware with advanced security algorithms.
Integrates secure API key management, JWT support, and performance monitoring.
"""

import time
import logging
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from src.config import get_settings
from src.infrastructure.security.auth_algorithms import get_auth_service
from src.infrastructure.monitoring.performance_analytics import get_performance_analyzer
from src.infrastructure.reliability.error_recovery import get_fault_tolerance

logger = logging.getLogger(__name__)
settings = get_settings()


class EnhancedAuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Enhanced authentication middleware with advanced security features.
    
    Features:
    - Secure API Key authentication with hashing and expiration
    - Full JWT authentication support with RSA signatures
    - Performance monitoring and metrics collection
    - Fault tolerance with circuit breaker protection
    - Constant-time comparison to prevent timing attacks
    - Comprehensive security auditing
    """

    def __init__(self, app):
        super().__init__(app)
        self.auth_service = get_auth_service()
        self.performance_analyzer = get_performance_analyzer()
        self.fault_tolerance = get_fault_tolerance()
        
        # Configure public paths
        self.public_paths = self._get_public_paths()
        
        # Register authentication service with fault tolerance
        from src.infrastructure.reliability.error_recovery import RetryConfig, CircuitBreakerConfig
        
        retry_config = RetryConfig(
            max_attempts=2,  # Quick retry for auth
            base_delay=0.1,
            max_delay=1.0,
            retry_on_exceptions=(ConnectionError, TimeoutError)
        )
        
        circuit_config = CircuitBreakerConfig(
            failure_threshold=10,  # Auth service is critical
            recovery_timeout=30.0,
            success_threshold=5
        )
        
        self.fault_tolerance.register_service(
            "authentication",
            retry_config=retry_config,
            circuit_config=circuit_config
        )

    async def dispatch(self, request: Request, call_next):
        """Main authentication dispatch with comprehensive monitoring."""
        start_time = time.time()
        auth_method = "none"
        success = False
        
        try:
            # Skip authentication for public paths
            if self._is_public_path(request.url.path):
                request.state.user = {
                    "user_id": "anonymous",
                    "user_type": "anonymous", 
                    "is_authenticated": False,
                    "rate_limit": 30,
                    "features": []
                }
                success = True
                return await call_next(request)

            # Perform authentication with fault tolerance
            user_info = await self._authenticate_with_protection(request)
            request.state.user = user_info
            
            auth_method = user_info.get("authentication_method", "unknown")
            success = True
            
            return await call_next(request)
            
        except HTTPException as e:
            # Re-raise HTTP exceptions (expected auth failures)
            raise
        except Exception as e:
            logger.error(f"Unexpected authentication error: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service temporarily unavailable"
            )
        finally:
            # Record authentication metrics
            duration = time.time() - start_time
            self.performance_analyzer.record_authentication(
                method=auth_method,
                success=success,
                duration=duration
            )

    async def _authenticate_with_protection(self, request: Request) -> Dict[str, Any]:
        """Authenticate request with fault tolerance protection."""
        
        async def _auth_operation():
            # Extract credentials
            api_key = self._extract_api_key(request)
            jwt_token = self._extract_jwt_token(request)
            
            # Authenticate using enhanced service
            auth_result = await self.auth_service.authenticate(
                api_key=api_key,
                jwt_token=jwt_token
            )
            
            if not auth_result.success:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=auth_result.error_message or "Authentication failed",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Convert auth result to user info
            return {
                "user_id": auth_result.user_id,
                "user_type": auth_result.user_type,
                "is_authenticated": True,
                "rate_limit": auth_result.rate_limit,
                "features": auth_result.features,
                "authentication_method": auth_result.auth_method.value,
                "expires_at": auth_result.expires_at
            }
        
        # Execute with fault tolerance
        return await self.fault_tolerance.execute_with_protection(
            "authentication",
            _auth_operation
        )

    def _is_public_path(self, path: str) -> bool:
        """Check if path requires authentication."""
        for public_path in self.public_paths:
            if path.startswith(public_path):
                return True
        return False

    def _get_public_paths(self) -> set:
        """Get list of public paths that don't require authentication."""
        return {
            # System endpoints
            "/health",
            "/metrics",
            
            # API documentation
            "/api/docs",
            "/api/redoc",
            "/api/openapi.json",
            
            # Public API endpoints (MVP)
            "/api/v1/analysis/calculate-strategy",  # Basic strategy calculation
            "/api/v1/training/scenarios/random",    # Random training scenarios
            
            # Root endpoints
            "/",
            "/api/v1"
        }

    def _extract_api_key(self, request: Request) -> Optional[str]:
        """
        Extract API key from request with multiple fallback methods.
        Prioritizes most secure methods first.
        """
        # Method 1: Authorization header with ApiKey scheme (most secure)
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("ApiKey "):
            return auth_header[7:]  # Remove "ApiKey " prefix
        
        # Method 2: X-API-Key header (common standard)
        api_key_header = request.headers.get("x-api-key")
        if api_key_header:
            return api_key_header
        
        # Method 3: Custom header (for compatibility)
        custom_key = request.headers.get("api-key")
        if custom_key:
            return custom_key
        
        # Method 4: Query parameter (only in development, least secure)
        if settings.is_development:
            query_key = request.query_params.get("api_key")
            if query_key:
                logger.warning("API key passed as query parameter - insecure in production")
                return query_key
        
        return None

    def _extract_jwt_token(self, request: Request) -> Optional[str]:
        """Extract JWT token from Authorization header."""
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]  # Remove "Bearer " prefix
        return None

    def get_auth_metrics(self) -> Dict[str, Any]:
        """Get comprehensive authentication metrics."""
        auth_service_metrics = self.auth_service.get_auth_metrics()
        fault_tolerance_metrics = self.fault_tolerance.get_system_health()
        
        return {
            "auth_service": auth_service_metrics,
            "fault_tolerance": fault_tolerance_metrics,
            "middleware_info": {
                "public_paths_count": len(self.public_paths),
                "supported_methods": ["API_KEY", "JWT"],
                "security_features": [
                    "constant_time_comparison",
                    "api_key_expiration", 
                    "jwt_rs256_signatures",
                    "fault_tolerance",
                    "performance_monitoring"
                ]
            }
        }


class AuthenticationMetricsEndpoint:
    """Endpoint for authentication metrics and health checks."""
    
    def __init__(self, auth_middleware: EnhancedAuthenticationMiddleware):
        self.auth_middleware = auth_middleware

    async def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive authentication metrics."""
        return self.auth_middleware.get_auth_metrics()

    async def get_health(self) -> Dict[str, Any]:
        """Get authentication system health status."""
        auth_service = get_auth_service()
        fault_tolerance = get_fault_tolerance()
        
        auth_metrics = auth_service.get_auth_metrics()
        system_health = fault_tolerance.get_system_health()
        
        # Determine health status
        success_rate = auth_metrics.get("success_rate", 0)
        system_success_rate = system_health.get("success_rate", 0)
        
        if success_rate > 0.95 and system_success_rate > 0.95:
            health_status = "healthy"
        elif success_rate > 0.90 and system_success_rate > 0.90:
            health_status = "warning"
        else:
            health_status = "critical"
        
        return {
            "status": health_status,
            "timestamp": time.time(),
            "auth_success_rate": success_rate,
            "system_success_rate": system_success_rate,
            "uptime_seconds": auth_metrics.get("uptime_seconds", 0),
            "total_auth_requests": auth_metrics.get("total_requests", 0),
            "circuit_breakers": system_health.get("circuit_breakers", {}),
            "recommendations": self._generate_health_recommendations(
                success_rate, system_success_rate
            )
        }

    def _generate_health_recommendations(
        self, 
        auth_success_rate: float, 
        system_success_rate: float
    ) -> list:
        """Generate health improvement recommendations."""
        recommendations = []
        
        if auth_success_rate < 0.95:
            recommendations.append(
                "Authentication success rate below 95%. Check API key validity and JWT configuration."
            )
        
        if system_success_rate < 0.95:
            recommendations.append(
                "System success rate below 95%. Check downstream services and circuit breaker status."
            )
        
        if auth_success_rate < 0.90:
            recommendations.append(
                "Critical: Authentication success rate below 90%. Immediate investigation required."
            )
        
        if not recommendations:
            recommendations.append("Authentication system is healthy. Continue monitoring.")
        
        return recommendations


# Dependency functions for FastAPI with enhanced features

async def get_current_user(request: Request) -> Dict[str, Any]:
    """
    Get current user from request state with validation.
    Enhanced with additional security checks.
    """
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication context not found"
        )
    
    user = request.state.user
    
    # Validate user context integrity
    required_fields = ["user_id", "is_authenticated"]
    for field in required_fields:
        if field not in user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid authentication context"
            )
    
    return user


async def require_authentication(request: Request) -> Dict[str, Any]:
    """
    Require authenticated user with enhanced validation.
    """
    user = await get_current_user(request)
    
    if not user.get("is_authenticated", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for this endpoint"
        )
    
    # Check token expiration for JWT
    expires_at = user.get("expires_at")
    if expires_at and time.time() > expires_at.timestamp():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired"
        )
    
    return user


async def require_feature(feature: str):
    """
    Require specific feature access with detailed error messages.
    """
    async def _require_feature(request: Request) -> Dict[str, Any]:
        user = await require_authentication(request)
        
        user_features = user.get("features", [])
        user_type = user.get("user_type", "unknown")
        
        # Check feature access
        if "all" not in user_features and feature not in user_features:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Feature '{feature}' not available for {user_type} users. "
                       f"Available features: {', '.join(user_features)}"
            )
        
        return user
    
    return _require_feature


async def require_user_type(allowed_types: list):
    """
    Require specific user types for access control.
    """
    async def _require_user_type(request: Request) -> Dict[str, Any]:
        user = await require_authentication(request)
        
        user_type = user.get("user_type", "unknown")
        
        if user_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required user types: {', '.join(allowed_types)}. "
                       f"Your type: {user_type}"
            )
        
        return user
    
    return _require_user_type


# Convenience functions for common access patterns

async def require_demo_or_higher(request: Request) -> Dict[str, Any]:
    """Require demo user or higher access level."""
    checker = await require_user_type(["demo", "basic", "premium", "enterprise", "test"])
    return await checker(request)


async def require_premium_access(request: Request) -> Dict[str, Any]:
    """Require premium user access level."""
    checker = await require_user_type(["premium", "enterprise", "test"])
    return await checker(request)


async def require_analysis_feature(request: Request) -> Dict[str, Any]:
    """Require analysis feature access."""
    checker = await require_feature("basic_analysis")
    return await checker(request)