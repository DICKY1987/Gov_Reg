"""Resilient Executor - WS-03-03A

Combines circuit breakers and retry logic for robust task execution.
"""

# DOC_ID: DOC-CORE-RESILIENCE-RESILIENT-EXECUTOR-188

from typing import Any, Callable, Dict, Optional

from .circuit_breaker import CircuitBreaker
from .retry import ExponentialBackoff, RetryStrategy


class ResilientExecutor:
    """Executor that combines circuit breakers and retry logic

    Provides robust execution with:
    - Circuit breakers to prevent cascading failures
    - Retry logic with exponential backoff
    - Per-tool failure tracking
    - Auto-recovery
    """

    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_strategies: Dict[str, RetryStrategy] = {}

    def register_tool(
        self,
        tool_id: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        max_retries: int = 3,
        base_delay: float = 1.0,
    ):
        """Register a tool with circuit breaker and retry strategy

        Args:
            tool_id: Tool identifier
            failure_threshold: Failures before opening circuit
            recovery_timeout: Seconds before attempting recovery
            max_retries: Maximum retry attempts
            base_delay: Initial retry delay
        """
        # Create circuit breaker
        self.circuit_breakers[tool_id] = CircuitBreaker(
            name=tool_id,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
        )

        # Create retry strategy
        self.retry_strategies[tool_id] = ExponentialBackoff(
            max_attempts=max_retries, base_delay=base_delay
        )

    def execute(self, tool_id: str, func: Callable, *args, **kwargs) -> Any:
        """Execute function with resilience patterns

        Args:
            tool_id: Tool identifier
            func: Function to execute
            *args, **kwargs: Arguments to pass to function

        Returns:
            Function result if successful

        Raises:
            CircuitBreakerOpen: If circuit is open
            RetryExhausted: If all retries exhausted
        """
        # Ensure tool is registered
        if tool_id not in self.circuit_breakers:
            self.register_tool(tool_id)

        circuit_breaker = self.circuit_breakers[tool_id]
        retry_strategy = self.retry_strategies[tool_id]

        # Execute with retry and circuit breaker
        def protected_func():
            return circuit_breaker.call(func, *args, **kwargs)

        return retry_strategy.execute(protected_func)

    def get_tool_state(self, tool_id: str) -> Optional[dict]:
        """Get circuit breaker state for a tool

        Args:
            tool_id: Tool identifier

        Returns:
            Circuit breaker state dict or None
        """
        if tool_id not in self.circuit_breakers:
            return None

        return self.circuit_breakers[tool_id].get_state()

    def reset_tool(self, tool_id: str):
        """Manually reset circuit breaker for a tool

        Args:
            tool_id: Tool identifier
        """
        if tool_id in self.circuit_breakers:
            self.circuit_breakers[tool_id].reset()

    def get_all_states(self) -> Dict[str, dict]:
        """Get circuit breaker states for all tools

        Returns:
            Dict mapping tool_id to state dict
        """
        return {
            tool_id: cb.get_state() for tool_id, cb in self.circuit_breakers.items()
        }
