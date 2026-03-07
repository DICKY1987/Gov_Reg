"""Circuit Breaker Pattern - WS-03-03A

Prevents cascading failures by stopping requests to failing services.
"""

# DOC_ID: DOC-CORE-RESILIENCE-CIRCUIT-BREAKER-186

from datetime import UTC, datetime
from enum import Enum
from typing import Any, Callable, Optional


class CircuitBreakerState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """Circuit breaker for tool adapters

    Prevents cascading failures by tracking failures and
    temporarily blocking requests to failing tools.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests blocked
    - HALF_OPEN: Testing if service recovered
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 1,
        name: str = "circuit_breaker",
    ):
        """
        Args:
            failure_threshold: Number of failures before opening
            recovery_timeout: Seconds before attempting recovery
            half_open_max_calls: Max calls to test recovery
            name: Circuit breaker identifier
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.name = name

        # State
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.opened_at: Optional[datetime] = None
        self.half_open_calls = 0

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection

        Args:
            func: Function to execute
            *args, **kwargs: Arguments to pass to function

        Returns:
            Function result if successful

        Raises:
            CircuitBreakerOpen: If circuit is open
            Exception: If function fails
        """
        # Check if circuit is open
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                raise CircuitBreakerOpen(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Opened {self._time_since_open()}s ago."
                )

        # Check half-open call limit
        if self.state == CircuitBreakerState.HALF_OPEN:
            if self.half_open_calls >= self.half_open_max_calls:
                raise CircuitBreakerOpen(
                    f"Circuit breaker '{self.name}' is HALF_OPEN. "
                    f"Max test calls ({self.half_open_max_calls}) reached."
                )
            self.half_open_calls += 1

        # Execute function
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.success_count += 1

        if self.state == CircuitBreakerState.HALF_OPEN:
            # Recovery successful
            self._transition_to_closed()

    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now(UTC)

        if self.state == CircuitBreakerState.HALF_OPEN:
            # Recovery failed
            self._transition_to_open()

        elif self.state == CircuitBreakerState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                self._transition_to_open()

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.opened_at is None:
            return True

        elapsed = (datetime.now(UTC) - self.opened_at).total_seconds()
        return elapsed >= self.recovery_timeout

    def _time_since_open(self) -> float:
        """Get seconds since circuit opened"""
        if self.opened_at is None:
            return 0.0
        return (datetime.now(UTC) - self.opened_at).total_seconds()

    def _transition_to_open(self):
        """Transition to OPEN state"""
        self.state = CircuitBreakerState.OPEN
        self.opened_at = datetime.now(UTC)
        self.half_open_calls = 0

    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state"""
        self.state = CircuitBreakerState.HALF_OPEN
        self.half_open_calls = 0

    def _transition_to_closed(self):
        """Transition to CLOSED state"""
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.opened_at = None
        self.half_open_calls = 0

    def reset(self):
        """Manually reset circuit breaker"""
        self._transition_to_closed()
        self.success_count = 0
        self.last_failure_time = None

    def get_state(self) -> dict:
        """Get current state as dict"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "time_until_recovery": (
                max(0, self.recovery_timeout - self._time_since_open())
                if self.opened_at
                else 0
            ),
        }


class CircuitBreakerOpen(Exception):
    """Exception raised when circuit breaker is open"""

    pass
