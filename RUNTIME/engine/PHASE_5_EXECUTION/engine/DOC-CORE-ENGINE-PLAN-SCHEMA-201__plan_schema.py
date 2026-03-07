# DOC_LINK: DOC-CORE-ENGINE-PLAN-SCHEMA-201
"""Plan Schema - JSON Plan Definitions for Orchestrator

Defines the structure for JSON plan files that drive the orchestrator.
"""

# DOC_ID: DOC-CORE-ENGINE-PLAN-SCHEMA-201

import json
from dataclasses import dataclass, field
from pathlib import Path
from string import Template
from typing import Any, Dict, List, Optional


@dataclass
class StepDef:
    """Definition of a single step in a plan."""

    id: str
    name: str
    command: str
    args: List[str]
    cwd: str = "."
    shell: bool = False
    env: Dict[str, str] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    timeout_sec: Optional[int] = None
    retries: int = 0
    retry_delay_sec: int = 0
    critical: bool = True
    condition: Optional[str] = None
    on_failure: str = "abort"
    provides: List[str] = field(default_factory=list)
    consumes: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    ui_hints: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

    def __post_init__(self):
        """Validate field constraints."""
        if self.on_failure not in ["abort", "skip_dependents", "continue"]:
            raise ValueError(
                f"Invalid on_failure policy '{self.on_failure}'. "
                f"Must be one of: abort, skip_dependents, continue"
            )

        if self.retries < 0:
            raise ValueError(f"retries must be >= 0, got {self.retries}")

        if self.retry_delay_sec < 0:
            raise ValueError(
                f"retry_delay_sec must be >= 0, got {self.retry_delay_sec}"
            )


@dataclass
class Plan:
    """Complete plan definition."""

    plan_id: str
    version: str
    globals: Dict[str, Any]
    steps: List[StepDef]
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_file(cls, path: str, variables: Optional[Dict[str, str]] = None) -> "Plan":
        """
        Load plan from JSON file with optional variable substitution.

        Args:
            path: Path to JSON plan file
            variables: Dictionary of variables for ${VAR} substitution

        Returns:
            Plan instance

        Raises:
            FileNotFoundError: If plan file doesn't exist
            ValueError: If plan is invalid
        """
        path_obj = Path(path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Plan file not found: {path}")

        with open(path_obj, "r", encoding="utf-8") as f:
            raw_json = f.read()

        # Substitute variables if provided
        if variables:
            template = Template(raw_json)
            # Use safe_substitute to avoid errors on ${VAR} not in dict
            raw_json = template.safe_substitute(variables)

        data = json.loads(raw_json)

        # Validate required top-level fields
        required = ["plan_id", "version", "globals", "steps"]
        for field_name in required:
            if field_name not in data:
                raise ValueError(f"Missing required field: {field_name}")

        # Parse steps
        steps = []
        for step_data in data["steps"]:
            # Extract only known fields for StepDef
            step_fields = {
                k: v for k, v in step_data.items() if k in StepDef.__dataclass_fields__
            }
            steps.append(StepDef(**step_fields))

        plan = cls(
            plan_id=data["plan_id"],
            version=data["version"],
            description=data.get("description", ""),
            globals=data["globals"],
            steps=steps,
            metadata=data.get("metadata", {}),
        )

        # Validate plan structure
        plan._validate()

        return plan

    def _validate(self):
        """Validate plan structure and dependencies."""
        # Check for duplicate step IDs
        step_ids = [s.id for s in self.steps]
        if len(step_ids) != len(set(step_ids)):
            duplicates = [sid for sid in step_ids if step_ids.count(sid) > 1]
            raise ValueError(f"Duplicate step IDs found: {set(duplicates)}")

        # Check all depends_on references exist
        for step in self.steps:
            for dep_id in step.depends_on:
                if dep_id not in step_ids:
                    raise ValueError(
                        f"Step '{step.id}' depends on unknown step '{dep_id}'"
                    )

        # Check for circular dependencies
        self._check_cycles()

    def _check_cycles(self):
        """Detect circular dependencies in step graph."""
        # Build adjacency list
        graph = {step.id: step.depends_on for step in self.steps}

        # Track visited nodes and recursion stack
        visited = set()
        rec_stack = set()

        def visit(node_id: str, path: List[str]) -> bool:
            """DFS to detect cycles."""
            if node_id in rec_stack:
                cycle = " -> ".join(path + [node_id])
                raise ValueError(f"Circular dependency detected: {cycle}")

            if node_id in visited:
                return False

            visited.add(node_id)
            rec_stack.add(node_id)

            for dep in graph.get(node_id, []):
                visit(dep, path + [node_id])

            rec_stack.remove(node_id)
            return False

        for step_id in graph.keys():
            if step_id not in visited:
                visit(step_id, [])

    def get_step(self, step_id: str) -> Optional[StepDef]:
        """Get step definition by ID."""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None
