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
async def test_client():
    """Test HTTP client."""
    from fastapi.testclient import TestClient

    from src.main import create_app

    app = create_app()
    with TestClient(app) as client:
        yield client
