"""
Strategy Domain Events

Events related to strategy analysis and calculations.
"""

from dataclasses import dataclass
from typing import Optional

from ..base import DomainEvent
from ..value_objects import Strategy


@dataclass(frozen=True)
class AnalysisRequestedEvent(DomainEvent):
    """Event fired when strategy analysis is requested."""
    session_id: str
    position_id: str
    analysis_type: str
    priority: int = 0
    user_id: Optional[str] = None


@dataclass(frozen=True)
class AnalysisCompletedEvent(DomainEvent):
    """Event fired when strategy analysis is completed."""
    session_id: str
    optimal_strategy: Strategy
    calculation_time_ms: int
    analysis_type: str
    confidence_level: Optional[float] = None


@dataclass(frozen=True)
class StrategyCalculatedEvent(DomainEvent):
    """Event fired when a strategy is calculated."""
    session_id: str
    position_id: str
    optimal_strategy: Strategy
    calculation_time_ms: int


@dataclass(frozen=True)
class CalculationStartedEvent(DomainEvent):
    """Event fired when a calculation starts."""
    calculation_id: str
    calculation_type: str
    position_id: str
    estimated_time_ms: Optional[int] = None


@dataclass(frozen=True)
class CalculationCompletedEvent(DomainEvent):
    """Event fired when a calculation completes."""
    calculation_id: str
    calculation_type: str
    elapsed_time_ms: int
    result_summary: str = ""