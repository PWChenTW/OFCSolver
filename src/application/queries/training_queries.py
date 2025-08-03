"""Training progress query handlers."""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID
from enum import Enum

from src.application.queries import (
    Query, QueryResult, QueryHandler,
    PaginationParams, PaginatedResult,
    DateRangeFilter, TimeRange
)
from src.domain.entities.training import TrainingSession, Exercise
from src.domain.entities.scenario import Scenario
from src.domain.value_objects.difficulty import Difficulty, DifficultyLevel
from src.domain.value_objects.performance import Performance
from src.domain.repositories.training_repository import TrainingRepository
from src.domain.repositories.scenario_repository import ScenarioRepository


# Enums
class ProgressMetric(str, Enum):
    """Metrics for tracking progress."""
    ACCURACY = "accuracy"
    SPEED = "speed"
    CONSISTENCY = "consistency"
    IMPROVEMENT = "improvement"
    COMPLETION_RATE = "completion_rate"


class LeaderboardType(str, Enum):
    """Types of leaderboards."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ALL_TIME = "all_time"
    SCENARIO_SPECIFIC = "scenario_specific"


# Query Types
@dataclass
class GetTrainingSessionQuery(Query):
    """Query to get a training session by ID."""
    session_id: UUID
    include_exercises: bool = True
    include_performance: bool = True


@dataclass
class GetUserProgressQuery(Query):
    """Query to get user's training progress."""
    user_id: UUID
    date_filter: Optional[DateRangeFilter] = None
    scenario_ids: Optional[List[UUID]] = None
    difficulty_filter: Optional[List[DifficultyLevel]] = None
    metrics: List[ProgressMetric] = None


@dataclass
class GetTrainingHistoryQuery(Query):
    """Query to get training history."""
    user_id: UUID
    scenario_id: Optional[UUID] = None
    difficulty_filter: Optional[List[DifficultyLevel]] = None
    completed_only: bool = False
    date_filter: Optional[DateRangeFilter] = None
    pagination: Optional[PaginationParams] = None


@dataclass
class GetScenarioStatsQuery(Query):
    """Query to get statistics for a specific scenario."""
    scenario_id: UUID
    user_id: Optional[UUID] = None
    time_range: TimeRange = TimeRange.LAST_MONTH


@dataclass
class GetLeaderboardQuery(Query):
    """Query to get leaderboard data."""
    leaderboard_type: LeaderboardType
    scenario_id: Optional[UUID] = None
    time_range: TimeRange = TimeRange.LAST_WEEK
    pagination: Optional[PaginationParams] = None


@dataclass
class GetPersonalBestsQuery(Query):
    """Query to get user's personal best performances."""
    user_id: UUID
    scenario_ids: Optional[List[UUID]] = None
    limit: int = 10


@dataclass
class GetRecommendedScenariosQuery(Query):
    """Query to get recommended scenarios for a user."""
    user_id: UUID
    max_recommendations: int = 5
    difficulty_preference: Optional[DifficultyLevel] = None


# DTOs
@dataclass
class TrainingSessionDTO:
    """Data transfer object for training session."""
    id: UUID
    user_id: UUID
    scenario_id: UUID
    difficulty: DifficultyLevel
    started_at: datetime
    completed_at: Optional[datetime]
    is_completed: bool
    score: float
    exercises_completed: int
    exercises_total: int
    average_accuracy: float
    
    @classmethod
    def from_domain(cls, session: TrainingSession) -> 'TrainingSessionDTO':
        """Create DTO from domain entity."""
        return cls(
            id=session.id,
            user_id=session.user_id,
            scenario_id=session.scenario_id,
            difficulty=session.difficulty.level,
            started_at=session.started_at,
            completed_at=session.completed_at,
            is_completed=session.is_completed,
            score=session.score,
            exercises_completed=len([e for e in session.exercises if e.is_completed]),
            exercises_total=len(session.exercises),
            average_accuracy=session.get_average_accuracy()
        )


