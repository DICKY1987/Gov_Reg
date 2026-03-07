# DOC_LINK: DOC-ENGINE-ENGINE-ROUTING-VALIDATOR-087
"""Phase 4 (Routing) Contract Validator - Task 2.5"""
DOC_ID: DOC-ENGINE-ENGINE-ROUTING-VALIDATOR-087

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

from core.contracts import PhaseContractValidator, ValidationResult


class RoutingContractValidator:
    """Validates Phase 4 (Tool Routing & Adapter Selection) entry/exit contracts"""

    def __init__(self, repo_root: Optional[Path] = None):
        """
        Initialize Routing contract validator

        Args:
            repo_root: Repository root path
        """
        self.repo_root = repo_root or Path.cwd()
        self.contract_validator = PhaseContractValidator(repo_root=self.repo_root)

    def validate_entry(self, context: Optional[Dict] = None) -> ValidationResult:
        """
        Validate Phase 4 entry requirements

        Entry requirements:
        - .state/task_queue.json exists
        - config/tool_profiles/*.yaml exist
        - tasks table populated
        - TASKS_QUEUED flag set

        Args:
            context: Optional context dict

        Returns:
            ValidationResult
        """
        result = self.contract_validator.validate_entry("phase4", context=context or {})

        # Verify tool profiles exist
        tool_profiles_dir = self.repo_root / "config" / "tool_profiles"
        if tool_profiles_dir.exists():
            profile_count = len(list(tool_profiles_dir.glob("*.yaml")))
            if profile_count == 0:
                result.warnings.append(
                    {
                        "type": "missing_file",
                        "message": "No tool profiles found in config/tool_profiles/",
                        "remediation": "Add tool profile YAML files",
                    }
                )

        return result

    def validate_exit(self, artifacts: Optional[Dict] = None) -> ValidationResult:
        """
        Validate Phase 4 exit artifacts

        Exit artifacts:
        - .state/routing_decisions.json created
        - tasks table updated (adapter_id assigned)
        - ROUTING_COMPLETE event emitted

        Args:
            artifacts: Optional artifacts dict

        Returns:
            ValidationResult
        """
        result = self.contract_validator.validate_exit(
            "phase4", artifacts=artifacts or {}
        )

        # Verify routing decisions file
        routing_path = self.repo_root / ".state" / "routing_decisions.json"
        if not routing_path.exists():
            result.violations.append(
                {
                    "type": "missing_file",
                    "message": "Routing decisions not found: .state/routing_decisions.json",
                    "remediation": "Phase 4 must create routing decisions",
                }
            )
            result.valid = False

        # Verify tasks have adapter_id assigned
        db_path = self.repo_root / ".state" / "orchestration.db"
        if db_path.exists():
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                # Check if tasks table has adapter_id column
                cursor.execute("PRAGMA table_info(tasks)")
                columns = [row[1] for row in cursor.fetchall()]

                if "adapter_id" not in columns:
                    result.violations.append(
                        {
                            "type": "missing_column",
                            "message": "Tasks table missing adapter_id column",
                            "remediation": "Add adapter_id column to tasks table",
                        }
                    )
                    result.valid = False
                else:
                    # Check if any tasks have adapter_id assigned
                    cursor.execute(
                        "SELECT COUNT(*) FROM tasks WHERE adapter_id IS NOT NULL"
                    )
                    assigned_count = cursor.fetchone()[0]

                    if assigned_count == 0:
                        result.warnings.append(
                            {
                                "type": "missing_data",
                                "message": "No tasks have adapter_id assigned",
                                "remediation": "Phase 4 should assign adapters to tasks",
                            }
                        )

                conn.close()
            except sqlite3.Error as e:
                result.violations.append(
                    {"type": "database_error", "message": f"Database error: {e}"}
                )
                result.valid = False

        return result

    def get_routing_metrics(self) -> Dict:
        """
        Get routing phase metrics

        Returns:
            Dict with adapter assignments, tool profile count, etc.
        """
        metrics = {
            "routing_decisions_exist": (
                self.repo_root / ".state" / "routing_decisions.json"
            ).exists(),
            "tool_profile_count": 0,
            "tasks_assigned": 0,
            "tasks_unassigned": 0,
        }

        # Count tool profiles
        tool_profiles_dir = self.repo_root / "config" / "tool_profiles"
        if tool_profiles_dir.exists():
            metrics["tool_profile_count"] = len(list(tool_profiles_dir.glob("*.yaml")))

        # Count assigned/unassigned tasks
        db_path = self.repo_root / ".state" / "orchestration.db"
        if db_path.exists():
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT COUNT(*) FROM tasks WHERE adapter_id IS NOT NULL"
                )
                metrics["tasks_assigned"] = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM tasks WHERE adapter_id IS NULL")
                metrics["tasks_unassigned"] = cursor.fetchone()[0]

                conn.close()
            except sqlite3.Error:
                pass

        return metrics
