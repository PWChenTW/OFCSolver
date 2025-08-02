"""
Base classes and abstractions for the domain layer.

This module provides fundamental building blocks for Domain-Driven Design
implementation following DDD principles and patterns.
"""

import uuid
from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar

# Type variables for generic implementations
T = TypeVar("T")
EntityId = TypeVar("EntityId")


class ValueObject(ABC):
    """
    Base class for value objects.

    Value objects are immutable and compared by their values rather than identity.
    They have no conceptual identity and should be side-effect free.
    """

    def __eq__(self, other: Any) -> bool:
        """Value objects are equal if all their attributes are equal."""
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __hash__(self) -> int:
        """Value objects should be hashable based on their values."""
        # Create hash from all non-private attributes
        values = tuple(
            v for k, v in sorted(self.__dict__.items()) if not k.startswith("_")
        )
        return hash(values)

    def __repr__(self) -> str:
        """String representation showing all attributes."""
        attrs = ", ".join(
            f"{k}={v!r}" for k, v in self.__dict__.items() if not k.startswith("_")
        )
        return f"{self.__class__.__name__}({attrs})"


@dataclass(frozen=False)
class DomainEvent:
    """
    Base class for domain events.

    Domain events represent something that happened in the domain that is
    important to domain experts. They are immutable and contain all the
    information needed to understand what happened.
    """

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    event_version: int = 1
    aggregate_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result


class DomainEntity(ABC):
    """
    Base class for domain entities.

    Entities have a distinct identity that runs through time and different
    representations. They are mutable and compared by their identity.
    """

    def __init__(self, entity_id: EntityId):
        self._id = entity_id
        self._version = 1
        self._created_at = datetime.utcnow()
        self._updated_at = datetime.utcnow()

    @property
    def id(self) -> EntityId:
        """Get entity identifier."""
        return self._id

    @property
    def version(self) -> int:
        """Get entity version for optimistic locking."""
        return self._version

    @property
    def created_at(self) -> datetime:
        """Get entity creation timestamp."""
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        """Get entity last update timestamp."""
        return self._updated_at

    def _increment_version(self) -> None:
        """Increment version and update timestamp."""
        self._version += 1
        self._updated_at = datetime.utcnow()

    def __eq__(self, other: Any) -> bool:
        """Entities are equal if they have the same identity."""
        if not isinstance(other, DomainEntity):
            return False
        return self._id == other._id

    def __hash__(self) -> int:
        """Entities are hashed by their identity."""
        return hash(self._id)

    def __repr__(self) -> str:
        """String representation showing entity type and ID."""
        return f"{self.__class__.__name__}(id={self._id!r})"


class AggregateRoot(DomainEntity):
    """
    Base class for aggregate roots.

    Aggregate roots are the only entities that can be obtained from repositories.
    They maintain consistency boundaries and manage domain events.
    """

    def __init__(self, entity_id: EntityId):
        super().__init__(entity_id)
        self._domain_events: List[Any] = []

    def add_domain_event(self, event: Any) -> None:
        """Add a domain event to the aggregate."""
        # Set aggregate ID if not already set
        if hasattr(event, "aggregate_id") and event.aggregate_id is None:
            # For frozen dataclasses, use object.__setattr__
            object.__setattr__(event, "aggregate_id", str(self._id))

        self._domain_events.append(event)

    def get_domain_events(self) -> List[Any]:
        """Get all domain events from the aggregate."""
        return deepcopy(self._domain_events)

    def clear_domain_events(self) -> None:
        """Clear all domain events from the aggregate."""
        self._domain_events.clear()

    def mark_events_as_committed(self) -> None:
        """Mark all events as committed and clear them."""
        self.clear_domain_events()


class DomainService(ABC):
    """
    Base class for domain services.

    Domain services encapsulate domain logic that doesn't naturally fit
    within a single entity or value object. They are stateless and focused
    on domain operations.
    """

    @abstractmethod
    def __init__(self) -> None:
        """Initialize domain service with required dependencies."""
        pass


class Repository(ABC, Generic[T, EntityId]):
    """
    Abstract base class for repositories.

    Repositories provide an abstraction over data access, allowing the domain
    to work with objects as if they were in memory collections.
    """

    @abstractmethod
    async def find_by_id(self, entity_id: EntityId) -> Optional[T]:
        """Find an entity by its identifier."""
        pass

    @abstractmethod
    async def save(self, entity: T) -> None:
        """Save an entity to the repository."""
        pass

    @abstractmethod
    async def delete(self, entity: T) -> None:
        """Delete an entity from the repository."""
        pass

    @abstractmethod
    async def find_all(self) -> List[T]:
        """Find all entities in the repository."""
        pass


class DomainException(Exception):
    """
    Base class for domain-specific exceptions.

    Domain exceptions represent business rule violations or invalid
    operations within the domain.
    """

    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for serialization."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "exception_type": self.__class__.__name__,
        }


class Specification(ABC, Generic[T]):
    """
    Base class for specifications (business rules).

    Specifications encapsulate business rules and can be combined using
    logical operators to create complex business logic.
    """

    @abstractmethod
    def is_satisfied_by(self, candidate: T) -> bool:
        """Check if the candidate satisfies this specification."""
        pass

    def and_(self, other: "Specification[T]") -> "AndSpecification[T]":
        """Combine with another specification using AND logic."""
        return AndSpecification(self, other)

    def or_(self, other: "Specification[T]") -> "OrSpecification[T]":
        """Combine with another specification using OR logic."""
        return OrSpecification(self, other)

    def not_(self) -> "NotSpecification[T]":
        """Create negation of this specification."""
        return NotSpecification(self)


class AndSpecification(Specification[T]):
    """Specification that combines two specifications with AND logic."""

    def __init__(self, left: Specification[T], right: Specification[T]):
        self.left = left
        self.right = right

    def is_satisfied_by(self, candidate: T) -> bool:
        return self.left.is_satisfied_by(candidate) and self.right.is_satisfied_by(
            candidate
        )


class OrSpecification(Specification[T]):
    """Specification that combines two specifications with OR logic."""

    def __init__(self, left: Specification[T], right: Specification[T]):
        self.left = left
        self.right = right

    def is_satisfied_by(self, candidate: T) -> bool:
        return self.left.is_satisfied_by(candidate) or self.right.is_satisfied_by(
            candidate
        )


class NotSpecification(Specification[T]):
    """Specification that negates another specification."""

    def __init__(self, spec: Specification[T]):
        self.spec = spec

    def is_satisfied_by(self, candidate: T) -> bool:
        return not self.spec.is_satisfied_by(candidate)
