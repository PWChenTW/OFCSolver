"""
Analysis API controller.
Handles strategy calculation, position analysis, and solver operations.
MVP implementation connecting to existing query processors.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field

from src.application.queries.analysis_queries import (
    GetAnalysisSessionQuery,
    GetAnalysisHistoryQuery,
    GetAnalysisResultQuery,
    GetStrategyRecommendationsQuery,
    CompareAnalysisResultsQuery,
    GetAnalysisSessionHandler,
    GetAnalysisHistoryHandler,
    GetAnalysisResultHandler,
    GetStrategyRecommendationsHandler,
    CompareAnalysisResultsHandler,
    AnalysisType,
    ResultFormat,
)
from src.application.queries import PaginationParams, DateRangeFilter
from src.infrastructure.web.middleware.auth_middleware import get_current_user, require_advanced_analysis
from src.infrastructure.web.dependencies import (
    get_analysis_command_handler,
    get_analysis_query_handler,
)

router = APIRouter()


# ===== Request Models =====

class PositionRequest(BaseModel):
    """Request model for position analysis."""
    
    players_hands: Dict[str, Dict[str, List[str]]] = Field(
        ..., 
        description="Player hands mapping with front/middle/back positions",
        example={
            "player_1": {
                "front": ["As", "Kh"], 
                "middle": ["Qd", "Jc", "10s"], 
                "back": ["9h", "8d", "7c", "6s", "5h"]
            }
        }
    )
    remaining_cards: List[str] = Field(
        ..., 
        description="Remaining cards in deck",
        example=["2h", "3c", "4d", "Ts"]
    )
    current_player: int = Field(..., description="Current player index", ge=0, le=3)
    round_number: int = Field(..., description="Current round number", ge=1, le=3)


class AnalysisRequest(BaseModel):
    """Request model for strategy analysis."""
    
    position: PositionRequest
    calculation_mode: str = Field(
        default="standard",
        description="Calculation mode: instant, standard, exhaustive",
        pattern="^(instant|standard|exhaustive)$"
    )
    max_calculation_time_seconds: int = Field(
        default=60, 
        description="Maximum calculation time", 
        ge=1, 
        le=300
    )
    monte_carlo_samples: Optional[int] = Field(
        default=None, 
        description="Number of Monte Carlo samples",
        ge=1000,
        le=1000000
    )
    force_recalculate: bool = Field(
        default=False, 
        description="Force recalculation even if cached"
    )


class CompareStrategiesRequest(BaseModel):
    """Request model for comparing multiple strategies."""
    
    positions: List[PositionRequest] = Field(
        ..., 
        description="List of positions to analyze",
        min_items=2,
        max_items=5
    )
    calculation_mode: str = Field(
        default="standard",
        pattern="^(instant|standard|exhaustive)$"
    )
    comparison_metrics: List[str] = Field(
        default=["expected_value", "confidence", "calculation_time"],
        description="Metrics to compare"
    )


# ===== Response Models =====

class StrategyResponse(BaseModel):
    """Response model for calculated strategy."""
    
    session_id: str
    strategy: Dict[str, Any]
    expected_value: float
    confidence: float
    calculation_method: str
    calculation_time_ms: int
    cache_hit: bool = False
    task_id: Optional[str] = None
    status: str = "completed"
    alternative_moves: List[Dict[str, Any]] = []
    reasoning: Optional[str] = None


class TaskStatusResponse(BaseModel):
    """Response model for background task status."""
    
    task_id: str
    status: str  # queued, processing, completed, failed
    progress_percentage: Optional[int] = None
    estimated_completion_time: Optional[str] = None
    result: Optional[StrategyResponse] = None
    error: Optional[str] = None


class AnalysisHistoryResponse(BaseModel):
    """Response model for analysis history."""
    
    id: str
    analysis_type: str
    status: str
    created_at: str
    completed_at: Optional[str]
    progress: float
    parameters: Dict[str, Any]


class AnalysisComparisonResponse(BaseModel):
    """Response model for strategy comparison."""
    
    session_ids: List[str]
    metrics: Dict[str, List[float]]
    summary: Dict[str, Any]
    charts: List[Dict[str, Any]]


class APIResponse(BaseModel):
    """Standard API response wrapper."""
    
    success: bool = True
    data: Any
    message: Optional[str] = None
    request_id: Optional[str] = None


# ===== Helper Functions =====

def create_success_response(data: Any, message: Optional[str] = None, request: Optional[Request] = None) -> APIResponse:
    """Create standardized success response."""
    return APIResponse(
        success=True,
        data=data,
        message=message,
        request_id=getattr(request.state, "request_id", None) if request else None
    )


# ===== Core Endpoints =====

@router.post("/calculate-strategy", response_model=APIResponse, status_code=status.HTTP_200_OK)
async def calculate_strategy(
    request_body: AnalysisRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    command_handler=Depends(get_analysis_command_handler),
) -> APIResponse:
    """
    Calculate optimal strategy for given position.
    
    This is the core functionality of the OFC Solver system.
    Supports different calculation modes with appropriate timeouts.
    
    **Public endpoint** - No authentication required for MVP.
    
    Args:
        request_body: Analysis request parameters
        request: FastAPI request object
        background_tasks: FastAPI background tasks
        command_handler: Injected command handler
    
    Returns:
        Calculated strategy with confidence metrics
    
    Raises:
        HTTPException: If calculation fails or invalid parameters
    """
    try:
        # Input validation
        if not request_body.position.players_hands:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Player hands are required"
            )
        
        if not request_body.position.remaining_cards:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Remaining cards are required"
            )
        
        # For MVP, we'll create a mock analysis session
        session_id = str(uuid4())
        
        # Determine calculation timeout based on mode
        timeout_mapping = {
            "instant": 5,
            "standard": 30,
            "exhaustive": 120
        }
        
        actual_timeout = min(
            request_body.max_calculation_time_seconds,
            timeout_mapping.get(request_body.calculation_mode, 30)
        )
        
        # Mock strategy calculation for MVP
        strategy_data = {
            "recommended_action": "place_card",
            "card": request_body.position.remaining_cards[0] if request_body.position.remaining_cards else "As",
            "position": "middle",
            "reasoning": f"Optimal placement based on {request_body.calculation_mode} analysis",
            "alternatives": [
                {
                    "action": "place_front",
                    "expected_value": 2.1,
                    "confidence": 0.85
                },
                {
                    "action": "place_back", 
                    "expected_value": 1.9,
                    "confidence": 0.82
                }
            ]
        }
        
        response_data = StrategyResponse(
            session_id=session_id,
            strategy=strategy_data,
            expected_value=2.5,
            confidence=0.95,
            calculation_method=request_body.calculation_mode,
            calculation_time_ms=min(actual_timeout * 1000, 5000),  # Mock timing
            cache_hit=False,
            status="completed",
            alternative_moves=strategy_data["alternatives"],
            reasoning=strategy_data["reasoning"]
        )
        
        return create_success_response(
            data=response_data,
            message="Strategy calculated successfully",
            request=request
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid position or parameters: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Strategy calculation failed: {str(e)}"
        )


@router.get("/sessions/{session_id}", response_model=APIResponse)
async def get_analysis_session(
    session_id: UUID,
    request: Request,
    include_calculations: bool = True,
    result_format: ResultFormat = ResultFormat.SUMMARY,
    user=Depends(get_current_user)
) -> APIResponse:
    """
    Get analysis session by ID.
    
    **Requires authentication** for accessing user's analysis history.
    
    Args:
        session_id: Analysis session identifier
        request: FastAPI request object
        include_calculations: Include calculation results
        result_format: Format for results (summary, detailed, tree_view, chart_data)
        user: Current authenticated user
    
    Returns:
        Analysis session information
    """
    try:
        # Mock query creation for MVP
        query = GetAnalysisSessionQuery(
            session_id=session_id,
            include_calculations=include_calculations,
            result_format=result_format
        )
        
        # For MVP, return mock data
        mock_session = {
            "id": str(session_id),
            "user_id": user.get("user_id", "anonymous"),
            "analysis_type": "position",
            "status": "completed",
            "created_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat(),
            "progress": 100.0,
            "parameters": {
                "calculation_mode": "standard",
                "position_hash": "abc123"
            }
        }
        
        calculations = None
        if include_calculations:
            calculations = [
                {
                    "session_id": str(session_id),
                    "position_id": str(uuid4()),
                    "ev_results": {"total": 2.5, "front": 0.5, "middle": 1.0, "back": 1.0},
                    "optimal_strategy": {"action": "place_middle", "confidence": 0.95},
                    "confidence_intervals": {"total": (2.2, 2.8)},
                    "calculation_time": 2.5,
                    "iterations": 10000
                }
            ]
        
        response_data = {
            "session": mock_session,
            "calculations": calculations
        }
        
        return create_success_response(
            data=response_data,
            message="Analysis session retrieved successfully",
            request=request
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analysis session: {str(e)}"
        )


@router.get("/history", response_model=APIResponse)
async def get_analysis_history(
    request: Request,
    limit: int = 20,
    offset: int = 0,
    analysis_type: Optional[AnalysisType] = None,
    user=Depends(get_current_user)
) -> APIResponse:
    """
    Get analysis history with pagination and filtering.
    
    **Requires authentication** to access user's history.
    
    Args:
        request: FastAPI request object
        limit: Maximum number of results to return (max 100)
        offset: Number of results to skip
        analysis_type: Filter by analysis type
        user: Current authenticated user
    
    Returns:
        Paginated list of analysis sessions
    """
    try:
        # Validate pagination parameters
        if limit > 100:
            limit = 100
        if limit < 1:
            limit = 20
        if offset < 0:
            offset = 0
        
        # Create pagination params
        pagination = PaginationParams(
            page=offset // limit + 1,
            page_size=limit,
            sort_by="created_at",
            sort_order="desc"
        )
        
        # Mock query for MVP
        query = GetAnalysisHistoryQuery(
            user_id=UUID(user.get("user_id", str(uuid4()))),
            analysis_type=analysis_type,
            pagination=pagination
        )
        
        # Mock response data
        mock_sessions = []
        for i in range(min(limit, 5)):  # Return up to 5 mock sessions
            mock_sessions.append(AnalysisHistoryResponse(
                id=str(uuid4()),
                analysis_type=analysis_type.value if analysis_type else "position",
                status="completed",
                created_at=datetime.now().isoformat(),
                completed_at=datetime.now().isoformat(),
                progress=100.0,
                parameters={"calculation_mode": "standard"}
            ))
        
        response_data = {
            "sessions": {
                "items": mock_sessions,
                "total": len(mock_sessions),
                "page": pagination.page,
                "page_size": pagination.page_size,
                "has_next": False,
                "has_prev": offset > 0
            }
        }
        
        return create_success_response(
            data=response_data,
            message=f"Retrieved {len(mock_sessions)} analysis sessions",
            request=request
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analysis history: {str(e)}"
        )


@router.post("/compare-strategies", response_model=APIResponse)
async def compare_strategies(
    request_body: CompareStrategiesRequest,
    request: Request,
    user=Depends(require_advanced_analysis)
) -> APIResponse:
    """
    Compare strategies for multiple positions.
    
    **Requires authentication and advanced_analysis feature**.
    
    Args:
        request_body: Comparison request with multiple positions
        request: FastAPI request object
        user: Current authenticated user with required features
    
    Returns:
        Comparison results with metrics and charts
    """
    try:
        if len(request_body.positions) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least 2 positions required for comparison"
            )
        
        # Create mock session IDs for each position
        session_ids = [str(uuid4()) for _ in request_body.positions]
        
        # Mock comparison query
        query = CompareAnalysisResultsQuery(
            session_ids=session_ids,
            comparison_metrics=request_body.comparison_metrics,
            result_format=ResultFormat.CHART_DATA
        )
        
        # Mock comparison results
        metrics = {}
        for metric in request_body.comparison_metrics:
            if metric == "expected_value":
                metrics[metric] = [2.5, 2.3, 2.7][:len(request_body.positions)]
            elif metric == "confidence":
                metrics[metric] = [0.95, 0.92, 0.97][:len(request_body.positions)]
            elif metric == "calculation_time":
                metrics[metric] = [2500, 3000, 2200][:len(request_body.positions)]
            else:
                metrics[metric] = [1.0] * len(request_body.positions)
        
        response_data = AnalysisComparisonResponse(
            session_ids=session_ids,
            metrics=metrics,
            summary={
                "best_position": 0,
                "average_ev": sum(metrics.get("expected_value", [0])) / len(request_body.positions),
                "ev_variance": 0.05
            },
            charts=[
                {
                    "type": "bar",
                    "title": "Expected Value Comparison",
                    "data": {
                        "labels": [f"Position {i+1}" for i in range(len(request_body.positions))],
                        "values": metrics.get("expected_value", [])
                    }
                }
            ]
        )
        
        return create_success_response(
            data=response_data,
            message=f"Compared {len(request_body.positions)} strategies successfully",
            request=request
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Strategy comparison failed: {str(e)}"
        )


@router.get("/statistics", response_model=APIResponse)
async def get_analysis_statistics(
    request: Request,
    user=Depends(get_current_user)
) -> APIResponse:
    """
    Get analysis statistics and performance metrics.
    
    **Requires authentication** to access personalized statistics.
    
    Args:
        request: FastAPI request object
        user: Current authenticated user
    
    Returns:
        Analysis statistics and performance metrics
    """
    try:
        # Mock statistics for MVP
        stats = {
            "user_stats": {
                "total_calculations": 42,
                "avg_calculation_time_ms": 2500,
                "favorite_calculation_mode": "standard",
                "total_time_saved_by_cache": 15000
            },
            "system_stats": {
                "total_calculations_today": 156,
                "avg_system_load": 0.65,
                "cache_hit_rate": 0.75,
                "active_users": 23
            },
            "calculations_by_method": {
                "instant": 15,
                "standard": 25,
                "exhaustive": 2
            },
            "recent_performance": [
                {"timestamp": datetime.now().isoformat(), "calculation_time": 2100, "success": True},
                {"timestamp": datetime.now().isoformat(), "calculation_time": 2800, "success": True},
                {"timestamp": datetime.now().isoformat(), "calculation_time": 1900, "success": True}
            ]
        }
        
        return create_success_response(
            data=stats,
            message="Statistics retrieved successfully",
            request=request
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


# ===== Health Check Endpoint =====

@router.get("/health", response_model=APIResponse)
async def analysis_health_check(request: Request) -> APIResponse:
    """
    Health check for analysis service.
    
    **Public endpoint** - No authentication required.
    """
    return create_success_response(
        data={
            "service": "analysis",
            "status": "healthy",
            "features": {
                "strategy_calculation": True,
                "position_analysis": True,
                "batch_comparison": True,
                "historical_data": True
            },
            "performance": {
                "avg_response_time_ms": 2500,
                "success_rate": 0.98,
                "cache_hit_rate": 0.75
            }
        },
        message="Analysis service is healthy",
        request=request
    )