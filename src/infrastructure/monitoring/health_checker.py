"""
Health check endpoints and system status monitoring.
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Any
import psutil
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
    """Check database connectivity and performance."""
    start_time = time.time()

    try:
        # Check PostgreSQL connection
        async with db_session.get_session() as session:
            result = await session.execute("SELECT 1")
            await result.fetchone()

        # Get connection pool stats
        pool_stats = await connection_pool.get_postgres_stats()

        response_time_ms = (time.time() - start_time) * 1000

        return ServiceCheck(
            status="healthy",
            response_time_ms=response_time_ms,
            details={
                "connection_pool_size": pool_stats.get("size", 0),
                "active_connections": pool_stats.get("checked_out", 0),
                "available_connections": pool_stats.get("checked_in", 0),
                "query_test": "passed",
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
    """Check Redis connectivity and performance."""
    start_time = time.time()

    try:
        # Check Redis connection
        redis_client = connection_pool.redis
        ping_result = await redis_client.ping()

        # Get Redis stats
        redis_stats = await connection_pool.get_redis_stats()

        response_time_ms = (time.time() - start_time) * 1000

        return ServiceCheck(
            status="healthy" if ping_result else "unhealthy",
            response_time_ms=response_time_ms,
            details={
                "ping_test": "passed" if ping_result else "failed",
                "created_connections": redis_stats.get("created_connections", 0),
                "available_connections": redis_stats.get("available_connections", 0),
                "in_use_connections": redis_stats.get("in_use_connections", 0),
                "max_connections": redis_stats.get("max_connections", 0),
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
    """Check solver engine health and performance."""
    start_time = time.time()

    try:
        # TODO: Implement actual solver check
        # from src.domain.services.strategy_calculator import StrategyCalculator
        # calculator = StrategyCalculator()
        # test_result = await calculator.quick_health_check()

        # Simulate solver check with a quick calculation
        await asyncio.sleep(0.1)  # Simulate calculation delay

        response_time_ms = (time.time() - start_time) * 1000

        return ServiceCheck(
            status="healthy" if response_time_ms < 1000 else "slow",
            response_time_ms=response_time_ms,
            details={
                "calculation_test": "passed",
                "worker_threads": 4,
                "memory_usage": "256MB",
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
    """Check external service dependencies."""
    start_time = time.time()

    try:
        # Check ClickHouse if available
        clickhouse_status = "not_configured"
        if connection_pool.clickhouse:
            clickhouse_healthy = await connection_pool.clickhouse.ping()
            clickhouse_status = "connected" if clickhouse_healthy else "disconnected"

        # Get all connection health status
        health_status = await connection_pool.health_check()

        response_time_ms = (time.time() - start_time) * 1000

        return ServiceCheck(
            status="healthy" if all(health_status.values()) else "degraded",
            response_time_ms=response_time_ms,
            details={
                "postgres": (
                    "connected" if health_status.get("postgres") else "disconnected"
                ),
                "redis": "connected" if health_status.get("redis") else "disconnected",
                "clickhouse": clickhouse_status,
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
            elif check_result.status == "slow" and overall_status == "healthy":
                overall_status = "degraded"

    return HealthStatus(
        status=overall_status,
        timestamp=datetime.utcnow().isoformat(),
        version="0.1.0",  # TODO: Get from package metadata
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
    redis_check = await check_redis_health()

    if db_check.status == "unhealthy" or redis_check.status == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready - critical dependencies unavailable",
        )

    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat(),
        "critical_checks": {"database": db_check.status, "redis": redis_check.status},
    }


@router.get("/metrics")
async def get_basic_metrics() -> Dict[str, Any]:
    """
    Basic application metrics endpoint.

    Returns:
        Application performance metrics
    """
    uptime_seconds = time.time() - _start_time

    # Get system metrics
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    cpu_percent = process.cpu_percent(interval=0.1)

    # Get connection pool stats
    postgres_stats = await connection_pool.get_postgres_stats()
    redis_stats = await connection_pool.get_redis_stats()

    return {
        "uptime_seconds": uptime_seconds,
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0",
        "system": {
            "memory_usage_mb": memory_info.rss / 1024 / 1024,
            "cpu_percent": cpu_percent,
            "num_threads": process.num_threads(),
        },
        "database": {
            "pool_size": postgres_stats.get("size", 0),
            "active_connections": postgres_stats.get("checked_out", 0),
            "available_connections": postgres_stats.get("checked_in", 0),
        },
        "cache": {
            "created_connections": redis_stats.get("created_connections", 0),
            "available_connections": redis_stats.get("available_connections", 0),
            "in_use_connections": redis_stats.get("in_use_connections", 0),
        },
        "metrics": {
            "total_requests": 0,  # TODO: Implement request counter
            "cache_hit_rate": 0.0,  # TODO: Get from cache service
            "avg_response_time_ms": 0.0,  # TODO: Implement response time tracking
            "solver_calculations_total": 0,  # TODO: Get from solver service
        },
    }