@dataclass
class ExerciseResultDTO:
    """Data transfer object for exercise result."""
    id: UUID
    position_id: UUID
    user_action: str
    optimal_action: str
    is_correct: bool
    ev_difference: float
    time_taken: float
    hints_used: int
    
    @classmethod
    def from_domain(cls, exercise: Exercise) -> 'ExerciseResultDTO':
        """Create DTO from domain entity."""
        return cls(
            id=exercise.id,
            position_id=exercise.position_id,
            user_action=exercise.user_action,
            optimal_action=exercise.optimal_action,
            is_correct=exercise.is_correct,
            ev_difference=exercise.ev_difference,
            time_taken=exercise.time_taken,
            hints_used=exercise.hints_used
        )


@dataclass
class ProgressDTO:
    """Data transfer object for user progress."""
    user_id: UUID
    total_sessions: int
    completed_sessions: int
    total_time_spent: float
    average_accuracy: float
    improvement_rate: float
    current_streak: int
    best_streak: int
    achievements: List[str]
    progress_by_difficulty: Dict[str, Dict[str, float]]
    progress_by_scenario: Dict[str, Dict[str, float]]
    recent_trend: Dict[str, List[float]]
    
    @classmethod
    def from_performance_data(cls, user_id: UUID, performance_data: Dict[str, Any]) -> 'ProgressDTO':
        """Create DTO from performance data."""
        return cls(
            user_id=user_id,
            total_sessions=performance_data.get('total_sessions', 0),
            completed_sessions=performance_data.get('completed_sessions', 0),
            total_time_spent=performance_data.get('total_time_spent', 0.0),
            average_accuracy=performance_data.get('average_accuracy', 0.0),
            improvement_rate=performance_data.get('improvement_rate', 0.0),
            current_streak=performance_data.get('current_streak', 0),
            best_streak=performance_data.get('best_streak', 0),
            achievements=performance_data.get('achievements', []),
            progress_by_difficulty=performance_data.get('progress_by_difficulty', {}),
            progress_by_scenario=performance_data.get('progress_by_scenario', {}),
            recent_trend=performance_data.get('recent_trend', {})
        )


@dataclass
class ScenarioStatsDTO:
    """Data transfer object for scenario statistics."""
    scenario_id: UUID
    scenario_name: str
    total_attempts: int
    unique_users: int
    completion_rate: float
    average_score: float
    average_time: float
    difficulty_distribution: Dict[str, int]
    performance_by_difficulty: Dict[str, Dict[str, float]]
    top_performers: List[Dict[str, Any]]


@dataclass
class LeaderboardEntryDTO:
    """Data transfer object for leaderboard entry."""
    rank: int
    user_id: UUID
    username: str
    score: float
    accuracy: float
    sessions_completed: int
    total_time: float
    best_performance: Dict[str, Any]


@dataclass
class PersonalBestDTO:
    """Data transfer object for personal best."""
    scenario_id: UUID
    scenario_name: str
    difficulty: DifficultyLevel
    best_score: float
    best_accuracy: float
    fastest_time: float
    achieved_at: datetime
    session_id: UUID


@dataclass
class ScenarioRecommendationDTO:
    """Data transfer object for scenario recommendation."""
    scenario_id: UUID
    scenario_name: str
    recommended_difficulty: DifficultyLevel
    reason: str
    expected_challenge_level: float
    estimated_completion_time: float
    skills_to_practice: List[str]


# Query Results
@dataclass
class GetTrainingSessionResult(QueryResult):
    """Result for getting a training session."""
    session: Optional[TrainingSessionDTO]
    exercises: Optional[List[ExerciseResultDTO]]
    performance_summary: Optional[Dict[str, Any]]


@dataclass
class GetUserProgressResult(QueryResult):
    """Result for getting user progress."""
    progress: ProgressDTO
    metrics: Dict[str, Dict[str, float]]


@dataclass
class GetTrainingHistoryResult(QueryResult):
    """Result for getting training history."""
    sessions: PaginatedResult[TrainingSessionDTO]
    summary_stats: Dict[str, Any]


@dataclass
class GetScenarioStatsResult(QueryResult):
    """Result for getting scenario statistics."""
    stats: ScenarioStatsDTO


@dataclass
class GetLeaderboardResult(QueryResult):
    """Result for getting leaderboard."""
    entries: PaginatedResult[LeaderboardEntryDTO]
    user_rank: Optional[int]
    time_period: str


