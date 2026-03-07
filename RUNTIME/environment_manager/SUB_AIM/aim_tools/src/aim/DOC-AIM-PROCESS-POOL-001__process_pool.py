# DOC_LINK: DOC-AIM-PROCESS-POOL-001
"""
Tool process pool for managing multiple CLI instances.

This module implements a process pool that manages multiple long-lived
CLI tool instances (aider, codex, claude-cli, etc.) with stdin/stdout
communication via background threads.

DOC_ID: DOC-AIM-PROCESS-POOL-001
"""

import queue
import subprocess
import threading
import DOC-ERROR-UTILS-TIME-145__time
from typing import Any, Dict, List, Optional

from .pool_interface import ProcessInstance


def load_aim_registry() -> Dict[str, Any]:
    """Load AIM registry configuration.

    Returns:
        Registry dictionary with tool configurations

    Note:
        This is a placeholder. Real implementation will load from
        .aim/aim-registry/registry.json
    """
    # TODO: Load actual registry in production
    return {
        "tools": {
            "aider": {
                "detectCommands": [["aider", "--yes-always"]],
                "capabilities": ["code_generation"],
            }
        }
    }


class ToolProcessPool:
    """Manage multiple long-lived tool CLI instances.

    Spawns N instances of a CLI tool and provides methods to:
    - Send prompts via stdin
    - Read responses from stdout
    - Monitor health and status
    - Gracefully shutdown

    Each instance runs in its own process with background threads
    reading stdout/stderr into queues for non-blocking access.

    Example:
        pool = ToolProcessPool("aider", count=3)
        pool.send_prompt(0, "/add core/state.py")
        response = pool.read_response(0, timeout=10)
        pool.shutdown()
    """

    def __init__(self, tool_id: str, count: int, registry: Optional[Dict] = None):
        """Initialize process pool.

        Args:
            tool_id: Tool from AIM registry (e.g., "aider")
            count: Number of instances to spawn (1-10)
            registry: Optional registry override (for testing)

        Raises:
            ValueError: If tool_id not in registry or count invalid
        """
        if count < 1 or count > 10:
            raise ValueError(f"count must be 1-10, got {count}")

        self.tool_id = tool_id
        self.count = count
        self.instances: List[ProcessInstance] = []
        self.registry = registry or load_aim_registry()

        # Validate tool exists
        if tool_id not in self.registry.get("tools", {}):
            raise ValueError(f"Tool '{tool_id}' not in AIM registry")

        # Spawn all instances
        for i in range(count):
            self._spawn_instance(i)

    def _spawn_instance(self, index: int) -> ProcessInstance:
        """Spawn a single tool instance with I/O threads.

        Args:
            index: Instance index (0-based)

        Returns:
            ProcessInstance with running process and queues
        """
        tool_config = self.registry["tools"][self.tool_id]

        # Build command from registry
        detect_cmds = tool_config["detectCommands"]
        cmd = detect_cmds[0] if isinstance(detect_cmds[0], list) else [detect_cmds[0]]

        # Add tool-specific flags for interactive mode
        if self.tool_id == "aider":
            # Ensure non-blocking, auto-confirm mode
            if "--yes-always" not in cmd:
                cmd.append("--yes-always")

        # Spawn process with pipes
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line-buffered
        )

        # Create output queues
        stdout_q = queue.Queue()
        stderr_q = queue.Queue()

        # Start reader threads
        threading.Thread(
            target=self._read_stream,
            args=(proc.stdout, stdout_q),
            daemon=True,
            name=f"{self.tool_id}-{index}-stdout",
        ).start()

        threading.Thread(
            target=self._read_stream,
            args=(proc.stderr, stderr_q),
            daemon=True,
            name=f"{self.tool_id}-{index}-stderr",
        ).start()

        instance = ProcessInstance(
            index=index,
            tool_id=self.tool_id,
            process=proc,
            stdout_queue=stdout_q,
            stderr_queue=stderr_q,
            alive=True,
        )

        self.instances.append(instance)
        return instance

    def _read_stream(self, stream, q: queue.Queue):
        """Background thread to read stream into queue.

        Args:
            stream: File-like object (stdout or stderr)
            q: Queue to push lines into
        """
        try:
            for line in stream:
                q.put(line.rstrip("\n"))
        except Exception:
            pass  # Stream closed or error
        finally:
            stream.close()

    def send_prompt(self, instance_idx: int, prompt: str) -> bool:
        """Send prompt to specific instance.

        Args:
            instance_idx: Instance index (0 to count-1)
            prompt: Command/prompt to send via stdin

        Returns:
            True if sent successfully, False otherwise
        """
        if instance_idx >= len(self.instances):
            return False

        instance = self.instances[instance_idx]
        if not instance.alive:
            return False

        try:
            instance.process.stdin.write(prompt + "\n")
            instance.process.stdin.flush()
            return True
        except (BrokenPipeError, OSError):
            instance.alive = False
            return False

    def read_response(self, instance_idx: int, timeout: float = 5.0) -> Optional[str]:
        """Read response from instance stdout.

        Args:
            instance_idx: Instance index
            timeout: Max seconds to wait for response

        Returns:
            Response line, or None if timeout/error
        """
        if instance_idx >= len(self.instances):
            return None

        instance = self.instances[instance_idx]

        try:
            line = instance.stdout_queue.get(timeout=timeout)
            return line
        except queue.Empty:
            return None

    def get_status(self) -> List[Dict[str, Any]]:
        """Get status of all instances.

        Returns:
            List of status dicts with keys: index, alive, return_code
        """
        statuses = []
        for inst in self.instances:
            poll_result = inst.process.poll()
            statuses.append(
                {
                    "index": inst.index,
                    "alive": inst.alive and poll_result is None,
                    "return_code": poll_result,
                }
            )
        return statuses

    def shutdown(self, timeout: float = 5.0):
        """Gracefully shutdown all instances.

        Attempts graceful termination first, then forces kill
        if processes don't exit within timeout.

        Args:
            timeout: Seconds to wait for graceful exit
        """
        # Send termination signal to all
        for inst in self.instances:
            if inst.process.poll() is None:
                try:
                    inst.process.terminate()
                except OSError:
                    pass  # Already dead

        # Wait for graceful exit
        start = time.time()
        while time.time() - start < timeout:
            if all(inst.process.poll() is not None for inst in self.instances):
                break
            time.sleep(0.1)

        # Force kill stragglers
        for inst in self.instances:
            if inst.process.poll() is None:
                try:
                    inst.process.kill()
                    inst.process.wait()
                except OSError:
                    pass  # Already dead

    def check_health(self) -> Dict[str, Any]:
        """Check health of all instances.

        Returns:
            Health report with alive count, dead count, instance details
        """
        statuses = self.get_status()
        alive_count = sum(1 for s in statuses if s["alive"])

        return {
            "total": len(self.instances),
            "alive": alive_count,
            "dead": len(self.instances) - alive_count,
            "instances": statuses,
        }

    def restart_instance(self, instance_idx: int) -> bool:
        """Restart a dead instance.

        Args:
            instance_idx: Instance to restart

        Returns:
            True if restarted successfully, False otherwise
        """
        if instance_idx >= len(self.instances):
            return False

        old_instance = self.instances[instance_idx]

        # Kill old process if still running
        if old_instance.process.poll() is None:
            old_instance.process.kill()
            old_instance.process.wait()

        # Spawn new instance
        try:
            new_instance = self._spawn_instance(instance_idx)
            self.instances[instance_idx] = new_instance
            return True
        except Exception:
            return False
