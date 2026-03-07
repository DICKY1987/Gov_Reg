# DOC_LINK: DOC-AIM-POOL-INTERFACE-001
"""
Process pool interface for managing multiple CLI tool instances.

This module defines the core interfaces and data structures for running
multiple instances of CLI tools (aider, codex, claude-cli, etc.) in parallel.

DOC_ID: DOC-AIM-POOL-INTERFACE-001
"""

import queue
import subprocess
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol


@dataclass
class ProcessInstance:
    """Represents a single tool process instance.

    Attributes:
        index: Instance index (0-based)
        tool_id: Tool identifier from AIM registry (e.g., "aider")
        process: Subprocess handle
        stdout_queue: Queue for stdout lines
        stderr_queue: Queue for stderr lines
        alive: Whether process is running
    """

    index: int
    tool_id: str
    process: subprocess.Popen
    stdout_queue: queue.Queue
    stderr_queue: queue.Queue
    alive: bool = True


class ToolProcessPoolInterface(Protocol):
    """Protocol for managing a pool of tool process instances.

    Implementations must support:
    - Spawning N instances of a CLI tool
    - Sending prompts via stdin
    - Reading responses from stdout
    - Health monitoring and graceful shutdown

    Example:
        pool = ToolProcessPool("aider", count=3)
        pool.send_prompt(0, "/add core/state.py")
        response = pool.read_response(0, timeout=10)
        pool.shutdown()
    """

    def send_prompt(self, instance_idx: int, prompt: str) -> bool:
        """Send prompt to specific instance.

        Args:
            instance_idx: Instance index (0 to count-1)
            prompt: Command/prompt to send via stdin

        Returns:
            True if sent successfully, False otherwise
        """
        ...

    def read_response(self, instance_idx: int, timeout: float = 5.0) -> Optional[str]:
        """Read response from instance stdout.

        Args:
            instance_idx: Instance index
            timeout: Max seconds to wait for response

        Returns:
            Response line, or None if timeout/error
        """
        ...

    def get_status(self) -> List[Dict[str, Any]]:
        """Get status of all instances.

        Returns:
            List of status dicts with keys: index, alive, return_code
        """
        ...

    def shutdown(self, timeout: float = 5.0):
        """Gracefully shutdown all instances.

        Args:
            timeout: Seconds to wait for graceful exit before force kill
        """
        ...


class RoutingStrategy:
    """Routing strategy for distributing prompts across instances."""

    ROUND_ROBIN = "round_robin"
    LEAST_BUSY = "least_busy"
    STICKY = "sticky"
