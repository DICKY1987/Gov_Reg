# DOC_LINK: DOC-ENGINE-ENGINE-EXECUTION-VALIDATOR-084
"""Phase 5 (Execution) Contract Validator - Task 2.6"""
DOC_ID: DOC-ENGINE-ENGINE-EXECUTION-VALIDATOR-084

import sqlite3
from pathlib import Path
from typing import Dict, Optional

from core.contracts import PhaseContractValidator, ValidationResult


class ExecutionContractValidator:
    """Validates Phase 5 (Execution & Validation) entry/exit contracts"""

    def __init__(self, repo_root: Optional[Path] = None):
        """
        Initialize Execution contract validator

        Args:
            repo_root: Repository root path
        """
        self.repo_root = repo_root or Path.cwd()
        self.contract_validator = PhaseContractValidator(repo_root=self.repo_root)

    def validate_entry(self, context: Optional[Dict] = None) -> ValidationResult:
        """
        Validate Phase 5 entry requirements

        Entry requirements:
        - .state/routing_decisions.json exists
        - tasks table with adapter_id
        - ROUTING_COMPLETE flag set

        Args:
            context: Optional context dict

        Returns:
            ValidationResult
        """
        result = self.contract_validator.validate_entry("phase5", context=context or {})

        # Verify tasks have adapters assigned
        db_path = self.repo_root / ".state" / "orchestration.db"
        if db_path.exists():
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM tasks WHERE adapter_id IS NULL")
                unassigned_count = cursor.fetchone()[0]

                if unassigned_count > 0:
                    result.warnings.append(
                        {
                            "type": "missing_data",
                            "message": f"{unassigned_count} tasks have no adapter assigned",
                            "remediation": "Phase 4 should assign adapters to all tasks",
                        }
                    )

                conn.close()
            except sqlite3.Error as e:
                result.violations.append(
                    {"type": "database_error", "message": f"Database error: {e}"}
                )
                result.valid = False

        return result

    def validate_exit(self, artifacts: Optional[Dict] = None) -> ValidationResult:
        """
        Validate Phase 5 exit artifacts

        Exit artifacts:
        - .state/execution_results.json created
        - .state/patch_ledger.jsonl created
        - tasks table updated (status = COMPLETED/FAILED/TIMEOUT)
        - TASK_COMPLETED/TASK_FAILED events emitted

        Args:
            artifacts: Optional artifacts dict

        Returns:
            ValidationResult
        """
        result = self.contract_validator.validate_exit(
            "phase5", artifacts=artifacts or {}
        )

        # Verify execution results
        results_path = self.repo_root / ".state" / "execution_results.json"
        if not results_path.exists():
            result.violations.append(
                {
                    "type": "missing_file",
                    "message": "Execution results not found: .state/execution_results.json",
                    "remediation": "Phase 5 must create execution results",
                }
            )
            result.valid = False

        # Verify patch ledger
        ledger_path = self.repo_root / ".state" / "patch_ledger.jsonl"
        if not ledger_path.exists():
            result.warnings.append(
                {
                    "type": "missing_file",
                    "message": "Patch ledger not found: .state/patch_ledger.jsonl",
                    "remediation": "Phase 5 should create patch ledger",
                }
            )

        # Verify task statuses updated
        db_path = self.repo_root / ".state" / "orchestration.db"
        if db_path.exists():
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                # Check task statuses
                cursor.execute(
                    """
                    SELECT status, COUNT(*)
                    FROM tasks
                    GROUP BY status
                """
                )
                status_counts = dict(cursor.fetchall())

                # Check if tasks have terminal statuses
                terminal_statuses = {"COMPLETED", "FAILED", "TIMEOUT"}
                has_terminal = any(s in terminal_statuses for s in status_counts.keys())

                if not has_terminal:
                    result.warnings.append(
                        {
                            "type": "missing_data",
                            "message": "No tasks have terminal status (COMPLETED/FAILED/TIMEOUT)",
                            "remediation": "Phase 5 should update task statuses",
                        }
                    )

                conn.close()
            except sqlite3.Error as e:
                result.violations.append(
                    {"type": "database_error", "message": f"Database error: {e}"}
                )
                result.valid = False

        return result

    def get_execution_metrics(self) -> Dict:
        """
        Get execution phase metrics

        Returns:
            Dict with task counts by status, patch count, etc.
        """
        metrics = {
            "execution_results_exist": (
                self.repo_root / ".state" / "execution_results.json"
            ).exists(),
            "patch_ledger_exists": (
                self.repo_root / ".state" / "patch_ledger.jsonl"
            ).exists(),
            "tasks_completed": 0,
            "tasks_failed": 0,
            "tasks_timeout": 0,
            "tasks_pending": 0,
        }

        db_path = self.repo_root / ".state" / "orchestration.db"
        if db_path.exists():
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'COMPLETED'")
                metrics["tasks_completed"] = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'FAILED'")
                metrics["tasks_failed"] = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'TIMEOUT'")
                metrics["tasks_timeout"] = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'PENDING'")
                metrics["tasks_pending"] = cursor.fetchone()[0]

                conn.close()
            except sqlite3.Error:
                pass

        return metrics
