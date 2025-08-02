"""Authentication middleware for API security."""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware to handle authentication for API requests."""

    async def dispatch(self, request: Request, call_next):
        """Process the request and apply authentication logic."""
        # For now, just pass through - authentication can be added later
        response = await call_next(request)
        return response