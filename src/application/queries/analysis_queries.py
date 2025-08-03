"""Analysis result query handlers."""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from enum import Enum

from src.application.queries import (
    Query, QueryResult, QueryHandler,
    PaginationParams, PaginatedResult,
    DateRangeFilter
)
from src.domain.entities.strategy import AnalysisSession, CalculationStatus
from src.domain.value_objects.expected_value import ExpectedValue
from src.domain.value_objects.strategy import Strategy
from src.domain.repositories.analysis_repository import AnalysisRepository
from src.domain.repositories.strategy_repository import StrategyRepository
from src.domain.repositories.calculation_repository import CalculationRepository


# Enums
class AnalysisType(str, Enum):
    """Types of analysis."""
    POSITION = "position"
    FULL_GAME = "full_game"
    SCENARIO = "scenario"
    COMPARISON = "comparison"


class ResultFormat(str, Enum):
    """Format for analysis results."""
    SUMMARY = "summary"
    DETAILED = "detailed"
    TREE_VIEW = "tree_view"
    CHART_DATA = "chart_data"


# Query Types
@dataclass
class GetAnalysisSessionQuery(Query):
    """Query to get an analysis session by ID."""
    session_id: UUID
    include_calculations: bool = True
    result_format: ResultFormat = ResultFormat.SUMMARY


@dataclass
class GetAnalysisHistoryQuery(Query):
    """Query to get analysis history."""
    user_id: Optional[UUID] = None
    game_id: Optional[UUID] = None
    analysis_type: Optional[AnalysisType] = None
    status_filter: Optional[List[CalculationStatus]] = None
    date_filter: Optional[DateRangeFilter] = None
    pagination: Optional[PaginationParams] = None


@dataclass
class GetAnalysisResultQuery(Query):
    """Query to get specific analysis results."""
    session_id: UUID
    calculation_id: Optional[UUID] = None
    result_format: ResultFormat = ResultFormat.DETAILED


@dataclass
class GetStrategyRecommendationsQuery(Query):
    """Query to get strategy recommendations for a position."""
    session_id: UUID
    position_id: UUID
    confidence_threshold: float = 0.8
    max_recommendations: int = 5


@dataclass
class CompareAnalysisResultsQuery(Query):
    """Query to compare multiple analysis results."""
    session_ids: List[UUID]
    comparison_metrics: List[str]
    result_format: ResultFormat = ResultFormat.CHART_DATA


# DTOs
@dataclass
class AnalysisSessionDTO:
    """Data transfer object for analysis session."""
    id: UUID
    game_id: UUID
    user_id: UUID
    analysis_type: AnalysisType
    status: CalculationStatus
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    progress: float
    parameters: Dict[str, Any]
    
    @classmethod
    def from_domain(cls, session: AnalysisSession) -> 'AnalysisSessionDTO':
        """Create DTO from domain entity."""
        return cls(
            id=session.id,
            game_id=session.game_id,
            user_id=session.user_id,
            analysis_type=AnalysisType(session.parameters.get('type', 'position')),
            status=session.status,
            created_at=session.created_at,
            started_at=session.started_at,
            completed_at=session.completed_at,
            progress=session.progress,
            parameters=session.parameters
        )


@dataclass
class AnalysisResultDTO:
    """Data transfer object for analysis results."""
    session_id: UUID
    position_id: UUID
    ev_results: Dict[str, float]
    optimal_strategy: Optional[Dict[str, Any]]
    confidence_intervals: Dict[str, tuple[float, float]]
    calculation_time: float
    iterations: int
    
    @classmethod
    def from_calculation(cls, calculation: Any) -> 'AnalysisResultDTO':
        """Create DTO from calculation result."""
        return cls(
            session_id=calculation.session_id,
            position_id=calculation.position_id,
            ev_results=calculation.ev_results,
            optimal_strategy=calculation.optimal_strategy,
            confidence_intervals=calculation.confidence_intervals,
            calculation_time=calculation.calculation_time,
            iterations=calculation.iterations
        )


