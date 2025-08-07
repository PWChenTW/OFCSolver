"""
Health check endpoints and system status monitoring.
MVP implementation with basic health checks.
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Any
import os

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from src.infrastructure.database.connection_pool import connection_pool
from src.infrastructure.database.session import db_session

router = APIRouter()


class HealthStatus(BaseModel):
    """Health check status model."""

    status: str
    timestamp: str
    version: str
    uptime_seconds: float
    checks: Dict[str, Any]


class ServiceCheck(BaseModel):
    """Individual service check model."""

    status: str
    response_time_ms: float
    details: Dict[str, Any] = {}


# Track application start time for uptime calculation
_start_time = time.time()


async def check_database_health() -> ServiceCheck:
    """Check database connectivity and performance - MVP version."""
    start_time = time.time()

    try:
        # Check if connection pool is initialized
        if not connection_pool._initialized:
            raise Exception("Connection pool not initialized")

        # Try to get connection stats
        pool_stats = await connection_pool.get_postgres_stats()

        response_time_ms = (time.time() - start_time) * 1000

        return ServiceCheck(
            status="healthy" if pool_stats.get("status") != "not_initialized" else "degraded",
            response_time_ms=response_time_ms,
            details={
                "connection_pool_status": pool_stats.get("status", "unknown"),
                "pool_size": pool_stats.get("size", "N/A"),
                "active_connections": pool_stats.get("checked_out", "N/A"),
                "available_connections": pool_stats.get("checked_in", "N/A"),
            },
        )
    except Exception as e:
        response_time_ms = (time.time() - start_time) * 1000
        return ServiceCheck(
            status="unhealthy",
            response_time_ms=response_time_ms,
            details={"error": str(e)},
        )


async def check_redis_health() -> ServiceCheck:
    """Check Redis connectivity - MVP placeholder."""
    start_time = time.time()

    try:
        # Use mock Redis for MVP
        redis_client = connection_pool.redis
        ping_result = await redis_client.ping()

        response_time_ms = (time.time() - start_time) * 1000

        return ServiceCheck(
            status="healthy" if ping_result else "unhealthy",
            response_time_ms=response_time_ms,
            details={
                "ping_test": "passed" if ping_result else "failed",
                "implementation": "mvp_mock",
                "note": "Using mock Redis for MVP"
            },
        )
    except Exception as e:
        response_time_ms = (time.time() - start_time) * 1000
        return ServiceCheck(
            status="unhealthy",
            response_time_ms=response_time_ms,
            details={"error": str(e)},
        )


async def check_solver_health() -> ServiceCheck:
    """Check solver engine health - MVP placeholder."""
    start_time = time.time()

    try:
        # Simulate solver check with a quick calculation
        await asyncio.sleep(0.1)  # Simulate calculation delay

        response_time_ms = (time.time() - start_time) * 1000

        return ServiceCheck(
            status="healthy" if response_time_ms < 1000 else "slow",
            response_time_ms=response_time_ms,
            details={
                "calculation_test": "passed",
                "implementation": "mvp_mock",
                "note": "Using mock solver for MVP"
            },
        )
    except Exception as e:
        response_time_ms = (time.time() - start_time) * 1000
        return ServiceCheck(
            status="unhealthy",
            response_time_ms=response_time_ms,
            details={"error": str(e)},
        )


async def check_external_services_health() -> ServiceCheck:
    """Check external service dependencies - MVP version."""
    start_time = time.time()

    try:
        # Get all connection health status
        health_status = await connection_pool.health_check()

        response_time_ms = (time.time() - start_time) * 1000

        return ServiceCheck(
            status="healthy" if health_status.get("postgres", False) else "degraded",
            response_time_ms=response_time_ms,
            details={
                "postgres": (
                    "connected" if health_status.get("postgres") else "disconnected"
                ),
                "redis": "mocked_healthy",
                "clickhouse": "not_implemented_in_mvp",
            },
        )
    except Exception as e:
        response_time_ms = (time.time() - start_time) * 1000
        return ServiceCheck(
            status="unhealthy",
            response_time_ms=response_time_ms,
            details={"error": str(e)},
        )


@router.get("/", response_model=HealthStatus)
async def health_check() -> HealthStatus:
    """
    Comprehensive health check endpoint.

    Returns overall system health with individual service checks.

    Returns:
        System health status with detailed check results
    """
    uptime_seconds = time.time() - _start_time

    # Run all health checks concurrently
    db_check, redis_check, solver_check, external_check = await asyncio.gather(
        check_database_health(),
        check_redis_health(),
        check_solver_health(),
        check_external_services_health(),
        return_exceptions=True,
    )

    # Handle any exceptions from health checks
    checks = {}
    overall_status = "healthy"

    for check_name, check_result in [
        ("database", db_check),
        ("redis", redis_check),
        ("solver", solver_check),
        ("external_services", external_check),
    ]:
        if isinstance(check_result, Exception):
            checks[check_name] = ServiceCheck(
                status="error", response_time_ms=0, details={"error": str(check_result)}
            ).dict()
            overall_status = "unhealthy"
        else:
            checks[check_name] = check_result.dict()
            if check_result.status in ["unhealthy", "error"]:
                overall_status = "unhealthy"
            elif check_result.status in ["slow", "degraded"] and overall_status == "healthy":
                overall_status = "degraded"

    return HealthStatus(
        status=overall_status,
        timestamp=datetime.utcnow().isoformat(),
        version="0.1.0-mvp",
        uptime_seconds=uptime_seconds,
        checks=checks,
    )


@router.get("/liveness")
async def liveness_check() -> Dict[str, str]:
    """
    Simple liveness check for Kubernetes.

    Returns:
        Basic status indicating the service is running
    """
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


@router.get("/readiness")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check for Kubernetes.

    Checks if the service is ready to handle requests.

    Returns:
        Readiness status with key dependency checks

    Raises:
        HTTPException: If service is not ready
    """
    # Check critical dependencies only
    db_check = await check_database_health()
    
    # For MVP, we're more permissive - only fail if database is completely unhealthy
    if db_check.status == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready - database unavailable",
        )

    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat(),
        "critical_checks": {"database": db_check.status},
        "note": "MVP version - reduced dependency requirements"
    }


@router.get("/metrics")
async def get_basic_metrics() -> Dict[str, Any]:
    """
    Basic application metrics endpoint.

    Returns:
        Application performance metrics
    """
    uptime_seconds = time.time() - _start_time

    # Get connection pool stats
    postgres_stats = await connection_pool.get_postgres_stats()
    redis_stats = await connection_pool.get_redis_stats()

    return {
        "uptime_seconds": uptime_seconds,
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0-mvp",
        "system": {
            "process_id": os.getpid(),
            "implementation": "mvp",
        },
        "database": {
            "status": postgres_stats.get("status", "unknown"),
            "pool_size": postgres_stats.get("size", "N/A"),
            "active_connections": postgres_stats.get("checked_out", "N/A"),
            "available_connections": postgres_stats.get("checked_in", "N/A"),
        },
        "cache": {
            "status": redis_stats.get("status", "unknown"),
            "implementation": "mock_for_mvp",
        },
        "metrics": {
            "total_requests": 0,  # TODO: Implement request counter
            "cache_hit_rate": 0.0,  # Placeholder for MVP
            "avg_response_time_ms": 0.0,  # Placeholder for MVP
            "solver_calculations_total": 0,  # Placeholder for MVP
        },
    }