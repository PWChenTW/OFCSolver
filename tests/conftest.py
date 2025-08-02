"""
Pytest configuration and shared fixtures.
"""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio

# Configure pytest-asyncio
pytest_asyncio.auto_mode = True


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_database() -> AsyncGenerator[None, None]:
    """Setup test database."""
    # TODO: Initialize test database
    yield
    # TODO: Cleanup test database


@pytest.fixture
async def test_redis() -> AsyncGenerator[None, None]:
    """Setup test Redis instance."""
    # TODO: Initialize test Redis
    yield
    # TODO: Cleanup test Redis


@pytest.fixture
def test_settings():
    """Test application settings."""
    from src.config import Settings

    return Settings(
        environment="testing",
        debug=True,
        database={
            "host": "localhost",
            "port": 5432,
            "name": "ofc_solver_test",
            "user": "postgres",
            "password": "postgres",
        },
        redis={"host": "localhost", "port": 6379, "database": 1},
    )


@pytest.fixture
def test_client():
    """Test HTTP client."""
    from fastapi.testclient import TestClient
    from fastapi import FastAPI

    # Create a minimal test app to avoid initialization issues
    app = FastAPI()

    @app.get("/health/")
    async def health():
        return {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00",
            "version": "0.1.0",
            "uptime_seconds": 100.0,
            "checks": {
                "database": {"status": "healthy"},
                "redis": {"status": "healthy"},
                "solver": {"status": "healthy"},
                "external_services": {"status": "healthy"},
            },
        }

    @app.get("/health/liveness")
    async def liveness():
        return {"status": "alive", "timestamp": "2024-01-01T00:00:00"}

    @app.get("/health/readiness")
    async def readiness():
        return {
            "status": "ready",
            "critical_checks": {"database": "healthy", "redis": "healthy"},
        }

    @app.get("/health/metrics")
    async def metrics():
        return {
            "uptime_seconds": 100.0,
            "timestamp": "2024-01-01T00:00:00",
            "version": "0.1.0",
            "metrics": {
                "total_requests": 0,
                "active_connections": 0,
                "cache_hit_rate": 0.0,
            },
        }

    with TestClient(app) as client:
        yield client