@dataclass
class GetPersonalBestsResult(QueryResult):
    """Result for getting personal bests."""
    personal_bests: List[PersonalBestDTO]


@dataclass
class GetRecommendedScenariosResult(QueryResult):
    """Result for getting recommended scenarios."""
    recommendations: List[ScenarioRecommendationDTO]


# Query Handlers
class GetTrainingSessionHandler(QueryHandler[GetTrainingSessionQuery, GetTrainingSessionResult]):
    """Handler for getting a training session."""
    
    def __init__(self, training_repository: TrainingRepository):
        self.training_repository = training_repository
    
    async def handle(self, query: GetTrainingSessionQuery) -> GetTrainingSessionResult:
        """Handle the query."""
        session = await self.training_repository.get_by_id(query.session_id)
        
        if not session:
            return GetTrainingSessionResult(
                session=None,
                exercises=None,
                performance_summary=None
            )
        
        session_dto = TrainingSessionDTO.from_domain(session)
        
        exercises = None
        if query.include_exercises:
            exercises = [ExerciseResultDTO.from_domain(e) for e in session.exercises]
        
        performance_summary = None
        if query.include_performance:
            performance_summary = await self._calculate_performance_summary(session)
        
        return GetTrainingSessionResult(
            session=session_dto,
            exercises=exercises,
            performance_summary=performance_summary
        )
    
    async def _calculate_performance_summary(self, session: TrainingSession) -> Dict[str, Any]:
        """Calculate performance summary for the session."""
        return {
            'accuracy': session.get_average_accuracy(),
            'speed': session.get_average_speed(),
            'improvement': session.calculate_improvement(),
            'strengths': session.identify_strengths(),
            'weaknesses': session.identify_weaknesses()
        }


class GetUserProgressHandler(QueryHandler[GetUserProgressQuery, GetUserProgressResult]):
    """Handler for getting user progress."""
    
    def __init__(self, training_repository: TrainingRepository):
        self.training_repository = training_repository
    
    async def handle(self, query: GetUserProgressQuery) -> GetUserProgressResult:
        """Handle the query."""
        # Get training sessions based on filters
        criteria = {'user_id': query.user_id}
        
        if query.date_filter:
            start_date, end_date = query.date_filter.to_datetime_range()
            if start_date:
                criteria['started_after'] = start_date
            if end_date:
                criteria['started_before'] = end_date
        
        if query.scenario_ids:
            criteria['scenario_id_in'] = query.scenario_ids
        
        if query.difficulty_filter:
            criteria['difficulty_in'] = query.difficulty_filter
        
        sessions = await self.training_repository.find_by_criteria(criteria)
        
        # Calculate progress metrics
        performance_data = await self._calculate_performance_data(sessions)
        progress_dto = ProgressDTO.from_performance_data(query.user_id, performance_data)
        
        # Calculate specific metrics if requested
        metrics = {}
        if query.metrics:
            for metric in query.metrics:
                metrics[metric.value] = await self._calculate_metric(sessions, metric)
        
        return GetUserProgressResult(progress=progress_dto, metrics=metrics)
    
    async def _calculate_performance_data(self, sessions: List[TrainingSession]) -> Dict[str, Any]:
        """Calculate overall performance data from sessions."""
        if not sessions:
            return {}
        
        completed_sessions = [s for s in sessions if s.is_completed]
        
        return {
            'total_sessions': len(sessions),
            'completed_sessions': len(completed_sessions),
            'total_time_spent': sum(s.get_duration() for s in sessions),
            'average_accuracy': sum(s.get_average_accuracy() for s in completed_sessions) / len(completed_sessions) if completed_sessions else 0,
            'improvement_rate': self._calculate_improvement_rate(sessions),
            'current_streak': self._calculate_current_streak(sessions),
            'best_streak': self._calculate_best_streak(sessions),
            'achievements': self._identify_achievements(sessions),
            'progress_by_difficulty': self._group_progress_by_difficulty(sessions),
            'progress_by_scenario': self._group_progress_by_scenario(sessions),
            'recent_trend': self._calculate_recent_trend(sessions)
        }
    
    async def _calculate_metric(self, sessions: List[TrainingSession], 
                               metric: ProgressMetric) -> Dict[str, float]:
        """Calculate specific metric values."""
        # Placeholder implementation
        return {
            'current': 0.0,
            'average': 0.0,
            'best': 0.0,
            'trend': 0.0
        }
    
    def _calculate_improvement_rate(self, sessions: List[TrainingSession]) -> float:
        """Calculate improvement rate over time."""
        # Placeholder implementation
        return 0.0
    
    def _calculate_current_streak(self, sessions: List[TrainingSession]) -> int:
        """Calculate current training streak."""
        # Placeholder implementation
        return 0
    
    def _calculate_best_streak(self, sessions: List[TrainingSession]) -> int:
        """Calculate best training streak."""
        # Placeholder implementation
        return 0
    
    def _identify_achievements(self, sessions: List[TrainingSession]) -> List[str]:
        """Identify earned achievements."""
        # Placeholder implementation
        return []
    
    def _group_progress_by_difficulty(self, sessions: List[TrainingSession]) -> Dict[str, Dict[str, float]]:
        """Group progress by difficulty level."""
        # Placeholder implementation
        return {}
    
    def _group_progress_by_scenario(self, sessions: List[TrainingSession]) -> Dict[str, Dict[str, float]]:
        """Group progress by scenario."""
        # Placeholder implementation
        return {}
    
    def _calculate_recent_trend(self, sessions: List[TrainingSession]) -> Dict[str, List[float]]:
        """Calculate recent performance trend."""
        # Placeholder implementation
        return {}


