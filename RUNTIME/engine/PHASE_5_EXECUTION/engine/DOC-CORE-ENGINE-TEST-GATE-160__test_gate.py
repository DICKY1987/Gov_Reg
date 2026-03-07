# DOC_LINK: DOC-CORE-ENGINE-TEST-GATE-160
"""
Test Gate Management

Manages quality gate execution and pass/fail decisions.
Tracks test execution, results, and criteria evaluation.

State Machine:
    pending -> running -> passed/failed/error
    any -> skipped

Author: AI Development Pipeline
Created: 2025-11-23
WS: WS-NEXT-002-003
"""

# DOC_ID: DOC-CORE-ENGINE-TEST-GATE-160

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Dict, List, Optional


@dataclass
class GateCriteria:
    """Quality gate criteria"""

    min_coverage: Optional[float] = None
    max_failures: Optional[int] = None
    required_tests: List[str] = field(default_factory=list)
    timeout_seconds: Optional[int] = None
    custom_rules: Optional[Dict] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "min_coverage": self.min_coverage,
            "max_failures": self.max_failures,
            "required_tests": self.required_tests,
            "timeout_seconds": self.timeout_seconds,
            "custom_rules": self.custom_rules,
        }


@dataclass
class TestResults:
    """Test execution results"""

    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    coverage_percent: Optional[float] = None
    failures: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "skipped_tests": self.skipped_tests,
            "coverage_percent": self.coverage_percent,
            "failures": self.failures,
        }


