# DOC_LINK: DOC-AIM-POOL-ADAPTER-MIXIN-001
"""
Pool-aware adapter mixin for AI agents.

Provides a simple mixin that adds pool support to existing agent adapters.
This allows gradual migration to pool-based execution.

DOC_ID: DOC-AIM-POOL-ADAPTER-MIXIN-001
"""

from typing import Any, Dict, List, Optional

from phase4_routing.modules.aim_tools.src.aim.cluster_manager import (
    ClusterManager,
    launch_cluster,
)


class PoolAwareMixin:
    """Mixin to add pool support to existing adapters.

    Usage:
        class AiderPoolAdapter(PoolAwareMixin, AiderAdapter):
            pass

        adapter = AiderPoolAdapter()
        adapter.use_pool(count=3)  # Enable pool mode
        result = adapter.invoke(invocation)  # Uses pool automatically
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cluster: Optional[ClusterManager] = None
        self._pool_enabled = False

    def use_pool(self, count: int = 3, routing: str = "round_robin"):
        """Enable pool mode.

        Args:
            count: Number of instances in pool
            routing: Routing strategy
        """
        if self._cluster is None:
            tool_name = getattr(self, "name", "aider")
            self._cluster = launch_cluster(tool_name, count=count, routing=routing)
            self._pool_enabled = True

    def disable_pool(self):
        """Disable pool mode and shutdown cluster."""
        if self._cluster:
            self._cluster.shutdown()
            self._cluster = None
        self._pool_enabled = False

    def is_pool_enabled(self) -> bool:
        """Check if pool mode is enabled."""
        return self._pool_enabled

    def get_pool_status(self) -> Optional[Dict[str, Any]]:
        """Get pool status if enabled."""
        if self._cluster:
            return self._cluster.get_status()
        return None

    def invoke_with_pool(self, invocation: Any) -> Any:
        """Invoke using pool (subclass should implement).

        This is a template method that subclasses can override
        to customize how they use the pool.

        Args:
            invocation: Request to invoke

        Returns:
            Result of invocation
        """
        raise NotImplementedError(
            "Subclass must implement invoke_with_pool() or override invoke()"
        )

    def __del__(self):
        """Cleanup pool on deletion."""
        if self._cluster:
            self._cluster.shutdown()


class PoolAwareAiderAdapter(PoolAwareMixin):
    """Example: Pool-aware Aider adapter.

    This is a standalone adapter that uses the pool-aware mixin.
    Can be used independently or integrated with existing adapters.

    Example:
        adapter = PoolAwareAiderAdapter()
        adapter.use_pool(count=3)

        # Send work
        result = adapter.invoke({
            "files": ["file1.py"],
            "prompt": "Add type hints"
        })

        adapter.disable_pool()
    """

    def __init__(self):
        self.name = "aider"
        super().__init__()

    def invoke(self, invocation: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke aider (uses pool if enabled).

        Args:
            invocation: Dict with keys:
                - files: List of file paths
                - prompt: Instruction for aider
                - timeout: Optional timeout in seconds

        Returns:
            Dict with keys:
                - success: bool
                - response: str (aider output)
                - files_modified: List[str]
        """
        if self._pool_enabled and self._cluster:
            return self._invoke_with_pool(invocation)
        else:
            return self._invoke_oneshot(invocation)

    def _invoke_with_pool(self, invocation: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke using pool."""
        files = invocation.get("files", [])
        prompt = invocation.get("prompt", "")
        timeout = invocation.get("timeout", 60)

        # Send to cluster
        for filepath in files:
            self._cluster.send(f"/add {filepath}")

        instance_idx = self._cluster.send(f"/ask '{prompt}'")

        # Read response
        response = self._cluster.read(instance_idx, timeout=timeout)

        return {
            "success": response is not None,
            "response": response or "",
            "files_modified": files if response else [],
            "instance_idx": instance_idx,
            "pool_stats": self._cluster.get_status(),
        }

    def _invoke_oneshot(self, invocation: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke as one-shot subprocess (fallback)."""
        import subprocess

        files = invocation.get("files", [])
        prompt = invocation.get("prompt", "")
        timeout = invocation.get("timeout", 60)

        cmd = ["aider", "--yes-always"] + files + ["--message", prompt]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )

            return {
                "success": result.returncode == 0,
                "response": result.stdout,
                "files_modified": files if result.returncode == 0 else [],
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "response": "",
                "files_modified": [],
                "error": "timeout",
            }


# Example integration with existing adapters
def make_pool_aware(adapter_instance, pool_count: int = 3):
    """Helper function to make any adapter pool-aware.

    This is a runtime approach for adapters you don't control.

    Args:
        adapter_instance: Existing adapter instance
        pool_count: Number of instances in pool

    Returns:
        Modified adapter with pool support

    Example:
        from phase6_error_recovery.modules.error_engine.src.engine.agent_adapters import AiderAdapter

        adapter = AiderAdapter()
        pool_adapter = make_pool_aware(adapter, pool_count=3)

        # Now uses pool automatically
        result = pool_adapter.invoke(invocation)
    """
    # Store original invoke method
    original_invoke = adapter_instance.invoke

    # Create cluster
    tool_name = getattr(adapter_instance, "name", "aider")
    cluster = launch_cluster(tool_name, count=pool_count)

    # Replace invoke method
    def pooled_invoke(invocation):
        # TODO: Convert invocation to pool commands
        # This is a template - customize for your adapter
        files = getattr(invocation, "files", [])

        for filepath in files:
            cluster.send(f"/add {filepath}")

        # Send prompt (customize this)
        cluster.send("/ask 'Fix errors'")

        # Read response
        result = cluster.read_any(timeout=60)

        # Convert back to adapter result format
        # This is adapter-specific
        return result

    adapter_instance.invoke = pooled_invoke
    adapter_instance._pool_cluster = cluster

    return adapter_instance
