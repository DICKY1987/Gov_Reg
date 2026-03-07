# DOC_LINK: DOC-ERROR-RETRY-COORDINATOR-001
"""Retry coordinator for mechanical error fixes.

DOC_ID: DOC-ERROR-RETRY-COORDINATOR-001
"""

from dataclasses import dataclass
from typing import Optional
import DOC-ERROR-UTILS-TIME-145__time
import logging

logger = logging.getLogger(__name__)


@dataclass
class RetryPolicy:
    max_attempts: int = 3
    backoff_base: float = 2.0
    mechanical_only: bool = True
    timeout_per_attempt: int = 60


@dataclass
class RetryResult:
    success: bool
    attempts_made: int
    final_fix_method: str
    error_message: Optional[str] = None
    fix_applied: Optional[str] = None


class RetryCoordinator:
    def __init__(self, error_engine, policy: Optional[RetryPolicy] = None):
        self.engine = error_engine
        self.policy = policy or RetryPolicy()

    def execute_with_retry(self, error_context) -> RetryResult:
        logger.info(f"Starting retry sequence")

        for attempt in range(1, self.policy.max_attempts + 1):
            logger.info(f"Retry attempt {attempt}/{self.policy.max_attempts}")

            try:
                fix_result = self.engine.detect_and_fix(error_context, timeout=self.policy.timeout_per_attempt)

                if fix_result.success:
                    logger.info(f"Fix succeeded on attempt {attempt}")
                    return RetryResult(
                        success=True, attempts_made=attempt,
                        final_fix_method=fix_result.method, fix_applied=fix_result.fix_description
                    )

                if fix_result.method == "mechanical":
                    if attempt < self.policy.max_attempts:
                        sleep_time = self.policy.backoff_base ** (attempt - 1)
                        time.sleep(sleep_time)
                        continue
                elif fix_result.method == "ai_agent":
                    return RetryResult(success=fix_result.success, attempts_made=attempt, final_fix_method="ai_agent")
            except Exception as e:
                logger.error(f"Exception during retry: {e}")
                if attempt == self.policy.max_attempts:
                    break
                time.sleep(self.policy.backoff_base ** (attempt - 1))

        return RetryResult(success=False, attempts_made=self.policy.max_attempts, final_fix_method="escalation", error_message="All retries failed")
