"""
Intelligent error recovery system with circuit breaker, retry mechanisms, and adaptive strategies.
Data-driven approach to system reliability and fault tolerance.
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, Callable, Awaitable, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import statistics
import random

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class ErrorSeverity(Enum):
    """Error severity levels for different retry strategies."""
    LOW = "low"           # Network timeouts, temporary unavailability
    MEDIUM = "medium"     # Service errors, rate limiting
    HIGH = "high"         # Authentication, validation errors
    CRITICAL = "critical" # Data corruption, security violations


@dataclass
class RetryConfig:
    """Configuration for retry mechanisms."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0
    jitter: bool = True
    retry_on_exceptions: tuple = (Exception,)
    stop_on_exceptions: tuple = ()


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5      # Failures to open circuit
    recovery_timeout: float = 60.0  # Seconds before trying half-open
    success_threshold: int = 3      # Successes to close circuit
    monitoring_window: float = 300.0  # Window for failure rate calculation


@dataclass
class ErrorStats:
    """Error statistics for monitoring and decisions."""
    total_requests: int = 0
    failed_requests: int = 0
    circuit_breaks: int = 0
    last_failure_time: float = 0
    failure_history: deque = field(default_factory=lambda: deque(maxlen=100))
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    
    @property
    def failure_rate(self) -> float:
        """Calculate current failure rate."""
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests
    
    @property
    def avg_response_time(self) -> float:
        """Calculate average response time."""
        if not self.response_times:
            return 0.0
        return statistics.mean(self.response_times)


class ExponentialBackoffRetry:
    """
    Exponential backoff retry mechanism with jitter and adaptive delays.
    Implements intelligent delay calculation based on error patterns.
    """

    def __init__(self, config: RetryConfig):
        self.config = config
        self.stats = ErrorStats()

    async def execute(
        self, 
        func: Callable[..., Awaitable[Any]], 
        *args, 
        **kwargs
    ) -> Any:
        """
        Execute function with exponential backoff retry.
        Adapts delay based on error patterns and service health.
        """
        last_exception = None
        
        for attempt in range(self.config.max_attempts):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                
                # Record successful execution
                response_time = time.time() - start_time
                self.stats.response_times.append(response_time)
                self.stats.total_requests += 1
                
                return result
                
            except Exception as e:
                last_exception = e
                response_time = time.time() - start_time
                
                # Record failure
                self.stats.total_requests += 1
                self.stats.failed_requests += 1
                self.stats.last_failure_time = time.time()
                self.stats.failure_history.append(time.time())
                self.stats.response_times.append(response_time)
                
                # Check if we should stop retrying
                if self._should_stop_retry(e, attempt):
                    logger.warning(f"Stopping retry for {type(e).__name__}: {str(e)}")
                    raise
                
                # Calculate adaptive delay
                if attempt < self.config.max_attempts - 1:
                    delay = self._calculate_delay(attempt, e)
                    logger.info(f"Retry attempt {attempt + 1} failed, waiting {delay:.2f}s before retry")
                    await asyncio.sleep(delay)
        
        # All attempts failed
        logger.error(f"All {self.config.max_attempts} retry attempts failed")
        raise last_exception

    def _should_stop_retry(self, exception: Exception, attempt: int) -> bool:
        """Determine if we should stop retrying based on exception type."""
        # Don't retry on critical exceptions
        if any(isinstance(exception, exc_type) for exc_type in self.config.stop_on_exceptions):
            return True
        
        # Don't retry on exceptions not in retry list
        if not any(isinstance(exception, exc_type) for exc_type in self.config.retry_on_exceptions):
            return True
        
        return False

    def _calculate_delay(self, attempt: int, exception: Exception) -> float:
        """
        Calculate adaptive delay based on attempt number and error type.
        Uses exponential backoff with jitter and error-specific adjustments.
        """
        # Base exponential backoff
        delay = min(
            self.config.base_delay * (self.config.backoff_multiplier ** attempt),
            self.config.max_delay
        )
        
        # Adjust based on error severity
        severity = self._classify_error_severity(exception)
        severity_multipliers = {
            ErrorSeverity.LOW: 0.5,      # Quick retry for transient issues
            ErrorSeverity.MEDIUM: 1.0,   # Standard delay
            ErrorSeverity.HIGH: 2.0,     # Longer delay for serious errors
            ErrorSeverity.CRITICAL: 5.0  # Much longer delay for critical errors
        }
        delay *= severity_multipliers.get(severity, 1.0)
        
        # Adaptive delay based on recent failure rate
        recent_failures = len([
            t for t in self.stats.failure_history 
            if time.time() - t < 60  # Last minute
        ])
        if recent_failures > 3:
            delay *= (1 + recent_failures * 0.2)  # Increase delay for high failure rate
        
        # Add jitter to prevent thundering herd
        if self.config.jitter:
            jitter_range = delay * 0.1
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0.1, delay)  # Minimum delay of 100ms

    def _classify_error_severity(self, exception: Exception) -> ErrorSeverity:
        """Classify error severity for adaptive retry strategies."""
        error_classifications = {
            # Low severity - transient network issues
            'ConnectionError': ErrorSeverity.LOW,
            'TimeoutError': ErrorSeverity.LOW,
            'ConnectionResetError': ErrorSeverity.LOW,
            
            # Medium severity - service issues
            'HTTPException': ErrorSeverity.MEDIUM,
            'ServiceUnavailableError': ErrorSeverity.MEDIUM,
            'RateLimitExceededError': ErrorSeverity.MEDIUM,
            
            # High severity - client errors
            'ValidationError': ErrorSeverity.HIGH,
            'AuthorizationError': ErrorSeverity.HIGH,
            'NotFoundError': ErrorSeverity.HIGH,
            
            # Critical severity - security/data issues
            'AuthenticationError': ErrorSeverity.CRITICAL,
            'SecurityError': ErrorSeverity.CRITICAL,
            'DataCorruptionError': ErrorSeverity.CRITICAL,
        }
        
        exception_name = type(exception).__name__
        return error_classifications.get(exception_name, ErrorSeverity.MEDIUM)


