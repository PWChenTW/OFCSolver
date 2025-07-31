"""
Analysis Session Entity - Aggregate Root for Strategy Analysis

The AnalysisSession entity represents a complete analysis workflow
for calculating optimal strategies for OFC positions.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

from ...base import AggregateRoot, DomainEvent
from ...value_objects import Strategy, ExpectedValue, ConfidenceInterval
from ..game.position import Position


SessionId = str


class AnalysisType(Enum):
    """Types of analysis that can be performed."""
    QUICK_HEURISTIC = "quick_heuristic"
    MONTE_CARLO = "monte_carlo"
    EXHAUSTIVE = "exhaustive"
    HYBRID = "hybrid"


class SessionStatus(Enum):
    """Status of an analysis session."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AnalysisRequestedEvent(DomainEvent):
    """Event fired when analysis is requested."""
    session_id: SessionId
    position_id: str
    analysis_type: AnalysisType
    priority: int = 0


@dataclass
class AnalysisCompletedEvent(DomainEvent):
    """Event fired when analysis is completed."""
    session_id: SessionId
    optimal_strategy: Strategy
    calculation_time_ms: int
    analysis_type: AnalysisType


@dataclass
class AnalysisFailedEvent(DomainEvent):
    """Event fired when analysis fails."""
    session_id: SessionId
    error_message: str
    error_code: str


