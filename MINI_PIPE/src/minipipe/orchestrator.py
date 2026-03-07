"""Run Orchestrator - WS-03-01A

Main orchestration logic for executing workstreams.
Manages run lifecycle, state transitions, and event emission.
"""

# DOC_ID: DOC-CORE-ENGINE-ORCHESTRATOR-151

import subprocess
import time
import uuid
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

from core.engine.plan_schema import Plan, StepDef
from core.engine.state_machine import RunStateMachine, StepStateMachine
from core.events.event_bus import Event, EventBus, EventSeverity
from core.state.db import Database, get_db
from patterns.decisions.decision_registry import Decision, DecisionRegistry


class Orchestrator:
    """Main orchestration engine for running workstreams"""

    def generate_ulid(self) -> str:
        """Generate ULID (deterministic if flag set)"""
        if self.deterministic_mode:
            self._deterministic_counter += 1
            return f"DET{self._deterministic_counter:022d}"
        else:
            return uuid.uuid4().hex.upper()[:26]

    def now_iso(self) -> str:
        """Get current timestamp (deterministic if flag set)"""
        if self.deterministic_mode:
            return "2024-01-01T00:00:00.000000Z"
        else:
            return datetime.now(UTC).isoformat() + "Z"

    def __init__(
        self,
        db: Optional[Database] = None,
        event_bus: Optional[EventBus] = None,
        deterministic_mode: bool = False,
    ):
        self.db = db or get_db()
        self.event_bus = event_bus or EventBus(db_path=str(self.db.db_path))
        self.deterministic_mode = deterministic_mode
        self._deterministic_counter = 0

    # Run lifecycle management

    def create_run(
        self,
        project_id: str,
        phase_id: str,
        workstream_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a new run in pending state.

        Args:
            project_id: Project identifier
            phase_id: Phase being executed
            workstream_id: Optional workstream being executed
            metadata: Optional metadata dictionary

        Returns:
            run_id: Created run identifier
        """
        if getattr(self.db, "conn", None) is None and hasattr(self.db, "connect"):
            self.db.connect()
        run_id = self.generate_ulid()

        run_data = {
            "run_id": run_id,
            "project_id": project_id,
            "phase_id": phase_id,
            "workstream_id": workstream_id,
            "created_at": self.now_iso(),
            "state": "pending",
            "metadata": metadata or {},
        }

        self.db.create_run(run_data)

        # Emit event
        self._emit_event(
            run_id,
            "run_created",
            {
                "project_id": project_id,
                "phase_id": phase_id,
                "workstream_id": workstream_id,
            },
        )

        return run_id

    def start_run(self, run_id: str) -> bool:
        """
        Transition run from pending to running.

        Args:
            run_id: Run to start

        Returns:
            True if transition succeeded, False otherwise
        """
        if getattr(self.db, "conn", None) is None and hasattr(self.db, "connect"):
            self.db.connect()
        run = self.db.get_run(run_id)
        if not run:
            raise ValueError(f"Run not found: {run_id}")

        # Validate transition
        error = RunStateMachine.validate_transition(run["state"], "running")
        if error:
            raise ValueError(error)

        # Update state
        self.db.update_run(run_id, {"state": "running", "started_at": now_iso()})

        # Emit event
        self._emit_event(run_id, "run_started", {})

        return True

    def complete_run(
        self,
        run_id: str,
        status: str,
        exit_code: int = 0,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        Complete a run with success/failure status.

        Args:
            run_id: Run to complete
            status: Final status ('succeeded', 'failed', 'quarantined', 'canceled')
            exit_code: Exit code (0 for success)
            error_message: Optional error message

        Returns:
            True if transition succeeded, False otherwise
        """
        if getattr(self.db, "conn", None) is None and hasattr(self.db, "connect"):
            self.db.connect()
        run = self.db.get_run(run_id)
        if not run:
            raise ValueError(f"Run not found: {run_id}")

        # Validate transition
        error = RunStateMachine.validate_transition(run["state"], status)
        if error:
            raise ValueError(error)

        # Update state
        updates = {"state": status, "ended_at": now_iso(), "exit_code": exit_code}

        if error_message:
            updates["error_message"] = error_message

        self.db.update_run(run_id, updates)

        # Emit event
        self._emit_event(
            run_id, "run_completed", {"status": status, "exit_code": exit_code}
        )

        return True

    def quarantine_run(self, run_id: str, reason: str) -> bool:
        """
        Quarantine a run due to errors or safety concerns.

        Args:
            run_id: Run to quarantine
            reason: Reason for quarantine

        Returns:
            True if successful
        """
        run = self.db.get_run(run_id)
        if not run:
            raise ValueError(f"Run not found: {run_id}")

        # Can quarantine from running or failed state
        current_state = run["state"]
        if current_state not in ["running", "failed"]:
            raise ValueError(f"Cannot quarantine run in state '{current_state}'")

        error = RunStateMachine.validate_transition(current_state, "quarantined")
        if error:
            raise ValueError(error)

        self.db.update_run(
            run_id,
            {"state": "quarantined", "ended_at": now_iso(), "error_message": reason},
        )

        self._emit_event(run_id, "run_quarantined", {"reason": reason})

        return True

    def cancel_run(self, run_id: str, reason: str = "Canceled by user") -> bool:
        """
        Cancel a pending or running run.

        Args:
            run_id: Run to cancel
            reason: Cancellation reason

        Returns:
            True if successful
        """
        run = self.db.get_run(run_id)
        if not run:
            raise ValueError(f"Run not found: {run_id}")

        error = RunStateMachine.validate_transition(run["state"], "canceled")
        if error:
            raise ValueError(error)

        self.db.update_run(
            run_id,
            {"state": "canceled", "ended_at": now_iso(), "error_message": reason},
        )

        self._emit_event(run_id, "run_canceled", {"reason": reason})

        return True

    # Step attempt management

    def create_step_attempt(
        self,
        run_id: str,
        tool_id: str,
        sequence: int,
        prompt: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a step attempt within a run.

        Args:
            run_id: Parent run ID
            tool_id: Tool being invoked
            sequence: Step sequence number
            prompt: Optional input prompt
            metadata: Optional metadata

        Returns:
            step_attempt_id: Created step attempt ID
        """
        # Verify run exists and is running
        run = self.db.get_run(run_id)
        if not run:
            raise ValueError(f"Run not found: {run_id}")

        if run["state"] != "running":
            raise ValueError(f"Cannot create step for run in state '{run['state']}'")

        step_id = generate_ulid()

        step_data = {
            "step_attempt_id": step_id,
            "run_id": run_id,
            "sequence": sequence,
            "tool_id": tool_id,
            "started_at": now_iso(),
            "state": "running",
            "metadata": metadata or {},
        }

        # Add prompt if provided (not in minimal schema)
        if prompt:
            step_data["input_prompt"] = prompt

        self.db.create_step_attempt(step_data)

        self._emit_event(
            run_id,
            "step_started",
            {"step_attempt_id": step_id, "sequence": sequence, "tool_id": tool_id},
        )

        return step_id

    def complete_step_attempt(
        self,
        step_attempt_id: str,
        status: str,
        exit_code: int = 0,
        output_patch_id: Optional[str] = None,
        error_log: Optional[str] = None,
    ) -> bool:
        """
        Complete a step attempt with status.

        Args:
            step_attempt_id: Step to complete
            status: Final status ('succeeded', 'failed', 'canceled')
            exit_code: Exit code
            output_patch_id: Optional patch artifact ID
            error_log: Optional error log

        Returns:
            True if successful
        """
        step = self.db.get_step_attempt(step_attempt_id)
        if not step:
            raise ValueError(f"Step attempt not found: {step_attempt_id}")

        error = StepStateMachine.validate_transition(step["state"], status)
        if error:
            raise ValueError(error)

        updates = {"state": status, "ended_at": now_iso(), "exit_code": exit_code}

        if output_patch_id:
            updates["output_patch_id"] = output_patch_id

        if error_log:
            updates["error_log"] = error_log

        self.db.update_step_attempt(step_attempt_id, updates)

        self._emit_event(
            step["run_id"],
            "step_completed",
            {
                "step_attempt_id": step_attempt_id,
                "status": status,
                "exit_code": exit_code,
            },
        )

        return True

    # Query methods

    def get_run_status(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get current run status"""
        return self.db.get_run(run_id)

    def list_runs(
        self,
        project_id: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List runs with optional filters"""
        filters = {}
        if project_id:
            filters["project_id"] = project_id
        if state:
            filters["state"] = state

        return self.db.list_runs(filters, limit)

    def get_run_steps(self, run_id: str) -> List[Dict[str, Any]]:
        """Get all steps for a run"""
        return self.db.list_step_attempts(run_id)

    def get_run_events(self, run_id: str) -> List[Dict[str, Any]]:
        """Get all events for a run"""
        return self.db.list_events(run_id)

    # Event emission

    def _emit_event(self, run_id: str, event_type: str, data: Dict[str, Any]):
        """Emit a run event to the shared event bus."""
        event = Event(
            event_type=event_type,
            timestamp=datetime.now(UTC),
            run_id=run_id,
            payload=data,
            severity=EventSeverity.INFO,
        )
        self.event_bus.emit(event)

    # Plan execution engine

    def execute_plan(
        self, plan_path: str, variables: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Execute a JSON plan file and return run_id.

        Args:
            plan_path: Path to JSON plan file
            variables: Runtime variables for ${VAR} substitution

        Returns:
            run_id: Created run identifier

        Raises:
            ValueError: If plan is invalid or execution fails
        """
        # Load and validate plan
        plan = Plan.from_file(plan_path, variables)

        # Create run
        run_id = self.create_run(
            project_id=plan.metadata.get("project", "unknown"),
            phase_id=plan.metadata.get("phase_id", "ORCHESTRATED"),
            metadata={
                "plan_id": plan.plan_id,
                "plan_version": plan.version,
                "plan_path": plan_path,
                "variables": variables or {},
            },
        )

        try:
            self.start_run(run_id)

            # Initialize plan state
            state = self._init_plan_state(plan)

            # Main execution loop
            while self._has_pending_or_running_steps(state):
                # Update running steps (check completion, timeouts)
                self._update_running_steps(run_id, state, plan)

                # Find and start runnable steps
                runnable = self._find_runnable_steps(state, plan)
                max_conc = plan.globals.get("max_concurrency", 1)
                running_count = len(state["running"])

                for step_def in runnable[: max(0, max_conc - running_count)]:
                    self._start_plan_step(run_id, step_def, state, plan)

                time.sleep(0.5)

            # Determine final status
            final_status = self._compute_final_status(state)
            exit_code = 0 if final_status == "succeeded" else 1

            self.complete_run(run_id, final_status, exit_code)

        except Exception as e:
            self.complete_run(run_id, "failed", exit_code=1, error_message=str(e))
            raise

        return run_id

    def _init_plan_state(self, plan: Plan) -> Dict[str, Any]:
        """Initialize state tracking for plan execution."""
        return {
            "steps": {
                step.id: {
                    "status": "PENDING",
                    "started_at": None,
                    "finished_at": None,
                    "attempt": 0,
                    "exit_code": None,
                    "error": None,
                    "process": None,
                    "step_attempt_id": None,
                }
                for step in plan.steps
            },
            "running": {},  # step_id -> subprocess.Popen
        }

    def _has_pending_or_running_steps(self, state: Dict[str, Any]) -> bool:
        """Check if there are any steps still pending or running."""
        pending_running = {"PENDING", "RUNNING"}
        for step_state in state["steps"].values():
            if step_state["status"] in pending_running:
                return True
        return False

    def _find_runnable_steps(self, state: Dict[str, Any], plan: Plan) -> List[StepDef]:
        """Find steps that are ready to run (dependencies met)."""
        runnable = []

        for step_def in plan.steps:
            step_state = state["steps"][step_def.id]

            # Skip if not pending
            if step_state["status"] != "PENDING":
                continue

            # Check all dependencies are successful
            deps_ok = all(
                state["steps"][dep_id]["status"] == "SUCCESS"
                for dep_id in step_def.depends_on
            )

            if deps_ok:
                runnable.append(step_def)

        return runnable

    def _start_plan_step(
        self, run_id: str, step_def: StepDef, state: Dict[str, Any], plan: Plan
    ):
        """Start executing a plan step."""
        step_state = state["steps"][step_def.id]
        step_state["attempt"] += 1

        # Create step attempt record
        step_attempt_id = self.create_step_attempt(
            run_id=run_id,
            tool_id=step_def.command,
            sequence=list(plan.steps).index(step_def),
            metadata={
                "step_id": step_def.id,
                "step_name": step_def.name,
                "attempt": step_state["attempt"],
            },
        )

        step_state["step_attempt_id"] = step_attempt_id
        step_state["status"] = "RUNNING"
        step_state["started_at"] = time.time()

        # Build command
        cmd = [step_def.command] + step_def.args

        # Merge environment variables
        env = dict(**plan.globals.get("env", {}))
        env.update(step_def.env)

        # Start subprocess
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=step_def.cwd,
                shell=step_def.shell,
                env=env if env else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            step_state["process"] = proc
            state["running"][step_def.id] = proc

            self._emit_event(
                run_id,
                "step_started",
                {
                    "step_id": step_def.id,
                    "step_attempt_id": step_attempt_id,
                    "command": step_def.command,
                    "attempt": step_state["attempt"],
                },
            )

        except Exception as e:
            step_state["status"] = "FAILED"
            step_state["error"] = str(e)
            self.complete_step_attempt(
                step_attempt_id, status="failed", exit_code=-1, error_log=str(e)
            )
            self._handle_step_failure(run_id, step_def, state, plan)

    def _update_running_steps(self, run_id: str, state: Dict[str, Any], plan: Plan):
        """Poll running steps and handle completion/timeout."""
        now = time.time()

        for step_id in list(state["running"].keys()):
            step_state = state["steps"][step_id]
            step_def = plan.get_step(step_id)
            proc = step_state["process"]

            # Check timeout
            timeout = step_def.timeout_sec or plan.globals.get(
                "default_timeout_sec", 1800
            )
            if step_state["started_at"] and (now - step_state["started_at"]) > timeout:
                proc.kill()
                step_state["status"] = "FAILED"
                step_state["error"] = f"Timeout after {timeout}s"
                step_state["finished_at"] = now
                step_state["exit_code"] = -1

                self.complete_step_attempt(
                    step_state["step_attempt_id"],
                    status="failed",
                    exit_code=-1,
                    error_log=f"Timeout after {timeout}s",
                )

                self._emit_event(
                    run_id, "step_timeout", {"step_id": step_id, "timeout_sec": timeout}
                )

                del state["running"][step_id]
                self._handle_step_failure(run_id, step_def, state, plan)
                continue

            # Check if process completed
            exit_code = proc.poll()
            if exit_code is None:
                continue  # Still running

            # Process completed
            stdout, stderr = proc.communicate()
            step_state["exit_code"] = exit_code
            step_state["finished_at"] = now

            if exit_code == 0:
                step_state["status"] = "SUCCESS"
                self.complete_step_attempt(
                    step_state["step_attempt_id"], status="succeeded", exit_code=0
                )
                self._emit_event(
                    run_id,
                    "step_succeeded",
                    {"step_id": step_id, "exit_code": exit_code},
                )
            else:
                step_state["status"] = "FAILED"
                step_state["error"] = stderr.strip() or f"Exit code {exit_code}"
                self.complete_step_attempt(
                    step_state["step_attempt_id"],
                    status="failed",
                    exit_code=exit_code,
                    error_log=stderr,
                )
                self._emit_event(
                    run_id, "step_failed", {"step_id": step_id, "exit_code": exit_code}
                )
                self._handle_step_failure(run_id, step_def, state, plan)

            del state["running"][step_id]

    def _handle_step_failure(
        self, run_id: str, step_def: StepDef, state: Dict[str, Any], plan: Plan
    ):
        """Handle step failure with retry and failure policies."""
        step_state = state["steps"][step_def.id]

        # Check if retry is possible
        max_retries = step_def.retries or plan.globals.get("default_retries", 0)

        if step_state["attempt"] < (max_retries + 1):
            # Retry
            time.sleep(step_def.retry_delay_sec)
            step_state["status"] = "PENDING"
            step_state["process"] = None
            self._emit_event(
                run_id,
                "step_retry",
                {"step_id": step_def.id, "attempt": step_state["attempt"] + 1},
            )
            return

        # No more retries, apply failure policy
        if step_def.on_failure == "abort" and step_def.critical:
            # Cancel all pending steps
            for sid, sstate in state["steps"].items():
                if sstate["status"] == "PENDING":
                    sstate["status"] = "CANCELED"
            self._emit_event(
                run_id,
                "plan_aborted",
                {"reason": f"Critical step '{step_def.id}' failed"},
            )

        elif step_def.on_failure == "skip_dependents":
            # Skip downstream steps
            self._skip_downstream_steps(step_def.id, state, plan)

        # "continue" does nothing - dependent steps remain runnable

    def _skip_downstream_steps(
        self, failed_step_id: str, state: Dict[str, Any], plan: Plan
    ):
        """Mark all steps that depend on failed step as SKIPPED."""
        for step_def in plan.steps:
            if failed_step_id in step_def.depends_on:
                step_state = state["steps"][step_def.id]
                if step_state["status"] == "PENDING":
                    step_state["status"] = "SKIPPED"
                    # Recursively skip downstream
                    self._skip_downstream_steps(step_def.id, state, plan)

    def _compute_final_status(self, state: Dict[str, Any]) -> str:
        """Compute final run status from step states."""
        statuses = [s["status"] for s in state["steps"].values()]

        if any(status == "FAILED" for status in statuses):
            return "failed"

        success_skipped = {"SUCCESS", "SKIPPED"}
        if all(status in success_skipped for status in statuses):
            return "succeeded"
        else:
            return "quarantined"
