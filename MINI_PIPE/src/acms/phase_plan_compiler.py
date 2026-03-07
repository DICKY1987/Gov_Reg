"""Phase Plan Compiler Module

Compiles phase plans into MINI_PIPE execution plans.
Supports PHASE_3_PLAN_GENERATION.

GUARDRAILS: Validates pattern_ids in tasks before execution.
"""

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from src.acms.execution_planner import Workstream

# GUARDRAILS: Import guardrails enforcement
try:
    from src.acms.guardrails import PatternGuardrails

    GUARDRAILS_AVAILABLE = True
except ImportError:
    GUARDRAILS_AVAILABLE = False
    PatternGuardrails = None


@dataclass
class MiniPipeTask:
    """MINI_PIPE task definition"""

    task_id: str
    task_kind: str
    description: str
    depends_on: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_kind": self.task_kind,
            "description": self.description,
            "depends_on": self.depends_on,
            "metadata": self.metadata,
        }


@dataclass
class MiniPipeExecutionPlan:
    """MINI_PIPE execution plan"""

    plan_id: str
    name: str
    description: str
    version: str = "1.0"
    tasks: List[MiniPipeTask] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "tasks": [t.to_dict() for t in self.tasks],
            "metadata": self.metadata,
        }


class PhasePlanCompiler:
    """Compiles phase plans to MINI_PIPE execution plans with guardrails validation"""

    def __init__(
        self, enable_guardrails: bool = True, pattern_index_path: Optional[Path] = None
    ):
        self.task_counter = 0

        # GUARDRAILS: Initialize pattern validation
        self.guardrails_enabled = enable_guardrails and GUARDRAILS_AVAILABLE
        self.guardrails = None
        self.validation_errors: List[str] = []

        if self.guardrails_enabled:
            try:
                pattern_index = (
                    pattern_index_path or Path(__file__).parent / "PATTERN_INDEX.yaml"
                )
                if pattern_index.exists():
                    self.guardrails = PatternGuardrails(pattern_index)
                    print(f"✓ Plan compiler initialized with guardrails")
                else:
                    self.guardrails_enabled = False
                    print(f"⚠ PATTERN_INDEX.yaml not found, plan validation disabled")
            except Exception as e:
                self.guardrails_enabled = False
                print(f"⚠ Failed to initialize guardrails: {e}")

    def compile_from_workstreams(
        self,
        workstreams: List[Workstream],
        repo_root: Path,
        validate: bool = True,
    ) -> MiniPipeExecutionPlan:
        """Compile workstreams into MINI_PIPE execution plan

        Args:
            workstreams: List of workstreams to compile
            repo_root: Repository root path
            validate: Whether to run guardrails validation (default: True)

        Returns:
            Compiled execution plan

        Raises:
            ValueError: If plan validation fails
        """
        plan_id = f"PLAN_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"

        plan = MiniPipeExecutionPlan(
            plan_id=plan_id,
            name="Gap-Driven Execution Plan",
            description=f"Execution plan for {len(workstreams)} workstreams",
            metadata={
                "repo_root": str(repo_root),
                "workstream_count": len(workstreams),
                "generated_at": datetime.now(UTC).isoformat(),
                "guardrails_enabled": self.guardrails_enabled,
            },
        )

        ws_id_to_task_ids: Dict[str, List[str]] = {}

        for ws in workstreams:
            task_ids = self._compile_workstream(ws, plan, repo_root)
            ws_id_to_task_ids[ws.workstream_id] = task_ids

        self._resolve_dependencies(plan, workstreams, ws_id_to_task_ids)

        # GUARDRAILS: Validate plan before returning
        if validate and self.guardrails_enabled:
            is_valid, errors = self.validate_plan(plan)
            if not is_valid:
                error_msg = f"Plan validation failed:\n  " + "\n  ".join(errors)
                raise ValueError(error_msg)

        return plan

    def compile_from_phase_plan_files(
        self,
        phase_plan_paths: List[Path],
        repo_root: Path,
        validate: bool = True,
    ) -> MiniPipeExecutionPlan:
        """Compile phase plan JSON files into MINI_PIPE execution plan

        Args:
            phase_plan_paths: List of phase plan file paths
            repo_root: Repository root path
            validate: Whether to run guardrails validation (default: True)

        Returns:
            Compiled execution plan

        Raises:
            ValueError: If plan validation fails
        """
        plan_id = f"PLAN_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"

        plan = MiniPipeExecutionPlan(
            plan_id=plan_id,
            name="Phase Plan Execution",
            description=f"Execution plan from {len(phase_plan_paths)} phase plans",
            metadata={
                "repo_root": str(repo_root),
                "phase_plan_count": len(phase_plan_paths),
                "generated_at": datetime.now(UTC).isoformat(),
                "guardrails_enabled": self.guardrails_enabled,
            },
        )

        for phase_plan_path in phase_plan_paths:
            self._compile_phase_plan_file(phase_plan_path, plan, repo_root)

        # GUARDRAILS: Validate plan before returning
        if validate and self.guardrails_enabled:
            is_valid, errors = self.validate_plan(plan)
            if not is_valid:
                error_msg = f"Plan validation failed:\n  " + "\n  ".join(errors)
                raise ValueError(error_msg)

        return plan

    def _compile_workstream(
        self,
        ws: Workstream,
        plan: MiniPipeExecutionPlan,
        repo_root: Path,
    ) -> List[str]:
        """Compile a single workstream into tasks"""
        task_ids = []

        analysis_task = self._create_task(
            task_kind="analysis",
            description=f"Analyze files for {ws.name}",
            metadata={
                "workstream_id": ws.workstream_id,
                "gap_ids": ws.gap_ids,
                "file_scope": list(ws.file_scope),
                "repo_root": str(repo_root),
            },
        )
        plan.tasks.append(analysis_task)
        task_ids.append(analysis_task.task_id)

        implementation_task = self._create_task(
            task_kind="implementation",
            description=f"Implement fixes for {ws.name}",
            depends_on=[analysis_task.task_id],
            metadata={
                "workstream_id": ws.workstream_id,
                "gap_ids": ws.gap_ids,
                "file_scope": list(ws.file_scope),
                "repo_root": str(repo_root),
                "categories": list(ws.categories),
            },
        )
        plan.tasks.append(implementation_task)
        task_ids.append(implementation_task.task_id)

        if self._should_add_test_task(ws):
            test_task = self._create_task(
                task_kind="test",
                description=f"Test changes for {ws.name}",
                depends_on=[implementation_task.task_id],
                metadata={
                    "workstream_id": ws.workstream_id,
                    "file_scope": list(ws.file_scope),
                    "repo_root": str(repo_root),
                },
            )
            plan.tasks.append(test_task)
            task_ids.append(test_task.task_id)

        return task_ids

    def _compile_phase_plan_file(
        self,
        phase_plan_path: Path,
        plan: MiniPipeExecutionPlan,
        repo_root: Path,
    ) -> None:
        """Compile a phase plan JSON file into tasks"""
        with open(phase_plan_path, "r", encoding="utf-8") as f:
            phase_plan = json.load(f)

        steps = phase_plan.get("steps", [])
        step_id_to_task_id: Dict[str, str] = {}

        for step in steps:
            step_id = step.get("step_id", f"STEP_{self.task_counter}")
            task_kind = self._infer_task_kind(step)

            step_deps = step.get("depends_on", [])
            task_deps = [
                step_id_to_task_id[dep]
                for dep in step_deps
                if dep in step_id_to_task_id
            ]

            task = self._create_task(
                task_kind=task_kind,
                description=step.get("description", step.get("title", "Unnamed step")),
                depends_on=task_deps,
                metadata={
                    "phase_plan_path": str(phase_plan_path),
                    "step_id": step_id,
                    "repo_root": str(repo_root),
                    "original_step": step,
                },
            )

            plan.tasks.append(task)
            step_id_to_task_id[step_id] = task.task_id

    def _resolve_dependencies(
        self,
        plan: MiniPipeExecutionPlan,
        workstreams: List[Workstream],
        ws_to_tasks: Dict[str, List[str]],
    ) -> None:
        """Resolve workstream dependencies to task dependencies"""
        for ws in workstreams:
            if not ws.dependencies:
                continue

            ws_tasks = ws_to_tasks.get(ws.workstream_id, [])
            if not ws_tasks:
                continue

            first_task_id = ws_tasks[0]
            first_task = next(
                (t for t in plan.tasks if t.task_id == first_task_id), None
            )

            if not first_task:
                continue

            for dep_ws_id in ws.dependencies:
                dep_tasks = ws_to_tasks.get(dep_ws_id, [])
                if dep_tasks:
                    last_dep_task = dep_tasks[-1]
                    if last_dep_task not in first_task.depends_on:
                        first_task.depends_on.append(last_dep_task)

    def _create_task(
        self,
        task_kind: str,
        description: str,
        depends_on: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MiniPipeTask:
        """Create a MINI_PIPE task"""
        self.task_counter += 1
        task_id = f"TASK_{self.task_counter:04d}"

        return MiniPipeTask(
            task_id=task_id,
            task_kind=task_kind,
            description=description,
            depends_on=depends_on or [],
            metadata=metadata or {},
        )

    def _should_add_test_task(self, ws: Workstream) -> bool:
        """Determine if workstream should have a test task"""
        test_categories = {"testing", "quality", "validation"}
        return bool(ws.categories & test_categories) or ws.estimated_effort in {
            "medium",
            "high",
        }

    def _infer_task_kind(self, step: Dict[str, Any]) -> str:
        """Infer task kind from phase plan step"""
        step_type = step.get("type", "").lower()
        title = step.get("title", "").lower()

        if "test" in step_type or "test" in title:
            return "test"
        elif "analyze" in step_type or "analyze" in title or "review" in title:
            return "analysis"
        elif "implement" in step_type or "fix" in title or "create" in title:
            return "implementation"
        elif "refactor" in step_type or "refactor" in title:
            return "refactor"
        else:
            return "implementation"

    def _validate_pattern_id(self, pattern_id: str, task_id: str) -> bool:
        """
        GUARDRAILS: Validate that pattern_id exists in PATTERN_INDEX

        Args:
            pattern_id: Pattern ID to validate
            task_id: Task ID for error reporting

        Returns:
            True if valid, False otherwise
        """
        if not self.guardrails_enabled or not self.guardrails:
            return True

        is_valid, error_msg = self.guardrails.validate_pattern_exists(pattern_id)

        if not is_valid:
            error = f"Task {task_id}: {error_msg}"
            self.validation_errors.append(error)
            print(f"  ✗ {error}")
            return False

        return True

    def _validate_task_dependencies(self, plan: MiniPipeExecutionPlan) -> bool:
        """
        GUARDRAILS: Validate task dependencies (no circular deps, all deps exist)

        Args:
            plan: Execution plan to validate

        Returns:
            True if valid, False otherwise
        """
        task_ids = {task.task_id for task in plan.tasks}
        valid = True

        # Check all dependencies exist
        for task in plan.tasks:
            for dep_id in task.depends_on:
                if dep_id not in task_ids:
                    error = f"Task {task.task_id} depends on non-existent task {dep_id}"
                    self.validation_errors.append(error)
                    print(f"  ✗ {error}")
                    valid = False

        # Check for circular dependencies
        if valid:
            visited = set()
            path = []

            def has_cycle(task_id: str) -> bool:
                if task_id in path:
                    cycle = " -> ".join(path + [task_id])
                    error = f"Circular dependency detected: {cycle}"
                    self.validation_errors.append(error)
                    print(f"  ✗ {error}")
                    return True

                if task_id in visited:
                    return False

                visited.add(task_id)
                path.append(task_id)

                task = next((t for t in plan.tasks if t.task_id == task_id), None)
                if task:
                    for dep_id in task.depends_on:
                        if has_cycle(dep_id):
                            return True

                path.pop()
                return False

            for task in plan.tasks:
                if has_cycle(task.task_id):
                    valid = False
                    break

        return valid

    def validate_plan(self, plan: MiniPipeExecutionPlan) -> tuple[bool, List[str]]:
        """
        GUARDRAILS: Validate entire execution plan

        Args:
            plan: Execution plan to validate

        Returns:
            (is_valid, list of error messages)
        """
        self.validation_errors = []

        if not self.guardrails_enabled:
            return True, []

        print(f"\n[GUARDRAILS] Validating execution plan: {plan.plan_id}")
        print(f"  Tasks to validate: {len(plan.tasks)}")

        # Validate each task's pattern_id (if present)
        for task in plan.tasks:
            pattern_id = task.metadata.get("pattern_id")
            if pattern_id:
                self._validate_pattern_id(pattern_id, task.task_id)
            else:
                # Warn but don't fail for legacy tasks
                print(f"  ⚠ Task {task.task_id} has no pattern_id (legacy mode)")

        # Validate task dependencies
        self._validate_task_dependencies(plan)

        # Summary
        if not self.validation_errors:
            print(f"  ✓ Plan validation passed")
            return True, []
        else:
            print(
                f"  ✗ Plan validation failed with {len(self.validation_errors)} errors"
            )
            return False, self.validation_errors

    def save_plan(self, plan: MiniPipeExecutionPlan, output_path: Path) -> None:
        """Save execution plan to JSON"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(plan.to_dict(), f, indent=2)
