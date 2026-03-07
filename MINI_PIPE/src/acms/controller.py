"""ACMS Controller - Gap Phase Execution Pipeline

GOLDEN PATH ORCHESTRATOR: Single recommended entrypoint for ACMS → MINI_PIPE execution.

Top-level CLI orchestrator for gap analysis → planning → execution.
Implements all 6 phases of the GAP_PHASE_EXECUTION_MINI_PIPE specification.

GUARDRAILS: Enforces pattern-based execution with anti-pattern detection.

See acms_golden_path.py for architecture documentation.
"""

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.acms.golden_path import RunState, DEFAULT_CONFIG
from src.acms.uet_execution_planner import UETExecutionPlanner
from src.acms.gap_registry import GapRegistry
from src.acms.phase_plan_compiler import PhasePlanCompiler
from src.acms.ai_adapter import create_ai_adapter, AIRequest
from src.acms.minipipe_adapter import create_minipipe_adapter, ExecutionRequest
from src.acms.uet_submodule_io_contracts import GitWorkspaceRefV1
from src.acms.path_registry import ensure_dir

# GUARDRAILS: Import guardrails enforcement
try:
    from src.acms.guardrails import PatternGuardrails, AntiPatternDetector

    GUARDRAILS_AVAILABLE = True
except ImportError:
    GUARDRAILS_AVAILABLE = False
    PatternGuardrails = None
    AntiPatternDetector = None

# MONITORING: Import monitoring and notifications
try:
    from src.acms.notifications import create_notifier_from_env
    from src.acms.monitoring import create_monitoring_system, PipelineMetrics

    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False
    create_notifier_from_env = None
    create_monitoring_system = None
    PipelineMetrics = None


