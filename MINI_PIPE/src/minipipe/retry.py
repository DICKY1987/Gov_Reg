"""Retry Strategies - WS-03-03A

Retry logic with exponential backoff and jitter.
"""

# DOC_ID: DOC-CORE-RESILIENCE-RETRY-189

import random
import time
from abc import ABC, abstractmethod
from typing import Any, Callable


class RetryStrategy(ABC):
    """Abstract base class for retry strategies"""

    def __init__(self, max_attempts: int = 3):
        self.max_attempts = max_attempts
        self.attempt_count = 0

    @abstractmethod
    def get_delay(self, attempt: int) -> float:
        """Get delay in seconds for the given attempt

        Args:
            attempt: Attempt number (1-indexed)

        Returns:
            Delay in seconds
        """
        pass

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic

        Args:
            func: Function to execute
            *args, **kwargs: Arguments to pass to function

        Returns:
            Function result if successful

        Raises:
            Exception: If all retries exhausted
        """
        last_exception = None

        for attempt in range(1, self.max_attempts + 1):
            self.attempt_count = attempt

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                last_exception = e

                if attempt < self.max_attempts:
                    delay = self.get_delay(attempt)
                    time.sleep(delay)
                else:
                    # Final attempt failed
                    raise RetryExhausted(
                        f"Failed after {self.max_attempts} attempts",
                        attempts=self.max_attempts,
                        last_exception=last_exception,
                    )

        # Should never reach here
        raise last_exception


class SimpleRetry(RetryStrategy):
    """Simple retry with fixed delay"""

    def __init__(self, max_attempts: int = 3, delay: float = 1.0):
        """
        Args:
            max_attempts: Maximum number of attempts
            delay: Fixed delay between attempts (seconds)
        """
        super().__init__(max_attempts)
        self.delay = delay

    def get_delay(self, attempt: int) -> float:
        """Get fixed delay"""
        return self.delay


class ExponentialBackoff(RetryStrategy):
    """Exponential backoff with optional jitter"""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ):
        """
        Args:
            max_attempts: Maximum number of attempts
            base_delay: Initial delay (seconds)
            max_delay: Maximum delay (seconds)
            exponential_base: Base for exponential calculation
            jitter: Add random jitter to prevent thundering herd
        """
        super().__init__(max_attempts)
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay

        Formula: min(base_delay * (exponential_base ** attempt), max_delay)
        With optional jitter: delay * random(0.5, 1.5)
        """
        # Calculate exponential delay
        delay = self.base_delay * (self.exponential_base**attempt)

        # Cap at max_delay
        delay = min(delay, self.max_delay)

        # Add jitter if enabled
        if self.jitter:
            # Random multiplier between 0.5 and 1.5
            jitter_factor = 0.5 + random.random()
            delay = delay * jitter_factor

        return delay


class RetryExhausted(Exception):
    """Exception raised when all retry attempts are exhausted"""

    def __init__(self, message: str, attempts: int, last_exception: Exception):
        super().__init__(message)
        self.attempts = attempts
        self.last_exception = last_exception
