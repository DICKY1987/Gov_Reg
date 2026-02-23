#!/usr/bin/env python3
"""
Phase Plan to Execution Task Converter
Converts YAML phase plans into PHASE_5 execution tasks.

DOC_ID: DOC-CORE-PHASE-1-CONVERTER-001
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys

# Add repo root to path for imports
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class PhasePlanConverter:
    """
    Converts phase plans to execution-ready task lists.

    Transforms workstream YAML structures into flat task lists
    suitable for PHASE_5 execution engine.
    """

    def __init__(self, registry=None, fs_adapter=None):
        """
        Initialize converter.

        Args:
            registry: PathRegistry instance (optional for standalone use)
            fs_adapter: FilesystemAdapter instance (optional)
        """
        self.registry = registry
        self.fs_adapter = fs_adapter
        self.conversion_log = []
        self.run_id = f"run-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    def load_phase_plan(self, plan_path: Path) -> Dict:
        """
        Load and validate phase plan YAML.

        Args:
            plan_path: Path to phase plan YAML file

        Returns:
            Parsed phase plan dictionary

        Raises:
            ValueError: If plan is invalid
        """
        if not plan_path.exists():
            raise FileNotFoundError(f"Phase plan not found: {plan_path}")

        with open(plan_path, "r", encoding="utf-8") as f:
            plan = yaml.safe_load(f)

        # Validate required fields
        required = ["phase_identity"]
        if not all(k in plan for k in required):
            raise ValueError(f"Invalid phase plan: missing {required}")

        self.conversion_log.append(
            {
                "timestamp": datetime.now().isoformat(),
                "action": "loaded",
                "plan_id": plan.get("phase_identity", {}).get("phase_id", "unknown"),
                "path": str(plan_path),
            }
        )

        return plan

    def extract_tasks(self, phase_plan: Dict) -> List[Dict]:
        """
        Extract executable tasks from workstreams.

        Transformation:
        - workstreams[].phases[].steps[] → ExecutionRequestV1 contracts
        - Add task_id, run_id, dependencies
        - Map semantic keys from phase plan

        Args:
            phase_plan: Parsed phase plan dictionary

        Returns:
            List of task dictionaries ready for execution
        """
        tasks = []

        # Extract phase identity
        phase_id = phase_plan.get("phase_identity", {}).get("phase_id", "unknown")

        # Process all workstreams
        for ws_key in phase_plan.keys():
            if not ws_key.startswith("workstream_"):
                continue

            workstream = phase_plan[ws_key]
            ws_id = workstream.get("workstream_id", ws_key)

            # Process all phases within workstream
            phases = workstream.get("phases", [])
            for phase in phases:
                phase_id_local = phase.get("phase_id", "unknown")

                # Process all steps within phase
                steps = phase.get("steps", [])
                for step in steps:
                    task = self._convert_step_to_task(
                        step=step,
                        phase_id=phase_id,
                        workstream_id=ws_id,
                        phase_local_id=phase_id_local,
                    )
                    tasks.append(task)

        self.conversion_log.append(
            {
                "timestamp": datetime.now().isoformat(),
                "action": "extracted",
                "task_count": len(tasks),
                "phase_id": phase_id,
            }
        )

        return tasks

    def _convert_step_to_task(
        self, step: Dict, phase_id: str, workstream_id: str, phase_local_id: str
    ) -> Dict:
        """
        Convert a single step to an execution task.

        Args:
            step: Step dictionary from phase plan
            phase_id: Phase identifier
            workstream_id: Workstream identifier
            phase_local_id: Local phase identifier

        Returns:
            Task dictionary conforming to ExecutionRequestV1 contract
        """
        step_id = step.get("id", "unknown")

        # Determine operation kind based on step attributes
        operation_kind = self._determine_operation_kind(step)

        # Extract file scope
        file_scope = self._extract_file_scope(step)

        # Build task
        task = {
            "task_id": f"{workstream_id}::{phase_local_id}::{step_id}",
            "run_id": self.run_id,
            "operation_kind": operation_kind,
            "workspace": step.get("workspace", "."),
            "file_scope": file_scope,
            "tools": step.get("tools", []),
            "context": {
                "phase_plan_id": phase_id,
                "workstream_id": workstream_id,
                "phase_id": phase_local_id,
                "step_id": step_id,
                "name": step.get("name", ""),
                "description": step.get("description", ""),
                "priority": step.get("priority", "NORMAL"),
                "pattern": step.get("pattern", "EXEC-001"),
                "verification": step.get("verification", []),
                "deliverables": step.get("deliverables", []),
            },
            "dependencies": step.get("depends_on", []),
            "timeout_seconds": step.get("timeout", 600),  # Default 10 minutes
            "effort_hours": step.get("effort", 0),
        }

        return task

    def _determine_operation_kind(self, step: Dict) -> str:
        """
        Determine operation kind based on step attributes.

        Args:
            step: Step dictionary

        Returns:
            Operation kind string
        """
        # Check for explicit operation type
        if "operation" in step:
            return step["operation"]

        # Infer from step attributes
        if "files_created" in step or "files_modified" in step:
            return "file_edit"

        if step.get("pattern") == "EXEC-001":  # Single execution
            return "command_execute"

        if "test" in step.get("name", "").lower():
            return "test_run"

        if "git" in step.get("name", "").lower():
            return "git_operation"

        # Default
        return "generic"

    def _extract_file_scope(self, step: Dict) -> Dict[str, Any]:
        """
        Extract file scope from step.

        Args:
            step: Step dictionary

        Returns:
            File scope dictionary with read/write/created files
        """
        file_scope = {
            "read": step.get("files_read", []),
            "write": step.get("files_modified", []),
            "create": step.get("files_created", []),
            "delete": step.get("files_deleted", []),
        }

        return file_scope

    def write_execution_plan(
        self,
        tasks: List[Dict],
        output_key: Optional[str] = None,
        output_path: Optional[Path] = None,
    ) -> str:
        """
        Write execution plan JSON for PHASE_5.

        Args:
            tasks: List of task dictionaries
            output_key: Semantic key for output (if using PathRegistry)
            output_path: Direct output path (if not using PathRegistry)

        Returns:
            Path to written execution plan
        """
        plan = {
            "version": "1.0.0",
            "generated_at": datetime.utcnow().isoformat(),
            "run_id": self.run_id,
            "tasks": tasks,
            "metadata": {
                "task_count": len(tasks),
                "converter": "phase_plan_converter_v1",
                "conversion_log": self.conversion_log,
            },
        }

        # Determine output path
        if output_path:
            final_path = output_path
        elif output_key and self.fs_adapter:
            # Use FilesystemAdapter if available
            self.fs_adapter.write_json(output_key, plan)
            return output_key
        elif output_key and self.registry:
            # Use PathRegistry directly
            final_path = self.registry.resolve(output_key)
        else:
            # Default fallback
            final_path = REPO_ROOT / "data" / "execution" / "current_plan.json"

        # Ensure directory exists
        final_path.parent.mkdir(parents=True, exist_ok=True)

        # Write JSON
        import json

        with open(final_path, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=2, sort_keys=True)

        self.conversion_log.append(
            {
                "timestamp": datetime.now().isoformat(),
                "action": "written",
                "output_path": str(final_path),
                "task_count": len(tasks),
            }
        )

        return str(final_path)

    def get_conversion_summary(self) -> Dict:
        """
        Get summary of conversion operations.

        Returns:
            Summary dictionary with conversion statistics
        """
        return {
            "run_id": self.run_id,
            "operations": len(self.conversion_log),
            "log": self.conversion_log,
        }


def main():
    """
    CLI entry point for standalone testing.

    Usage:
        python phase_plan_converter.py path/to/plan.yml [output.json]
    """
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python phase_plan_converter.py <plan.yml> [output.json]")
        sys.exit(1)

    plan_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    # Create converter
    converter = PhasePlanConverter()

    try:
        # Load and convert
        print(f"Loading plan: {plan_path}")
        phase_plan = converter.load_phase_plan(plan_path)

        print(f"Extracting tasks...")
        tasks = converter.extract_tasks(phase_plan)

        print(f"Writing execution plan...")
        output = converter.write_execution_plan(tasks, output_path=output_path)

        # Print summary
        summary = converter.get_conversion_summary()
        print(f"\n✓ Conversion complete:")
        print(f"  - Tasks generated: {len(tasks)}")
        print(f"  - Output: {output}")
        print(f"  - Operations: {summary['operations']}")

        # Print first task as example
        if tasks:
            print(f"\nExample task:")
            print(json.dumps(tasks[0], indent=2))

        sys.exit(0)

    except Exception as e:
        print(f"✗ Conversion failed: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
