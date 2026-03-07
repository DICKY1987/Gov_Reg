"""Worker process spawning for parallel execution.

Manages subprocess creation, sandboxing, and lifecycle for tool adapters.
Phase I-1 WS-I2 implementation.
"""

# DOC_ID: DOC-CORE-ENGINE-PROCESS-SPAWNER-154

from __future__ import annotations

import os
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional


@dataclass
class WorkerProcess:
    """Represents a spawned worker process."""

    worker_id: str
    pid: int
    adapter_type: str
    sandbox_path: Path
    process: subprocess.Popen
    spawned_at: datetime
    env: Dict[str, str]


class ProcessSpawner:
    """Manages worker process spawning and lifecycle."""

    def __init__(self, base_sandbox_dir: Optional[Path] = None):
        """Initialize process spawner.

        Args:
            base_sandbox_dir: Base directory for worker sandboxes
        """
        self.base_sandbox_dir = (
            base_sandbox_dir or Path(tempfile.gettempdir()) / "uet_workers"
        )
        self.processes: Dict[str, WorkerProcess] = {}

    def spawn_worker_process(
        self,
        worker_id: str,
        adapter_type: str,
        repo_root: Path,
        env_overrides: Optional[Dict[str, str]] = None,
    ) -> WorkerProcess:
        """Spawn a new worker process.

        Args:
            worker_id: Unique worker identifier
            adapter_type: Tool adapter type ('aider', 'codex', etc.)
            repo_root: Repository root path
            env_overrides: Environment variable overrides

        Returns:
            WorkerProcess instance
        """
        # Create sandbox directory
        sandbox_path = self.base_sandbox_dir / worker_id
        sandbox_path.mkdir(parents=True, exist_ok=True)

        # Prepare environment
        worker_env = os.environ.copy()
        worker_env.update(
            {
                "UET_WORKER_ID": worker_id,
                "UET_ADAPTER_TYPE": adapter_type,
                "UET_SANDBOX_PATH": str(sandbox_path),
                "REPO_ROOT": str(repo_root),
            }
        )

        if env_overrides:
            worker_env.update(env_overrides)

        # Resolve command: allow adapter-specific override via env, otherwise use a safe idle loop.
        cmd = self._resolve_command(adapter_type, worker_env)
        process = subprocess.Popen(
            cmd,
            env=worker_env,
            cwd=str(repo_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        worker_process = WorkerProcess(
            worker_id=worker_id,
            pid=process.pid,
            adapter_type=adapter_type,
            sandbox_path=sandbox_path,
            process=process,
            spawned_at=datetime.now(timezone.utc),
            env=worker_env,
        )

        self.processes[worker_id] = worker_process

        return worker_process

    def terminate_worker_process(self, worker_id: str) -> None:
        """Terminate a worker process.

        Args:
            worker_id: Worker ID to terminate
        """
        worker_process = self.processes.get(worker_id)
        if not worker_process:
            return

        try:
            worker_process.process.terminate()
            worker_process.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            worker_process.process.kill()
        except:
            pass

        # Cleanup sandbox (optional - keep for debugging)
        # import shutil
        # if worker_process.sandbox_path.exists():
        #     shutil.rmtree(worker_process.sandbox_path)

        del self.processes[worker_id]

    def is_alive(self, worker_id: str) -> bool:
        """Check if worker process is alive.

        Args:
            worker_id: Worker ID

        Returns:
            True if process is running
        """
        worker_process = self.processes.get(worker_id)
        if not worker_process:
            return False

        return worker_process.process.poll() is None

    def cleanup_all(self) -> None:
        """Terminate all worker processes."""
        for worker_id in list(self.processes.keys()):
            self.terminate_worker_process(worker_id)

    def _resolve_command(self, adapter_type: str, env: Dict[str, str]) -> list[str]:
        """
        Choose the worker command. Prefer adapter-specific override (UET_ADAPTER_CMD_*),
        otherwise fall back to a harmless long-running Python loop.
        """
        override_key = f"UET_ADAPTER_CMD_{adapter_type.upper()}"
        if override_key in env and env[override_key]:
            return env[override_key].split()

        # Default: long-lived Python process to keep worker alive until reused.
        return ["python", "-c", "import time; time.sleep(3600)"]
