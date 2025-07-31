"""
Main application entry point for the OFC Solver System.
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from src.infrastructure.web.middleware.auth_middleware import AuthenticationMiddleware
from src.infrastructure.web.middleware.rate_limiter import RateLimitMiddleware
from src.infrastructure.web.api.game_controller import router as game_router
from src.infrastructure.web.api.analysis_controller import router as analysis_router
from src.infrastructure.web.api.training_controller import router as training_router
from src.infrastructure.monitoring.health_checker import router as health_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/app.log")
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting OFC Solver System...")
    
    # Initialize database connections
    # Initialize Redis connections
    # Initialize background task queues
    # Warm up caches
    
    logger.info("OFC Solver System started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down OFC Solver System...")
    
    # Close database connections
    # Close Redis connections
    # Stop background tasks
    # Clean up resources
    
    logger.info("OFC Solver System shutdown completed")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    """
    app = FastAPI(
        title="OFC Solver API",
        description="Open Face Chinese Poker Solver with advanced GTO calculations",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan
    )
    
    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Add custom middleware (will be implemented later)
    # app.add_middleware(AuthenticationMiddleware)
    # app.add_middleware(RateLimitMiddleware)
    
    # Include routers
    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(game_router, prefix="/api/v1/games", tags=["games"])
    app.include_router(analysis_router, prefix="/api/v1/analysis", tags=["analysis"])
    app.include_router(training_router, prefix="/api/v1/training", tags=["training"])
    
    return app


def run_server():
    """
    Run the development server.
    """
    app = create_app()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    run_server()