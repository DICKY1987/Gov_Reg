# DOC_LINK: DOC-CORE-ENGINE-PHASE-COORDINATOR-500
"""Phase Coordinator - Central automation orchestrator for Phase 4→5→6 flow.

Coordinates routing, execution, and error recovery in a fully automated loop.
"""

# DOC_ID: DOC-CORE-ENGINE-PHASE-COORDINATOR-500

from __future__ import annotations

import logging
import DOC-ERROR-UTILS-TIME-145__time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.engine.executor import Executor
from core.engine.orchestrator import Orchestrator
from core.engine.recovery import RecoveryConfig, RecoveryCoordinator
from core.engine.router import TaskRouter
from core.engine.scheduler import ExecutionScheduler, Task
from core.engine.state_file_manager import StateFileManager
from core.events.event_bus import EventBus, EventType

logger = logging.getLogger(__name__)


@dataclass
class PhaseCoordinatorConfig:
    """Configuration for phase coordinator."""

    routing_enabled: bool = True
    execution_enabled: bool = True
    error_recovery_enabled: bool = True

    routing_timeout_seconds: int = 300
    execution_timeout_seconds: int = 1800
    error_recovery_timeout_seconds: int = 900

    max_parallel_tasks: int = 5
    max_retries: int = 2

    auto_fix_enabled: bool = True
    agents: List[str] = None
    fallback_agent: str = "aider"

    state_output_dir: str = ".state"
    archive_on_completion: bool = True
    retention_days: int = 30

    events_enabled: bool = True
    export_to_jsonl: bool = True
    jsonl_path: str = "logs/phase_events.jsonl"

    def __post_init__(self):
        if self.agents is None:
            self.agents = ["aider", "codex", "claude"]


