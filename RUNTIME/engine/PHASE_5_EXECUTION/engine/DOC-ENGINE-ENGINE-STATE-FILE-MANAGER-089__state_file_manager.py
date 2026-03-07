# DOC_LINK: DOC-ENGINE-ENGINE-STATE-FILE-MANAGER-089
"""State file export utilities for cross-phase automation."""
DOC_ID: DOC-ENGINE-ENGINE-STATE-FILE-MANAGER-089

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional

if TYPE_CHECKING:
    from core.engine.router import RoutingDecision
    from core.engine.scheduler import Task


class StateFileManager:
    """Writes phase handoff state files in a consistent, atomic manner."""

    def __init__(self, output_dir: str | Path = ".state"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_routing_decisions(
        self, run_id: str, decisions: Iterable["RoutingDecision"]
    ) -> Path:
        """Write routing decisions for downstream consumers."""
        payload = {
            "run_id": run_id,
            "decisions": [
                self._with_run_id(getattr(decision, "to_dict", lambda: {})(), run_id)
                for decision in decisions
            ],
        }
        return self._write_json("routing_decisions.json", payload)

    def export_adapter_assignments(self, run_id: str, tasks: Iterable["Task"]) -> Path:
        """Persist tool assignments for executed tasks."""
        assignments: List[Dict[str, Any]] = []
        for task in tasks:
            tool_id = getattr(task, "selected_tool", None)
            if not tool_id:
                continue

            assignments.append(
                {
                    "run_id": run_id,
                    "task_id": task.task_id,
                    "task_kind": task.task_kind,
                    "tool_id": tool_id,
                }
            )

        payload = {"run_id": run_id, "assignments": assignments}
        return self._write_json("adapter_assignments.json", payload)

    def export_execution_results(self, run_id: str, tasks: Iterable["Task"]) -> Path:
        """Capture execution outcomes for error recovery and audits."""
        results: List[Dict[str, Any]] = []
        for task in tasks:
            results.append(
                {
                    "run_id": run_id,
                    "task_id": task.task_id,
                    "task_kind": task.task_kind,
                    "status": task.status,
                    "tool_id": getattr(task, "selected_tool", None),
                    "exit_code": getattr(task, "exit_code", None),
                    "output_patch_id": getattr(task, "output_patch_id", None),
                    "error": getattr(task, "error_log", None) or task.error,
                    "metadata": getattr(task, "result_metadata", {}) or task.metadata,
                }
            )

        payload = {"run_id": run_id, "results": results}
        return self._write_json("execution_results.json", payload)

    def _write_json(self, filename: str, payload: Dict[str, Any]) -> Path:
        """Write JSON atomically to the output directory."""
        path = self.output_dir / filename
        tmp_path = path.with_suffix(path.suffix + ".tmp")

        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        tmp_path.replace(path)
        return path

    @staticmethod
    def _with_run_id(record: Dict[str, Any], run_id: str) -> Dict[str, Any]:
        """Ensure run_id is present on exported decision records."""
        if "run_id" not in record:
            record["run_id"] = run_id
        return record
