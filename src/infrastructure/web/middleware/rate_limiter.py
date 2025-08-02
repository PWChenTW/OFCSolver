"""Rate limiting middleware to prevent API abuse."""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to handle rate limiting for API requests."""

    async def dispatch(self, request: Request, call_next):
        """Process the request and apply rate limiting logic."""
        # For now, just pass through - rate limiting can be added later
        response = await call_next(request)
        return response