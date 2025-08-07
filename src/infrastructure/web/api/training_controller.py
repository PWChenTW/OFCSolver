"""
Training API controller.
Handles training sessions, progress tracking, and scenario management.
MVP implementation connecting to existing query processors.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field

from src.application.queries.training_queries import (
    GetTrainingSessionQuery,
    GetUserProgressQuery,
    GetTrainingHistoryQuery,
    GetScenarioStatsQuery,
    GetLeaderboardQuery,
    GetPersonalBestsQuery,
    GetRecommendedScenariosQuery,
    GetTrainingSessionHandler,
    GetUserProgressHandler,
    GetTrainingHistoryHandler,
    GetScenarioStatsHandler,
    GetLeaderboardHandler,
    GetPersonalBestsHandler,
    GetRecommendedScenariosHandler,
    ProgressMetric,
    LeaderboardType,
)
from src.application.queries import PaginationParams, DateRangeFilter, TimeRange
from src.domain.value_objects.difficulty import DifficultyLevel
from src.infrastructure.web.middleware.auth_middleware import get_current_user, require_training_access
from src.infrastructure.web.dependencies import (
    get_training_command_handler,
    get_training_query_handler,
)

router = APIRouter()


# ===== Request Models =====

class StartTrainingSessionRequest(BaseModel):
    """Request model for starting a new training session."""
    
    scenario_id: UUID = Field(..., description="Scenario to practice")
    difficulty: DifficultyLevel = Field(
        default=DifficultyLevel.MEDIUM,
        description="Difficulty level for the session"
    )
    max_exercises: int = Field(
        default=10,
        description="Maximum number of exercises in the session",
        ge=1,
        le=50
    )
    time_limit_minutes: Optional[int] = Field(
        default=None,
        description="Optional time limit in minutes",
        ge=5,
        le=120
    )
    training_mode: str = Field(
        default="guided",
        description="Training mode: guided, timed, freestyle",
        pattern="^(guided|timed|freestyle)$"
    )


class SubmitAnswerRequest(BaseModel):
    """Request model for submitting an exercise answer."""
    
    exercise_id: UUID = Field(..., description="Exercise identifier")
    user_action: str = Field(..., description="User's action/answer")
    time_taken_seconds: float = Field(
        ...,
        description="Time taken to answer in seconds",
        ge=0,
        le=300
    )
    used_hints: int = Field(
        default=0,
        description="Number of hints used",
        ge=0,
        le=5
    )


class GetProgressRequest(BaseModel):
    """Request model for getting user progress."""
    
    date_range_days: Optional[int] = Field(
        default=30,
        description="Number of days to look back",
        ge=1,
        le=365
    )
    scenario_ids: Optional[List[UUID]] = Field(
        default=None,
        description="Filter by specific scenarios"
    )
    difficulty_levels: Optional[List[DifficultyLevel]] = Field(
        default=None,
        description="Filter by difficulty levels"
    )
    metrics: List[ProgressMetric] = Field(
        default=[ProgressMetric.ACCURACY, ProgressMetric.SPEED, ProgressMetric.IMPROVEMENT],
        description="Metrics to include in progress report"
    )


# ===== Response Models =====

class TrainingSessionResponse(BaseModel):
    """Response model for training session information."""
    
    id: str
    user_id: str
    scenario_id: str
    scenario_name: str
    difficulty: str
    started_at: str
    completed_at: Optional[str]
    is_completed: bool
    score: float
    exercises_completed: int
    exercises_total: int
    average_accuracy: float
    time_elapsed_minutes: float


class ExerciseResponse(BaseModel):
    """Response model for exercise result."""
    
    id: str
    position_id: str
    question: str
    user_action: Optional[str]
    optimal_action: str
    is_correct: Optional[bool]
    ev_difference: Optional[float]
    time_taken: Optional[float]
    hints_used: int
    explanation: str


class ProgressResponse(BaseModel):
    """Response model for user progress."""
    
    user_id: str
    total_sessions: int
    completed_sessions: int
    total_time_spent_hours: float
    average_accuracy: float
    improvement_rate: float
    current_streak: int
    best_streak: int
    achievements: List[str]
    progress_by_difficulty: Dict[str, Dict[str, float]]
    progress_by_scenario: Dict[str, Dict[str, float]]
    recent_trend: Dict[str, List[float]]


class LeaderboardEntryResponse(BaseModel):
    """Response model for leaderboard entry."""
    
    rank: int
    user_id: str
    username: str
    score: float
    accuracy: float
    sessions_completed: int
    total_time_hours: float
    badge: Optional[str]


class PersonalBestResponse(BaseModel):
    """Response model for personal best."""
    
    scenario_id: str
    scenario_name: str
    difficulty: str
    best_score: float
    best_accuracy: float
    fastest_time_minutes: float
    achieved_at: str
    session_id: str


class ScenarioRecommendationResponse(BaseModel):
    """Response model for scenario recommendation."""
    
    scenario_id: str
    scenario_name: str
    recommended_difficulty: str
    reason: str
    expected_challenge_level: float
    estimated_completion_minutes: float
    skills_to_practice: List[str]


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

@router.post("/sessions", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def start_training_session(
    request_body: StartTrainingSessionRequest,
    request: Request,
    user=Depends(get_current_user),
    command_handler=Depends(get_training_command_handler),
) -> APIResponse:
    """
    Start a new training session.
    
    **Requires authentication** to track user progress.
    
    Args:
        request_body: Training session parameters
        request: FastAPI request object
        user: Current authenticated user
        command_handler: Injected command handler
    
    Returns:
        Created training session information
    """
    try:
        # Generate session ID for MVP
        session_id = str(uuid4())
        
        # Mock scenario name lookup
        scenario_names = {
            "basic": "Basic Hand Analysis",
            "intermediate": "Intermediate Position Play",
            "advanced": "Advanced GTO Strategy",
            "fantasy": "Fantasy Land Scenarios"
        }
        
        # Create mock training session
        mock_session = TrainingSessionResponse(
            id=session_id,
            user_id=user.get("user_id", "anonymous"),
            scenario_id=str(request_body.scenario_id),
            scenario_name=scenario_names.get("basic", "Practice Scenario"),
            difficulty=request_body.difficulty.value,
            started_at=datetime.now().isoformat(),
            completed_at=None,
            is_completed=False,
            score=0.0,
            exercises_completed=0,
            exercises_total=request_body.max_exercises,
            average_accuracy=0.0,
            time_elapsed_minutes=0.0
        )
        
        return create_success_response(
            data=mock_session,
            message="Training session started successfully",
            request=request
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start training session: {str(e)}"
        )


@router.get("/sessions/{session_id}", response_model=APIResponse)
async def get_training_session(
    session_id: UUID,
    request: Request,
    include_exercises: bool = True,
    include_performance: bool = True,
    user=Depends(get_current_user)
) -> APIResponse:
    """
    Get training session by ID.
    
    **Requires authentication** to access user's training data.
    
    Args:
        session_id: Training session identifier
        request: FastAPI request object
        include_exercises: Include detailed exercise results
        include_performance: Include performance analysis
        user: Current authenticated user
    
    Returns:
        Training session information
    """
    try:
        # Mock query creation for MVP
        query = GetTrainingSessionQuery(
            session_id=session_id,
            include_exercises=include_exercises,
            include_performance=include_performance
        )
        
        # Mock session data
        mock_session = TrainingSessionResponse(
            id=str(session_id),
            user_id=user.get("user_id", "anonymous"),
            scenario_id=str(uuid4()),
            scenario_name="Basic Hand Analysis",
            difficulty="medium",
            started_at=datetime.now().isoformat(),
            completed_at=datetime.now().isoformat(),
            is_completed=True,
            score=85.5,
            exercises_completed=8,
            exercises_total=10,
            average_accuracy=0.85,
            time_elapsed_minutes=15.5
        )
        
        response_data = {"session": mock_session}
        
        if include_exercises:
            mock_exercises = [
                ExerciseResponse(
                    id=str(uuid4()),
                    position_id=str(uuid4()),
                    question="Where should you place Ace of Spades?",
                    user_action="front",
                    optimal_action="back",
                    is_correct=False,
                    ev_difference=-0.5,
                    time_taken=25.0,
                    hints_used=1,
                    explanation="Ace of Spades has higher value in back hand for scoring"
                ),
                ExerciseResponse(
                    id=str(uuid4()),
                    position_id=str(uuid4()),
                    question="Best placement for pair of Kings?",
                    user_action="middle",
                    optimal_action="middle",
                    is_correct=True,
                    ev_difference=0.0,
                    time_taken=18.0,
                    hints_used=0,
                    explanation="Pair of Kings is strong for middle hand"
                )
            ]
            response_data["exercises"] = mock_exercises
        
        if include_performance:
            response_data["performance_summary"] = {
                "accuracy": 0.85,
                "speed_score": 0.75,
                "improvement": 0.12,
                "strengths": ["pair_recognition", "basic_strategy"],
                "weaknesses": ["high_card_placement", "timing"]
            }
        
        return create_success_response(
            data=response_data,
            message="Training session retrieved successfully",
            request=request
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get training session: {str(e)}"
        )


@router.post("/sessions/{session_id}/submit-answer", response_model=APIResponse)
async def submit_exercise_answer(
    session_id: UUID,
    request_body: SubmitAnswerRequest,
    request: Request,
    user=Depends(get_current_user),
    command_handler=Depends(get_training_command_handler),
) -> APIResponse:
    """
    Submit answer for an exercise in a training session.
    
    **Requires authentication** to track user progress.
    
    Args:
        session_id: Training session identifier
        request_body: Answer submission data
        request: FastAPI request object
        user: Current authenticated user
        command_handler: Injected command handler
    
    Returns:
        Exercise result and feedback
    """
    try:
        # Mock answer evaluation for MVP
        optimal_action = "middle"  # Mock optimal action
        is_correct = request_body.user_action == optimal_action
        ev_difference = 0.0 if is_correct else -0.3
        
        result = {
            "exercise_id": str(request_body.exercise_id),
            "is_correct": is_correct,
            "user_action": request_body.user_action,
            "optimal_action": optimal_action,
            "ev_difference": ev_difference,
            "time_taken": request_body.time_taken_seconds,
            "hints_used": request_body.used_hints,
            "feedback": "Correct! Good placement." if is_correct else "Consider the hand strength distribution.",
            "explanation": "The middle hand should contain moderate strength hands.",
            "score_earned": 10 if is_correct else 5,
            "next_exercise_available": True
        }
        
        return create_success_response(
            data=result,
            message="Answer submitted successfully",
            request=request
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit answer: {str(e)}"
        )


@router.get("/progress/{user_id}", response_model=APIResponse)
async def get_user_progress(
    user_id: UUID,
    request: Request,
    days_back: int = 30,
    scenario_ids: Optional[str] = None,
    current_user=Depends(get_current_user)
) -> APIResponse:
    """
    Get user's training progress and statistics.
    
    **Requires authentication** and user must access own data or have admin rights.
    
    Args:
        user_id: User identifier
        request: FastAPI request object
        days_back: Number of days to look back
        scenario_ids: Comma-separated scenario IDs to filter
        current_user: Current authenticated user
    
    Returns:
        User progress and statistics
    """
    try:
        # Check if user can access this data
        if str(user_id) != current_user.get("user_id") and current_user.get("user_type") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access other user's progress data"
            )
        
        # Parse scenario filter
        scenario_list = None
        if scenario_ids:
            scenario_list = [UUID(sid.strip()) for sid in scenario_ids.split(",")]
        
        # Create date filter
        date_filter = DateRangeFilter(days_back=days_back)
        
        # Mock query for MVP
        query = GetUserProgressQuery(
            user_id=user_id,
            date_filter=date_filter,
            scenario_ids=scenario_list,
            metrics=[ProgressMetric.ACCURACY, ProgressMetric.SPEED, ProgressMetric.IMPROVEMENT]
        )
        
        # Mock progress data
        mock_progress = ProgressResponse(
            user_id=str(user_id),
            total_sessions=42,
            completed_sessions=38,
            total_time_spent_hours=12.5,
            average_accuracy=0.78,
            improvement_rate=0.15,
            current_streak=5,
            best_streak=12,
            achievements=["First Session", "Week Warrior", "Accuracy Master"],
            progress_by_difficulty={
                "easy": {"accuracy": 0.90, "avg_time": 8.5, "sessions": 15},
                "medium": {"accuracy": 0.75, "avg_time": 12.0, "sessions": 20},
                "hard": {"accuracy": 0.65, "avg_time": 18.5, "sessions": 7}
            },
            progress_by_scenario={
                "basic_analysis": {"accuracy": 0.85, "sessions": 20, "best_score": 95},
                "position_play": {"accuracy": 0.70, "sessions": 15, "best_score": 82},
                "advanced_gto": {"accuracy": 0.60, "sessions": 7, "best_score": 75}
            },
            recent_trend={
                "accuracy": [0.70, 0.72, 0.75, 0.78, 0.76, 0.80, 0.78],
                "speed": [85, 88, 82, 90, 87, 92, 89],
                "sessions_per_day": [1, 2, 1, 0, 1, 3, 2]
            }
        )
        
        return create_success_response(
            data=mock_progress,
            message="User progress retrieved successfully",
            request=request
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user progress: {str(e)}"
        )


@router.get("/leaderboard", response_model=APIResponse)
async def get_leaderboard(
    request: Request,
    leaderboard_type: LeaderboardType = LeaderboardType.WEEKLY,
    scenario_id: Optional[UUID] = None,
    limit: int = 20,
    user=Depends(get_current_user)
) -> APIResponse:
    """
    Get leaderboard data.
    
    **Requires authentication** to view leaderboards and find user rank.
    
    Args:
        request: FastAPI request object
        leaderboard_type: Type of leaderboard (daily, weekly, monthly, all_time)
        scenario_id: Optional scenario filter
        limit: Maximum entries to return
        user: Current authenticated user
    
    Returns:
        Leaderboard data with user's rank
    """
    try:
        # Validate limit
        if limit > 100:
            limit = 100
        if limit < 1:
            limit = 20
        
        # Create pagination
        pagination = PaginationParams(
            page=1,
            page_size=limit,
            sort_by="score",
            sort_order="desc"
        )
        
        # Mock query for MVP
        query = GetLeaderboardQuery(
            leaderboard_type=leaderboard_type,
            scenario_id=scenario_id,
            pagination=pagination
        )
        
        # Mock leaderboard entries
        mock_entries = []
        user_rank = None
        
        for i in range(min(limit, 10)):  # Generate up to 10 mock entries
            entry = LeaderboardEntryResponse(
                rank=i + 1,
                user_id=f"user_{i + 1}",
                username=f"Player{i + 1}",
                score=95.0 - (i * 2.5),
                accuracy=0.95 - (i * 0.02),
                sessions_completed=50 - (i * 3),
                total_time_hours=25.0 - (i * 1.5),
                badge="Gold" if i < 3 else "Silver" if i < 10 else None
            )
            mock_entries.append(entry)
            
            # Check if this is current user
            if entry.user_id == user.get("user_id"):
                user_rank = i + 1
        
        # If user not in top entries, assign a mock rank
        if user_rank is None:
            user_rank = 15
        
        response_data = {
            "entries": {
                "items": mock_entries,
                "total": len(mock_entries),
                "page": 1,
                "page_size": limit
            },
            "user_rank": user_rank,
            "time_period": leaderboard_type.value,
            "scenario_filter": str(scenario_id) if scenario_id else None
        }
        
        return create_success_response(
            data=response_data,
            message=f"Retrieved {leaderboard_type.value} leaderboard",
            request=request
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get leaderboard: {str(e)}"
        )


@router.get("/personal-bests", response_model=APIResponse)
async def get_personal_bests(
    request: Request,
    limit: int = 10,
    scenario_ids: Optional[str] = None,
    user=Depends(get_current_user)
) -> APIResponse:
    """
    Get user's personal best performances.
    
    **Requires authentication** to access personal data.
    
    Args:
        request: FastAPI request object
        limit: Maximum number of personal bests to return
        scenario_ids: Comma-separated scenario IDs to filter
        user: Current authenticated user
    
    Returns:
        List of personal best performances
    """
    try:
        # Parse scenario filter
        scenario_list = None
        if scenario_ids:
            scenario_list = [UUID(sid.strip()) for sid in scenario_ids.split(",")]
        
        # Mock query for MVP
        query = GetPersonalBestsQuery(
            user_id=UUID(user.get("user_id", str(uuid4()))),
            scenario_ids=scenario_list,
            limit=limit
        )
        
        # Mock personal bests
        mock_bests = [
            PersonalBestResponse(
                scenario_id=str(uuid4()),
                scenario_name="Basic Hand Analysis",
                difficulty="medium",
                best_score=95.5,
                best_accuracy=0.95,
                fastest_time_minutes=8.5,
                achieved_at=datetime.now().isoformat(),
                session_id=str(uuid4())
            ),
            PersonalBestResponse(
                scenario_id=str(uuid4()),
                scenario_name="Advanced Position Play",
                difficulty="hard",
                best_score=82.0,
                best_accuracy=0.82,
                fastest_time_minutes=15.2,
                achieved_at=datetime.now().isoformat(),
                session_id=str(uuid4())
            )
        ]
        
        return create_success_response(
            data={"personal_bests": mock_bests[:limit]},
            message=f"Retrieved {len(mock_bests[:limit])} personal bests",
            request=request
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get personal bests: {str(e)}"
        )


@router.get("/recommendations", response_model=APIResponse)
async def get_scenario_recommendations(
    request: Request,
    max_recommendations: int = 5,
    difficulty_preference: Optional[DifficultyLevel] = None,
    user=Depends(get_current_user)
) -> APIResponse:
    """
    Get personalized scenario recommendations for the user.
    
    **Requires authentication** to provide personalized recommendations.
    
    Args:
        request: FastAPI request object
        max_recommendations: Maximum number of recommendations
        difficulty_preference: Preferred difficulty level
        user: Current authenticated user
    
    Returns:
        List of scenario recommendations
    """
    try:
        # Mock query for MVP
        query = GetRecommendedScenariosQuery(
            user_id=UUID(user.get("user_id", str(uuid4()))),
            max_recommendations=max_recommendations,
            difficulty_preference=difficulty_preference
        )
        
        # Mock recommendations based on user profile
        mock_recommendations = [
            ScenarioRecommendationResponse(
                scenario_id=str(uuid4()),
                scenario_name="Intermediate Fantasy Land",
                recommended_difficulty="medium",
                reason="You've mastered basic scenarios and show good pattern recognition",
                expected_challenge_level=0.7,
                estimated_completion_minutes=20,
                skills_to_practice=["fantasy_land_strategy", "card_counting", "position_optimization"]
            ),
            ScenarioRecommendationResponse(
                scenario_id=str(uuid4()),
                scenario_name="Advanced Middle Hand Play",
                recommended_difficulty="hard",
                reason="Your middle hand accuracy is lower than other positions",
                expected_challenge_level=0.8,
                estimated_completion_minutes=25,
                skills_to_practice=["middle_hand_optimization", "two_pair_strategy", "flush_draw_play"]
            )
        ]
        
        return create_success_response(
            data={"recommendations": mock_recommendations[:max_recommendations]},
            message=f"Generated {len(mock_recommendations[:max_recommendations])} personalized recommendations",
            request=request
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendations: {str(e)}"
        )


# ===== Health Check Endpoint =====

@router.get("/health", response_model=APIResponse)
async def training_health_check(request: Request) -> APIResponse:
    """
    Health check for training service.
    
    **Public endpoint** - No authentication required.
    """
    return create_success_response(
        data={
            "service": "training",
            "status": "healthy",
            "features": {
                "session_management": True,
                "progress_tracking": True,
                "leaderboards": True,
                "recommendations": True,
                "personal_bests": True
            },
            "active_sessions": 15,
            "total_exercises_today": 342,
            "avg_session_duration_minutes": 18.5
        },
        message="Training service is healthy",
        request=request
    )