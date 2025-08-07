"""
Authentication middleware for API Key and JWT support.
MVP implementation with basic authentication for protected endpoints.
"""

import logging
from typing import Set, Optional, Dict, Any
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware supporting API Key and JWT authentication.
    
    MVP Features:
    - API Key authentication for basic protection
    - Public endpoints bypass authentication
    - Request context enrichment with user info
    - Simple rate limiting by authentication status
    """

    def __init__(self, app):
        super().__init__(app)
        self.public_paths = self._get_public_paths()
        self.api_keys = self._get_valid_api_keys()

    async def dispatch(self, request: Request, call_next):
        # Skip authentication for public paths
        if self._is_public_path(request.url.path):
            request.state.user = {"user_id": "anonymous", "is_authenticated": False}
            return await call_next(request)

        # Check for API key authentication
        try:
            user_info = await self._authenticate_request(request)
            request.state.user = user_info
            return await call_next(request)
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"Authentication error: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service error"
            )

    def _is_public_path(self, path: str) -> bool:
        """Check if path requires authentication."""
        for public_path in self.public_paths:
            if path.startswith(public_path):
                return True
        return False

    def _get_public_paths(self) -> Set[str]:
        """Get list of public paths that don't require authentication."""
        return {
            "/health",
            "/api/docs",
            "/api/redoc", 
            "/api/openapi.json",
            "/api/v1/analysis/calculate-strategy",  # MVP: Basic strategy calculation is public
            "/api/v1/training/scenarios/random",    # MVP: Random scenarios are public
        }

    def _get_valid_api_keys(self) -> Set[str]:
        """Get valid API keys for authentication."""
        # MVP: Simple hardcoded API keys
        # In production, this would come from database or secure storage
        return {
            "ofc-solver-demo-key-2024",  # Demo key
            "ofc-solver-test-key-2024",  # Test key
        }

    async def _authenticate_request(self, request: Request) -> Dict[str, Any]:
        """Authenticate the request and return user information."""
        
        # Try API Key authentication first
        api_key = self._extract_api_key(request)
        if api_key:
            return await self._authenticate_api_key(api_key)

        # Try JWT authentication (for future implementation)
        jwt_token = self._extract_jwt_token(request)
        if jwt_token:
            return await self._authenticate_jwt_token(jwt_token)

        # No authentication provided
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    def _extract_api_key(self, request: Request) -> Optional[str]:
        """Extract API key from request headers or query parameters."""
        
        # Check Authorization header (preferred)
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("ApiKey "):
            return auth_header[7:]  # Remove "ApiKey " prefix
        
        # Check X-API-Key header
        api_key_header = request.headers.get("x-api-key")
        if api_key_header:
            return api_key_header
        
        # Check query parameter (less secure, for development only)
        if not settings.is_production:
            return request.query_params.get("api_key")
        
        return None

    def _extract_jwt_token(self, request: Request) -> Optional[str]:
        """Extract JWT token from Authorization header."""
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]  # Remove "Bearer " prefix
        return None

    async def _authenticate_api_key(self, api_key: str) -> Dict[str, Any]:
        """Authenticate using API key."""
        
        if api_key not in self.api_keys:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )

        # MVP: Simple user mapping based on API key
        user_mapping = {
            "ofc-solver-demo-key-2024": {
                "user_id": "demo_user",
                "user_type": "demo",
                "rate_limit": 100,  # requests per minute
                "features": ["basic_analysis", "game_management"]
            },
            "ofc-solver-test-key-2024": {
                "user_id": "test_user", 
                "user_type": "test",
                "rate_limit": 1000,
                "features": ["all"]
            }
        }

        user_info = user_mapping.get(api_key, {
            "user_id": "unknown",
            "user_type": "basic",
            "rate_limit": 60,
            "features": ["basic_analysis"]
        })

        user_info.update({
            "is_authenticated": True,
            "authentication_method": "api_key"
        })

        return user_info

    async def _authenticate_jwt_token(self, token: str) -> Dict[str, Any]:
        """Authenticate using JWT token (placeholder for future implementation)."""
        
        # MVP: Placeholder for JWT authentication
        # In phase 2, this would:
        # 1. Validate JWT signature
        # 2. Check expiration
        # 3. Extract user claims
        # 4. Validate against user database
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT authentication not yet implemented"
        )


# Dependency functions for FastAPI

async def get_current_user(request: Request) -> Dict[str, Any]:
    """Get current user from request state."""
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found in request state"
        )
    return request.state.user


async def require_authentication(request: Request) -> Dict[str, Any]:
    """Require authenticated user."""
    user = await get_current_user(request)
    if not user.get("is_authenticated", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user


def require_feature(feature: str):
    """Require specific feature access - returns a dependency function."""
    async def _require_feature(request: Request) -> Dict[str, Any]:
        user = await require_authentication(request)
        
        user_features = user.get("features", [])
        if "all" not in user_features and feature not in user_features:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Feature '{feature}' not available for your plan"
            )
        
        return user
    
    return _require_feature


# Pre-defined feature dependencies for common use cases
async def require_advanced_analysis(request: Request) -> Dict[str, Any]:
    """Require advanced analysis feature."""
    return await require_feature("advanced_analysis")(request)


async def require_training_access(request: Request) -> Dict[str, Any]:
    """Require training feature access."""
    return await require_feature("training")(request)


async def require_game_management(request: Request) -> Dict[str, Any]:
    """Require game management feature."""
    return await require_feature("game_management")(request)