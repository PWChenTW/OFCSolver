"""Strategy Domain Exceptions - Placeholder"""

from .base_exceptions import DomainError


class AnalysisError(DomainError):
    """Analysis error placeholder."""

    pass


class CalculationTimeoutError(DomainError):
    """Calculation timeout placeholder."""

    pass


class InvalidPositionError(DomainError):
    """Invalid position placeholder."""

    pass


class StrategyNotFoundError(DomainError):
    """Strategy not found placeholder."""

    pass


class InsufficientDataError(DomainError):
    """Insufficient data placeholder."""

    pass