@dataclass
class StrategyRecommendationDTO:
    """Data transfer object for strategy recommendations."""
    action: str
    expected_value: float
    confidence: float
    reasoning: str
    alternatives: List[Dict[str, Any]]
    
    @classmethod
    def from_strategy(cls, strategy: Strategy, ev: ExpectedValue) -> 'StrategyRecommendationDTO':
        """Create DTO from strategy and EV."""
        return cls(
            action=strategy.action_description,
            expected_value=ev.value,
            confidence=ev.confidence,
            reasoning=strategy.reasoning,
            alternatives=[{
                'action': alt.action_description,
                'ev': alt.expected_value,
                'delta': ev.value - alt.expected_value
            } for alt in strategy.alternatives[:3]]
        )


@dataclass
class AnalysisComparisonDTO:
    """Data transfer object for analysis comparison."""
    session_ids: List[UUID]
    metrics: Dict[str, List[float]]
    summary: Dict[str, Any]
    charts: List[Dict[str, Any]]


# Query Results
@dataclass
class GetAnalysisSessionResult(QueryResult):
    """Result for getting an analysis session."""
    session: Optional[AnalysisSessionDTO]
    calculations: Optional[List[AnalysisResultDTO]]


@dataclass
class GetAnalysisHistoryResult(QueryResult):
    """Result for getting analysis history."""
    sessions: PaginatedResult[AnalysisSessionDTO]


@dataclass  
class GetAnalysisResultResult(QueryResult):
    """Result for getting analysis results."""
    result: Optional[AnalysisResultDTO]
    visualization_data: Optional[Dict[str, Any]]


@dataclass
class GetStrategyRecommendationsResult(QueryResult):
    """Result for getting strategy recommendations."""
    recommendations: List[StrategyRecommendationDTO]
    position_summary: Dict[str, Any]


@dataclass
class CompareAnalysisResultsResult(QueryResult):
    """Result for comparing analysis results."""
    comparison: AnalysisComparisonDTO


# Query Handlers
class GetAnalysisSessionHandler(QueryHandler[GetAnalysisSessionQuery, GetAnalysisSessionResult]):
    """Handler for getting an analysis session."""
    
    def __init__(self, analysis_repository: AnalysisRepository,
                 calculation_repository: CalculationRepository):
        self.analysis_repository = analysis_repository
        self.calculation_repository = calculation_repository
    
    async def handle(self, query: GetAnalysisSessionQuery) -> GetAnalysisSessionResult:
        """Handle the query."""
        session = await self.analysis_repository.get_by_id(query.session_id)
        
        if not session:
            return GetAnalysisSessionResult(session=None, calculations=None)
        
        session_dto = AnalysisSessionDTO.from_domain(session)
        
        calculations = None
        if query.include_calculations:
            calcs = await self.calculation_repository.find_by_session(query.session_id)
            calculations = [AnalysisResultDTO.from_calculation(calc) for calc in calcs]
        
        return GetAnalysisSessionResult(session=session_dto, calculations=calculations)


