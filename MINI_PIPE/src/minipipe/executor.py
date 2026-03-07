"""Parallel execution workers

Runs scheduled workstream tasks with isolation and telemetry capture.

GUARDRAILS: This module enforces pattern-based execution with pre/post validation.
"""

# DOC_ID: DOC-CORE-ENGINE-EXECUTOR-149

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from core.adapters.base import ToolConfig
from core.adapters.subprocess_adapter import SubprocessAdapter
from core.contracts.decorators import enforce_entry_contract, enforce_exit_contract
from core.engine.execution_request_builder import ExecutionRequestBuilder
from src.minipipe.orchestrator import Orchestrator
from src.minipipe.router import TaskRouter
from src.minipipe.scheduler import ExecutionScheduler, Task
from core.engine.state_file_manager import StateFileManager
from core.events.event_bus import EventBus, EventSeverity, EventType

# GUARDRAILS: Import guardrails enforcement
try:
    from src.acms.guardrails import PatternGuardrails, AntiPatternDetector

    GUARDRAILS_AVAILABLE = True
except ImportError:
    GUARDRAILS_AVAILABLE = False
    PatternGuardrails = None
    AntiPatternDetector = None

__all__ = ["AdapterResult", "Executor"]


@dataclass
class AdapterResult:
    """Container for adapter execution outcomes."""

    exit_code: int = 0
    output_patch_id: Optional[str] = None
    error_log: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class Executor:
    """Executes scheduled tasks by routing them to adapters and updating run state."""

    def __init__(
        self,
        orchestrator: Orchestrator,
        router: TaskRouter,
        scheduler: ExecutionScheduler,
        adapter_runner: Optional[
            Callable[[Task, str, Dict[str, Any]], AdapterResult]
        ] = None,
        gate_callback: Optional[Callable[[str, Task, AdapterResult], bool]] = None,
        state_manager: Optional[StateFileManager] = None,
        event_bus: Optional[EventBus] = None,
        enable_recovery: bool = False,
        enable_guardrails: bool = True,
        pattern_index_path: Optional[Path] = None,
    ):
        """
        Args:
            orchestrator: Run/state orchestrator
            router: Task router for selecting tool_id
            scheduler: Scheduler holding tasks to execute
            adapter_runner: Callable that executes a task with a tool and returns AdapterResult
                (run metadata is provided as third arg). If omitted, a default subprocess
                adapter is used based on router config.
            gate_callback: Optional quality gate callable (run_id, task, result) -> bool
            enable_guardrails: Enable pattern guardrails enforcement (default: True)
            pattern_index_path: Path to PATTERN_INDEX.yaml (default: ./PATTERN_INDEX.yaml)
        """
        self.orchestrator = orchestrator
        self.router = router
        self.scheduler = scheduler
        self.adapter_runner = adapter_runner or self._run_with_adapter
        self.gate_callback = gate_callback
        self.state_manager = state_manager or StateFileManager()
        self.event_bus = (
            event_bus or getattr(orchestrator, "event_bus", None) or EventBus()
        )
        self.recovery_enabled = enable_recovery
        self.recovery_coordinator = None
        if self.recovery_enabled:
            try:
                from src.minipipe.recovery import RecoveryCoordinator

                self.recovery_coordinator = RecoveryCoordinator(
                    scheduler=self.scheduler, event_bus=self.event_bus
                )
            except Exception:
                self.recovery_coordinator = None

        # GUARDRAILS: Initialize pattern guardrails
        self.guardrails_enabled = enable_guardrails and GUARDRAILS_AVAILABLE
        self.guardrails = None
        self.anti_pattern_detector = None

        if self.guardrails_enabled:
            try:
                pattern_index = (
                    pattern_index_path or Path(__file__).parent / "PATTERN_INDEX.yaml"
                )
                if pattern_index.exists():
                    self.guardrails = PatternGuardrails(pattern_index)

                    # Initialize anti-pattern detector
                    anti_patterns_dir = Path(__file__).parent / "anti_patterns"
                    if anti_patterns_dir.exists():
                        self.anti_pattern_detector = AntiPatternDetector(
                            anti_patterns_dir
                        )
                else:
                    self.guardrails_enabled = False
            except Exception as e:
                self.guardrails_enabled = False

    def _emit_guardrail_event(
        self,
        event_type: EventType,
        run_id: str,
        task: Task,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Emit guardrail-specific events (doesn't require tool_id)"""
        if not self.event_bus:
            return

        base_payload = {}
        if task:
            base_payload["task_id"] = task.task_id
            if hasattr(task, "task_kind"):
                base_payload["task_kind"] = task.task_kind

        merged_payload = {**base_payload, **(payload or {})}
        self.event_bus.emit(event_type, run_id or "system", merged_payload)

    def _check_guardrails_pre_execution(
        self, task: Task, run_id: str
    ) -> tuple[bool, list]:
        """
        GUARDRAILS: Run pre-execution checks

        Returns:
            (passed, violations)
        """
        if not self.guardrails_enabled or not self.guardrails:
            return True, []

        # Extract pattern_id from task
        pattern_id = task.metadata.get("pattern_id")
        if not pattern_id:
            # No pattern_id means this is a legacy task - allow it but warn
            self._emit_guardrail_event(
                EventType.SYSTEM_WARNING,
                run_id,
                task,
                payload={"message": "Task has no pattern_id (violates invariant PG-1)"},
            )
            return True, []

        # Build task data for guardrail checks
        task_data = {
            "file_paths": task.metadata.get("file_paths", []),
            "tools_used": [task.selected_tool] if task.selected_tool else [],
            "operations": task.metadata.get("operations", []),
        }

        # Run pre-execution checks
        try:
            passed, violations = self.guardrails.pre_execution_checks(
                pattern_id=pattern_id, task_data=task_data
            )

            if not passed:
                # Log violations
                for violation in violations:
                    self._emit_guardrail_event(
                        EventType.TASK_FAILED,
                        run_id,
                        task,
                        payload={
                            "guardrail_violation": {
                                "rule_id": violation.rule_id,
                                "severity": violation.severity,
                                "message": violation.message,
                                "context": violation.context,
                            }
                        },
                    )

            return passed, violations

        except Exception as e:
            self._emit_guardrail_event(
                EventType.SYSTEM_WARNING,
                run_id,
                task,
                payload={"message": f"Guardrail pre-check failed: {e}"},
            )
            return True, []  # Don't block on guardrail errors

    def _check_guardrails_post_execution(
        self, task: Task, result: AdapterResult, run_id: str
    ) -> tuple[bool, list]:
        """
        GUARDRAILS: Run post-execution checks

        Returns:
            (passed, violations)
        """
        if not self.guardrails_enabled or not self.guardrails:
            return True, []

        pattern_id = task.metadata.get("pattern_id")
        if not pattern_id:
            return True, []

        # Build task result for guardrail checks
        task_result = {
            "status": "success" if result.exit_code == 0 else "failed",
            "changes": task.metadata.get("changes", {}),
            "verification": {
                "exit_code": result.exit_code,
                "tests_run": task.result_metadata.get("tests_run", 0),
                "tests_passed": task.result_metadata.get("tests_passed", 0),
            },
            "expected_outputs": task.metadata.get("expected_outputs", []),
        }

        # Run post-execution checks
        try:
            passed, violations = self.guardrails.post_execution_checks(
                pattern_id=pattern_id, task_result=task_result
            )

            if not passed:
                # Check if this is hallucinated success
                for violation in violations:
                    if violation.rule_id == "AP_HALLUCINATED_SUCCESS":
                        self._emit_guardrail_event(
                            EventType.SYSTEM_WARNING,
                            run_id,
                            task,
                            payload={
                                "anti_pattern_detected": "AP_HALLUCINATED_SUCCESS",
                                "evidence": violation.message,
                            },
                        )

                    self._emit_guardrail_event(
                        EventType.TASK_FAILED,
                        run_id,
                        task,
                        payload={
                            "guardrail_violation": {
                                "rule_id": violation.rule_id,
                                "severity": violation.severity,
                                "message": violation.message,
                            }
                        },
                    )

            return passed, violations

        except Exception as e:
            self._emit_guardrail_event(
                EventType.SYSTEM_WARNING,
                run_id,
                task,
                payload={"message": f"Guardrail post-check failed: {e}"},
            )
            return True, []

    @enforce_entry_contract(phase="phase5_execution")
    def execute_task(self, run_id: str, task: Task) -> Optional[AdapterResult]:
        """Execute a single task and return its result.

        Args:
            run_id: Run identifier
            task: Task to execute

        Returns:
            AdapterResult or None if execution failed
        """
        run = self.orchestrator.get_run_status(run_id)
        if not run:
            raise ValueError(f"Run not found: {run_id}")

        # GUARDRAILS: Pre-execution checks
        passed, violations = self._check_guardrails_pre_execution(task, run_id)
        if not passed:
            task.exit_code = 1
            task.error_log = f"Pre-execution guardrail violations: {len(violations)}"
            task.status = "blocked"
            task.result_metadata = {
                "guardrail_violations": [
                    {"rule_id": v.rule_id, "severity": v.severity, "message": v.message}
                    for v in violations
                ]
            }
            return None

        tool_id = task.selected_tool or task.metadata.get("selected_tool")
        if not tool_id:
            task.exit_code = 1
            task.error_log = "No tool assigned to task"
            task.status = "failed"
            return None

        try:
            result = self.adapter_runner(task, tool_id, run)
            task.exit_code = result.exit_code
            task.output_patch_id = result.output_patch_id
            task.error_log = result.error_log
            task.result_metadata = result.metadata or {}

            # GUARDRAILS: Post-execution checks
            passed, violations = self._check_guardrails_post_execution(
                task, result, run_id
            )

            if not passed:
                # Override status if guardrails failed
                # This catches hallucinated success
                if result.exit_code == 0:
                    self._emit_guardrail_event(
                        EventType.SYSTEM_WARNING,
                        run_id,
                        task,
                        payload={
                            "message": "Overriding claimed success due to guardrail violations",
                            "original_exit_code": result.exit_code,
                        },
                    )

                task.exit_code = 1
                task.status = "failed"
                task.error_log = (
                    f"Post-execution guardrail violations: {len(violations)}"
                )
                task.result_metadata["guardrail_violations"] = [
                    {"rule_id": v.rule_id, "severity": v.severity, "message": v.message}
                    for v in violations
                ]
            elif result.exit_code == 0:
                task.status = "completed"
            else:
                task.status = "failed"
                task.error = result.error_log

            return result

        except Exception as e:
            task.exit_code = 1
            task.error_log = str(e)
            task.status = "failed"
            task.error = str(e)
            return None

    def run(self, run_id: str) -> Dict[str, Any]:
        """Execute all ready tasks in the scheduler for the given run.

        Returns:
            Summary dict with run_id and final state.
        """
        run = self.orchestrator.get_run_status(run_id)
        if not run:
            raise ValueError(f"Run not found: {run_id}")

        if run["state"] == "pending":
            self.orchestrator.start_run(run_id)
            # Fresh decision log per run to avoid leaking prior assignments
            if hasattr(self.router, "clear_decision_log"):
                self.router.clear_decision_log()

        sequence = 0

        while True:
            ready_tasks = self.scheduler.get_ready_tasks()
            if not ready_tasks:
                break

            for task in ready_tasks:
                sequence += 1
                self.scheduler.mark_running(task.task_id)

                tool_id = self.router.route_task(
                    task.task_kind,
                    task_id=task.task_id,
                    run_id=run_id,
                )
                task.selected_tool = tool_id

                if not tool_id:
                    task.exit_code = 1
                    task.error_log = "No capable tool found"
                    self.scheduler.mark_failed(task.task_id, "No capable tool found")
                    self._emit_event(
                        EventType.TASK_FAILED,
                        run_id,
                        task,
                        tool_id=None,
                        payload={"reason": "No capable tool found"},
                    )
                    continue

                step_id = self.orchestrator.create_step_attempt(
                    run_id=run_id,
                    tool_id=tool_id,
                    sequence=sequence,
                    prompt=task.metadata.get("description"),
                )

                self._emit_event(
                    EventType.TASK_ASSIGNED,
                    run_id,
                    task,
                    tool_id=tool_id,
                    payload={"description": task.metadata.get("description")},
                )
                self._emit_event(EventType.TASK_STARTED, run_id, task, tool_id=tool_id)

                try:
                    result = self.adapter_runner(task, tool_id, run)
                except Exception as exc:  # pragma: no cover - defensive
                    # Ensure we capture execution failure cleanly
                    self.orchestrator.complete_step_attempt(
                        step_id,
                        "failed",
                        exit_code=1,
                        error_log=str(exc),
                    )
                    task.exit_code = 1
                    task.error_log = str(exc)
                    self.scheduler.mark_failed(task.task_id, str(exc))
                    self._emit_event(
                        EventType.TASK_FAILED,
                        run_id,
                        task,
                        tool_id=tool_id,
                        payload={"error": str(exc)},
                    )
                    continue

                exit_code = result.exit_code
                status = "succeeded" if exit_code == 0 else "failed"
                task.exit_code = exit_code
                task.output_patch_id = result.output_patch_id
                task.error_log = result.error_log
                task.result_metadata = result.metadata or {}

                # Optional quality gate hook
                if status == "succeeded" and self.gate_callback:
                    gate_passed = bool(self.gate_callback(run_id, task, result))
                    if not gate_passed:
                        status = "failed"
                        exit_code = exit_code or 1
                        task.error_log = task.error_log or "Gate rejected result"

                self.orchestrator.complete_step_attempt(
                    step_id,
                    status,
                    exit_code=exit_code,
                    output_patch_id=result.output_patch_id,
                    error_log=result.error_log,
                )

                if status == "succeeded":
                    self.scheduler.mark_completed(task.task_id, result)
                    self._emit_event(
                        EventType.TASK_COMPLETED,
                        run_id,
                        task,
                        tool_id=tool_id,
                        payload={
                            "exit_code": exit_code,
                            "output_patch_id": result.output_patch_id,
                            "metadata": task.result_metadata,
                        },
                    )
                else:
                    task.error_log = (
                        task.error_log or result.error_log or "Execution failed"
                    )
                    self.scheduler.mark_failed(
                        task.task_id, result.error_log or "Execution failed"
                    )
                    self._emit_event(
                        EventType.TASK_FAILED,
                        run_id,
                        task,
                        tool_id=tool_id,
                        payload={
                            "exit_code": exit_code,
                            "error": task.error_log,
                            "metadata": task.result_metadata,
                        },
                    )

        final_state = (
            "succeeded"
            if self.scheduler.is_complete() and not self.scheduler.has_failures()
            else "failed"
        )
        exit_code = 0 if final_state == "succeeded" else 1

        self.orchestrator.complete_run(run_id, final_state, exit_code=exit_code)

        # Flush router state to disk
        if hasattr(self.router, "state_store") and hasattr(
            self.router.state_store, "flush"
        ):
            self.router.state_store.flush()

        if self.state_manager:
            tasks = list(self.scheduler.tasks.values())
            decisions = []
            if hasattr(self.router, "decision_log"):
                decisions = [
                    decision
                    for decision in getattr(self.router, "decision_log", [])
                    if getattr(decision, "run_id", None) in (None, run_id)
                ]
            self.state_manager.export_routing_decisions(run_id, decisions)
            self.state_manager.export_adapter_assignments(run_id, tasks)
            self.state_manager.export_execution_results(run_id, tasks)
            if self.event_bus:
                self.event_bus.emit(
                    EventType.ROUTING_COMPLETE,
                    run_id=run_id,
                    payload={
                        "decision_count": len(decisions),
                        "adapter_assignments": len(tasks),
                        "state_files": {
                            "routing": ".state/routing_decisions.json",
                            "assignments": ".state/adapter_assignments.json",
                            "execution": ".state/execution_results.json",
                        },
                    },
                )

        return {"run_id": run_id, "state": final_state}

    def _emit_event(
        self,
        event_type: EventType,
        run_id: str,
        task: Task,
        tool_id: Optional[str],
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Publish task lifecycle events."""
        if not self.event_bus:
            return

        base_payload = {
            "task_id": task.task_id,
            "task_kind": task.task_kind,
            "tool_id": tool_id,
        }
        merged_payload = {**base_payload, **(payload or {})}
        self.event_bus.emit(
            event_type,
            run_id=run_id,
            task_id=task.task_id,
            tool_id=tool_id,
            payload=merged_payload,
            severity=EventSeverity.INFO,
        )

    def _run_with_adapter(
        self, task: Task, tool_id: str, run: Dict[str, Any]
    ) -> AdapterResult:
        """Default adapter runner that shells out using SubprocessAdapter."""
        tool_config = self.router.get_tool_config(tool_id)
        if not tool_config:
            raise ValueError(f"Tool config not found for {tool_id}")

        config = ToolConfig(
            tool_id=tool_id,
            kind=tool_config.get("kind", "tool"),
            command=tool_config["command"],
            capabilities=tool_config.get("capabilities", {}),
            limits=tool_config.get("limits", {}),
            safety_tier=tool_config.get("safety_tier", "medium"),
        )
        adapter = SubprocessAdapter(config)

        builder = (
            ExecutionRequestBuilder()
            .with_task(task.task_kind, task.metadata.get("description", ""))
            .with_tool(tool_id, config.command)
        )

        if constraints := task.metadata.get("constraints"):
            builder.with_constraints(constraints)

        request = builder.build()
        request["project_id"] = run.get("project_id")
        request["phase_id"] = run.get("phase_id")
        request["workstream_id"] = run.get("workstream_id")

        result = adapter.execute(request, timeout=config.get_timeout())

        return AdapterResult(
            exit_code=result.exit_code,
            error_log=result.error_message or result.stderr,
            metadata={
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": result.metadata.get("command") if result.metadata else None,
            },
        )