class GetTrainingHistoryHandler(QueryHandler[GetTrainingHistoryQuery, GetTrainingHistoryResult]):
    """Handler for getting training history."""
    
    def __init__(self, training_repository: TrainingRepository):
        self.training_repository = training_repository
    
    async def handle(self, query: GetTrainingHistoryQuery) -> GetTrainingHistoryResult:
        """Handle the query."""
        pagination = query.pagination or PaginationParams()
        
        # Build filter criteria
        criteria = {'user_id': query.user_id}
        
        if query.scenario_id:
            criteria['scenario_id'] = query.scenario_id
        
        if query.difficulty_filter:
            criteria['difficulty_in'] = query.difficulty_filter
        
        if query.completed_only:
            criteria['is_completed'] = True
        
        if query.date_filter:
            start_date, end_date = query.date_filter.to_datetime_range()
            if start_date:
                criteria['started_after'] = start_date
            if end_date:
                criteria['started_before'] = end_date
        
        # Get sessions from repository
        sessions = await self.training_repository.find_by_criteria(
            criteria,
            offset=pagination.offset,
            limit=pagination.limit,
            sort_by=pagination.sort_by or 'started_at',
            sort_order=pagination.sort_order
        )
        
        total = await self.training_repository.count_by_criteria(criteria)
        
        # Convert to DTOs
        session_dtos = [TrainingSessionDTO.from_domain(session) for session in sessions]
        
        paginated_result = PaginatedResult(
            items=session_dtos,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size
        )
        
        # Calculate summary statistics
        summary_stats = await self._calculate_summary_stats(criteria)
        
        return GetTrainingHistoryResult(
            sessions=paginated_result,
            summary_stats=summary_stats
        )
    
    async def _calculate_summary_stats(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate summary statistics for the filtered sessions."""
        # Placeholder implementation
        return {
            'total_time': 0.0,
            'average_score': 0.0,
            'completion_rate': 0.0,
            'most_practiced_scenario': None
        }


class GetScenarioStatsHandler(QueryHandler[GetScenarioStatsQuery, GetScenarioStatsResult]):
    """Handler for getting scenario statistics."""
    
    def __init__(self, scenario_repository: ScenarioRepository,
                 training_repository: TrainingRepository):
        self.scenario_repository = scenario_repository
        self.training_repository = training_repository
    
    async def handle(self, query: GetScenarioStatsQuery) -> GetScenarioStatsResult:
        """Handle the query."""
        scenario = await self.scenario_repository.get_by_id(query.scenario_id)
        
        if not scenario:
            return GetScenarioStatsResult(stats=None)
        
        # Get time range for stats
        end_date = datetime.now()
        start_date = self._calculate_start_date(end_date, query.time_range)
        
        # Get training sessions for the scenario
        criteria = {
            'scenario_id': query.scenario_id,
            'started_after': start_date,
            'started_before': end_date
        }
        
        if query.user_id:
            criteria['user_id'] = query.user_id
        
        sessions = await self.training_repository.find_by_criteria(criteria)
        
        # Calculate statistics
        stats = await self._calculate_scenario_stats(scenario, sessions)
        
        return GetScenarioStatsResult(stats=stats)
    
    def _calculate_start_date(self, end_date: datetime, time_range: TimeRange) -> datetime:
        """Calculate start date based on time range."""
        time_deltas = {
            TimeRange.LAST_HOUR: timedelta(hours=1),
            TimeRange.LAST_DAY: timedelta(days=1),
            TimeRange.LAST_WEEK: timedelta(weeks=1),
            TimeRange.LAST_MONTH: timedelta(days=30),
            TimeRange.LAST_YEAR: timedelta(days=365),
            TimeRange.ALL_TIME: timedelta(days=36500)  # ~100 years
        }
        
        return end_date - time_deltas.get(time_range, timedelta(days=30))
    
    async def _calculate_scenario_stats(self, scenario: Scenario, 
                                      sessions: List[TrainingSession]) -> ScenarioStatsDTO:
        """Calculate scenario statistics."""
        # Placeholder implementation
        return ScenarioStatsDTO(
            scenario_id=scenario.id,
            scenario_name=scenario.name,
            total_attempts=len(sessions),
            unique_users=len(set(s.user_id for s in sessions)),
            completion_rate=len([s for s in sessions if s.is_completed]) / len(sessions) if sessions else 0,
            average_score=sum(s.score for s in sessions) / len(sessions) if sessions else 0,
            average_time=sum(s.get_duration() for s in sessions) / len(sessions) if sessions else 0,
            difficulty_distribution={},
            performance_by_difficulty={},
            top_performers=[]
        )


class GetLeaderboardHandler(QueryHandler[GetLeaderboardQuery, GetLeaderboardResult]):
    """Handler for getting leaderboard data."""
    
    def __init__(self, training_repository: TrainingRepository):
        self.training_repository = training_repository
    
    async def handle(self, query: GetLeaderboardQuery) -> GetLeaderboardResult:
        """Handle the query."""
        pagination = query.pagination or PaginationParams()
        
        # Get leaderboard data based on type
        entries, total, time_period = await self._get_leaderboard_data(
            query.leaderboard_type,
            query.scenario_id,
            query.time_range,
            pagination
        )
        
        # Convert to DTOs
        entry_dtos = [self._create_leaderboard_entry(i + 1, entry) 
                     for i, entry in enumerate(entries)]
        
        paginated_result = PaginatedResult(
            items=entry_dtos,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size
        )
        
        # Get current user's rank if available
        user_rank = None  # Would need user context to calculate
        
        return GetLeaderboardResult(
            entries=paginated_result,
            user_rank=user_rank,
            time_period=time_period
        )
    
    async def _get_leaderboard_data(self, leaderboard_type: LeaderboardType,
                                   scenario_id: Optional[UUID],
                                   time_range: TimeRange,
                                   pagination: PaginationParams) -> tuple:
        """Get leaderboard data from repository."""
        # Placeholder implementation
        return [], 0, time_range.value
    
    def _create_leaderboard_entry(self, rank: int, data: Dict[str, Any]) -> LeaderboardEntryDTO:
        """Create leaderboard entry DTO."""
        return LeaderboardEntryDTO(
            rank=rank,
            user_id=data['user_id'],
            username=data['username'],
            score=data['score'],
            accuracy=data['accuracy'],
            sessions_completed=data['sessions_completed'],
            total_time=data['total_time'],
            best_performance=data['best_performance']
        )


class GetPersonalBestsHandler(QueryHandler[GetPersonalBestsQuery, GetPersonalBestsResult]):
    """Handler for getting personal bests."""
    
    def __init__(self, training_repository: TrainingRepository,
                 scenario_repository: ScenarioRepository):
        self.training_repository = training_repository
        self.scenario_repository = scenario_repository
    
    async def handle(self, query: GetPersonalBestsQuery) -> GetPersonalBestsResult:
        """Handle the query."""
        # Get user's best performances
        criteria = {'user_id': query.user_id, 'is_completed': True}
        
        if query.scenario_ids:
            criteria['scenario_id_in'] = query.scenario_ids
        
        # Get best sessions grouped by scenario
        best_sessions = await self.training_repository.find_best_by_user(
            query.user_id,
            scenario_ids=query.scenario_ids,
            limit=query.limit
        )
        
        # Convert to DTOs
        personal_bests = []
        for session in best_sessions:
            scenario = await self.scenario_repository.get_by_id(session.scenario_id)
            if scenario:
                personal_bests.append(
                    PersonalBestDTO(
                        scenario_id=scenario.id,
                        scenario_name=scenario.name,
                        difficulty=session.difficulty.level,
                        best_score=session.score,
                        best_accuracy=session.get_average_accuracy(),
                        fastest_time=session.get_duration(),
                        achieved_at=session.completed_at,
                        session_id=session.id
                    )
                )
        
        return GetPersonalBestsResult(personal_bests=personal_bests)


class GetRecommendedScenariosHandler(
    QueryHandler[GetRecommendedScenariosQuery, GetRecommendedScenariosResult]
):
    """Handler for getting recommended scenarios."""
    
    def __init__(self, scenario_repository: ScenarioRepository,
                 training_repository: TrainingRepository):
        self.scenario_repository = scenario_repository
        self.training_repository = training_repository
    
    async def handle(self, query: GetRecommendedScenariosQuery) -> GetRecommendedScenariosResult:
        """Handle the query."""
        # Get user's training history
        user_sessions = await self.training_repository.find_by_user(
            query.user_id,
            limit=50  # Last 50 sessions for analysis
        )
        
        # Analyze user's performance and preferences
        user_profile = await self._analyze_user_profile(user_sessions)
        
        # Get scenarios matching user profile
        recommended_scenarios = await self._find_matching_scenarios(
            user_profile,
            query.difficulty_preference,
            query.max_recommendations
        )
        
        # Convert to DTOs
        recommendations = []
        for scenario, reason, challenge_level in recommended_scenarios:
            recommendations.append(
                ScenarioRecommendationDTO(
                    scenario_id=scenario.id,
                    scenario_name=scenario.name,
                    recommended_difficulty=self._suggest_difficulty(
                        user_profile,
                        scenario,
                        query.difficulty_preference
                    ),
                    reason=reason,
                    expected_challenge_level=challenge_level,
                    estimated_completion_time=self._estimate_completion_time(
                        user_profile,
                        scenario
                    ),
                    skills_to_practice=scenario.skills_covered
                )
            )
        
        return GetRecommendedScenariosResult(recommendations=recommendations)
    
    async def _analyze_user_profile(self, sessions: List[TrainingSession]) -> Dict[str, Any]:
        """Analyze user's training profile."""
        # Placeholder implementation
        return {
            'skill_level': 'intermediate',
            'preferred_difficulty': DifficultyLevel.MEDIUM,
            'average_session_time': 30.0,
            'strengths': [],
            'weaknesses': []
        }
    
    async def _find_matching_scenarios(self, user_profile: Dict[str, Any],
                                     difficulty_preference: Optional[DifficultyLevel],
                                     limit: int) -> List[tuple]:
        """Find scenarios matching user profile."""
        # Placeholder implementation
        return []
    
    def _suggest_difficulty(self, user_profile: Dict[str, Any],
                          scenario: Scenario,
                          preference: Optional[DifficultyLevel]) -> DifficultyLevel:
        """Suggest appropriate difficulty for the scenario."""
        # Placeholder implementation
        return preference or DifficultyLevel.MEDIUM
    
    def _estimate_completion_time(self, user_profile: Dict[str, Any],
                                scenario: Scenario) -> float:
        """Estimate completion time for the scenario."""
        # Placeholder implementation
        return 30.0