class GetAnalysisHistoryHandler(QueryHandler[GetAnalysisHistoryQuery, GetAnalysisHistoryResult]):
    """Handler for getting analysis history."""
    
    def __init__(self, analysis_repository: AnalysisRepository):
        self.analysis_repository = analysis_repository
    
    async def handle(self, query: GetAnalysisHistoryQuery) -> GetAnalysisHistoryResult:
        """Handle the query."""
        pagination = query.pagination or PaginationParams()
        
        # Build filter criteria
        criteria = {}
        if query.user_id:
            criteria['user_id'] = query.user_id
        if query.game_id:
            criteria['game_id'] = query.game_id
        if query.analysis_type:
            criteria['type'] = query.analysis_type.value
        if query.status_filter:
            criteria['status_in'] = query.status_filter
        if query.date_filter:
            start_date, end_date = query.date_filter.to_datetime_range()
            if start_date:
                criteria['created_after'] = start_date
            if end_date:
                criteria['created_before'] = end_date
        
        # Get sessions from repository
        sessions = await self.analysis_repository.find_by_criteria(
            criteria,
            offset=pagination.offset,
            limit=pagination.limit,
            sort_by=pagination.sort_by or 'created_at',
            sort_order=pagination.sort_order
        )
        
        total = await self.analysis_repository.count_by_criteria(criteria)
        
        # Convert to DTOs
        session_dtos = [AnalysisSessionDTO.from_domain(session) for session in sessions]
        
        paginated_result = PaginatedResult(
            items=session_dtos,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size
        )
        
        return GetAnalysisHistoryResult(sessions=paginated_result)


class GetAnalysisResultHandler(QueryHandler[GetAnalysisResultQuery, GetAnalysisResultResult]):
    """Handler for getting analysis results."""
    
    def __init__(self, calculation_repository: CalculationRepository):
        self.calculation_repository = calculation_repository
    
    async def handle(self, query: GetAnalysisResultQuery) -> GetAnalysisResultResult:
        """Handle the query."""
        if query.calculation_id:
            calculation = await self.calculation_repository.get_by_id(query.calculation_id)
        else:
            # Get the latest calculation for the session
            calculations = await self.calculation_repository.find_by_session(
                query.session_id,
                limit=1
            )
            calculation = calculations[0] if calculations else None
        
        if not calculation:
            return GetAnalysisResultResult(result=None, visualization_data=None)
        
        result_dto = AnalysisResultDTO.from_calculation(calculation)
        
        # Generate visualization data based on format
        visualization_data = None
        if query.result_format == ResultFormat.CHART_DATA:
            visualization_data = self._generate_chart_data(calculation)
        elif query.result_format == ResultFormat.TREE_VIEW:
            visualization_data = self._generate_tree_view(calculation)
        
        return GetAnalysisResultResult(result=result_dto, visualization_data=visualization_data)
    
    def _generate_chart_data(self, calculation: Any) -> Dict[str, Any]:
        """Generate chart visualization data."""
        return {
            'ev_distribution': {
                'labels': list(calculation.ev_results.keys()),
                'values': list(calculation.ev_results.values())
            },
            'confidence_chart': {
                'labels': list(calculation.confidence_intervals.keys()),
                'lower_bounds': [ci[0] for ci in calculation.confidence_intervals.values()],
                'upper_bounds': [ci[1] for ci in calculation.confidence_intervals.values()]
            }
        }
    
    def _generate_tree_view(self, calculation: Any) -> Dict[str, Any]:
        """Generate tree view visualization data."""
        # Placeholder for tree view generation
        return {
            'nodes': [],
            'edges': []
        }


class GetStrategyRecommendationsHandler(
    QueryHandler[GetStrategyRecommendationsQuery, GetStrategyRecommendationsResult]
):
    """Handler for getting strategy recommendations."""
    
    def __init__(self, strategy_repository: StrategyRepository,
                 calculation_repository: CalculationRepository):
        self.strategy_repository = strategy_repository
        self.calculation_repository = calculation_repository
    
    async def handle(self, query: GetStrategyRecommendationsQuery) -> GetStrategyRecommendationsResult:
        """Handle the query."""
        # Get strategies for the position
        strategies = await self.strategy_repository.find_by_position(
            query.session_id,
            query.position_id,
            confidence_threshold=query.confidence_threshold,
            limit=query.max_recommendations
        )
        
        # Convert to DTOs
        recommendations = []
        for strategy in strategies:
            ev = await self.calculation_repository.get_ev_for_strategy(
                query.session_id,
                strategy.id
            )
            if ev:
                recommendations.append(
                    StrategyRecommendationDTO.from_strategy(strategy, ev)
                )
        
        # Get position summary
        position_summary = await self._get_position_summary(
            query.session_id,
            query.position_id
        )
        
        return GetStrategyRecommendationsResult(
            recommendations=recommendations,
            position_summary=position_summary
        )
    
    async def _get_position_summary(self, session_id: UUID, position_id: UUID) -> Dict[str, Any]:
        """Get summary information for the position."""
        # Placeholder implementation
        return {
            'cards_played': 0,
            'cards_remaining': 0,
            'current_ev': 0.0,
            'win_probability': 0.0
        }


