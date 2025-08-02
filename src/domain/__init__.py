"""
Domain Layer for OFC Solver System

This package contains the core business logic and domain model following
Domain-Driven Design (DDD) principles. The domain layer is independent of
external concerns and focuses purely on business rules and logic.

Package Structure:
- entities/: Domain entities and aggregate roots
- value_objects/: Immutable value objects
- events/: Domain events for inter-context communication
- repositories/: Repository interfaces (abstract)
- services/: Domain services for complex business logic
- exceptions/: Domain-specific exceptions
- base.py: Base classes and common abstractions
"""

__version__ = "1.0.0"
__author__ = "OFC Solver Team"

# Import key domain abstractions for easy access
from .base import (
    AggregateRoot,
    DomainEntity,
    DomainEvent,
    DomainService,
    Repository,
    ValueObject,
)

__all__ = [
    "DomainEntity",
    "ValueObject",
    "DomainEvent",
    "DomainService",
    "Repository",
    "AggregateRoot",
]
