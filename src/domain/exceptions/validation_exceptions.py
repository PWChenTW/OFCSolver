"""Validation Domain Exceptions - Placeholder"""
from .base_exceptions import DomainError

class ValidationError(DomainError):
    """Validation error placeholder."""
    pass

class InvalidCardError(DomainError):
    """Invalid card placeholder."""
    pass

class InvalidMoveError(DomainError):
    """Invalid move placeholder."""
    pass

class HandValidationError(DomainError):
    """Hand validation placeholder."""
    pass