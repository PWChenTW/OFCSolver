"""
Health check endpoints and system status monitoring.
MVP implementation with basic health checks.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import psutil
import os

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from src.infrastructure.database.connection_pool import connection_pool
from src.infrastructure.database.session import db_session

router = APIRouter()
logger = logging.getLogger(__name__)


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


class WorkflowMonitorData(BaseModel):
    """Workflow monitoring data for TASK-014"""
    
    workflow_id: str
    status: str
    progress_percentage: float
    started_at: str
    estimated_completion: Optional[str] = None
    current_step: Optional[str] = None


class OrchestratorMetrics(BaseModel):
    """Orchestrator performance metrics"""
    
    active_workflows: int
    completed_today: int
    failed_today: int
    avg_execution_time_ms: float
    circuit_breaker_open: bool
    error_rate_percentage: float


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


# TASK-014 Orchestrator Monitoring Endpoints

@router.get("/orchestrator/metrics", response_model=OrchestratorMetrics)
async def get_orchestrator_metrics() -> OrchestratorMetrics:
    """
    Get Analysis Orchestrator performance metrics.
    
    Returns:
        Current orchestrator performance data
    """
    try:
        # TODO: Get actual metrics from OrchestratorService
        # For MVP, return mock data with realistic values
        return OrchestratorMetrics(
            active_workflows=3,
            completed_today=45,
            failed_today=2,
            avg_execution_time_ms=8500.0,
            circuit_breaker_open=False,
            error_rate_percentage=4.2
        )
    except Exception as e:
        logger.error(f"Failed to get orchestrator metrics: {e}")
        # Return safe defaults
        return OrchestratorMetrics(
            active_workflows=0,
            completed_today=0,
            failed_today=0,
            avg_execution_time_ms=0.0,
            circuit_breaker_open=False,
            error_rate_percentage=0.0
        )


@router.get("/orchestrator/workflows", response_model=List[WorkflowMonitorData])
async def get_active_workflows() -> List[WorkflowMonitorData]:
    """
    Get list of active analysis workflows.
    
    Returns:
        List of currently running workflows
    """
    try:
        # TODO: Get actual workflows from OrchestratorService
        # For MVP, return mock data
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        mock_workflows = [
            WorkflowMonitorData(
                workflow_id="wf_001",
                status="running",
                progress_percentage=65.0,
                started_at=(now - timedelta(minutes=3)).isoformat(),
                estimated_completion=(now + timedelta(minutes=2)).isoformat(),
                current_step="calculate_standard"
            ),
            WorkflowMonitorData(
                workflow_id="wf_002",
                status="running",
                progress_percentage=30.0,
                started_at=(now - timedelta(minutes=1)).isoformat(),
                estimated_completion=(now + timedelta(minutes=4)).isoformat(),
                current_step="validate_position"
            )
        ]
        
        return mock_workflows
    except Exception as e:
        logger.error(f"Failed to get active workflows: {e}")
        return []


@router.get("/orchestrator/workflows/{workflow_id}", response_model=Dict[str, Any])
async def get_workflow_details(workflow_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific workflow.
    
    Args:
        workflow_id: Workflow identifier
        
    Returns:
        Detailed workflow information
        
    Raises:
        HTTPException: If workflow not found
    """
    try:
        # TODO: Get actual workflow from OrchestratorService
        # For MVP, return mock data based on workflow_id
        from datetime import datetime, timedelta
        
        if workflow_id in ["wf_001", "wf_002"]:
            return {
                "workflow_id": workflow_id,
                "name": f"Analysis Workflow {workflow_id}",
                "status": "running",
                "progress_percentage": 65.0,
                "created_at": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
                "started_at": (datetime.utcnow() - timedelta(minutes=3)).isoformat(),
                "estimated_duration_seconds": 300,
                "execution_time_ms": 180000,
                "steps": [
                    {"step_id": "validate", "status": "completed", "execution_time_ms": 50},
                    {"step_id": "calculate", "status": "running", "execution_time_ms": None},
                    {"step_id": "aggregate", "status": "pending", "execution_time_ms": None}
                ],
                "current_step": "calculate_standard",
                "error_message": None
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow details: {str(e)}"
        )


@router.get("/orchestrator/dashboard", response_model=Dict[str, Any])
async def get_orchestrator_dashboard() -> Dict[str, Any]:
    """
    Get comprehensive orchestrator dashboard data.
    
    Returns:
        Dashboard overview with key metrics and active workflows
    """
    try:
        # Get metrics and workflows
        metrics = await get_orchestrator_metrics()
        workflows = await get_active_workflows()
        
        # Get system health from existing endpoint
        health_status = await health_check()
        
        return {
            "system_health": health_status.status,
            "timestamp": datetime.utcnow().isoformat(),
            "orchestrator_metrics": metrics.dict(),
            "active_workflows": [w.dict() for w in workflows],
            "summary": {
                "total_active": len(workflows),
                "system_status": health_status.status,
                "error_rate": metrics.error_rate_percentage,
                "avg_response_time_ms": metrics.avg_execution_time_ms
            }
        }
    except Exception as e:
        logger.error(f"Failed to get orchestrator dashboard: {e}")
        return {
            "system_health": "unknown",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }
