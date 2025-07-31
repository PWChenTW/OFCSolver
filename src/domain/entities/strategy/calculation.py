"""
Calculation Entity for Individual Solver Computations

The Calculation entity represents an individual computation task
within a larger analysis session.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

from ...base import DomainEntity
from ...value_objects import Move, ExpectedValue
from ..game.position import Position


CalculationId = str


class CalculationType(Enum):
    """Types of calculations that can be performed."""
    MOVE_EVALUATION = "move_evaluation"
    POSITION_EVALUATION = "position_evaluation"
    GAME_TREE_SEARCH = "game_tree_search"
    MONTE_CARLO_SIMULATION = "monte_carlo_simulation"
    MINIMAX_SEARCH = "minimax_search"
    ALPHA_BETA_SEARCH = "alpha_beta_search"


class CalculationStatus(Enum):
    """Status of a calculation."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class CalculationResult:
    """Result of a calculation."""
    expected_value: ExpectedValue
    best_move: Optional[Move] = None
    confidence: float = 1.0
    nodes_evaluated: int = 0
    pruned_nodes: int = 0
    cache_hits: int = 0
    metadata: Dict[str, Any] = None


class Calculation(DomainEntity):
    """
    Represents an individual calculation task.
    
    Each calculation is a specific computational task like evaluating
    a move, searching a game tree, or running simulations.
    """
    
    def __init__(
        self,
        calculation_id: CalculationId,
        calculation_type: CalculationType,
        position: Position,
        target_move: Optional[Move] = None,
        session_id: Optional[str] = None
    ):
        super().__init__(calculation_id)
        
        self._calculation_type = calculation_type
        self._position = position
        self._target_move = target_move
        self._session_id = session_id
        self._status = CalculationStatus.QUEUED
        
        # Execution tracking
        self._queued_at = datetime.utcnow()
        self._started_at: Optional[datetime] = None
        self._completed_at: Optional[datetime] = None
        
        # Results
        self._result: Optional[CalculationResult] = None
        self._error_message: Optional[str] = None
        self._error_code: Optional[str] = None
        
        # Configuration
        self._timeout_ms: int = 30000  # 30 seconds default
        self._max_depth: int = 10
        self._samples: int = 10000
        self._parallel_workers: int = 1
        self._use_cache: bool = True
        
        # Progress tracking
        self._progress_percentage: float = 0.0
        self._current_step: str = "Queued"
        self._estimated_remaining_ms: Optional[int] = None
    
    @property
    def calculation_type(self) -> CalculationType:
        """Get calculation type."""
        return self._calculation_type
    
    @property
    def position(self) -> Position:
        """Get position being calculated."""
        return self._position
    
    @property
    def target_move(self) -> Optional[Move]:
        """Get target move being evaluated."""
        return self._target_move
    
    @property
    def session_id(self) -> Optional[str]:
        """Get parent session ID."""
        return self._session_id
    
    @property
    def status(self) -> CalculationStatus:
        """Get calculation status."""
        return self._status
    
    @property
    def result(self) -> Optional[CalculationResult]:
        """Get calculation result."""
        return self._result
    
    @property
    def error_message(self) -> Optional[str]:
        """Get error message if failed."""
        return self._error_message
    
    @property
    def error_code(self) -> Optional[str]:
        """Get error code if failed."""
        return self._error_code
    
    @property
    def progress_percentage(self) -> float:
        """Get progress percentage (0-100)."""
        return self._progress_percentage
    
    @property
    def current_step(self) -> str:
        """Get current processing step."""
        return self._current_step
    
    @property
    def is_completed(self) -> bool:
        """Check if calculation is completed."""
        return self._status == CalculationStatus.COMPLETED
    
    @property
    def is_running(self) -> bool:
        """Check if calculation is running."""
        return self._status == CalculationStatus.RUNNING
    
    @property
    def is_failed(self) -> bool:
        """Check if calculation failed."""
        return self._status in [CalculationStatus.FAILED, CalculationStatus.TIMEOUT]
    
    def start_calculation(self) -> None:
        """Start the calculation."""
        if self._status != CalculationStatus.QUEUED:
            raise ValueError(f"Cannot start calculation in status {self._status}")
        
        self._status = CalculationStatus.RUNNING
        self._started_at = datetime.utcnow()
        self._progress_percentage = 0.0
        self._current_step = "Initializing"
        self._increment_version()
    
    def complete_calculation(self, result: CalculationResult) -> None:
        """
        Complete the calculation with results.
        
        Args:
            result: Calculation result
        """
        if self._status != CalculationStatus.RUNNING:
            raise ValueError(f"Cannot complete calculation in status {self._status}")
        
        self._result = result
        self._status = CalculationStatus.COMPLETED
        self._completed_at = datetime.utcnow()
        self._progress_percentage = 100.0
        self._current_step = "Completed"
        self._increment_version()
    
    def fail_calculation(
        self, 
        error_message: str, 
        error_code: str = "CALCULATION_ERROR"
    ) -> None:
        """
        Mark calculation as failed.
        
        Args:
            error_message: Human-readable error message
            error_code: Machine-readable error code
        """
        self._status = CalculationStatus.FAILED
        self._error_message = error_message
        self._error_code = error_code
        self._completed_at = datetime.utcnow()
        self._current_step = f"Failed: {error_message}"
        self._increment_version()
    
    def timeout_calculation(self) -> None:
        """Mark calculation as timed out."""
        self._status = CalculationStatus.TIMEOUT
        self._error_message = f"Calculation timed out after {self._timeout_ms}ms"
        self._error_code = "TIMEOUT"
        self._completed_at = datetime.utcnow()
        self._current_step = "Timed out"
        self._increment_version()
    
    def cancel_calculation(self) -> None:
        """Cancel the calculation."""
        if self._status in [CalculationStatus.COMPLETED, CalculationStatus.FAILED]:
            raise ValueError(f"Cannot cancel calculation in status {self._status}")
        
        self._status = CalculationStatus.CANCELLED
        self._completed_at = datetime.utcnow()
        self._current_step = "Cancelled"
        self._increment_version()
    
    def update_progress(
        self,
        progress_percentage: float,
        current_step: str = "",
        estimated_remaining_ms: Optional[int] = None
    ) -> None:
        """
        Update calculation progress.
        
        Args:
            progress_percentage: Progress as percentage (0-100)
            current_step: Description of current step
            estimated_remaining_ms: Estimated remaining time
        """
        if not self.is_running:
            return
        
        self._progress_percentage = max(0, min(100, progress_percentage))
        if current_step:
            self._current_step = current_step
        self._estimated_remaining_ms = estimated_remaining_ms
        self._increment_version()
    
    def configure(
        self,
        timeout_ms: Optional[int] = None,
        max_depth: Optional[int] = None,
        samples: Optional[int] = None,
        parallel_workers: Optional[int] = None,
        use_cache: Optional[bool] = None
    ) -> None:
        """
        Configure calculation parameters.
        
        Args:
            timeout_ms: Timeout in milliseconds
            max_depth: Maximum search depth
            samples: Number of samples for Monte Carlo
            parallel_workers: Number of parallel workers
            use_cache: Whether to use caching
        """
        if self._status != CalculationStatus.QUEUED:
            raise ValueError("Cannot configure calculation after it starts")
        
        if timeout_ms is not None:
            self._timeout_ms = timeout_ms
        if max_depth is not None:
            self._max_depth = max_depth
        if samples is not None:
            self._samples = samples
        if parallel_workers is not None:
            self._parallel_workers = parallel_workers
        if use_cache is not None:
            self._use_cache = use_cache
        
        self._increment_version()
    
    def get_configuration(self) -> Dict[str, Any]:
        """Get current configuration."""
        return {
            'timeout_ms': self._timeout_ms,
            'max_depth': self._max_depth,
            'samples': self._samples,
            'parallel_workers': self._parallel_workers,
            'use_cache': self._use_cache
        }
    
    def get_elapsed_time_ms(self) -> int:
        """Get elapsed time since calculation started."""
        if not self._started_at:
            return 0
        
        end_time = self._completed_at or datetime.utcnow()
        return int((end_time - self._started_at).total_seconds() * 1000)
    
    def get_queue_time_ms(self) -> int:
        """Get time spent in queue."""
        start_time = self._started_at or datetime.utcnow()
        return int((start_time - self._queued_at).total_seconds() * 1000)
    
    def is_timeout_exceeded(self) -> bool:
        """Check if calculation has exceeded timeout."""
        return self.get_elapsed_time_ms() > self._timeout_ms
    
    def get_summary(self) -> Dict[str, Any]:
        """Get calculation summary."""
        return {
            'calculation_id': str(self.id),
            'calculation_type': self._calculation_type.value,
            'position_id': str(self._position.id),
            'target_move': str(self._target_move) if self._target_move else None,
            'session_id': self._session_id,
            'status': self._status.value,
            'progress_percentage': self._progress_percentage,
            'current_step': self._current_step,
            'queued_at': self._queued_at.isoformat(),
            'started_at': self._started_at.isoformat() if self._started_at else None,
            'completed_at': self._completed_at.isoformat() if self._completed_at else None,
            'elapsed_time_ms': self.get_elapsed_time_ms(),
            'queue_time_ms': self.get_queue_time_ms(),
            'estimated_remaining_ms': self._estimated_remaining_ms,
            'result': (
                {
                    'expected_value': self._result.expected_value.value,
                    'best_move': str(self._result.best_move) if self._result.best_move else None,
                    'confidence': self._result.confidence,
                    'nodes_evaluated': self._result.nodes_evaluated,
                    'pruned_nodes': self._result.pruned_nodes,
                    'cache_hits': self._result.cache_hits
                } if self._result else None
            ),
            'error_message': self._error_message,
            'error_code': self._error_code,
            'configuration': self.get_configuration()
        }
    
    def __repr__(self) -> str:
        """String representation of calculation."""
        return (f"Calculation(id={self.id}, "
                f"type={self._calculation_type.value}, "
                f"status={self._status.value}, "
                f"progress={self._progress_percentage:.1f}%)")