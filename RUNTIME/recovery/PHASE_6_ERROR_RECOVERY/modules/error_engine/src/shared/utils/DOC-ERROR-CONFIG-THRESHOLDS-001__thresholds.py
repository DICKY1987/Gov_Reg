# DOC_LINK: DOC-ERROR-CONFIG-THRESHOLDS-001
"""Success Rate Threshold Configuration

Defines quality gates for error pipeline certification.
"""

# DOC_ID: DOC-ERROR-CONFIG-THRESHOLDS-001

from dataclasses import dataclass
from typing import Dict


@dataclass
class CertificationThresholds:
    """Quality gate thresholds for pipeline certification"""

    # Minimum success rate (0-100)
    minimum_success_rate: float = 95.0

    # Maximum allowed failures by severity
    max_failures: Dict[str, int] = None

    # Block release on certification failure
    block_release_on_failure: bool = True

    # Certification validity period (hours)
    validity_hours: int = 24

    def __post_init__(self):
        if self.max_failures is None:
            self.max_failures = {
                "critical": 0,  # Zero tolerance for critical
                "high": 2,  # Allow 2 high-severity
                "medium": 10,
                "low": 50,
            }

    def is_certified(
        self, success_rate: float, failures_by_severity: Dict[str, int]
    ) -> tuple[bool, str]:
        """
        Check if results meet certification thresholds.

        Args:
            success_rate: Success rate percentage
            failures_by_severity: Count of failures by severity

        Returns:
            (is_certified, reason)
        """
        # Check success rate
        if success_rate < self.minimum_success_rate:
            return (
                False,
                f"Success rate {success_rate:.1f}% below threshold {self.minimum_success_rate}%",
            )

        # Check severity limits
        for severity, max_count in self.max_failures.items():
            actual = failures_by_severity.get(severity, 0)
            if actual > max_count:
                return (
                    False,
                    f"{severity} failures ({actual}) exceed limit ({max_count})",
                )

        return True, "All thresholds met"


# Default thresholds
DEFAULT_THRESHOLDS = CertificationThresholds()

# Strict thresholds (for production releases)
STRICT_THRESHOLDS = CertificationThresholds(
    minimum_success_rate=100.0,
    max_failures={"critical": 0, "high": 0, "medium": 0, "low": 5},
    block_release_on_failure=True,
    validity_hours=12,
)

# Lenient thresholds (for development)
LENIENT_THRESHOLDS = CertificationThresholds(
    minimum_success_rate=80.0,
    max_failures={"critical": 2, "high": 10, "medium": 50, "low": 100},
    block_release_on_failure=False,
    validity_hours=48,
)
