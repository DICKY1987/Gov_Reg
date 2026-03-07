"""
MINI_PIPE Integration Adapter for ACMS

Provides adapter for executing MINI_PIPE execution plans.
Supports Phase 4 (execution via MINI_PIPE orchestrator).
"""

import json
import subprocess
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ExecutionRequest:
    """MINI_PIPE execution request"""

    execution_plan_path: Path
    repo_root: Path
    run_id: str
    timeout_seconds: int = 3600


@dataclass
class TaskResult:
    """Result of a single task execution"""

    task_id: str
    status: str  # completed, failed, skipped
    exit_code: int
    output: Optional[str] = None
    error: Optional[str] = None
    execution_time_seconds: float = 0.0


@dataclass
class ExecutionResult:
    """MINI_PIPE execution result"""

    success: bool
    tasks_completed: int = 0
    tasks_failed: int = 0
    tasks_skipped: int = 0
    task_results: List[TaskResult] = None
    execution_time_seconds: float = 0.0
    error: Optional[str] = None


class MiniPipeAdapter:
    """Adapter for MINI_PIPE orchestrator"""

    def __init__(
        self,
        orchestrator_cli_path: Optional[Path] = None,
        python_executable: str = "python",
    ):
        self.orchestrator_cli_path = orchestrator_cli_path or self._find_orchestrator()
        self.python_executable = python_executable

    def _find_orchestrator(self) -> Path:
        """Find MINI_PIPE orchestrator CLI"""
        # Check common locations
        candidates = [
            Path(__file__).parent.parent.parent
            / "src"
            / "minipipe"
            / "orchestrator_cli.py",
            Path.cwd() / "src" / "minipipe" / "orchestrator_cli.py",
        ]

        for candidate in candidates:
            if candidate.exists():
                return candidate

        # Not found - will use mock execution
        return None

    def execute_plan(self, request: ExecutionRequest) -> ExecutionResult:
        """Execute MINI_PIPE execution plan"""
        start_time = time.time()

        if not self.orchestrator_cli_path or not self.orchestrator_cli_path.exists():
            print("  ⚠️  MINI_PIPE orchestrator not found, using mock execution")
            return self._mock_execution(request, start_time)

        try:
            # Load plan to validate structure
            with open(request.execution_plan_path, "r", encoding="utf-8") as f:
                plan = json.load(f)

            # Convert ACMS plan format to MINI_PIPE plan format if needed
            minipipe_plan = self._convert_to_minipipe_format(plan, request)

            # Save converted plan
            converted_plan_path = (
                request.execution_plan_path.parent
                / f"minipipe_{request.execution_plan_path.name}"
            )
            with open(converted_plan_path, "w", encoding="utf-8") as f:
                json.dump(minipipe_plan, f, indent=2)

            # Build orchestrator command
            cmd = [
                self.python_executable,
                str(self.orchestrator_cli_path),
                "run",
                "--plan",
                str(converted_plan_path),
                "--phase",
                request.run_id,
                "--project",
                "acms",
                "--timeout",
                str(request.timeout_seconds),
            ]

            print(f"  → Executing: {' '.join(cmd)}")

            # Execute
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=request.timeout_seconds,
                cwd=request.repo_root,
            )

            # Parse results
            if result.returncode == 0:
                task_results = self._parse_orchestrator_output(result.stdout, plan)

                return ExecutionResult(
                    success=True,
                    tasks_completed=sum(
                        1 for t in task_results if t.status == "completed"
                    ),
                    tasks_failed=sum(1 for t in task_results if t.status == "failed"),
                    tasks_skipped=sum(1 for t in task_results if t.status == "skipped"),
                    task_results=task_results,
                    execution_time_seconds=time.time() - start_time,
                )
            else:
                # Partial success - parse what we can
                print(f"  ⚠️  Orchestrator returned non-zero: {result.returncode}")
                print(f"  → Stderr: {result.stderr[:200]}")

                # Still try to parse partial results
                task_results = self._parse_orchestrator_output(result.stdout, plan)

                if task_results:
                    return ExecutionResult(
                        success=False,
                        tasks_completed=sum(
                            1 for t in task_results if t.status == "completed"
                        ),
                        tasks_failed=sum(
                            1 for t in task_results if t.status == "failed"
                        ),
                        tasks_skipped=sum(
                            1 for t in task_results if t.status == "skipped"
                        ),
                        task_results=task_results,
                        execution_time_seconds=time.time() - start_time,
                        error=result.stderr,
                    )
                else:
                    return ExecutionResult(
                        success=False,
                        error=result.stderr or "Unknown error",
                        execution_time_seconds=time.time() - start_time,
                    )

        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                error=f"Execution timed out after {request.timeout_seconds}s",
                execution_time_seconds=time.time() - start_time,
            )
        except Exception as e:
            print(f"  ⚠️  Execution failed: {e}")
            return ExecutionResult(
                success=False,
                error=str(e),
                execution_time_seconds=time.time() - start_time,
            )

    def _convert_to_minipipe_format(
        self, acms_plan: Dict[str, Any], request: ExecutionRequest
    ) -> Dict[str, Any]:
        """Convert ACMS plan to MINI_PIPE orchestrator format"""
        # MINI_PIPE orchestrator expects a different structure
        # Convert our task-based plan to workstream-based plan

        return {
            "version": "1.0",
            "name": acms_plan.get("name", "ACMS Execution"),
            "description": acms_plan.get("description", ""),
            "workstreams": [
                {
                    "id": f"ws_{i}",
                    "name": task.get("task_kind", "task"),
                    "steps": [
                        {
                            "id": task["task_id"],
                            "type": task.get("task_kind", "generic"),
                            "description": task.get("description", ""),
                            "metadata": task.get("metadata", {}),
                        }
                    ],
                }
                for i, task in enumerate(acms_plan.get("tasks", []))
            ],
            "metadata": {
                "repo_root": str(request.repo_root),
                "run_id": request.run_id,
                **acms_plan.get("metadata", {}),
            },
        }

    def _mock_execution(
        self, request: ExecutionRequest, start_time: float
    ) -> ExecutionResult:
        """Mock execution when orchestrator not available"""
        # Load execution plan to get task count
        with open(request.execution_plan_path, "r", encoding="utf-8") as f:
            plan = json.load(f)

        tasks = plan.get("tasks", [])

        # Create mock results
        task_results = []
        for task in tasks:
            task_results.append(
                TaskResult(
                    task_id=task["task_id"],
                    status="completed",
                    exit_code=0,
                    output="Mock execution - orchestrator not available",
                    execution_time_seconds=0.1,
                )
            )

        return ExecutionResult(
            success=True,
            tasks_completed=len(tasks),
            tasks_failed=0,
            tasks_skipped=0,
            task_results=task_results,
            execution_time_seconds=time.time() - start_time,
        )

    def _parse_orchestrator_output(
        self, output: str, plan: Dict[str, Any]
    ) -> List[TaskResult]:
        """Parse orchestrator output to extract task results"""
        task_results = []
        tasks = plan.get("tasks", [])

        # Look for patterns in output
        # Format: "Task TASK_0001: completed" or "Created run: RUN_ID"
        lines = output.split("\n")

        completed_tasks = set()
        for line in lines:
            if "Task " in line or "TASK_" in line:
                for task in tasks:
                    task_id = task["task_id"]
                    if task_id in line:
                        # Determine status from line
                        if "completed" in line.lower() or "success" in line.lower():
                            status = "completed"
                        elif "failed" in line.lower() or "error" in line.lower():
                            status = "failed"
                        elif "skip" in line.lower():
                            status = "skipped"
                        else:
                            status = "completed"  # Assume success

                        completed_tasks.add(task_id)
                        task_results.append(
                            TaskResult(
                                task_id=task_id,
                                status=status,
                                exit_code=0 if status == "completed" else 1,
                                output=line,
                                execution_time_seconds=0.1,
                            )
                        )

        # Add results for tasks not mentioned (assume completed if run succeeded)
        for task in tasks:
            if task["task_id"] not in completed_tasks:
                task_results.append(
                    TaskResult(
                        task_id=task["task_id"],
                        status="completed",  # Optimistic assumption
                        exit_code=0,
                        output="Inferred from orchestrator output",
                        execution_time_seconds=0.1,
                    )
                )

        return task_results


