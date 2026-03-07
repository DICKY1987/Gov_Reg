#!/usr/bin/env python3
"""
PHASE_5 Execution Engine - PATH ABSTRACTION VERSION

Migrated to use PathRegistry and environment adapters for deterministic execution.
All file I/O, git operations, and subprocess calls now use adapters with audit logging.

DOC_ID: DOC-CORE-PHASE-5-EXECUTION-ENGINE-V2-389
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add modules to path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
)
)

from path_abstraction.path_registry import PathRegistry
from adapters.fs_adapter import FilesystemAdapter
from adapters.git_adapter import GitAdapter

# Event emission (Phase 3: Observability)
try:
    )
    from event_emitter import get_event_emitter
    EVENT_SYSTEM_AVAILABLE = True
except ImportError:
    EVENT_SYSTEM_AVAILABLE = False
    def get_event_emitter():
        return None

def _emit_event(subsystem: str, step_id: str, subject: str, summary: str,
                severity: str = "INFO", details: dict = None):
    """Helper to emit events with graceful degradation if event system unavailable."""
    if EVENT_SYSTEM_AVAILABLE:
        try:
            emitter = get_event_emitter()
            if emitter:
                emitter.emit(
                    subsystem=subsystem,
                    step_id=step_id,
                    subject=subject,
                    summary=summary,
                    severity=severity,
                    details=details or {}
                )
        except Exception:
            pass  # Gracefully degrade if event system fails

# Import TaskExecutor
try:
    from .task_executor import TaskExecutor
except ImportError:
    # Fallback: add engine directory to path
    engine_path = Path(__file__).parent
    if str(engine_path) not in sys.path:
        )
    from task_executor import TaskExecutor


class ExecutionEngine:
    """
    Phase 5 execution engine with path abstraction.

    Replaces hardcoded paths and subprocess calls with:
    - PathRegistry for all path resolution
    - FilesystemAdapter for file I/O with write containment
    - GitAdapter for git operations with deterministic output
    """

    def __init__(self, run_id: Optional[str] = None):
        # Initialize PathRegistry
        self.registry = PathRegistry(
            index_path=str(REPO_ROOT / "SUB_PATH_REGISTRY" / "path_index.yaml"),
            repo_root=str(REPO_ROOT)
        )

        # Initialize adapters with write containment
        self.fs_adapter = FilesystemAdapter(
            self.registry,
            allowed_write_keys=['logs:phase_5', 'data:', 'phase:5:']
        )
        self.git_adapter = GitAdapter(self.registry, repo_root=REPO_ROOT)

        # Run metadata
        self.run_id = run_id or f"phase5-run-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.start_time = datetime.now()
        self.tasks: List[Dict] = []
        self.results: Dict[str, Any] = {
            "run_id": self.run_id,
            "start_time": self.start_time.isoformat(),
            "tasks_executed": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "errors": []
        }

        # Ensure output directories exist
        self._ensure_directories()

        # Emit ENGINE_INITIALIZED event
        _emit_event(
            subsystem="PHASE_5_EXECUTION",
            step_id="ENGINE_INITIALIZED",
            subject="execution_engine_v2",
            summary=f"Execution engine initialized (run_id={self.run_id})",
            severity="INFO",
            details={"run_id": self.run_id, "start_time": self.start_time.isoformat()}
        )

    def _ensure_directories(self) -> None:
        """Ensure required directories exist using PathRegistry."""
        required_dirs = ['logs:phase_5', 'phase:5:root']

        for key in required_dirs:
            try:
                path = self.registry.resolve(key)
                path.mkdir(parents=True, exist_ok=True)
            except KeyError:
                pass

    def log(self, message: str, level: str = "INFO") -> None:
        """Log a message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {
            "INFO": "[INFO]",
            "SUCCESS": "[ OK ]",
            "ERROR": "[FAIL]",
            "WARN": "[WARN]",
        }
        print(f"[{timestamp}] {prefix.get(level, '[INFO]')} {message}")

    def load_execution_plan(self, plan_key: str) -> bool:
        """
        Load execution plan from semantic key.

        OLD: Path("/path/to/plan.json").read_text()
        NEW: fs_adapter.read_json(plan_key)
        """
        self.log(f"Loading execution plan: {plan_key}")

        # Emit PLAN_LOAD_STARTED event
        _emit_event(
            subsystem="PHASE_5_EXECUTION",
            step_id="PLAN_LOAD_STARTED",
            subject=plan_key,
            summary=f"Loading execution plan: {plan_key}",
            severity="INFO",
            details={"plan_key": plan_key, "run_id": self.run_id}
        )

        try:
            # Use FilesystemAdapter for read operations
            plan_data = self.fs_adapter.read_json(plan_key)

            # Extract tasks from plan
            self.tasks = plan_data.get('tasks', [])
            self.log(f"Loaded {len(self.tasks)} task(s)", "SUCCESS")

            # Emit PLAN_LOADED event
            _emit_event(
                subsystem="PHASE_5_EXECUTION",
                step_id="PLAN_LOADED",
                subject=plan_key,
                summary=f"Plan loaded successfully: {len(self.tasks)} tasks",
                severity="INFO",
                details={"plan_key": plan_key, "task_count": len(self.tasks), "run_id": self.run_id}
            )
            return True

        except Exception as exc:
            self.log(f"Failed to load plan: {exc}", "ERROR")
            self.results["errors"].append(f"Plan load failed: {exc}")

            # Emit PLAN_LOAD_FAILED event
            _emit_event(
                subsystem="PHASE_5_EXECUTION",
                step_id="PLAN_LOAD_FAILED",
                subject=plan_key,
                summary=f"Failed to load plan: {exc}",
                severity="ERROR",
                details={"plan_key": plan_key, "error": str(exc), "run_id": self.run_id}
            )
            return False

    def check_prerequisites(self) -> bool:
        """
        Check prerequisites using PathRegistry.

        OLD: Path("/hardcoded/path").exists()
        NEW: registry.resolve(semantic_key).exists()
        """
        self.log("Checking prerequisites...")

        required_keys = [
            'phase:5:root',
            'modules:types',
            'common:system_determinism'
        ]

        missing = []
        for key in required_keys:
            try:
                path = self.registry.resolve(key)
                if not path.exists():
                    missing.append(f"{key} -> {path}")
            except KeyError:
                missing.append(f"{key} (not in registry)")

        if missing:
            for item in missing:
                self.log(f"Missing: {item}", "ERROR")
            return False

        self.log("Prerequisites validated", "SUCCESS")
        return True

    def check_git_status(self) -> Dict:
        """
        Check git status using GitAdapter.

        OLD: subprocess.run(['git', 'status'], ...)
        NEW: git_adapter.status()
        """
        self.log("Checking git repository status...")

        try:
            status = self.git_adapter.status()
            status_msg = 'clean' if status['is_clean'] else f"{len(status['changes'])} changes"
            level = "SUCCESS" if status['is_clean'] else "WARN"
            self.log(f"Repository status: {status_msg}", level)
            return status
        except Exception as exc:
            self.log(f"Git status check failed: {exc}", "ERROR")
            return {"is_clean": False, "changes": [], "error": str(exc)}

    def execute_task(self, task: Dict) -> Dict:
        """
        Execute a single task using TaskExecutor.

        All operations go through TaskExecutor which handles:
        - test_run: Execute pytest with specified scope
        - git_operation: Git operations via GitAdapter
        - file_edit: File operations with write containment
        - command_execute: Shell commands with timeout
        - generic: Log task details
        """
        task_id = task.get('task_id', 'unknown')
        operation = task.get('operation_kind', 'generic')
        self.log(f"Executing task: {task_id} ({operation})")

        # Emit TASK_STARTED event
        _emit_event(
            subsystem="PHASE_5_EXECUTION",
            step_id="TASK_STARTED",
            subject=task_id,
            summary=f"Starting task: {task_id} ({operation})",
            severity="INFO",
            details={"task_id": task_id, "operation": operation, "run_id": self.run_id}
        )

        try:
            # Create TaskExecutor with adapters
            executor = TaskExecutor(
                registry=self.registry,
                fs_adapter=self.fs_adapter,
                git_adapter=self.git_adapter
            )

            # Execute task
            result = executor.execute(task)

            # Update counters based on exit code
            if result.get('exit_code', 1) == 0:
                self.results["tasks_completed"] += 1
                self.log(f"Task {task_id} completed", "SUCCESS")

                # Emit TASK_COMPLETED event
                _emit_event(
                    subsystem="PHASE_5_EXECUTION",
                    step_id="TASK_COMPLETED",
                    subject=task_id,
                    summary=f"Task completed: {task_id}",
                    severity="INFO",
                    details={"task_id": task_id, "operation": operation, "exit_code": 0, "run_id": self.run_id}
                )
            else:
                self.results["tasks_failed"] += 1
                error_msg = result.get('stderr', result.get('error', 'Unknown error'))
                self.log(f"Task {task_id} failed: {error_msg}", "ERROR")
                self.results["errors"].append(f"Task {task_id}: {error_msg}")

                # Emit TASK_FAILED event
                _emit_event(
                    subsystem="PHASE_5_EXECUTION",
                    step_id="TASK_FAILED",
                    subject=task_id,
                    summary=f"Task failed: {task_id} - {error_msg}",
                    severity="ERROR",
                    details={"task_id": task_id, "operation": operation, "error": error_msg, "run_id": self.run_id}
                )

            return result

        except Exception as exc:
            self.log(f"Task {task_id} execution error: {exc}", "ERROR")
            self.results["tasks_failed"] += 1
            self.results["errors"].append(f"Task {task_id}: {exc}")

            # Emit TASK_FAILED event
            _emit_event(
                subsystem="PHASE_5_EXECUTION",
                step_id="TASK_FAILED",
                subject=task_id,
                summary=f"Task execution error: {task_id} - {exc}",
                severity="ERROR",
                details={"task_id": task_id, "operation": operation, "error": str(exc), "run_id": self.run_id}
            )

            return {
                "task_id": task_id,
                "operation_kind": operation,
                "status": "failed",
                "exit_code": 1,
                "error": str(exc),
                "stdout": "",
                "stderr": str(exc),
                "timestamp": datetime.now().isoformat()
            }

    def execute_all(self) -> bool:
        """Execute all loaded tasks."""
        if not self.tasks:
            self.log("No tasks to execute", "WARN")
            return False

        self.log(f"Executing {len(self.tasks)} task(s)...")

        # Emit EXECUTION_STARTED event
        _emit_event(
            subsystem="PHASE_5_EXECUTION",
            step_id="EXECUTION_STARTED",
            subject="execute_all",
            summary=f"Starting execution of {len(self.tasks)} tasks",
            severity="INFO",
            details={"task_count": len(self.tasks), "run_id": self.run_id}
        )

        task_results = []

        for idx, task in enumerate(self.tasks, 1):
            result = self.execute_task(task)
            task_results.append(result)
            self.results["tasks_executed"] += 1

            # Emit progress event every 5 tasks
            if idx % 5 == 0:
                _emit_event(
                    subsystem="PHASE_5_EXECUTION",
                    step_id="EXECUTION_PROGRESS",
                    subject="execute_all",
                    summary=f"Progress: {idx}/{len(self.tasks)} tasks executed",
                    severity="INFO",
                    details={
                        "tasks_executed": idx,
                        "total_tasks": len(self.tasks),
                        "tasks_completed": self.results["tasks_completed"],
                        "tasks_failed": self.results["tasks_failed"],
                        "run_id": self.run_id
                    }
                )

        # Store results in task_results key
        self.results["task_results"] = task_results

        success = self.results["tasks_failed"] == 0
        if success:
            self.log("All tasks completed successfully", "SUCCESS")
        else:
            self.log(f"{self.results['tasks_failed']} task(s) failed", "ERROR")

        # Emit EXECUTION_COMPLETED event
        _emit_event(
            subsystem="PHASE_5_EXECUTION",
            step_id="EXECUTION_COMPLETED",
            subject="execute_all",
            summary=f"Execution completed: {self.results['tasks_completed']}/{len(self.tasks)} tasks succeeded",
            severity="NOTICE" if success else "ERROR",
            details={
                "total_tasks": len(self.tasks),
                "tasks_completed": self.results["tasks_completed"],
                "tasks_failed": self.results["tasks_failed"],
                "success": success,
                "run_id": self.run_id
            }
        )

        return success

    def generate_report(self) -> None:
        """
        Generate execution report using FilesystemAdapter.

        OLD: open("/path/to/report.json", "w").write(...)
        NEW: fs_adapter.write_json(semantic_key, data)
        """
        self.log("Generating execution report...")

        try:
            self.results["end_time"] = datetime.now().isoformat()
            self.results["duration_seconds"] = (datetime.now() - self.start_time).total_seconds()
            self.results["success"] = self.results["tasks_failed"] == 0

            # Write report to logs directory using semantic key
            import json
            log_path = self.registry.resolve('logs:phase_5')
            report_file = log_path / f"{self.run_id}_results.json"
            report_file.write_text(json.dumps(self.results, indent=2), encoding='utf-8')

            self.log(f"Report written to: logs:phase_5/{self.run_id}_results.json", "SUCCESS")

            # Export adapter audit logs
            fs_audit = self.fs_adapter.export_audit_log()
            git_audit = self.git_adapter.export_audit_log()

            audit_file = log_path / f"{self.run_id}_audit.json"
            audit_file.write_text(json.dumps({
                "filesystem_operations": fs_audit,
                "git_operations": git_audit,
                "total_operations": len(fs_audit) + len(git_audit)
            }, indent=2), encoding='utf-8')

            self.log(f"Audit log: {len(fs_audit)} fs ops, {len(git_audit)} git ops", "SUCCESS")

        except Exception as exc:
            self.log(f"Report generation failed: {exc}", "ERROR")
            self.results["errors"].append(f"Report generation: {exc}")

    def run(self) -> int:
        """Execute the full workflow."""
        self.log("=" * 70)
        self.log("PHASE 5 EXECUTION ENGINE - PATH ABSTRACTION VERSION")
        self.log(f"Run ID: {self.run_id}")
        self.log("=" * 70)

        # Workflow steps
        if not self.check_prerequisites():
            self.log("Prerequisites check failed", "ERROR")
            return 1

        self.check_git_status()

        # For demo, create a stub execution plan
        self.tasks = [
            {"id": "task-1", "action": "stub-action-1"},
            {"id": "task-2", "action": "stub-action-2"},
            {"id": "task-3", "action": "stub-action-3"}
        ]
        self.log(f"Loaded {len(self.tasks)} stub task(s)", "INFO")

        self.execute_all()
        self.generate_report()

        # Final summary
        self.log("=" * 70)
        if self.results["errors"]:
            self.log(f"Execution completed with {len(self.results['errors'])} error(s)", "WARN")
            return 1
        else:
            self.log("Execution completed successfully", "SUCCESS")
            return 0


def main() -> int:
    """Entry point."""
    engine = ExecutionEngine()
    return engine.run()


if __name__ == "__main__":
    sys.exit(main())