class PhaseCoordinator:
    """Coordinates automated flow between Phase 4 (Routing), Phase 5 (Execution), and Phase 6 (Error Recovery)."""

    def __init__(
        self,
        orchestrator: Orchestrator,
        router: TaskRouter,
        scheduler: ExecutionScheduler,
        config: Optional[PhaseCoordinatorConfig] = None,
        state_manager: Optional[StateFileManager] = None,
        event_bus: Optional[EventBus] = None,
    ):
        self.orchestrator = orchestrator
        self.router = router
        self.scheduler = scheduler
        self.config = config or PhaseCoordinatorConfig()
        self.state_manager = state_manager or StateFileManager(
            self.config.state_output_dir
        )
        self.event_bus = event_bus or EventBus()
        # Ensure shared bus across components
        self.router.event_bus = (
            getattr(self.router, "event_bus", None) or self.event_bus
        )
        self.orchestrator.event_bus = (
            getattr(self.orchestrator, "event_bus", None) or self.event_bus
        )

        # Initialize executor with recovery enabled
        self.executor = Executor(
            orchestrator=orchestrator,
            router=router,
            scheduler=scheduler,
            state_manager=self.state_manager,
            event_bus=self.event_bus,
            enable_recovery=self.config.error_recovery_enabled,
        )

        # Initialize recovery coordinator if enabled
        self.recovery_coordinator = None
        if self.config.error_recovery_enabled:
            recovery_config = RecoveryConfig(max_retries=self.config.max_retries)
            self.recovery_coordinator = RecoveryCoordinator(
                scheduler=self.scheduler,
                event_bus=self.event_bus,
                recovery_config=recovery_config,
            )

        self._subscribe_events()

    def _subscribe_events(self):
        """Subscribe to relevant events for coordination."""
        if not self.config.events_enabled:
            return

        self.event_bus.subscribe(EventType.ROUTING_COMPLETE, self._on_routing_complete)
        self.event_bus.subscribe(EventType.TASK_FAILED, self._on_task_failed)
        self.event_bus.subscribe(EventType.FIX_APPLIED, self._on_fix_applied)

    def run_full_pipeline(self, run_id: str, tasks: List[Task]) -> Dict[str, Any]:
        """Execute the full Phase 4→5→6 pipeline with automated recovery.

        Args:
            run_id: Unique run identifier
            tasks: List of tasks to execute

        Returns:
            Summary of execution results
        """
        start_time = time.time()
        logger.info(f"Starting full pipeline for run {run_id} with {len(tasks)} tasks")

        results = {
            "run_id": run_id,
            "total_tasks": len(tasks),
            "routing_results": {},
            "execution_results": {},
            "recovery_results": {},
            "success": False,
            "duration_seconds": 0,
        }

        try:
            # Phase 4: Routing
            if self.config.routing_enabled:
                logger.info(f"Phase 4: Routing {len(tasks)} tasks")
                routing_results = self._run_routing_phase(run_id, tasks)
                results["routing_results"] = routing_results

            # Phase 5: Execution
            if self.config.execution_enabled:
                logger.info(f"Phase 5: Executing {len(tasks)} tasks")
                execution_results = self._run_execution_phase(run_id, tasks)
                results["execution_results"] = execution_results

            # Phase 6: Error Recovery (if there were failures)
            if self.config.error_recovery_enabled:
                failed_tasks = [t for t in tasks if t.status == "failed"]
                if failed_tasks:
                    logger.info(f"Phase 6: Recovering {len(failed_tasks)} failed tasks")
                    recovery_results = self._run_error_recovery_phase(
                        run_id, failed_tasks
                    )
                    results["recovery_results"] = recovery_results

            results["success"] = True

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            results["error"] = str(e)
            results["success"] = False

        results["duration_seconds"] = time.time() - start_time

        # Export final state
        self._export_final_state(run_id, results)

        logger.info(
            f"Pipeline completed for run {run_id} in {results['duration_seconds']:.2f}s"
        )
        return results

    def _run_routing_phase(self, run_id: str, tasks: List[Task]) -> Dict[str, Any]:
        """Execute Phase 4: Route tasks to appropriate tools."""
        routing_decisions = []

        for task in tasks:
            selected_tool = self.router.route_task(
                task_kind=task.task_kind,
                risk_tier=task.metadata.get("risk_tier"),
                complexity=task.metadata.get("complexity"),
                domain=task.metadata.get("domain"),
                task_id=task.task_id,
                run_id=run_id,
            )

            if selected_tool:
                task.selected_tool = selected_tool
                task.metadata["selected_tool"] = selected_tool
                routing_decisions.append(
                    {
                        "task_id": task.task_id,
                        "selected_tool": selected_tool,
                    }
                )
            else:
                logger.warning(f"No tool selected for task {task.task_id}")

        # Export routing decisions
        decisions_file = self.state_manager.export_routing_decisions(
            run_id=run_id,
            decisions=self.router.decision_log,
        )

        # Export adapter assignments
        assignments_file = self.state_manager.export_adapter_assignments(
            run_id=run_id,
            tasks=tasks,
        )

        # Emit routing complete event
        self.event_bus.emit(
            EventType.ROUTING_COMPLETE,
            run_id=run_id,
            payload={
                "decisions_count": (
                    len(self.router.decision_log)
                    if hasattr(self.router, "decision_log")
                    else len(routing_decisions)
                ),
                "decisions_file": str(decisions_file),
                "assignments_file": str(assignments_file),
            },
        )

        return {
            "decisions_count": (
                len(self.router.decision_log)
                if hasattr(self.router, "decision_log")
                else len(routing_decisions)
            ),
            "decisions_file": str(decisions_file),
            "assignments_file": str(assignments_file),
        }

    def _run_execution_phase(self, run_id: str, tasks: List[Task]) -> Dict[str, Any]:
        """Execute Phase 5: Run tasks with assigned tools."""
        execution_summary = {
            "total": len(tasks),
            "succeeded": 0,
            "failed": 0,
            "skipped": 0,
        }

        # Add tasks to scheduler
        for task in tasks:
            self.scheduler.add_task(task)

        exec_result = None
        manual_counted = False
        if hasattr(self.executor, "execute_task"):
            while True:
                ready_tasks = self.scheduler.get_ready_tasks()
                if not ready_tasks:
                    break

                for task in ready_tasks[: self.config.max_parallel_tasks]:
                    try:
                        result = self.executor.execute_task(run_id, task)
                        exec_result = result
                        if result and result.exit_code == 0:
                            task.status = "completed"
                            execution_summary["succeeded"] += 1
                        else:
                            task.status = "failed"
                            execution_summary["failed"] += 1
                    except Exception as e:
                        logger.error(f"Task {task.task_id} failed: {e}")
                        task.status = "failed"
                        task.error = str(e)
                        execution_summary["failed"] += 1
            manual_counted = True
        else:
            exec_result = self.executor.run(run_id)

        if not manual_counted:
            for task in tasks:
                if task.status in ("completed", "succeeded"):
                    execution_summary["succeeded"] += 1
                elif task.status == "failed":
                    execution_summary["failed"] += 1
                else:
                    execution_summary["skipped"] += 1

        # Export execution results
        results_file = self.state_manager.export_execution_results(
            run_id=run_id,
            tasks=tasks,
        )

        return {
            **execution_summary,
            "results_file": str(results_file),
            "executor_state": self._serialize_obj(exec_result),
        }

    def _run_error_recovery_phase(
        self, run_id: str, failed_tasks: List[Task]
    ) -> Dict[str, Any]:
        """Execute Phase 6: Analyze and fix errors."""
        recovery_summary = {
            "total_failures": len(failed_tasks),
            "auto_fixed": 0,
            "manual_required": 0,
            "quarantined": 0,
            "retried": 0,
            "retry_succeeded": 0,
            "retry_failed": 0,
        }
        retry_candidates: List[Task] = []

        for task in failed_tasks:
            try:
                # Invoke error pipeline
                fix_result = self._invoke_error_pipeline(run_id, task)

                if fix_result.get("success"):
                    recovery_summary["auto_fixed"] += 1
                    task.status = "pending"
                    task.error = None
                    retry_candidates.append(task)

                    # Emit fix applied event
                    self.event_bus.emit(
                        EventType.FIX_APPLIED,
                        run_id=run_id,
                        task_id=task.task_id,
                        payload={
                            "fix_agent": fix_result.get("agent"),
                            "files_modified": fix_result.get("files_modified", []),
                            "retry_task_ids": [task.task_id],
                        },
                    )
                elif fix_result.get("quarantined"):
                    recovery_summary["quarantined"] += 1
                else:
                    recovery_summary["manual_required"] += 1

            except Exception as e:
                logger.error(f"Error recovery failed for task {task.task_id}: {e}")
                recovery_summary["manual_required"] += 1

        # Retry recovered tasks
        if retry_candidates:
            for task in retry_candidates:
                task.status = "pending"
            self.executor.run(run_id)
            recovery_summary["retried"] = len(retry_candidates)
            for task in retry_candidates:
                if task.status in ("completed", "succeeded"):
                    recovery_summary["retry_succeeded"] += 1
                elif task.status == "failed":
                    recovery_summary["retry_failed"] += 1

        return recovery_summary

    def _invoke_error_pipeline(self, run_id: str, task: Task) -> Dict[str, Any]:
        """Invoke Phase 6 error pipeline for a failed task."""
        try:
            from phase6_error_recovery.modules.error_engine.src.engine.agent_adapters import (
                AgentInvocation,
                get_agent_adapter,
            )

            # Build error report
            error_report = {
                "task_id": task.task_id,
                "run_id": run_id,
                "issues": [
                    {
                        "path": task.metadata.get("file", "unknown"),
                        "message": task.error or "Unknown error",
                        "category": "execution_failure",
                    }
                ],
            }

            # Try agents in order
            for agent_name in self.config.agents:
                try:
                    adapter = get_agent_adapter(agent_name)

                    if not adapter.check_available():
                        continue

                    invocation = AgentInvocation(
                        agent_name=agent_name,
                        files=[task.metadata.get("file", "")],
                        error_report=error_report,
                        timeout_seconds=self.config.error_recovery_timeout_seconds,
                    )

                    result = adapter.invoke(invocation)

                    if result.success:
                        return {
                            "success": True,
                            "agent": agent_name,
                            "files_modified": result.files_modified,
                        }

                except Exception as e:
                    logger.warning(f"Agent {agent_name} failed: {e}")
                    continue

            # All agents failed
            return {"success": False, "quarantined": False}

        except Exception as e:
            logger.error(f"Error pipeline invocation failed: {e}")
            return {"success": False, "quarantined": False}

    def _export_final_state(self, run_id: str, results: Dict[str, Any]):
        """Export final pipeline state to JSON."""
        final_state_file = (
            Path(self.config.state_output_dir) / f"pipeline_results_{run_id}.json"
        )

        import json

        serializable = self._serialize_obj(results)

        with open(final_state_file, "w") as f:
            json.dump(serializable, f, indent=2)

        logger.info(f"Final state exported to {final_state_file}")

    def _on_routing_complete(self, event):
        """Handle ROUTING_COMPLETE event."""
        logger.debug(f"Routing complete: {event}")

    def _on_task_failed(self, event):
        """Handle TASK_FAILED event."""
        logger.debug(f"Task failed: {event}")

    def _on_fix_applied(self, event):
        """Handle FIX_APPLIED event."""
        logger.debug(f"Fix applied: {event}")

    def _serialize_obj(self, obj: Any):
        """Best-effort serialization for JSON export."""
        if obj is None:
            return None
        if isinstance(obj, dict):
            return {k: self._serialize_obj(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [self._serialize_obj(v) for v in obj]
        if hasattr(obj, "__dict__"):
            return {k: self._serialize_obj(v) for k, v in obj.__dict__.items()}
        if hasattr(obj, "_asdict"):
            return self._serialize_obj(obj._asdict())
        return obj


def create_phase_coordinator(
    orchestrator: Orchestrator,
    router: TaskRouter,
    scheduler: ExecutionScheduler,
    config: Optional[PhaseCoordinatorConfig] = None,
) -> PhaseCoordinator:
    """Factory function to create a phase coordinator.

    Args:
        orchestrator: Run orchestrator
        router: Task router
        scheduler: Execution scheduler
        config: Optional configuration

    Returns:
        Configured PhaseCoordinator instance
    """
    return PhaseCoordinator(
        orchestrator=orchestrator,
        router=router,
        scheduler=scheduler,
        config=config,
    )
