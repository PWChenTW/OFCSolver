"""Query handlers for the OFC Solver application layer."""

from typing import Any, Dict, List, Optional, TypeVar, Generic
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


# Base Query Types
@dataclass
class Query(ABC):
    """Base class for all queries."""
    pass


@dataclass 
class QueryResult(ABC):
    """Base class for all query results."""
    pass


T = TypeVar('T', bound=Query)
R = TypeVar('R', bound=QueryResult)


class QueryHandler(ABC, Generic[T, R]):
    """Base interface for query handlers."""
    
    @abstractmethod
    async def handle(self, query: T) -> R:
        """Handle the query and return the result."""
        pass


# Pagination Support
@dataclass
class PaginationParams:
    """Pagination parameters for queries."""
    page: int = 1
    page_size: int = 20
    sort_by: Optional[str] = None
    sort_order: str = "asc"
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Get limit for database queries."""
        return self.page_size


@dataclass
class PaginatedResult(Generic[T]):
    """Container for paginated results."""
    items: List[T]
    total: int
    page: int
    page_size: int
    
    @property
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        return (self.total + self.page_size - 1) // self.page_size if self.page_size > 0 else 0
    
    @property
    def has_next(self) -> bool:
        """Check if there's a next page."""
        return self.page < self.total_pages
    
    @property
    def has_previous(self) -> bool:
        """Check if there's a previous page."""
        return self.page > 1


# Common Query Types
class TimeRange(Enum):
    """Time range options for queries."""
    LAST_HOUR = "1h"
    LAST_DAY = "1d"
    LAST_WEEK = "1w"
    LAST_MONTH = "1m"
    LAST_YEAR = "1y"
    ALL_TIME = "all"


@dataclass
class DateRangeFilter:
    """Date range filter for queries."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    time_range: Optional[TimeRange] = None
    
    def to_datetime_range(self) -> tuple[Optional[datetime], Optional[datetime]]:
        """Convert to datetime range."""
        if self.time_range:
            # Implement time range conversion logic
            # This is a placeholder - would need proper implementation
            return (None, None)
        return (self.start_date, self.end_date)