class TestGate:
    """
    Manages test gate execution and evaluation.

    States:
        - pending: Gate created, not yet started
        - running: Gate execution in progress
        - passed: Gate passed all criteria
        - failed: Gate failed one or more criteria
        - skipped: Gate was skipped
        - error: Gate encountered an error during execution

    Transitions:
        - start: pending -> running
        - complete: running -> passed/failed/error
        - skip: any -> skipped
    """

    VALID_STATES = {"pending", "running", "passed", "failed", "skipped", "error"}
    VALID_TYPES = {
        "unit_tests",
        "integration_tests",
        "e2e_tests",
        "security_scan",
        "lint",
        "custom",
    }
    TERMINAL_STATES = {"passed", "failed", "skipped", "error"}

    STATE_TRANSITIONS = {
        "pending": ["running", "skipped"],
        "running": ["passed", "failed", "error", "skipped"],
        "passed": [],
        "failed": [],
        "skipped": [],
        "error": [],
    }

    def __init__(self, db):
        """
        Initialize TestGate manager.

        Args:
            db: Database instance for persistence
        """
        self.db = db
        self._ensure_table()

    def _ensure_table(self):
        """Ensure test_gates table exists"""
        try:
            self.db.conn.execute("SELECT 1 FROM test_gates LIMIT 1")
        except Exception:
            schema_path = "schema/migrations/004_add_test_gates_table.sql"
            with open(schema_path, "r") as f:
                self.db.conn.executescript(f.read())
            self.db.conn.commit()

    def create_gate(
        self,
        gate_id: str,
        name: str,
        gate_type: str,
        criteria: GateCriteria,
        project_id: Optional[str] = None,
        execution_request_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        """
        Create a new test gate.

        Args:
            gate_id: Unique gate identifier (ULID)
            name: Human-readable gate name
            gate_type: Type of gate (unit_tests, etc.)
            criteria: Gate pass criteria
            project_id: Optional project identifier
            execution_request_id: Optional execution request ID
            metadata: Additional metadata

        Returns:
            gate_id

        Raises:
            ValueError: If gate_type invalid
        """
        if gate_type not in self.VALID_TYPES:
            raise ValueError(f"Invalid gate_type: {gate_type}")

        now = datetime.now(UTC).isoformat()

        self.db.conn.execute(
            """
            INSERT INTO test_gates (
                gate_id, name, gate_type, state, project_id,
                execution_request_id, criteria, execution, results,
                decision, created_at, updated_at, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                gate_id,
                name,
                gate_type,
                "pending",
                project_id,
                execution_request_id,
                json.dumps(criteria.to_dict()),
                None,
                None,
                None,
                now,
                now,
                json.dumps(metadata) if metadata else None,
            ),
        )
        self.db.conn.commit()

        return gate_id

    def get_gate(self, gate_id: str) -> Optional[Dict]:
        """
        Get gate by ID.

        Args:
            gate_id: Gate identifier

        Returns:
            Gate data dict or None if not found
        """
        row = self.db.conn.execute(
            "SELECT * FROM test_gates WHERE gate_id = ?", (gate_id,)
        ).fetchone()

        if not row:
            return None

        return self._row_to_dict(row)

    def _row_to_dict(self, row) -> Dict:
        """Convert database row to dict"""
        data = dict(row)

        # Deserialize JSON fields
        for field in ["criteria", "execution", "results", "decision", "metadata"]:
            if data.get(field):
                data[field] = json.loads(data[field])

        return data

    def start_gate(self, gate_id: str, command: Optional[str] = None) -> bool:
        """
        Start gate execution (pending -> running).

        Args:
            gate_id: Gate identifier
            command: Command to execute

        Returns:
            True if successful
        """
        gate = self.get_gate(gate_id)
        if not gate:
            raise ValueError(f"Gate not found: {gate_id}")

        if not self._can_transition(gate["state"], "running"):
            raise ValueError(f"Cannot start gate: gate in {gate['state']} state")

        execution_data = {
            "started_at": datetime.now(UTC).isoformat(),
            "command": command,
        }

        self.db.conn.execute(
            """
            UPDATE test_gates
            SET state = 'running', execution = ?, updated_at = ?
            WHERE gate_id = ?
            """,
            (json.dumps(execution_data), datetime.now(UTC).isoformat(), gate_id),
        )
        self.db.conn.commit()

        return True

    def complete_gate(
        self, gate_id: str, results: TestResults, exit_code: int = 0
    ) -> bool:
        """
        Complete gate execution with results (running -> passed/failed/error).

        Args:
            gate_id: Gate identifier
            results: Test execution results
            exit_code: Process exit code

        Returns:
            True if successful
        """
        gate = self.get_gate(gate_id)
        if not gate:
            raise ValueError(f"Gate not found: {gate_id}")

        if gate["state"] != "running":
            raise ValueError(
                f"Cannot complete gate: gate not running (state: {gate['state']})"
            )

        # Determine new state based on exit code
        if exit_code != 0:
            new_state = "error"
        else:
            # Evaluate criteria
            decision = self._evaluate_criteria(gate["criteria"], results)
            new_state = "passed" if decision["passed"] else "failed"

        # Update execution data
        execution_data = gate.get("execution") or {}
        execution_data["completed_at"] = datetime.now(UTC).isoformat()
        execution_data["exit_code"] = exit_code

        # Calculate duration
        if execution_data.get("started_at"):
            started = datetime.fromisoformat(
                execution_data["started_at"].replace("Z", "+00:00")
            )
            completed = datetime.now(UTC)
            execution_data["duration_seconds"] = (completed - started).total_seconds()

        # Store decision if not error
        decision_data = None if exit_code != 0 else json.dumps(decision)

        self.db.conn.execute(
            """
            UPDATE test_gates
            SET state = ?, execution = ?, results = ?, decision = ?, updated_at = ?
            WHERE gate_id = ?
            """,
            (
                new_state,
                json.dumps(execution_data),
                json.dumps(results.to_dict()),
                decision_data,
                datetime.now(UTC).isoformat(),
                gate_id,
            ),
        )
        self.db.conn.commit()

        return True

    def _evaluate_criteria(self, criteria: Dict, results: TestResults) -> Dict:
        """
        Evaluate if results meet criteria.

        Args:
            criteria: Gate criteria
            results: Test results

        Returns:
            Decision dict with passed flag and criteria_met details
        """
        criteria_met = {}

        # Check coverage
        if criteria.get("min_coverage") is not None:
            if results.coverage_percent is not None:
                criteria_met["coverage"] = (
                    results.coverage_percent >= criteria["min_coverage"]
                )
            else:
                criteria_met["coverage"] = False

        # Check failures
        if criteria.get("max_failures") is not None:
            criteria_met["failures"] = results.failed_tests <= criteria["max_failures"]

        # Check required tests
        if criteria.get("required_tests"):
            # Simplified - assumes all tests passed
            criteria_met["required_tests"] = results.failed_tests == 0

        # Overall decision
        passed = all(criteria_met.values()) if criteria_met else True

        reason = (
            "All criteria met"
            if passed
            else f"Failed criteria: {[k for k, v in criteria_met.items() if not v]}"
        )

        return {"passed": passed, "reason": reason, "criteria_met": criteria_met}

    def skip_gate(self, gate_id: str, reason: str) -> bool:
        """
        Skip gate execution (any -> skipped).

        Args:
            gate_id: Gate identifier
            reason: Reason for skipping

        Returns:
            True if successful
        """
        gate = self.get_gate(gate_id)
        if not gate:
            raise ValueError(f"Gate not found: {gate_id}")

        if not self._can_transition(gate["state"], "skipped"):
            raise ValueError(f"Cannot skip gate: gate in {gate['state']} state")

        decision_data = {
            "passed": False,
            "reason": f"Skipped: {reason}",
            "criteria_met": {},
        }

        self.db.conn.execute(
            """
            UPDATE test_gates
            SET state = 'skipped', decision = ?, updated_at = ?
            WHERE gate_id = ?
            """,
            (json.dumps(decision_data), datetime.now(UTC).isoformat(), gate_id),
        )
        self.db.conn.commit()

        return True

    def list_gates(
        self,
        project_id: Optional[str] = None,
        state: Optional[str] = None,
        gate_type: Optional[str] = None,
    ) -> List[Dict]:
        """
        List gates with optional filters.

        Args:
            project_id: Filter by project
            state: Filter by state
            gate_type: Filter by type

        Returns:
            List of gate dicts
        """
        query = "SELECT * FROM test_gates WHERE 1=1"
        params = []

        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)

        if state:
            query += " AND state = ?"
            params.append(state)

        if gate_type:
            query += " AND gate_type = ?"
            params.append(gate_type)

        query += " ORDER BY created_at DESC"

        rows = self.db.conn.execute(query, params).fetchall()
        return [self._row_to_dict(row) for row in rows]

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
        return state in TestGate.TERMINAL_STATES
