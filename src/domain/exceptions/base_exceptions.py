"""
Base Domain Exceptions

Fundamental exception classes for the domain layer.
"""

from datetime import datetime
from typing import Any, Dict, Optional


class DomainError(Exception):
    """Base class for all domain errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.context = context or {}
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "exception_type": self.__class__.__name__,
        }


class BusinessRuleViolationError(DomainError):
    """Exception for business rule violations."""

    def __init__(
        self, rule_name: str, message: str, context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, f"BUSINESS_RULE_{rule_name.upper()}", context)
        self.rule_name = rule_name


class InvalidOperationError(DomainError):
    """Exception for invalid operations on domain objects."""

    def __init__(
        self, operation: str, message: str, context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, f"INVALID_OPERATION_{operation.upper()}", context)
        self.operation = operation


class ResourceNotFoundError(DomainError):
    """Exception for resource not found errors."""

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        context: Optional[Dict[str, Any]] = None,
    ):
        message = f"{resource_type} with ID '{resource_id}' not found"
        super().__init__(message, f"{resource_type.upper()}_NOT_FOUND", context)
        self.resource_type = resource_type
        self.resource_id = resource_id
