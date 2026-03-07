# DOC_LINK: DOC-ENGINE-ENGINE-SCHEDULING-VALIDATOR-088
"""Phase 3 (Scheduling) Contract Validator - Task 2.4"""
DOC_ID: DOC-ENGINE-ENGINE-SCHEDULING-VALIDATOR-088

import json
import sqlite3
from pathlib import Path
from typing import Dict, Optional

from core.contracts import PhaseContractValidator, ValidationResult


class SchedulingContractValidator:
    """Validates Phase 3 (Scheduling & Task Graph) entry/exit contracts"""

    def __init__(self, repo_root: Optional[Path] = None):
        """
        Initialize Scheduling contract validator

        Args:
            repo_root: Repository root path
        """
        self.repo_root = repo_root or Path.cwd()
        self.contract_validator = PhaseContractValidator(repo_root=self.repo_root)

    def validate_entry(self, context: Optional[Dict] = None) -> ValidationResult:
        """
        Validate Phase 3 entry requirements

        Entry requirements:
        - .state/orchestration.db with run record
        - workstreams/*.json exist
        - runs table populated
        - RUN_CREATED flag set

        Args:
            context: Optional context dict

        Returns:
            ValidationResult
        """
        result = self.contract_validator.validate_entry("phase3", context=context or {})

        # Additional validation: check if runs table has records
        db_path = self.repo_root / ".state" / "orchestration.db"
        if db_path.exists():
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM runs")
                run_count = cursor.fetchone()[0]
                conn.close()

                if run_count == 0:
                    result.violations.append(
                        {
                            "type": "missing_data",
                            "message": "No run records found in database",
                            "remediation": "Phase 2 must create at least one run",
                        }
                    )
                    result.valid = False
            except sqlite3.Error as e:
                result.violations.append(
                    {"type": "database_error", "message": f"Database error: {e}"}
                )
                result.valid = False

        return result

    def validate_exit(self, artifacts: Optional[Dict] = None) -> ValidationResult:
        """
        Validate Phase 3 exit artifacts

        Exit artifacts:
        - .state/task_queue.json created
        - .state/dag_graph.json created
        - tasks table populated
        - DAG_BUILT, TASKS_QUEUED events emitted

        Args:
            artifacts: Optional artifacts dict

        Returns:
            ValidationResult
        """
        result = self.contract_validator.validate_exit(
            "phase3", artifacts=artifacts or {}
        )

        # Verify task queue exists
        task_queue_path = self.repo_root / ".state" / "task_queue.json"
        if not task_queue_path.exists():
            result.violations.append(
                {
                    "type": "missing_file",
                    "message": "Task queue not found: .state/task_queue.json",
                    "remediation": "Phase 3 must create task queue",
                }
            )
            result.valid = False

        # Verify DAG graph exists
        dag_path = self.repo_root / ".state" / "dag_graph.json"
        if not dag_path.exists():
            result.violations.append(
                {
                    "type": "missing_file",
                    "message": "DAG graph not found: .state/dag_graph.json",
                    "remediation": "Phase 3 must create DAG graph",
                }
            )
            result.valid = False

        # Validate DAG is acyclic
        if dag_path.exists():
            try:
                with open(dag_path, "r") as f:
                    dag_data = json.load(f)

                if self._has_cycle(dag_data):
                    result.violations.append(
                        {
                            "type": "constraint_violation",
                            "message": "DAG contains cycles (circular dependencies)",
                            "remediation": "Remove circular dependencies from task graph",
                        }
                    )
                    result.valid = False
            except (json.JSONDecodeError, KeyError):
                result.warnings.append(
                    {
                        "type": "invalid_format",
                        "message": "DAG graph file is malformed",
                    }
                )

        return result

    def _has_cycle(self, dag_data: Dict) -> bool:
        """
        Check if DAG has cycles using DFS

        Args:
            dag_data: DAG data structure

        Returns:
            True if cycle detected
        """
        # Simple cycle detection - assumes dag_data has 'nodes' and 'edges'
        if "edges" not in dag_data:
            return False

        visited = set()
        rec_stack = set()

        def dfs(node):
            visited.add(node)
            rec_stack.add(node)

            for edge in dag_data["edges"]:
                if edge.get("from") == node:
                    neighbor = edge.get("to")
                    if neighbor not in visited:
                        if dfs(neighbor):
                            return True
                    elif neighbor in rec_stack:
                        return True

            rec_stack.remove(node)
            return False

        for node in dag_data.get("nodes", []):
            node_id = node.get("id")
            if node_id and node_id not in visited:
                if dfs(node_id):
                    return True

        return False

    def get_scheduling_metrics(self) -> Dict:
        """
        Get scheduling phase metrics

        Returns:
            Dict with task count, DAG stats, etc.
        """
        metrics = {
            "task_queue_exists": (
                self.repo_root / ".state" / "task_queue.json"
            ).exists(),
            "dag_graph_exists": (self.repo_root / ".state" / "dag_graph.json").exists(),
            "task_count": 0,
            "dag_node_count": 0,
        }

        # Get task count from queue
        task_queue_path = self.repo_root / ".state" / "task_queue.json"
        if task_queue_path.exists():
            try:
                with open(task_queue_path, "r") as f:
                    queue_data = json.load(f)
                    metrics["task_count"] = (
                        len(queue_data) if isinstance(queue_data, list) else 0
                    )
            except json.JSONDecodeError:
                pass

        # Get DAG stats
        dag_path = self.repo_root / ".state" / "dag_graph.json"
        if dag_path.exists():
            try:
                with open(dag_path, "r") as f:
                    dag_data = json.load(f)
                    metrics["dag_node_count"] = len(dag_data.get("nodes", []))
                    metrics["dag_edge_count"] = len(dag_data.get("edges", []))
                    metrics["has_cycle"] = self._has_cycle(dag_data)
            except json.JSONDecodeError:
                pass

        return metrics