class AnalysisSession(AggregateRoot):
    """
    Aggregate root for strategy analysis sessions.
    
    Manages the complete lifecycle of analyzing a position and
    calculating optimal strategies using various algorithms.
    """
    
    def __init__(
        self,
        session_id: SessionId,
        position: Position,
        analysis_type: AnalysisType,
        user_id: Optional[str] = None,
        priority: int = 0
    ):
        super().__init__(session_id)
        
        self._position = position
        self._analysis_type = analysis_type
        self._user_id = user_id
        self._priority = priority
        self._status = SessionStatus.PENDING
        
        # Analysis results
        self._optimal_strategy: Optional[Strategy] = None
        self._alternative_strategies: List[Strategy] = []
        self._calculation_time_ms: Optional[int] = None
        self._confidence_interval: Optional[ConfidenceInterval] = None
        
        # Analysis parameters
        self._max_calculation_time_ms: int = 60000  # 1 minute default
        self._target_confidence: float = 0.95
        self._monte_carlo_samples: int = 100000
        self._search_depth: int = 5
        
        # Execution tracking
        self._started_at: Optional[datetime] = None
        self._completed_at: Optional[datetime] = None
        self._error_message: Optional[str] = None
        self._error_code: Optional[str] = None
        
        # Emit creation event
        self.add_domain_event(AnalysisRequestedEvent(
            session_id=str(self.id),
            position_id=str(position.id),
            analysis_type=analysis_type,
            priority=priority
        ))
    
    @property
    def position(self) -> Position:
        """Get the position being analyzed."""
        return self._position
    
    @property
    def analysis_type(self) -> AnalysisType:
        """Get the type of analysis being performed."""
        return self._analysis_type
    
    @property
    def user_id(self) -> Optional[str]:
        """Get the user ID who requested this analysis."""
        return self._user_id
    
    @property
    def priority(self) -> int:
        """Get analysis priority (higher = more urgent)."""
        return self._priority
    
    @property
    def status(self) -> SessionStatus:
        """Get current session status."""
        return self._status
    
    @property
    def optimal_strategy(self) -> Optional[Strategy]:
        """Get the calculated optimal strategy."""
        return self._optimal_strategy
    
    @property
    def alternative_strategies(self) -> List[Strategy]:
        """Get alternative strategies."""
        return self._alternative_strategies.copy()
    
    @property
    def calculation_time_ms(self) -> Optional[int]:
        """Get calculation time in milliseconds."""
        return self._calculation_time_ms
    
    @property
    def confidence_interval(self) -> Optional[ConfidenceInterval]:
        """Get confidence interval for the analysis."""
        return self._confidence_interval
    
    @property
    def is_completed(self) -> bool:
        """Check if analysis session is completed."""
        return self._status == SessionStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """Check if analysis session failed."""
        return self._status == SessionStatus.FAILED
    
    @property
    def is_running(self) -> bool:
        """Check if analysis session is running."""
        return self._status == SessionStatus.RUNNING
    
    def start_analysis(self) -> None:
        """Start the analysis process."""
        if self._status != SessionStatus.PENDING:
            raise ValueError(f"Cannot start analysis in status {self._status}")
        
        self._status = SessionStatus.RUNNING
        self._started_at = datetime.utcnow()
        self._increment_version()
    
    def complete_analysis(
        self,
        optimal_strategy: Strategy,
        alternative_strategies: List[Strategy] = None,
        confidence_interval: Optional[ConfidenceInterval] = None
    ) -> None:
        """
        Complete the analysis with results.
        
        Args:
            optimal_strategy: The calculated optimal strategy
            alternative_strategies: List of alternative strategies
            confidence_interval: Statistical confidence interval
        """
        if self._status != SessionStatus.RUNNING:
            raise ValueError(f"Cannot complete analysis in status {self._status}")
        
        self._optimal_strategy = optimal_strategy
        self._alternative_strategies = alternative_strategies or []
        self._confidence_interval = confidence_interval
        self._status = SessionStatus.COMPLETED
        self._completed_at = datetime.utcnow()
        
        # Calculate execution time
        if self._started_at:
            elapsed = (self._completed_at - self._started_at).total_seconds()
            self._calculation_time_ms = int(elapsed * 1000)
        
        # Emit completion event
        self.add_domain_event(AnalysisCompletedEvent(
            session_id=str(self.id),
            optimal_strategy=optimal_strategy,
            calculation_time_ms=self._calculation_time_ms or 0,
            analysis_type=self._analysis_type
        ))
        
        self._increment_version()
    
    def fail_analysis(self, error_message: str, error_code: str = "ANALYSIS_ERROR") -> None:
        """
        Mark analysis as failed.
        
        Args:
            error_message: Human-readable error message
            error_code: Machine-readable error code
        """
        self._status = SessionStatus.FAILED
        self._error_message = error_message
        self._error_code = error_code
        self._completed_at = datetime.utcnow()
        
        # Calculate execution time if started
        if self._started_at:
            elapsed = (self._completed_at - self._started_at).total_seconds()
            self._calculation_time_ms = int(elapsed * 1000)
        
        # Emit failure event
        self.add_domain_event(AnalysisFailedEvent(
            session_id=str(self.id),
            error_message=error_message,
            error_code=error_code
        ))
        
        self._increment_version()
    
    def cancel_analysis(self) -> None:
        """Cancel the analysis session."""
        if self._status in [SessionStatus.COMPLETED, SessionStatus.FAILED]:
            raise ValueError(f"Cannot cancel analysis in status {self._status}")
        
        self._status = SessionStatus.CANCELLED
        self._completed_at = datetime.utcnow()
        
        # Calculate execution time if started
        if self._started_at:
            elapsed = (self._completed_at - self._started_at).total_seconds()
            self._calculation_time_ms = int(elapsed * 1000)
        
        self._increment_version()
    
    def update_progress(self, progress_percentage: float, current_step: str = "") -> None:
        """
        Update analysis progress.
        
        Args:
            progress_percentage: Progress as percentage (0-100)
            current_step: Description of current processing step
        """
        if not self.is_running:
            return
        
        # Could emit progress events here for real-time updates
        # For now, just update internal state
        self._increment_version()
    
    def set_parameters(
        self,
        max_calculation_time_ms: Optional[int] = None,
        target_confidence: Optional[float] = None,
        monte_carlo_samples: Optional[int] = None,
        search_depth: Optional[int] = None
    ) -> None:
        """
        Set analysis parameters.
        
        Args:
            max_calculation_time_ms: Maximum calculation time
            target_confidence: Target confidence level (0-1)
            monte_carlo_samples: Number of Monte Carlo samples
            search_depth: Maximum search depth
        """
        if self._status != SessionStatus.PENDING:
            raise ValueError("Cannot modify parameters after analysis starts")
        
        if max_calculation_time_ms is not None:
            self._max_calculation_time_ms = max_calculation_time_ms
        if target_confidence is not None:
            self._target_confidence = target_confidence
        if monte_carlo_samples is not None:
            self._monte_carlo_samples = monte_carlo_samples
        if search_depth is not None:
            self._search_depth = search_depth
        
        self._increment_version()
    
    def get_analysis_parameters(self) -> Dict[str, Any]:
        """Get current analysis parameters."""
        return {
            'max_calculation_time_ms': self._max_calculation_time_ms,
            'target_confidence': self._target_confidence,
            'monte_carlo_samples': self._monte_carlo_samples,
            'search_depth': self._search_depth,
            'analysis_type': self._analysis_type.value
        }
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get comprehensive session summary."""
        return {
            'session_id': str(self.id),
            'position_id': str(self._position.id),
            'analysis_type': self._analysis_type.value,
            'status': self._status.value,
            'user_id': self._user_id,
            'priority': self._priority,
            'started_at': self._started_at.isoformat() if self._started_at else None,
            'completed_at': self._completed_at.isoformat() if self._completed_at else None,
            'calculation_time_ms': self._calculation_time_ms,
            'optimal_strategy': self._optimal_strategy.to_dict() if self._optimal_strategy else None,
            'alternative_strategies_count': len(self._alternative_strategies),
            'confidence_interval': (
                self._confidence_interval.to_dict() 
                if self._confidence_interval else None
            ),
            'error_message': self._error_message,
            'error_code': self._error_code,
            'parameters': self.get_analysis_parameters()
        }
    
    def get_elapsed_time_ms(self) -> int:
        """Get elapsed time since analysis started."""
        if not self._started_at:
            return 0
        
        end_time = self._completed_at or datetime.utcnow()
        return int((end_time - self._started_at).total_seconds() * 1000)
    
    def is_timeout_exceeded(self) -> bool:
        """Check if analysis has exceeded timeout."""
        return self.get_elapsed_time_ms() > self._max_calculation_time_ms
    
    def __repr__(self) -> str:
        """String representation of analysis session."""
        return (f"AnalysisSession(id={self.id}, "
                f"type={self._analysis_type.value}, "
                f"status={self._status.value}, "
                f"position={self._position.id})")