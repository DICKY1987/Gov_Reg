# DOC_LINK: DOC-AIM-ROUTING-STRATEGIES-001
"""
Routing strategies for distributing work across process pool instances.

DOC_ID: DOC-AIM-ROUTING-STRATEGIES-001
"""

from enum import Enum
from typing import List, Protocol


class RoutingStrategy(str, Enum):
    """Strategy for routing prompts to instances."""

    ROUND_ROBIN = "round_robin"
    LEAST_BUSY = "least_busy"
    STICKY = "sticky"


class Router(Protocol):
    """Protocol for routing strategies."""

    def select_instance(self, instance_count: int) -> int:
        """Select next instance index.

        Args:
            instance_count: Total number of instances

        Returns:
            Instance index (0-based)
        """
        ...

    def record_assignment(self, instance_idx: int):
        """Record that work was assigned to instance.

        Args:
            instance_idx: Instance that received work
        """
        ...

    def record_completion(self, instance_idx: int):
        """Record that instance completed work.

        Args:
            instance_idx: Instance that completed work
        """
        ...


class RoundRobinRouter:
    """Round-robin routing strategy.

    Distributes work evenly across all instances in sequential order.

    Example:
        router = RoundRobinRouter()
        idx1 = router.select_instance(3)  # 0
        idx2 = router.select_instance(3)  # 1
        idx3 = router.select_instance(3)  # 2
        idx4 = router.select_instance(3)  # 0 (wraps around)
    """

    def __init__(self):
        self._current_idx = 0

    def select_instance(self, instance_count: int) -> int:
        """Select next instance in round-robin order."""
        if instance_count == 0:
            raise ValueError("No instances available")

        idx = self._current_idx % instance_count
        self._current_idx += 1
        return idx

    def record_assignment(self, instance_idx: int):
        """No-op for round-robin."""
        pass

    def record_completion(self, instance_idx: int):
        """No-op for round-robin."""
        pass


class LeastBusyRouter:
    """Least-busy routing strategy.

    Sends work to the instance with fewest pending requests.

    Example:
        router = LeastBusyRouter()
        idx = router.select_instance(3)  # Picks least busy
        router.record_assignment(idx)    # Track work assigned
        router.record_completion(idx)    # Track work done
    """

    def __init__(self):
        self._pending_counts: List[int] = []

    def select_instance(self, instance_count: int) -> int:
        """Select instance with fewest pending requests."""
        if instance_count == 0:
            raise ValueError("No instances available")

        # Initialize counts if needed
        while len(self._pending_counts) < instance_count:
            self._pending_counts.append(0)

        # Find index with minimum pending work
        min_count = min(self._pending_counts[:instance_count])
        return self._pending_counts.index(min_count)

    def record_assignment(self, instance_idx: int):
        """Increment pending count for instance."""
        if instance_idx < len(self._pending_counts):
            self._pending_counts[instance_idx] += 1

    def record_completion(self, instance_idx: int):
        """Decrement pending count for instance."""
        if instance_idx < len(self._pending_counts):
            self._pending_counts[instance_idx] = max(
                0, self._pending_counts[instance_idx] - 1
            )


class StickyRouter:
    """Sticky routing strategy.

    Always routes to the same instance (instance 0).
    Useful for debugging or when work must be sequential.

    Example:
        router = StickyRouter()
        idx = router.select_instance(3)  # Always 0
    """

    def select_instance(self, instance_count: int) -> int:
        """Always select instance 0."""
        if instance_count == 0:
            raise ValueError("No instances available")
        return 0

    def record_assignment(self, instance_idx: int):
        """No-op for sticky."""
        pass

    def record_completion(self, instance_idx: int):
        """No-op for sticky."""
        pass


def create_router(strategy: RoutingStrategy) -> Router:
    """Factory function to create router by strategy.

    Args:
        strategy: Routing strategy enum

    Returns:
        Router instance

    Example:
        router = create_router(RoutingStrategy.ROUND_ROBIN)
    """
    if strategy == RoutingStrategy.ROUND_ROBIN:
        return RoundRobinRouter()
    elif strategy == RoutingStrategy.LEAST_BUSY:
        return LeastBusyRouter()
    elif strategy == RoutingStrategy.STICKY:
        return StickyRouter()
    else:
        raise ValueError(f"Unknown routing strategy: {strategy}")
