"""
UET Workstream Loader
Loads workstream JSON files and converts to Task objects
"""

# DOC_ID: DOC-SCRIPT-SCRIPTS-UET-WORKSTREAM-LOADER-240
# DOC_ID: DOC-SCRIPT-SCRIPTS-UET-WORKSTREAM-LOADER-177

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class WorkstreamLoader:
    """Load and validate workstream JSON files."""

    def __init__(self, workstream_dir: str = "workstreams", pattern: str = "ws-*.json"):
        self.workstream_dir = Path(workstream_dir)
        self.pattern = pattern
        self.loaded_workstreams = []
        self.failed_workstreams = []

    def load_all(self) -> List[Dict[str, Any]]:
        """
        Load all workstream files matching pattern.

        Returns:
            List of workstream dictionaries
        """
        workstreams = []

        if not self.workstream_dir.exists():
            logger.error(f"Workstream directory not found: {self.workstream_dir}")
            return []

        files = sorted(self.workstream_dir.glob(self.pattern))
        logger.info(f"Found {len(files)} workstream files")

        for ws_file in files:
            try:
                workstream = self._load_file(ws_file)
                self._validate_workstream(workstream)
                workstreams.append(workstream)
                self.loaded_workstreams.append(ws_file.name)
                logger.info(f"Loaded: {workstream.get('id', ws_file.name)}")
            except Exception as e:
                logger.error(f"Failed to load {ws_file.name}: {e}")
                self.failed_workstreams.append((ws_file.name, str(e)))

        logger.info(f"Successfully loaded {len(workstreams)} workstreams")
        if self.failed_workstreams:
            logger.warning(f"Failed to load {len(self.failed_workstreams)} workstreams")

        return workstreams

    def _load_file(self, file_path: Path) -> Dict[str, Any]:
        """Load single workstream JSON file."""
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _validate_workstream(self, workstream: Dict[str, Any]) -> None:
        """
        Validate workstream structure.

        Raises:
            ValueError: If workstream is invalid
        """
        required_fields = ["id"]

        for field in required_fields:
            if field not in workstream:
                raise ValueError(f"Missing required field: {field}")

        # Normalize depends_on field
        if "depends_on" not in workstream:
            workstream["depends_on"] = []
        elif isinstance(workstream["depends_on"], str):
            workstream["depends_on"] = (
                [workstream["depends_on"]] if workstream["depends_on"] else []
            )

        # Ensure depends_on is a list
        if not isinstance(workstream["depends_on"], list):
            raise ValueError(
                f"'depends_on' must be a list, got {type(workstream['depends_on'])}"
            )

    def convert_to_tasks(
        self, workstreams: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Convert workstreams to Task-compatible format.

        Args:
            workstreams: List of workstream dictionaries

        Returns:
            List of task dictionaries
        """
        tasks = []

        for ws in workstreams:
            task = {
                "task_id": ws.get("id"),
                "task_kind": "workstream",
                "depends_on": ws.get("depends_on", []),
                "metadata": {
                    "workstream": ws,
                    "tool": ws.get("tool", "aider"),
                    "files": ws.get("files_scope", []),
                    "tasks": ws.get("tasks", []),
                    "title": ws.get("title", ""),
                },
            }
            tasks.append(task)

        return tasks

    def get_summary(self) -> Dict[str, Any]:
        """Get loader summary statistics."""
        return {
            "total_found": len(self.loaded_workstreams) + len(self.failed_workstreams),
            "successfully_loaded": len(self.loaded_workstreams),
            "failed": len(self.failed_workstreams),
            "loaded_files": self.loaded_workstreams,
            "failed_files": self.failed_workstreams,
        }


if __name__ == "__main__":
    # Test the loader
    logging.basicConfig(level=logging.INFO)

    loader = WorkstreamLoader()
    workstreams = loader.load_all()

    print(f"\n📊 Loader Summary:")
    summary = loader.get_summary()
    print(f"   Total files: {summary['total_found']}")
    print(f"   Loaded: {summary['successfully_loaded']}")
    print(f"   Failed: {summary['failed']}")

    if workstreams:
        tasks = loader.convert_to_tasks(workstreams)
        print(f"\n✅ Converted {len(tasks)} workstreams to tasks")