class CompareAnalysisResultsHandler(
    QueryHandler[CompareAnalysisResultsQuery, CompareAnalysisResultsResult]
):
    """Handler for comparing analysis results."""
    
    def __init__(self, analysis_repository: AnalysisRepository,
                 calculation_repository: CalculationRepository):
        self.analysis_repository = analysis_repository
        self.calculation_repository = calculation_repository
    
    async def handle(self, query: CompareAnalysisResultsQuery) -> CompareAnalysisResultsResult:
        """Handle the query."""
        # Get all sessions
        sessions = []
        for session_id in query.session_ids:
            session = await self.analysis_repository.get_by_id(session_id)
            if session:
                sessions.append(session)
        
        if not sessions:
            return CompareAnalysisResultsResult(
                comparison=AnalysisComparisonDTO(
                    session_ids=[],
                    metrics={},
                    summary={},
                    charts=[]
                )
            )
        
        # Get calculations for each session
        metrics = {metric: [] for metric in query.comparison_metrics}
        
        for session in sessions:
            calculations = await self.calculation_repository.find_by_session(session.id)
            if calculations:
                latest_calc = calculations[0]
                for metric in query.comparison_metrics:
                    value = self._extract_metric_value(latest_calc, metric)
                    metrics[metric].append(value)
        
        # Generate comparison summary
        summary = self._generate_comparison_summary(sessions, metrics)
        
        # Generate charts based on format
        charts = []
        if query.result_format == ResultFormat.CHART_DATA:
            charts = self._generate_comparison_charts(sessions, metrics)
        
        comparison = AnalysisComparisonDTO(
            session_ids=query.session_ids,
            metrics=metrics,
            summary=summary,
            charts=charts
        )
        
        return CompareAnalysisResultsResult(comparison=comparison)
    
    def _extract_metric_value(self, calculation: Any, metric: str) -> float:
        """Extract metric value from calculation."""
        # Placeholder implementation
        metric_map = {
            'expected_value': lambda c: c.ev_results.get('total', 0.0),
            'confidence': lambda c: c.confidence_intervals.get('total', (0, 0))[1],
            'calculation_time': lambda c: c.calculation_time,
            'iterations': lambda c: float(c.iterations)
        }
        
        extractor = metric_map.get(metric, lambda c: 0.0)
        return extractor(calculation)
    
    def _generate_comparison_summary(self, sessions: List[Any], 
                                   metrics: Dict[str, List[float]]) -> Dict[str, Any]:
        """Generate comparison summary."""
        return {
            'session_count': len(sessions),
            'metric_averages': {
                metric: sum(values) / len(values) if values else 0
                for metric, values in metrics.items()
            },
            'best_performers': {
                metric: max(range(len(values)), key=values.__getitem__) if values else -1
                for metric, values in metrics.items()
            }
        }
    
    def _generate_comparison_charts(self, sessions: List[Any],
                                  metrics: Dict[str, List[float]]) -> List[Dict[str, Any]]:
        """Generate comparison charts."""
        charts = []
        
        # Bar chart for each metric
        for metric, values in metrics.items():
            charts.append({
                'type': 'bar',
                'title': f'{metric.replace("_", " ").title()} Comparison',
                'data': {
                    'labels': [f'Session {i+1}' for i in range(len(values))],
                    'values': values
                }
            })
        
        return charts