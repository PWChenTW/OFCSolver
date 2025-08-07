"""
Error handling middleware for consistent error responses.
MVP implementation with basic error mapping and response formatting.
"""

import logging
import traceback
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling exceptions and formatting error responses.
    
    MVP Features:
    - Map domain exceptions to HTTP status codes
    - Consistent error response format
    - Environment-based error detail levels
    - Error logging with request context
    """

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            return await self._handle_exception(request, exc)

    async def _handle_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle exception and return formatted error response."""
        
        # Log the error with request context
        logger.error(
            f"Exception in {request.method} {request.url}: {str(exc)}",
            extra={
                "request_id": getattr(request.state, "request_id", None),
                "user_agent": request.headers.get("user-agent"),
                "client_ip": request.client.host if request.client else None,
            },
            exc_info=not settings.is_production
        )

        # Map exception to HTTP response
        if isinstance(exc, HTTPException):
            return self._create_error_response(
                status_code=exc.status_code,
                error_code=self._get_error_code(exc),
                message=exc.detail,
                request=request
            )

        # Domain exceptions mapping
        error_mapping = self._get_error_mapping()
        exc_type = type(exc).__name__
        
        if exc_type in error_mapping:
            status_code, error_code, message = error_mapping[exc_type]
            return self._create_error_response(
                status_code=status_code,
                error_code=error_code,
                message=message or str(exc),
                request=request
            )

        # Unknown exceptions
        return self._create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred" if settings.is_production else str(exc),
            request=request,
            include_trace=not settings.is_production
        )

    def _get_error_mapping(self) -> Dict[str, tuple]:
        """Map domain exceptions to HTTP responses."""
        return {
            # Validation errors
            "ValidationError": (status.HTTP_400_BAD_REQUEST, "VALIDATION_ERROR", None),
            "ValueError": (status.HTTP_400_BAD_REQUEST, "INVALID_INPUT", None),
            
            # Not found errors
            "GameNotFoundError": (status.HTTP_404_NOT_FOUND, "GAME_NOT_FOUND", None),
            "PositionNotFoundError": (status.HTTP_404_NOT_FOUND, "POSITION_NOT_FOUND", None),
            
            # Business logic errors
            "InvalidGameStateError": (status.HTTP_409_CONFLICT, "INVALID_GAME_STATE", None),
            "CalculationTimeoutError": (status.HTTP_408_REQUEST_TIMEOUT, "CALCULATION_TIMEOUT", None),
            "ResourceExhaustionError": (status.HTTP_503_SERVICE_UNAVAILABLE, "RESOURCE_EXHAUSTION", None),
            
            # Authentication/Authorization
            "AuthenticationError": (status.HTTP_401_UNAUTHORIZED, "AUTHENTICATION_FAILED", None),
            "AuthorizationError": (status.HTTP_403_FORBIDDEN, "ACCESS_DENIED", None),
            
            # Rate limiting
            "RateLimitExceededError": (status.HTTP_429_TOO_MANY_REQUESTS, "RATE_LIMIT_EXCEEDED", None),
        }

    def _get_error_code(self, exc: HTTPException) -> str:
        """Extract error code from HTTPException."""
        if hasattr(exc, "error_code"):
            return exc.error_code
        
        # Default error codes based on status code
        status_code_mapping = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED", 
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            409: "CONFLICT",
            422: "UNPROCESSABLE_ENTITY",
            429: "TOO_MANY_REQUESTS",
            500: "INTERNAL_SERVER_ERROR",
            502: "BAD_GATEWAY",
            503: "SERVICE_UNAVAILABLE",
        }
        
        return status_code_mapping.get(exc.status_code, "UNKNOWN_ERROR")

    def _create_error_response(
        self,
        status_code: int,
        error_code: str,
        message: str,
        request: Request,
        include_trace: bool = False
    ) -> JSONResponse:
        """Create standardized error response."""
        
        error_data = {
            "error": {
                "code": error_code,
                "message": message,
                "timestamp": self._get_current_timestamp(),
                "path": str(request.url.path),
                "method": request.method,
            }
        }
        
        # Add request ID if available
        if hasattr(request.state, "request_id"):
            error_data["error"]["request_id"] = request.state.request_id
        
        # Add trace in development
        if include_trace:
            error_data["error"]["trace"] = traceback.format_exc()
        
        return JSONResponse(
            status_code=status_code,
            content=error_data
        )
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()


# Custom HTTPException with error code
class APIException(HTTPException):
    """Custom HTTPException with error code support."""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code