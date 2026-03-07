# DOC_LINK: DOC-ENGINE-ENGINE-REQUEST-VALIDATOR-086
"""Phase 2 (Request Building) Contract Validator - Task 2.3"""
DOC_ID: DOC-ENGINE-ENGINE-REQUEST-VALIDATOR-086

import sqlite3
from pathlib import Path
from typing import Dict, Optional

from core.contracts import PhaseContractValidator, ValidationResult


class RequestBuildingContractValidator:
    """Validates Phase 2 (Request Building & Run Creation) entry/exit contracts"""

    def __init__(self, repo_root: Optional[Path] = None):
        """
        Initialize Request Building contract validator

        Args:
            repo_root: Repository root path
        """
        self.repo_root = repo_root or Path.cwd()
        self.contract_validator = PhaseContractValidator(repo_root=self.repo_root)

    def validate_entry(self, context: Optional[Dict] = None) -> ValidationResult:
        """
        Validate Phase 2 entry requirements

        Entry requirements:
        - workstreams/*.json exist (from phase1)
        - schema/execution_request.v1.json exists
        - workstreams table exists
        - PLANNING_COMPLETE flag set

        Args:
            context: Optional context dict

        Returns:
            ValidationResult
        """
        result = self.contract_validator.validate_entry("phase2", context=context or {})

        # Verify execution request schema exists
        schema_path = self.repo_root / "schema" / "execution_request.v1.json"
        if not schema_path.exists():
            result.violations.append(
                {
                    "type": "missing_file",
                    "message": "Execution request schema missing: schema/execution_request.v1.json",
                    "remediation": "Create execution request schema",
                }
            )
            result.valid = False

        return result

    def validate_exit(self, artifacts: Optional[Dict] = None) -> ValidationResult:
        """
        Validate Phase 2 exit artifacts

        Exit artifacts:
        - .state/orchestration.db updated
        - runs table populated
        - RUN_CREATED event emitted

        Args:
            artifacts: Optional artifacts dict

        Returns:
            ValidationResult
        """
        result = self.contract_validator.validate_exit(
            "phase2", artifacts=artifacts or {}
        )

        # Verify runs table exists and has data
        db_path = self.repo_root / ".state" / "orchestration.db"
        if db_path.exists():
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                # Check runs table
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='runs'"
                )
                if not cursor.fetchone():
                    result.violations.append(
                        {
                            "type": "missing_db_table",
                            "message": "Runs table not found in orchestration.db",
                            "remediation": "Phase 2 must create runs table",
                        }
                    )
                    result.valid = False
                else:
                    # Check if runs table has at least one row
                    cursor.execute("SELECT COUNT(*) FROM runs")
                    run_count = cursor.fetchone()[0]
                    if run_count == 0:
                        result.warnings.append(
                            {
                                "type": "empty_table",
                                "message": "Runs table is empty",
                                "remediation": "Phase 2 should create at least one run record",
                            }
                        )

                conn.close()
            except sqlite3.Error as e:
                result.violations.append(
                    {
                        "type": "database_error",
                        "message": f"Database error: {e}",
                    }
                )
                result.valid = False

        return result

    def validate_run_exists(self, run_id: str) -> bool:
        """
        Validate specific run exists in DB

        Args:
            run_id: Run identifier

        Returns:
            True if run exists
        """
        db_path = self.repo_root / ".state" / "orchestration.db"
        if not db_path.exists():
            return False

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM runs WHERE id = ?", (run_id,))
            exists = cursor.fetchone() is not None
            conn.close()
            return exists
        except sqlite3.Error:
            return False

    def get_request_building_metrics(self) -> Dict:
        """
        Get request building metrics

        Returns:
            Dict with run count, workstream count, etc.
        """
        db_path = self.repo_root / ".state" / "orchestration.db"
        metrics = {"run_count": 0, "workstream_count": 0, "db_exists": db_path.exists()}

        if db_path.exists():
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM runs")
                metrics["run_count"] = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM workstreams")
                metrics["workstream_count"] = cursor.fetchone()[0]

                conn.close()
            except sqlite3.Error:
                pass

        return metrics