class ACMSController:
    """
    ACMS Controller - Golden Path Orchestrator

    This is the single recommended entrypoint for ACMS execution.
    All runs follow the state machine: INIT → GAP_ANALYSIS → PLANNING → EXECUTION → SUMMARY → DONE
    """

    def __init__(
        self,
        repo_root: Path,
        run_id: Optional[str] = None,
        ai_adapter_type: str = "auto",  # Changed from "mock" to "auto" (Phase 2)
        minipipe_adapter_type: str = "auto",
        config: Optional[Dict[str, Any]] = None,
        enable_guardrails: bool = True,
    ):
        self.repo_root = repo_root.resolve()
        self.run_id = run_id or self._generate_ulid()
        self.run_dir = self.repo_root / ".acms_runs" / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)

        # Configuration (defaults from golden path)
        self.config = {**DEFAULT_CONFIG, **(config or {})}

        # Core components
        self.gap_registry = GapRegistry(self.run_dir / "gap_registry.json")
        self.execution_planner = UETExecutionPlanner(self.gap_registry, self.run_id)
        self.phase_plan_compiler = PhasePlanCompiler()
        self.ai_adapter = create_ai_adapter(ai_adapter_type)
        self.minipipe_adapter = create_minipipe_adapter(
            minipipe_adapter_type,
            repo_root=self.repo_root,  # Pass repo_root for real adapter
        )

        # GUARDRAILS: Initialize guardrails system
        self.guardrails_enabled = enable_guardrails and GUARDRAILS_AVAILABLE
        self.guardrails = None
        self.anti_pattern_detector = None
        self.run_stats = {
            "planning_attempts": 0,
            "patches_applied": 0,
            "hallucination_count": 0,
            "anti_patterns_detected": [],
        }

        if self.guardrails_enabled:
            try:
                pattern_index = self.repo_root / "patterns" / "PATTERN_INDEX.yaml"
                if pattern_index.exists():
                    self.guardrails = PatternGuardrails(pattern_index)

                    # Initialize anti-pattern detector
                    anti_patterns_dir = self.repo_root / "anti_patterns"
                    if anti_patterns_dir.exists():
                        self.anti_pattern_detector = AntiPatternDetector(
                            anti_patterns_dir
                        )
                        print(
                            f"✓ Guardrails enabled with {len(self.anti_pattern_detector.runbooks)} anti-pattern runbooks"
                        )
                    else:
                        print(
                            "⚠ Anti-patterns directory not found, anti-pattern detection disabled"
                        )
                else:
                    self.guardrails_enabled = False
                    print(
                        f"⚠ PATTERN_INDEX.yaml not found at {pattern_index}, guardrails disabled"
                    )
            except Exception as e:
                self.guardrails_enabled = False
                print(f"⚠ Failed to initialize guardrails: {e}")

        # MONITORING: Initialize monitoring and notifications
        self.notifier = None
        self.metrics_collector = None
        self.health_monitor = None
        self.current_metrics = None

        if MONITORING_AVAILABLE:
            try:
                self.notifier = create_notifier_from_env()
                monitoring = create_monitoring_system(self.repo_root)
                self.metrics_collector, self.health_monitor, _ = monitoring
                self.current_metrics = PipelineMetrics(
                    run_id=self.run_id, start_time=datetime.now()
                )
                print("✓ Monitoring and notifications enabled")
            except Exception as e:
                print(f"⚠ Failed to initialize monitoring: {e}")

        # Initialize workspace reference for UET workstreams
        self.workspace_ref = GitWorkspaceRefV1(
            ws_id=f"ws_{self.run_id}",
            root_path=str(self.repo_root),
            branch_name=self._get_current_branch(),
        )

        # Run state (immutable record with explicit state machine)
        self.current_state = RunState.INIT
        self.state = {
            "run_id": self.run_id,
            "repo_root": str(self.repo_root),
            "started_at": datetime.now(UTC).isoformat(),
            "current_state": self.current_state.value,
            "phases_completed": [],
            "ai_adapter_type": ai_adapter_type,
            "minipipe_adapter_type": minipipe_adapter_type,
            "config": self.config,
            "guardrails_enabled": self.guardrails_enabled,
            "run_stats": self.run_stats,
        }

        # Initialize ledger
        self.ledger_path = self.run_dir / "run.ledger.jsonl"
        self._log_state_transition(
            RunState.INIT,
            {"message": "Run initialized", "guardrails": self.guardrails_enabled},
        )

    def _log_state_transition(
        self, new_state: RunState, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log state transition to JSONL ledger"""
        old_state = self.current_state
        self.current_state = new_state

        # Update state in memory
        self.state["current_state"] = new_state.value
        self.state["last_transition"] = datetime.now(UTC).isoformat()

        # Create ledger entry
        entry = {
            "ts": datetime.now(UTC).isoformat(),
            "run_id": self.run_id,
            "state": new_state.value,
            "event": "enter_state",
            "previous_state": old_state.value if old_state else None,
            "meta": metadata or {},
        }

        # Append to JSONL ledger
        with open(self.ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

        # Also log to console for visibility
        transition = (
            f"{old_state.value} → {new_state.value}" if old_state else new_state.value
        )
        print(f"[STATE] {transition}")

    def _get_current_branch(self) -> str:
        """Get current git branch name."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return "main"  # Default fallback

    def _log_event(
        self, event_type: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log event (non-state-transition) to JSONL ledger"""
        entry = {
            "ts": datetime.now(UTC).isoformat(),
            "run_id": self.run_id,
            "state": self.current_state.value,
            "event": event_type,
            "meta": metadata or {},
        }

        with open(self.ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def _check_anti_patterns(self, context: Optional[Dict[str, Any]] = None) -> None:
        """
        GUARDRAILS: Check for anti-patterns and trigger automatic responses

        Args:
            context: Additional context for anti-pattern detection
        """
        if not self.guardrails_enabled or not self.anti_pattern_detector:
            return

        # Build detection context
        run_context = {
            "task_status": context.get("task_status") if context else None,
            "verification": context.get("verification", {}) if context else {},
            "run_stats": self.run_stats,
        }

        # Run anti-pattern detection
        detections = self.anti_pattern_detector.detect_all(run_context)

        # Handle detections
        for detection in detections:
            anti_pattern_id = detection["anti_pattern_id"]
            rule = detection.get("rule", "unknown")
            evidence = detection.get("evidence", "No evidence provided")

            print(f"\n⚠️  ANTI-PATTERN DETECTED: {anti_pattern_id}")
            print(f"   Rule: {rule}")
            print(f"   Evidence: {evidence}\n")

            # Log to ledger
            self._log_event(
                "anti_pattern_detected",
                {
                    "anti_pattern_id": anti_pattern_id,
                    "rule": rule,
                    "evidence": evidence,
                },
            )

            # Add to run stats
            self.run_stats["anti_patterns_detected"].append(
                {
                    "id": anti_pattern_id,
                    "rule": rule,
                    "evidence": evidence,
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )

            # Trigger automatic response
            self._handle_anti_pattern(anti_pattern_id, detection)

    def _handle_anti_pattern(
        self, anti_pattern_id: str, detection: Dict[str, Any]
    ) -> None:
        """
        GUARDRAILS: Handle detected anti-pattern with automatic response

        Args:
            anti_pattern_id: ID of detected anti-pattern
            detection: Full detection details
        """
        if anti_pattern_id == "AP_HALLUCINATED_SUCCESS":
            # Increment counter
            self.run_stats["hallucination_count"] += 1

            print(f"   → Hallucination count: {self.run_stats['hallucination_count']}")

            # If repeated, escalate
            if self.run_stats["hallucination_count"] >= 3:
                print("   → CRITICAL: Repeated hallucinations detected")
                print("   → Recommendation: Review AI adapter configuration\n")

                self._log_event(
                    "critical_anti_pattern",
                    {
                        "anti_pattern_id": anti_pattern_id,
                        "count": self.run_stats["hallucination_count"],
                        "action": "escalation_recommended",
                    },
                )

        elif anti_pattern_id == "AP_PLANNING_LOOP":
            print("   → Planning loop detected")
            print("   → Recommendation: Simplify scope or force plan commitment\n")

            self._log_event(
                "planning_loop_detected",
                {
                    "planning_attempts": self.run_stats["planning_attempts"],
                    "patches_applied": self.run_stats["patches_applied"],
                },
            )

    def _generate_ulid(self) -> str:
        """Generate ULID-like run identifier"""
        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        import secrets

        random_suffix = secrets.token_hex(6).upper()
        return f"{timestamp}_{random_suffix}"

    def run_full_cycle(self, mode: str = "full") -> Dict[str, Any]:
        """
        GOLDEN PATH: Single entrypoint for complete ACMS execution

        State machine: INIT → GAP_ANALYSIS → PLANNING → EXECUTION → SUMMARY → DONE
        """
        try:
            print(f"\n[ACMS] Starting run {self.run_id}")
            print(f"[ACMS] Repository: {self.repo_root}")
            print(f"[ACMS] Mode: {mode}\n")

            # MONITORING: Send pipeline started notification
            if self.notifier:
                self.notifier.pipeline_started(self.run_id, mode)

            # Phase 0: Already in INIT state
            self._phase_0_run_config()

            # Phase 1: Gap Discovery
            if mode in ["full", "analyze_only", "plan_only"]:
                self._log_state_transition(RunState.GAP_ANALYSIS, {"mode": mode})
                self._phase_1_gap_discovery()
                self._log_event(
                    "gap_discovery_complete", {"gap_count": len(self.gap_registry.gaps)}
                )

                # MONITORING: Update metrics
                if self.current_metrics:
                    self.current_metrics.gaps_discovered = len(self.gap_registry.gaps)

            if mode == "analyze_only":
                self._log_state_transition(RunState.DONE, {"completed_mode": mode})
                return self._finalize_run("success")

            # Phase 2 & 3: Planning
            if mode in ["full", "plan_only", "execute_only"]:
                self._log_state_transition(RunState.PLANNING, {"mode": mode})
                self._phase_2_gap_consolidation()
                self._phase_3_plan_generation()

                # GUARDRAILS: Increment planning attempts
                self.run_stats["planning_attempts"] += 1

                self._log_event(
                    "planning_complete",
                    {
                        "workstream_count": len(self.execution_planner.workstreams),
                        "task_count": self.state.get("task_count", 0),
                        "planning_attempt": self.run_stats["planning_attempts"],
                    },
                )

                # GUARDRAILS: Check for planning loop
                self._check_anti_patterns()

            if mode == "plan_only":
                self._log_state_transition(RunState.DONE, {"completed_mode": mode})
                return self._finalize_run("success")

            # Phase 4: Execution
            if mode in ["full", "execute_only"]:
                self._log_state_transition(RunState.EXECUTION, {"mode": mode})
                self._phase_4_execution()

                # GUARDRAILS: Track patches applied (would come from execution results)
                # self.run_stats["patches_applied"] = ...

                self._log_event(
                    "execution_complete",
                    {
                        "tasks_completed": self.state.get("tasks_completed", 0),
                        "tasks_failed": self.state.get("tasks_failed", 0),
                        "patches_applied": self.run_stats["patches_applied"],
                    },
                )

                # MONITORING: Update execution metrics
                if self.current_metrics:
                    self.current_metrics.tasks_executed = self.state.get(
                        "tasks_completed", 0
                    )
                    self.current_metrics.tasks_failed = self.state.get(
                        "tasks_failed", 0
                    )

                if self.notifier:
                    self.notifier.execution_completed(
                        self.run_id,
                        self.state.get("tasks_completed", 0),
                        self.state.get("tasks_failed", 0),
                    )

                # GUARDRAILS: Final anti-pattern check after execution
                self._check_anti_patterns()

            # Phase 5: Summary
            self._log_state_transition(RunState.SUMMARY, {"mode": mode})
            self._phase_5_summary()

            # Done
            self._log_state_transition(RunState.DONE, {"completed_mode": mode})
            print(f"\n[ACMS] Run completed successfully\n")

            return self._finalize_run("success")

        except Exception as e:
            self._log_state_transition(RunState.FAILED, {"error": str(e)})
            print(f"\n[ACMS] Run failed: {e}\n")

            # MONITORING: Send failure notification
            if self.notifier:
                phase = self.current_state.value if self.current_state else "unknown"
                self.notifier.pipeline_failed(self.run_id, str(e), phase)

            return self._finalize_run("failed", str(e))

    def _finalize_run(self, status: str, error: Optional[str] = None) -> Dict[str, Any]:
        """Generate final run status and save state"""
        self.state["completed_at"] = datetime.now(UTC).isoformat()
        self.state["final_status"] = status
        self.state["run_stats"] = self.run_stats  # Include guardrails stats

        if error:
            self.state["error"] = error

        # Save final state
        self._save_state()

        # MONITORING: Complete metrics and record
        if self.current_metrics and self.metrics_collector:
            self.current_metrics.complete(success=(status == "success"), error=error)
            self.current_metrics.gaps_fixed = self.state.get("tasks_completed", 0)
            self.metrics_collector.record_run(self.current_metrics)

            # Send completion notification
            if self.notifier and status == "success":
                self.notifier.pipeline_completed(
                    self.run_id,
                    self.current_metrics.gaps_discovered,
                    self.current_metrics.duration_seconds,
                )

        # Generate run_status.json
        run_status = self._generate_run_status()
        status_path = self.run_dir / "run_status.json"
        with open(status_path, "w", encoding="utf-8") as f:
            json.dump(run_status, f, indent=2)

        self._log_event(
            "run_finalized", {"status": status, "run_stats": self.run_stats}
        )

        return run_status

    def _generate_run_status(self) -> Dict[str, Any]:
        """Generate unified run status from all sources"""
        return {
            "run_id": self.run_id,
            "repo_root": str(self.repo_root),
            "started_at": self.state["started_at"],
            "completed_at": self.state.get("completed_at"),
            "final_status": self.state.get("final_status", "unknown"),
            "error": self.state.get("error"),
            "state_transitions": self._read_ledger_states(),
            "metrics": {
                "gaps_discovered": len(self.gap_registry.gaps),
                "gaps_resolved": sum(
                    1
                    for g in self.gap_registry.gaps.values()
                    if g.status.value in ["resolved", "verified"]
                ),
                "workstreams_created": len(self.execution_planner.workstreams),
                "tasks_executed": self.state.get("tasks_completed", 0),
                "tasks_failed": self.state.get("tasks_failed", 0),
            },
            "config": self.config,
            "artifacts": {
                "ledger": str(self.ledger_path.relative_to(self.repo_root)),
                "state": "acms_state.json",
                "gap_registry": "gap_registry.json",
                "workstreams": "workstreams.json"
                if (self.run_dir / "workstreams.json").exists()
                else None,
                "execution_plan": "mini_pipe_execution_plan.json"
                if (self.run_dir / "mini_pipe_execution_plan.json").exists()
                else None,
            },
        }

    def _read_ledger_states(self) -> list:
        """Read state transitions from ledger"""
        states = []
        if self.ledger_path.exists():
            with open(self.ledger_path, "r", encoding="utf-8") as f:
                for line in f:
                    entry = json.loads(line.strip())
                    if entry.get("event") == "enter_state":
                        states.append(
                            {
                                "state": entry["state"],
                                "timestamp": entry["ts"],
                                "previous": entry.get("previous_state"),
                            }
                        )
        return states
        """Execute full gap-phase pipeline"""
        print(f"[ACMS] Starting run {self.run_id}")
        print(f"[ACMS] Repository: {self.repo_root}")
        print(f"[ACMS] Mode: {mode}")

        try:
            if mode in {"full", "analyze_only", "plan_only"}:
                self._phase_0_run_config()
                self._phase_1_gap_discovery()

            if mode in {"full", "plan_only"}:
                self._phase_2_gap_consolidation()
                self._phase_3_plan_generation()

            if mode in {"full", "execute_only"}:
                self._phase_4_execution()
                self._phase_5_summary()

            self.state["status"] = "completed"
            self.state["completed_at"] = datetime.now(UTC).isoformat()

        except Exception as e:
            self.state["status"] = "failed"
            self.state["error"] = str(e)
            self._save_state()
            raise

        self._save_state()
        return self.state

    def _phase_0_run_config(self) -> None:
        """PHASE_0: Run Configuration and Initialization"""
        self.state["current_phase"] = "PHASE_0_RUN_CONFIG"
        print(f"\n[PHASE 0] Run Configuration")
        print(f"  Run ID: {self.run_id}")
        print(f"  Run directory: {self.run_dir}")

        self.state["phases_completed"].append("PHASE_0_RUN_CONFIG")

    def _phase_1_gap_discovery(self) -> None:
        """PHASE_1: Multi-lens Gap Discovery"""
        self.state["current_phase"] = "PHASE_1_GAP_DISCOVERY"
        print(f"\n[PHASE 1] Gap Discovery")

        prompt_path = (
            Path(__file__).parent.parent.parent
            / "docs"
            / "analysis_frameworks"
            / "OVERLAP_AUTOMATION_AND_MASTER_GAP_ANALYSIS.merged.json"
        )

        if not prompt_path.exists():
            print(f"  ⚠️  Gap analysis prompt not found: {prompt_path}")
            print(f"  Creating placeholder gap report")
            self._create_placeholder_gap_report()
        else:
            print(f"  Using gap analysis prompt: {prompt_path.name}")
            self._run_ai_gap_analysis(prompt_path)

        gap_report_path = self.run_dir / "gap_analysis_report.json"
        if gap_report_path.exists():
            count = self.gap_registry.load_from_report(gap_report_path)
            print(f"  ✓ Loaded {count} gaps from report")
            self.gap_registry.save()
        else:
            print(f"  ⚠️  No gap report generated")

        self.state["gap_count"] = len(self.gap_registry.gaps)
        self.state["phases_completed"].append("PHASE_1_GAP_DISCOVERY")

    def _phase_2_gap_consolidation(self) -> None:
        """PHASE_2: Gap Consolidation and Clustering - UET Workstream Generation"""
        self.state["current_phase"] = "PHASE_2_GAP_CONSOLIDATION_AND_CLUSTERING"
        print(f"\n[PHASE 2] Gap Consolidation and Clustering (UET)")

        # Use UET execution planner to create workstreams
        workstreams = self.execution_planner.cluster_gaps_to_workstreams(
            max_files_per_workstream=10,
            category_based=True,
            workspace_ref=self.workspace_ref,
        )

        print(f"  ✓ Created {len(workstreams)} UET workstreams")

        # Validate workstreams
        errors = self.execution_planner.validate_workstreams()
        if errors:
            print(f"  ⚠️  Validation warnings: {len(errors)} issues")
            for error in errors[:5]:  # Show first 5
                print(f"     - {error}")

        # Save to UET format (individual JSON files)
        workstreams_dir = ensure_dir(
            "workstreams.runtime.plans_dir", run_id=self.run_id
        )
        saved_paths = self.execution_planner.save_workstreams(workstreams_dir)
        print(
            f"  ✓ Saved {len(saved_paths)} workstream files to {workstreams_dir.name}"
        )

        self.state["workstream_count"] = len(workstreams)
        self.state["workstreams_dir"] = str(workstreams_dir)
        self.state["phases_completed"].append(
            "PHASE_2_GAP_CONSOLIDATION_AND_CLUSTERING"
        )

    def _phase_3_plan_generation(self) -> None:
        """PHASE_3: Phase Plan and Workstream Plan Generation - UET Compatible"""
        self.state["current_phase"] = "PHASE_3_PLAN_GENERATION"
        print(f"\n[PHASE 3] Plan Generation (UET)")

        # UET workstreams are already generated in Phase 2
        # This phase is now lighter - just prepare execution summary
        workstreams_dir = Path(
            self.state.get("workstreams_dir", self.run_dir / "workstreams")
        )

        if not workstreams_dir.exists():
            print(f"  ⚠️  Workstreams directory not found, re-running clustering")
            self._phase_2_gap_consolidation()
            workstreams_dir = Path(self.state["workstreams_dir"])

        # Count tasks across all workstreams and collect for execution plan
        all_tasks = []
        task_count = 0
        for ws_file in workstreams_dir.glob("ws-*.json"):
            try:
                with open(ws_file, "r", encoding="utf-8") as f:
                    ws_data = json.load(f)
                    tasks = ws_data.get("tasks", [])
                    task_count += len(tasks)
                    all_tasks.extend(tasks)
            except Exception:
                pass

        # Generate consolidated execution plan for backward compatibility
        execution_plan = {
            "version": "1.0",
            "run_id": self.run_id,
            "generated_at": datetime.now(UTC).isoformat(),
            "tasks": all_tasks,
            "workstreams_dir": str(workstreams_dir),
        }

        plan_path = self.run_dir / "mini_pipe_execution_plan.json"
        with open(plan_path, "w", encoding="utf-8") as f:
            json.dump(execution_plan, f, indent=2)

        print(f"  ✓ UET workstreams ready with {task_count} tasks total")
        print(f"  ✓ Execution plan saved to {plan_path.name}")
        try:
            rel_path = workstreams_dir.relative_to(self.repo_root)
            print(f"  ✓ Workstreams stored in {rel_path}")
        except ValueError:
            print(f"  ✓ Workstreams stored in {workstreams_dir}")

        self.state["task_count"] = task_count
        self.state["phases_completed"].append("PHASE_3_PLAN_GENERATION")

    def _phase_4_execution(self) -> None:
        """PHASE_4: Phase Execution via MINI_PIPE - UET Workstream Execution"""
        self.state["current_phase"] = "PHASE_4_PHASE_EXECUTION_MINI_PIPE"
        print(f"\n[PHASE 4] Execution via MINI_PIPE (UET)")

        workstreams_dir = Path(
            self.state.get("workstreams_dir", self.run_dir / "workstreams")
        )

        if not workstreams_dir.exists():
            print(f"  ⚠️  Workstreams directory not found: {workstreams_dir}")
            print(f"  Skipping execution phase")
            return

        # Load workstreams using UET adapter
        from src.acms.uet_workstream_adapter import UETWorkstreamAdapter

        adapter = UETWorkstreamAdapter(workspace_ref=self.workspace_ref)
        workstreams = adapter.load_workstreams_from_directory(workstreams_dir)

        if not workstreams:
            print(f"  ⚠️  No workstreams found in {workstreams_dir}")
            return

        print(f"  ✓ Loaded {len(workstreams)} UET workstreams")

        # Convert to execution requests
        all_requests = []
        for ws in workstreams:
            requests = adapter.workstream_to_execution_requests(ws)
            all_requests.extend(requests)
            print(f"    - {ws.ws_id}: {len(requests)} tasks")

        print(f"  ✓ Generated {len(all_requests)} execution requests")
        print(f"  ℹ️  Execution via orchestrator integration pending")
        print(f"     (Requests ready for MINI_PIPE orchestrator)")

        # Store execution summary
        self.state["execution_requests_count"] = len(all_requests)
        self.state["tasks_completed"] = 0  # Placeholder
        self.state["tasks_failed"] = 0
        self.state["phases_completed"].append("PHASE_4_PHASE_EXECUTION_MINI_PIPE")

    def _phase_5_summary(self) -> None:
        """PHASE_5: Summary, Snapshot, and Reporting"""
        self.state["current_phase"] = "PHASE_5_SUMMARY_AND_SNAPSHOT"
        print(f"\n[PHASE 5] Summary and Snapshot")

        summary = self._generate_summary()

        summary_path = self.run_dir / "summary_report.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        print(f"  ✓ Summary saved to {summary_path.name}")

        self._print_summary(summary)

        self.state["summary_path"] = str(summary_path)
        self.state["phases_completed"].append("PHASE_5_SUMMARY_AND_SNAPSHOT")

    def _create_placeholder_gap_report(self) -> None:
        """Create placeholder gap report for testing"""
        report = {
            "version": "1.0",
            "generated_at": datetime.now(UTC).isoformat(),
            "gaps": [
                {
                    "gap_id": "GAP_0001",
                    "title": "Example gap placeholder",
                    "description": "Placeholder gap for testing pipeline",
                    "category": "testing",
                    "severity": "low",
                    "file_paths": [],
                    "dependencies": [],
                }
            ],
        }

        report_path = self.run_dir / "gap_analysis_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

    def _run_ai_gap_analysis(self, prompt_path: Path) -> None:
        """Run AI-powered gap analysis"""
        print(f"  Executing AI gap analysis using: {prompt_path.name}")
        print(f"  Adapter: {self.state['ai_adapter_type']}")

        # Prepare AI request
        request = AIRequest(
            prompt_template_path=prompt_path,
            context={
                "run_id": self.run_id,
                "repo_root": str(self.repo_root),
            },
            repo_root=self.repo_root,
            timeout_seconds=300,
        )

        # Execute gap analysis
        response = self.ai_adapter.analyze_gaps(request)

        if response.success:
            print(
                f"  ✓ Gap analysis completed in {response.execution_time_seconds:.1f}s"
            )

            # Save gap report
            report_path = self.run_dir / "gap_analysis_report.json"
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(response.output, f, indent=2)

            print(f"  ✓ Saved gap report")
        else:
            print(f"  ⚠️  Gap analysis failed: {response.error}")
            print(f"  Creating placeholder gap report")
            self._create_placeholder_gap_report()

    def _run_mini_pipe(self, plan_path: Path, orchestrator_cli: Path) -> None:
        """Execute MINI_PIPE orchestrator"""
        print(f"  Invoking MINI_PIPE orchestrator...")
        print(f"  Adapter: {self.state['minipipe_adapter_type']}")

        # Prepare execution request
        request = ExecutionRequest(
            execution_plan_path=plan_path,
            repo_root=self.repo_root,
            run_id=self.run_id,
            timeout_seconds=3600,
        )

        # Execute plan
        result = self.minipipe_adapter.execute_plan(request)

        # ... (rest of the if result.success block) ...

        # Always update task counts, even if execution failed (partial results)
        self.state["tasks_completed"] = result.tasks_completed
        self.state["tasks_failed"] = result.tasks_failed

        if not result.success:
            print(f"  ⚠️  Execution failed: {result.error}")
            self.state["execution_error"] = result.error
            raise RuntimeError(f"MINI_PIPE execution failed: {result.error}")

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate execution summary"""
        stats = self.gap_registry.get_stats()

        return {
            "run_id": self.run_id,
            "repo_root": str(self.repo_root),
            "started_at": self.state.get("started_at"),
            "completed_at": datetime.now(UTC).isoformat(),
            "phases_completed": self.state["phases_completed"],
            "gap_stats": stats,
            "workstream_count": self.state.get("workstream_count", 0),
            "task_count": self.state.get("task_count", 0),
        }

    def _print_summary(self, summary: Dict[str, Any]) -> None:
        """Print summary to console"""
        print(f"\n{'='*60}")
        print(f"  RUN SUMMARY")
        print(f"{'='*60}")
        print(f"  Run ID: {summary['run_id']}")
        print(f"  Phases: {len(summary['phases_completed'])} completed")
        print(f"  Gaps: {summary['gap_stats']['total']} discovered")
        print(f"  Workstreams: {summary['workstream_count']}")
        print(f"  Tasks: {summary['task_count']}")
        print(f"{'='*60}\n")

    def _save_state(self) -> None:
        """Save controller state"""
        state_path = self.run_dir / "acms_state.json"
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2)


def main():
    """CLI entrypoint"""
    parser = argparse.ArgumentParser(
        description="Gap Phase Execution Pipeline - ACMS Controller"
    )

    parser.add_argument(
        "repo_root",
        type=Path,
        help="Path to repository root",
    )

    parser.add_argument(
        "--run_id",
        type=str,
        help="Optional run identifier (ULID generated if omitted)",
    )

    parser.add_argument(
        "--mode",
        choices=["full", "analyze_only", "plan_only", "execute_only"],
        default="full",
        help="Execution mode",
    )

    parser.add_argument(
        "--ai-adapter",
        choices=["mock", "copilot", "openai", "anthropic"],
        default="mock",
        help="AI adapter to use for gap analysis",
    )

    parser.add_argument(
        "--minipipe-adapter",
        choices=["auto", "mock"],
        default="auto",
        help="MINI_PIPE adapter to use for execution",
    )

    args = parser.parse_args()

    if not args.repo_root.exists():
        print(f"Error: Repository root does not exist: {args.repo_root}")
        sys.exit(1)

    controller = ACMSController(
        args.repo_root, args.run_id, args.ai_adapter, args.minipipe_adapter
    )

    try:
        result = controller.run_full_cycle(args.mode)
        print(f"\n[ACMS] Run completed successfully")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ACMS] Run failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
