"""
Patch Ledger Management

Manages patch lifecycle with state machine transitions.
Tracks patch validation, application, verification, and quarantine.

State Machine:
    created -> validated -> queued -> applied -> verified -> committed
    any -> apply_failed (retry or quarantine)
    any -> quarantined (safety)
    any -> dropped (reject)

Author: AI Development Pipeline
Created: 2025-11-23
WS: WS-NEXT-002-002
"""

# DOC_ID: DOC-CORE-ENGINE-PATCH-LEDGER-153

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Dict, List, Optional


@dataclass
class ValidationResult:
    """Patch validation results"""

    format_ok: bool = False
    scope_ok: bool = False
    constraints_ok: bool = False
    tests_ran: bool = False
    tests_passed: bool = False
    validation_errors: List[str] = None

    def __post_init__(self):
        if self.validation_errors is None:
            self.validation_errors = []

    @property
    def is_valid(self) -> bool:
        """Check if validation passed"""
        return self.format_ok and self.scope_ok and self.constraints_ok

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "format_ok": self.format_ok,
            "scope_ok": self.scope_ok,
            "constraints_ok": self.constraints_ok,
            "tests_ran": self.tests_ran,
            "tests_passed": self.tests_passed,
            "validation_errors": self.validation_errors,
        }


class PatchLedger:
    """
    Manages patch ledger state machine and tracking.

    States:
        - created: Patch entry created
        - validated: Patch validation passed
        - queued: Patch queued for application
        - applied: Patch successfully applied
        - apply_failed: Patch application failed
        - verified: Patch verified (tests passed)
        - committed: Patch committed to repository
        - rolled_back: Patch was rolled back
        - quarantined: Patch quarantined for safety
        - dropped: Patch rejected/dropped

    Transitions:
        - validate: created -> validated (or apply_failed)
        - queue: validated -> queued
        - apply: queued -> applied (or apply_failed)
        - verify: applied -> verified (or apply_failed)
        - commit: verified -> committed
        - rollback: applied/verified -> rolled_back
        - quarantine: any -> quarantined
        - drop: any -> dropped
    """

    VALID_STATES = {
        "created",
        "validated",
        "queued",
        "applied",
        "apply_failed",
        "verified",
        "committed",
        "rolled_back",
        "quarantined",
        "dropped",
    }

    TERMINAL_STATES = {"committed", "rolled_back", "dropped"}

    STATE_TRANSITIONS = {
        "created": ["validated", "apply_failed", "quarantined", "dropped"],
        "validated": ["queued", "quarantined", "dropped"],
        "queued": ["applied", "apply_failed", "quarantined", "dropped"],
        "applied": [
            "verified",
            "apply_failed",
            "rolled_back",
            "quarantined",
            "dropped",
        ],
        "apply_failed": ["queued", "quarantined", "dropped"],
        "verified": ["committed", "rolled_back", "quarantined", "dropped"],
        "committed": [],  # Terminal
        "rolled_back": [],  # Terminal
        "quarantined": ["dropped"],
        "dropped": [],  # Terminal
    }

    def __init__(self, db):
        """
        Initialize PatchLedger manager.

        Args:
            db: Database instance for persistence
        """
        self.db = db
        self._ensure_table()

    def _ensure_table(self):
        """Ensure patch_ledger table exists"""
        try:
            self.db.conn.execute("SELECT 1 FROM patch_ledger LIMIT 1")
        except Exception:
            # Table doesn't exist, create it
            # Try multiple possible paths for the migration file
            possible_paths = [
                "schema/migrations/003_add_patch_ledger_table.sql",
                "phase0_bootstrap/modules/bootstrap_orchestrator/schemas/schema/migrations/003_add_patch_ledger_table.sql",
            ]

            schema_path = None
            for path in possible_paths:
                from pathlib import Path

                if Path(path).exists():
                    schema_path = path
                    break

            if schema_path is None:
                raise FileNotFoundError(
                    f"Could not find patch_ledger migration file in any of: {possible_paths}"
                )

            with open(schema_path, "r") as f:
                self.db.conn.executescript(f.read())
            self.db.conn.commit()

    def create_entry(
        self,
        ledger_id: str,
        patch_id: str,
        project_id: str,
        validation: Optional[ValidationResult] = None,
        phase_id: Optional[str] = None,
        workstream_id: Optional[str] = None,
        execution_request_id: Optional[str] = None,
    ) -> str:
        """
        Create a new patch ledger entry.

        Args:
            ledger_id: Unique ledger entry identifier (ULID)
            patch_id: Patch identifier
            project_id: Project identifier
            validation: Initial validation result
            phase_id: Optional phase identifier
            workstream_id: Optional workstream identifier
            execution_request_id: Optional execution request ID

        Returns:
            ledger_id
        """
        if validation is None:
            validation = ValidationResult()

        now = datetime.now(UTC).isoformat()

        entry_data = {
            "ledger_id": ledger_id,
            "patch_id": patch_id,
            "project_id": project_id,
            "phase_id": phase_id,
            "workstream_id": workstream_id,
            "execution_request_id": execution_request_id,
            "state": "created",
            "state_history": json.dumps(
                [{"state": "created", "at": now, "reason": "Initial creation"}]
            ),
            "validation": json.dumps(validation.to_dict()),
            "apply": None,
            "quarantine": None,
            "relations": None,
            "created_at": now,
            "updated_at": now,
        }

        self.db.conn.execute(
            """
            INSERT INTO patch_ledger (
                ledger_id, patch_id, project_id, phase_id, workstream_id,
                execution_request_id, state, state_history, validation,
                apply, quarantine, relations, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry_data["ledger_id"],
                entry_data["patch_id"],
                entry_data["project_id"],
                entry_data["phase_id"],
                entry_data["workstream_id"],
                entry_data["execution_request_id"],
                entry_data["state"],
                entry_data["state_history"],
                entry_data["validation"],
                entry_data["apply"],
                entry_data["quarantine"],
                entry_data["relations"],
                entry_data["created_at"],
                entry_data["updated_at"],
            ),
        )
        self.db.conn.commit()

        return ledger_id

    def get_entry(self, ledger_id: str) -> Optional[Dict]:
        """
        Get ledger entry by ID.

        Args:
            ledger_id: Ledger entry identifier

        Returns:
            Entry data dict or None if not found
        """
        row = self.db.conn.execute(
            "SELECT * FROM patch_ledger WHERE ledger_id = ?", (ledger_id,)
        ).fetchone()

        if not row:
            return None

        return self._row_to_dict(row)

    def _row_to_dict(self, row) -> Dict:
        """Convert database row to dict"""
        data = dict(row)

        # Deserialize JSON fields
        for field in [
            "state_history",
            "validation",
            "apply",
            "quarantine",
            "relations",
        ]:
            if data.get(field):
                data[field] = json.loads(data[field])

        return data

    def _add_state_history(self, ledger_id: str, state: str, reason: str):
        """Add state transition to history"""
        entry = self.get_entry(ledger_id)
        history = entry["state_history"] or []

        history.append(
            {"state": state, "at": datetime.now(UTC).isoformat(), "reason": reason}
        )

        self.db.conn.execute(
            "UPDATE patch_ledger SET state_history = ? WHERE ledger_id = ?",
            (json.dumps(history), ledger_id),
        )

    def validate_patch(self, ledger_id: str, validation: ValidationResult) -> bool:
        """
        Validate patch (created -> validated or apply_failed).

        Args:
            ledger_id: Ledger entry identifier
            validation: Validation result

        Returns:
            True if successful
        """
        entry = self.get_entry(ledger_id)
        if not entry:
            raise ValueError(f"Ledger entry not found: {ledger_id}")

        new_state = "validated" if validation.is_valid else "apply_failed"

        if not self._can_transition(entry["state"], new_state):
            raise ValueError(f"Cannot validate: entry in {entry['state']} state")

        self._add_state_history(
            ledger_id,
            new_state,
            "Validation completed" if validation.is_valid else "Validation failed",
        )

        self.db.conn.execute(
            """
            UPDATE patch_ledger
            SET state = ?, validation = ?, updated_at = ?
            WHERE ledger_id = ?
            """,
            (
                new_state,
                json.dumps(validation.to_dict()),
                datetime.now(UTC).isoformat(),
                ledger_id,
            ),
        )
        self.db.conn.commit()

        return True

    def queue_patch(self, ledger_id: str) -> bool:
        """
        Queue patch for application (validated -> queued).

        Args:
            ledger_id: Ledger entry identifier

        Returns:
            True if successful
        """
        entry = self.get_entry(ledger_id)
        if not entry:
            raise ValueError(f"Ledger entry not found: {ledger_id}")

        if not self._can_transition(entry["state"], "queued"):
            raise ValueError(f"Cannot queue: entry in {entry['state']} state")

        self._add_state_history(ledger_id, "queued", "Queued for application")

        self.db.conn.execute(
            "UPDATE patch_ledger SET state = 'queued', updated_at = ? WHERE ledger_id = ?",
            (datetime.now(UTC).isoformat(), ledger_id),
        )
        self.db.conn.commit()

        return True

    def apply_patch(
        self,
        ledger_id: str,
        success: bool,
        workspace_path: Optional[str] = None,
        applied_files: Optional[List[str]] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        Apply patch (queued -> applied or apply_failed).

        Args:
            ledger_id: Ledger entry identifier
            success: Whether application succeeded
            workspace_path: Path where patch was applied
            applied_files: List of files modified
            error_code: Error code if failed
            error_message: Error message if failed

        Returns:
            True if successful
        """
        entry = self.get_entry(ledger_id)
        if not entry:
            raise ValueError(f"Ledger entry not found: {ledger_id}")

        new_state = "applied" if success else "apply_failed"

        if not self._can_transition(entry["state"], new_state):
            raise ValueError(f"Cannot apply: entry in {entry['state']} state")

        # Update apply info
        apply_data = entry.get("apply") or {}
        apply_data["attempts"] = apply_data.get("attempts", 0) + 1
        apply_data["last_attempt_at"] = datetime.now(UTC).isoformat()

        if success:
            apply_data["workspace_path"] = workspace_path
            apply_data["applied_files"] = applied_files or []
        else:
            apply_data["last_error_code"] = error_code
            apply_data["last_error_message"] = error_message

        self._add_state_history(
            ledger_id,
            new_state,
            (
                "Application succeeded"
                if success
                else f"Application failed: {error_message}"
            ),
        )

        self.db.conn.execute(
            """
            UPDATE patch_ledger
            SET state = ?, apply = ?, updated_at = ?
            WHERE ledger_id = ?
            """,
            (
                new_state,
                json.dumps(apply_data),
                datetime.now(UTC).isoformat(),
                ledger_id,
            ),
        )
        self.db.conn.commit()

        return True

    def verify_patch(self, ledger_id: str, tests_passed: bool) -> bool:
        """
        Verify patch (applied -> verified or apply_failed).

        Args:
            ledger_id: Ledger entry identifier
            tests_passed: Whether tests passed

        Returns:
            True if successful
        """
        entry = self.get_entry(ledger_id)
        if not entry:
            raise ValueError(f"Ledger entry not found: {ledger_id}")

        new_state = "verified" if tests_passed else "apply_failed"

        if not self._can_transition(entry["state"], new_state):
            raise ValueError(f"Cannot verify: entry in {entry['state']} state")

        self._add_state_history(
            ledger_id,
            new_state,
            "Verification passed" if tests_passed else "Verification failed",
        )

        self.db.conn.execute(
            "UPDATE patch_ledger SET state = ?, updated_at = ? WHERE ledger_id = ?",
            (new_state, datetime.now(UTC).isoformat(), ledger_id),
        )
        self.db.conn.commit()

        return True

    def commit_patch(self, ledger_id: str) -> bool:
        """
        Commit patch (verified -> committed).

        Args:
            ledger_id: Ledger entry identifier

        Returns:
            True if successful
        """
        entry = self.get_entry(ledger_id)
        if not entry:
            raise ValueError(f"Ledger entry not found: {ledger_id}")

        if not self._can_transition(entry["state"], "committed"):
            raise ValueError(f"Cannot commit: entry in {entry['state']} state")

        self._add_state_history(ledger_id, "committed", "Patch committed")

        self.db.conn.execute(
            "UPDATE patch_ledger SET state = 'committed', updated_at = ? WHERE ledger_id = ?",
            (datetime.now(UTC).isoformat(), ledger_id),
        )
        self.db.conn.commit()

        return True

    def rollback_patch(self, ledger_id: str, reason: str) -> bool:
        """
        Rollback patch (applied/verified -> rolled_back).

        Args:
            ledger_id: Ledger entry identifier
            reason: Reason for rollback

        Returns:
            True if successful
        """
        entry = self.get_entry(ledger_id)
        if not entry:
            raise ValueError(f"Ledger entry not found: {ledger_id}")

        if not self._can_transition(entry["state"], "rolled_back"):
            raise ValueError(f"Cannot rollback: entry in {entry['state']} state")

        self._add_state_history(ledger_id, "rolled_back", reason)

        self.db.conn.execute(
            "UPDATE patch_ledger SET state = 'rolled_back', updated_at = ? WHERE ledger_id = ?",
            (datetime.now(UTC).isoformat(), ledger_id),
        )
        self.db.conn.commit()

        return True

    def quarantine_patch(
        self, ledger_id: str, reason: str, quarantine_path: Optional[str] = None
    ) -> bool:
        """
        Quarantine patch (any -> quarantined).

        Args:
            ledger_id: Ledger entry identifier
            reason: Reason for quarantine
            quarantine_path: Path where patch is quarantined

        Returns:
            True if successful
        """
        entry = self.get_entry(ledger_id)
        if not entry:
            raise ValueError(f"Ledger entry not found: {ledger_id}")

        if not self._can_transition(entry["state"], "quarantined"):
            raise ValueError(f"Cannot quarantine: entry in {entry['state']} state")

        quarantine_data = {
            "is_quarantined": True,
            "quarantine_reason": reason,
            "quarantine_path": quarantine_path,
            "quarantined_at": datetime.now(UTC).isoformat(),
        }

        self._add_state_history(ledger_id, "quarantined", reason)

        self.db.conn.execute(
            """
            UPDATE patch_ledger
            SET state = 'quarantined', quarantine = ?, updated_at = ?
            WHERE ledger_id = ?
            """,
            (json.dumps(quarantine_data), datetime.now(UTC).isoformat(), ledger_id),
        )
        self.db.conn.commit()

        return True

    def drop_patch(self, ledger_id: str, reason: str) -> bool:
        """
        Drop/reject patch (any -> dropped).

        Args:
            ledger_id: Ledger entry identifier
            reason: Reason for dropping

        Returns:
            True if successful
        """
        entry = self.get_entry(ledger_id)
        if not entry:
            raise ValueError(f"Ledger entry not found: {ledger_id}")

        if not self._can_transition(entry["state"], "dropped"):
            raise ValueError(f"Cannot drop: entry in {entry['state']} state")

        self._add_state_history(ledger_id, "dropped", reason)

        self.db.conn.execute(
            "UPDATE patch_ledger SET state = 'dropped', updated_at = ? WHERE ledger_id = ?",
            (datetime.now(UTC).isoformat(), ledger_id),
        )
        self.db.conn.commit()

        return True

    def list_entries(
        self,
        project_id: Optional[str] = None,
        state: Optional[str] = None,
        workstream_id: Optional[str] = None,
    ) -> List[Dict]:
        """
        List ledger entries with optional filters.

        Args:
            project_id: Filter by project
            state: Filter by state
            workstream_id: Filter by workstream

        Returns:
            List of entry dicts
        """
        return list(self.iter_entries(project_id, state, workstream_id))
    
    def iter_entries(
        self,
        project_id: Optional[str] = None,
        state: Optional[str] = None,
        workstream_id: Optional[str] = None,
    ):
        """
        Iterate ledger entries with optional filters (memory-efficient generator).

        Args:
            project_id: Filter by project
            state: Filter by state
            workstream_id: Filter by workstream

        Yields:
            Entry dicts one at a time
        """
        query = "SELECT * FROM patch_ledger WHERE 1=1"
        params = []

        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)

        if state:
            query += " AND state = ?"
            params.append(state)

        if workstream_id:
            query += " AND workstream_id = ?"
            params.append(workstream_id)

        query += " ORDER BY created_at DESC"

        for row in self.db.conn.execute(query, params):
            yield self._row_to_dict(row)

    def _can_transition(self, from_state: str, to_state: str) -> bool:
        """
        Check if state transition is valid.

        Args:
            from_state: Current state
            to_state: Target state

        Returns:
            True if transition is valid
        """
        if from_state in self.TERMINAL_STATES:
            return False

        return to_state in self.STATE_TRANSITIONS.get(from_state, [])

    @staticmethod
    def is_terminal(state: str) -> bool:
        """Check if state is terminal"""
        return state in PatchLedger.TERMINAL_STATES
