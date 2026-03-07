# DOC_LINK: DOC-AIM-CLUSTER-MANAGER-001
"""
High-level cluster management for tool process pools.

ClusterManager provides automatic routing, health monitoring,
and simplified API for managing multiple CLI tool instances.

DOC_ID: DOC-AIM-CLUSTER-MANAGER-001
"""

from typing import Any, Dict, List, Optional

from .process_pool import ToolProcessPool
from .routing import Router, RoutingStrategy, create_router


class ClusterManager:
    """High-level cluster management with automatic routing.

    Wraps ToolProcessPool with intelligent routing and health monitoring.

    Example:
        cluster = ClusterManager("aider", count=3, routing=RoutingStrategy.ROUND_ROBIN)

        # Send with automatic routing
        cluster.send("/add file.py")  # Routes to instance 0
        cluster.send("/add file2.py") # Routes to instance 1

        # Or target specific instance
        cluster.send_to(0, "/help")

        # Read from any instance with work
        response = cluster.read_any(timeout=10)

        cluster.shutdown()
    """

    def __init__(
        self,
        tool_id: str,
        count: int,
        routing: RoutingStrategy = RoutingStrategy.ROUND_ROBIN,
        registry: Optional[Dict] = None,
    ):
        """Initialize cluster manager.

        Args:
            tool_id: Tool from AIM registry (e.g., "aider")
            count: Number of instances to spawn
            routing: Routing strategy (default: round-robin)
            registry: Optional registry override for testing
        """
        self.tool_id = tool_id
        self.count = count
        self.routing_strategy = routing

        # Create underlying pool
        self.pool = ToolProcessPool(tool_id, count, registry)

        # Create router
        self.router: Router = create_router(routing)

        # Track metrics
        self._total_sent = 0
        self._total_received = 0

    def send(self, prompt: str) -> int:
        """Send prompt using routing strategy.

        Args:
            prompt: Command/prompt to send

        Returns:
            Instance index that received the prompt

        Example:
            idx = cluster.send("/add core/state.py")
            print(f"Sent to instance {idx}")
        """
        # Select instance using router
        instance_idx = self.router.select_instance(self.count)

        # Send to selected instance
        success = self.pool.send_prompt(instance_idx, prompt)

        if success:
            self.router.record_assignment(instance_idx)
            self._total_sent += 1

        return instance_idx

    def send_to(self, instance_idx: int, prompt: str) -> bool:
        """Send prompt to specific instance.

        Args:
            instance_idx: Target instance index
            prompt: Command/prompt to send

        Returns:
            True if sent successfully

        Example:
            cluster.send_to(0, "/help")
        """
        success = self.pool.send_prompt(instance_idx, prompt)

        if success:
            self.router.record_assignment(instance_idx)
            self._total_sent += 1

        return success

    def read(self, instance_idx: int, timeout: float = 5.0) -> Optional[str]:
        """Read response from specific instance.

        Args:
            instance_idx: Instance to read from
            timeout: Max seconds to wait

        Returns:
            Response line or None if timeout
        """
        response = self.pool.read_response(instance_idx, timeout)

        if response:
            self.router.record_completion(instance_idx)
            self._total_received += 1

        return response

    def read_any(self, timeout: float = 5.0) -> Optional[tuple[int, str]]:
        """Read response from first instance that responds.

        Polls all instances and returns first response.

        Args:
            timeout: Total time to wait across all instances

        Returns:
            Tuple of (instance_idx, response) or None if all timeout

        Example:
            result = cluster.read_any(timeout=10)
            if result:
                idx, response = result
                print(f"Instance {idx}: {response}")
        """
        per_instance_timeout = timeout / self.count if self.count > 0 else timeout

        for i in range(self.count):
            response = self.pool.read_response(i, timeout=per_instance_timeout)
            if response:
                self.router.record_completion(i)
                self._total_received += 1
                return (i, response)

        return None

    def get_status(self) -> Dict[str, Any]:
        """Get cluster status including pool health and metrics.

        Returns:
            Status dict with health, routing, and metrics
        """
        health = self.pool.check_health()

        return {
            "tool": self.tool_id,
            "instances": self.count,
            "health": health,
            "routing": self.routing_strategy.value,
            "metrics": {
                "total_sent": self._total_sent,
                "total_received": self._total_received,
            },
        }

    def check_health(self) -> Dict[str, Any]:
        """Check cluster health.

        Returns:
            Health report from underlying pool
        """
        return self.pool.check_health()

    def restart_instance(self, instance_idx: int) -> bool:
        """Restart a dead instance.

        Args:
            instance_idx: Instance to restart

        Returns:
            True if restarted successfully
        """
        return self.pool.restart_instance(instance_idx)

    def shutdown(self, timeout: float = 5.0):
        """Gracefully shutdown cluster.

        Args:
            timeout: Seconds to wait for graceful exit
        """
        self.pool.shutdown(timeout)


def launch_cluster(
    tool_id: str, count: int = 3, routing: str = "round_robin"
) -> ClusterManager:
    """Launch a managed cluster of tool instances.

    Convenience function to create ClusterManager with sensible defaults.

    Args:
        tool_id: Tool from AIM registry (e.g., "aider", "codex")
        count: Number of instances (default: 3)
        routing: Routing strategy name (default: "round_robin")
            Options: "round_robin", "least_busy", "sticky"

    Returns:
        ClusterManager instance

    Example:
        cluster = launch_cluster("aider", count=3)
        cluster.send("/add core/state.py")
        response = cluster.read_any(timeout=10)
        cluster.shutdown()
    """
    strategy = RoutingStrategy(routing)
    return ClusterManager(tool_id, count, strategy)