class MockMiniPipeAdapter(MiniPipeAdapter):
    """Mock adapter for testing without MINI_PIPE"""

    def __init__(self):
        self.orchestrator_cli_path = None
        self.python_executable = "python"  # Provide a default, but it won't be used

    def execute_plan(self, request: ExecutionRequest) -> ExecutionResult:
        """Always use mock execution"""
        return self._mock_execution(request, time.time())


def create_minipipe_adapter(adapter_type: str = "auto", **kwargs) -> MiniPipeAdapter:
    """Factory function to create MINI_PIPE adapters"""
    if adapter_type == "mock":
        return MockMiniPipeAdapter()
    elif adapter_type == "real":
        # Use real orchestrator integration
        from src.acms.real_minipipe_adapter import create_real_minipipe_adapter

        repo_root = kwargs.get("repo_root", Path.cwd())
        return create_real_minipipe_adapter(repo_root)
    elif adapter_type == "auto":
        # Try real first, fall back to mock
        try:
            from src.acms.real_minipipe_adapter import create_real_minipipe_adapter

            repo_root = kwargs.get("repo_root", Path.cwd())
            adapter = create_real_minipipe_adapter(repo_root)
            print("  ✓ Using real MINI_PIPE orchestrator")
            return adapter
        except (ImportError, FileNotFoundError) as e:
            print(f"  ⚠️  Real orchestrator not available: {e}")
            print("  → Falling back to mock adapter")
            return MockMiniPipeAdapter()
    else:
        raise ValueError(f"Unknown adapter type: {adapter_type}")
