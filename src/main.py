"""
Main application entry point for the OFC Solver System.
MVP implementation with integrated middleware stack and dependency injection.
"""

import logging
import sys
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

# Import middleware
from src.infrastructure.web.middleware.auth_middleware import AuthenticationMiddleware
from src.infrastructure.web.middleware.rate_limiter import RateLimitMiddleware
from src.infrastructure.web.middleware.error_handler import ErrorHandlerMiddleware

# Import routers
from src.infrastructure.web.api.game_controller import router as game_router
from src.infrastructure.web.api.analysis_controller import router as analysis_router
from src.infrastructure.web.api.training_controller import router as training_router
from src.infrastructure.monitoring.health_checker import router as health_router

# Import infrastructure components
from src.infrastructure.database.connection_pool import connection_pool
from src.infrastructure.database.session import db_session
from src.infrastructure.web.dependencies import initialize_dependencies, shutdown_dependencies
from src.config import get_settings

# Configure logging
import os

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("logs/app.log")],
)

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting OFC Solver System...")

    try:
        # Initialize dependencies
        initialize_dependencies()
        logger.info("Dependencies initialized")

        # Initialize all connection pools
        await connection_pool.initialize()
        logger.info("Connection pools initialized")

        # Initialize database session
        db_session.init()
        logger.info("Database session initialized")

        # Warm up connections
        health_status = await connection_pool.health_check()
        logger.info(f"Connection health status: {health_status}")

        logger.info("🚀 OFC Solver System started successfully")

    except Exception as e:
        logger.error(f"Failed to start OFC Solver System: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down OFC Solver System...")

    try:
        # Shutdown dependencies
        shutdown_dependencies()

        # Close all connections
        await connection_pool.shutdown()

        # Close database session
        await db_session.close()

        logger.info("✅ OFC Solver System shutdown completed")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application with full middleware stack.
    """
    app = FastAPI(
        title="OFC Solver API",
        description="Open Face Chinese Poker Solver with advanced GTO calculations",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # Add request ID middleware (for tracing)
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        """Add unique request ID for tracing."""
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    # Add middleware stack (order matters!)
    
    # 1. CORS - Handle cross-origin requests first
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.security.allowed_origins,
        allow_credentials=True,
        allow_methods=settings.security.allowed_methods,
        allow_headers=settings.security.allowed_headers,
    )

    # 2. GZip - Compress responses
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # 3. Error handling - Catch and format errors
    app.add_middleware(ErrorHandlerMiddleware)

    # 4. Rate limiting - Throttle requests
    if not settings.is_development:  # Skip rate limiting in development
        app.add_middleware(RateLimitMiddleware)

    # 5. Authentication - Authenticate users (optional for MVP)
    if settings.environment != "development":  # Enable auth in non-dev environments
        app.add_middleware(AuthenticationMiddleware)

    # Include routers
    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(game_router, prefix="/api/v1/games", tags=["games"])
    app.include_router(analysis_router, prefix="/api/v1/analysis", tags=["analysis"])
    app.include_router(training_router, prefix="/api/v1/training", tags=["training"])

    # Add custom routes
    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "name": "OFC Solver API",
            "version": "0.1.0",
            "status": "active",
            "environment": settings.environment,
            "docs": "/api/docs",
            "health": "/health",
        }

    @app.get("/api/v1")
    async def api_info():
        """API version information."""
        return {
            "version": "v1",
            "endpoints": {
                "games": "/api/v1/games",
                "analysis": "/api/v1/analysis", 
                "training": "/api/v1/training",
                "health": "/health",
            },
            "features": {
                "authentication": "API Key",
                "rate_limiting": "Enabled" if not settings.is_development else "Disabled",
                "error_handling": "Standardized",
                "monitoring": "Basic",
            },
        }

    return app


def run_server():
    """
    Run the development server with optimized configuration.
    """
    app = create_app()

    # Development server configuration
    server_config = {
        "host": settings.api_host,
        "port": settings.api_port,
        "log_level": "info",
        "access_log": True,
    }

    # Add reload in development
    if settings.is_development:
        server_config.update({
            "reload": True,
            "reload_dirs": ["src"],
            "reload_excludes": ["*.pyc", "__pycache__"],
        })

    logger.info(f"Starting server on {settings.api_host}:{settings.api_port}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    
    if settings.is_development:
        logger.info("📚 API Documentation: http://localhost:8000/api/docs")
        logger.info("🔍 Alternative docs: http://localhost:8000/api/redoc")
        logger.info("❤️  Health check: http://localhost:8000/health")

    uvicorn.run(app, **server_config)


def run_production_server():
    """
    Run the production server with optimized settings.
    """
    app = create_app()
    
    # Production server configuration
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        workers=4,  # Multiple workers for production
        loop="uvloop",  # Faster event loop
        http="httptools",  # Faster HTTP parser
        log_level="warning",  # Less verbose logging
        access_log=False,  # Disable access log for performance
        server_header=False,  # Hide server header for security
    )


if __name__ == "__main__":
    if settings.is_production:
        run_production_server()
    else:
        run_server()