class CircuitBreaker:
    """
    Circuit breaker pattern implementation with adaptive thresholds.
    Protects downstream services from cascading failures.
    """

    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitState.CLOSED
        self.stats = ErrorStats()
        self.state_changed_at = time.time()
        self.consecutive_failures = 0
        self.consecutive_successes = 0

    async def execute(
        self, 
        func: Callable[..., Awaitable[Any]], 
        *args, 
        **kwargs
    ) -> Any:
        """
        Execute function with circuit breaker protection.
        """
        # Check circuit state before execution
        if not self._can_execute():
            raise CircuitOpenError(f"Circuit breaker '{self.name}' is open")
        
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            await self._on_success(time.time() - start_time)
            return result
            
        except Exception as e:
            await self._on_failure(time.time() - start_time, e)
            raise

    def _can_execute(self) -> bool:
        """Check if request can be executed based on circuit state."""
        current_time = time.time()
        
        if self.state == CircuitState.CLOSED:
            return True
        
        elif self.state == CircuitState.OPEN:
            # Check if we should try half-open
            if current_time - self.state_changed_at >= self.config.recovery_timeout:
                self._transition_to_half_open()
                return True
            return False
        
        elif self.state == CircuitState.HALF_OPEN:
            return True
        
        return False

    async def _on_success(self, response_time: float):
        """Handle successful execution."""
        self.stats.total_requests += 1
        self.stats.response_times.append(response_time)
        self.consecutive_failures = 0
        self.consecutive_successes += 1
        
        # Transition from half-open to closed if enough successes
        if (self.state == CircuitState.HALF_OPEN and 
            self.consecutive_successes >= self.config.success_threshold):
            self._transition_to_closed()

    async def _on_failure(self, response_time: float, exception: Exception):
        """Handle failed execution."""
        self.stats.total_requests += 1
        self.stats.failed_requests += 1
        self.stats.response_times.append(response_time)
        self.stats.last_failure_time = time.time()
        self.stats.failure_history.append(time.time())
        
        self.consecutive_successes = 0
        self.consecutive_failures += 1
        
        # Check if circuit should open
        if self.state in [CircuitState.CLOSED, CircuitState.HALF_OPEN]:
            if self._should_open_circuit():
                self._transition_to_open()

    def _should_open_circuit(self) -> bool:
        """Determine if circuit should open based on failure patterns."""
        # Simple threshold check
        if self.consecutive_failures >= self.config.failure_threshold:
            return True
        
        # Adaptive threshold based on failure rate in monitoring window
        current_time = time.time()
        window_start = current_time - self.config.monitoring_window
        
        recent_failures = [
            t for t in self.stats.failure_history 
            if t >= window_start
        ]
        
        if len(recent_failures) >= self.config.failure_threshold:
            failure_rate = len(recent_failures) / max(1, self.stats.total_requests)
            return failure_rate > 0.5  # 50% failure rate threshold
        
        return False

    def _transition_to_open(self):
        """Transition circuit to OPEN state."""
        self.state = CircuitState.OPEN
        self.state_changed_at = time.time()
        self.stats.circuit_breaks += 1
        logger.warning(f"Circuit breaker '{self.name}' opened due to failures")

    def _transition_to_half_open(self):
        """Transition circuit to HALF_OPEN state."""
        self.state = CircuitState.HALF_OPEN
        self.state_changed_at = time.time()
        self.consecutive_successes = 0
        logger.info(f"Circuit breaker '{self.name}' attempting recovery (half-open)")

    def _transition_to_closed(self):
        """Transition circuit to CLOSED state."""
        self.state = CircuitState.CLOSED
        self.state_changed_at = time.time()
        self.consecutive_failures = 0
        logger.info(f"Circuit breaker '{self.name}' closed - service recovered")

    def get_health_status(self) -> Dict[str, Any]:
        """Get circuit breaker health status."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_rate": self.stats.failure_rate,
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes,
            "total_requests": self.stats.total_requests,
            "circuit_breaks": self.stats.circuit_breaks,
            "avg_response_time": self.stats.avg_response_time,
            "last_failure_time": self.stats.last_failure_time,
            "state_duration": time.time() - self.state_changed_at
        }


class FaultToleranceManager:
    """
    Comprehensive fault tolerance management.
    Combines retry mechanisms, circuit breakers, and adaptive strategies.
    """

    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_configs: Dict[str, RetryConfig] = {}
        self.global_stats = {
            "total_operations": 0,
            "failed_operations": 0,
            "recovered_operations": 0,
            "circuit_breaks": 0,
            "start_time": time.time()
        }

    def register_service(
        self, 
        name: str, 
        retry_config: Optional[RetryConfig] = None,
        circuit_config: Optional[CircuitBreakerConfig] = None
    ):
        """Register a service with fault tolerance policies."""
        if retry_config:
            self.retry_configs[name] = retry_config
        
        if circuit_config:
            self.circuit_breakers[name] = CircuitBreaker(name, circuit_config)

    async def execute_with_protection(
        self,
        service_name: str,
        func: Callable[..., Awaitable[Any]],
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with full fault tolerance protection.
        Combines circuit breaker and retry mechanisms.
        """
        self.global_stats["total_operations"] += 1
        
        try:
            # Get circuit breaker if configured
            circuit_breaker = self.circuit_breakers.get(service_name)
            
            # Get retry configuration
            retry_config = self.retry_configs.get(service_name, RetryConfig())
            retry_handler = ExponentialBackoffRetry(retry_config)
            
            # Execute with protection
            if circuit_breaker:
                result = await retry_handler.execute(
                    circuit_breaker.execute, func, *args, **kwargs
                )
            else:
                result = await retry_handler.execute(func, *args, **kwargs)
            
            return result
            
        except Exception as e:
            self.global_stats["failed_operations"] += 1
            raise
        finally:
            # Update circuit break count
            if service_name in self.circuit_breakers:
                self.global_stats["circuit_breaks"] = sum(
                    cb.stats.circuit_breaks 
                    for cb in self.circuit_breakers.values()
                )

    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status."""
        current_time = time.time()
        uptime = current_time - self.global_stats["start_time"]
        
        circuit_statuses = {
            name: cb.get_health_status() 
            for name, cb in self.circuit_breakers.items()
        }
        
        return {
            "uptime_seconds": uptime,
            "total_operations": self.global_stats["total_operations"],
            "failed_operations": self.global_stats["failed_operations"],
            "success_rate": (
                (self.global_stats["total_operations"] - self.global_stats["failed_operations"]) /
                max(1, self.global_stats["total_operations"])
            ),
            "operations_per_minute": self.global_stats["total_operations"] / max(1, uptime / 60),
            "circuit_breaks": self.global_stats["circuit_breaks"],
            "circuit_breakers": circuit_statuses,
            "services_registered": len(self.circuit_breakers)
        }

    def reset_metrics(self):
        """Reset all metrics for fresh monitoring period."""
        self.global_stats = {
            "total_operations": 0,
            "failed_operations": 0,
            "recovered_operations": 0,
            "circuit_breaks": 0,
            "start_time": time.time()
        }
        
        for cb in self.circuit_breakers.values():
            cb.stats = ErrorStats()


class CircuitOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


# Global fault tolerance manager
fault_tolerance = FaultToleranceManager()

# Default configurations for common services
fault_tolerance.register_service(
    "database",
    retry_config=RetryConfig(
        max_attempts=3,
        base_delay=0.5,
        max_delay=10.0,
        retry_on_exceptions=(ConnectionError, TimeoutError)
    ),
    circuit_config=CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=30.0,
        success_threshold=3
    )
)

fault_tolerance.register_service(
    "external_api",
    retry_config=RetryConfig(
        max_attempts=5,
        base_delay=1.0,
        max_delay=30.0,
        retry_on_exceptions=(ConnectionError, TimeoutError)
    ),
    circuit_config=CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=60.0,
        success_threshold=2
    )
)


def get_fault_tolerance() -> FaultToleranceManager:
    """Get the fault tolerance manager instance."""
    return fault_tolerance