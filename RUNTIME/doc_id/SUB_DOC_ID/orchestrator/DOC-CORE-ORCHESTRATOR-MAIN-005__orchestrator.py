# DOC_LINK: DOC-CORE-ORCHESTRATOR-MAIN-005
"""ID System Orchestrator

Master orchestration engine implementing the automation architecture
from DOC-GUIDE-PROCESS-FLOW-AND-AUTOMATION-LOGIC-638 Section 9.1.

DOC_ID: DOC-CORE-ORCHESTRATOR-MAIN-005
"""

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .state.state_machine import State, StateMachine
from .state.rollback_manager import RollbackManager


@dataclass
class Context:
    """Execution context"""
    name: str  # 'pre-commit', 'ci', 'watcher', 'manual'
    mode: str  # 'safe_only', 'conditional', 'all', 'dry_run'
    files: Optional[List[str]] = None
    full_validation: bool = False
    repo_root: Optional[Path] = None


class Orchestrator:
    """Central orchestration engine for ID system automation

    Coordinates:
    - Change detection
    - Entity classification
    - Identity resolution
    - Remediation application
    - Validation execution
    - Gate aggregation

    State machine ensures deterministic execution paths.
    Rollback manager provides atomic operations.
    """

    def __init__(self, context: Context):
        """Initialize orchestrator

        Args:
            context: Execution context
        """
        self.context = context
        self.repo_root = context.repo_root or Path.cwd()
        self.run_dir = self.repo_root / 'run' / 'id_automation' / context.name
        self.run_dir.mkdir(parents=True, exist_ok=True)

        # Initialize state machine
        self.state = StateMachine(
            current_state=State.INITIAL,
            context=context.name
        )

        # Initialize rollback manager
        self.rollback_mgr = RollbackManager(repo_root=self.repo_root)

    def run(self) -> int:
        """Main execution flow

        Returns:
            Exit code: 0=success, 1=failure
        """
        try:
            # === PHASE 1: DETECTING ===
            self.state.transition(State.DETECTING, reason="Starting change detection")
            self.state.save(self.run_dir)

            changes = self.detect_changes()
            self.state.add_evidence('changes.json')

            if not changes:
                print("No changes detected")
                self.state.transition(State.SUCCESS, reason="No changes to process")
                self.state.save(self.run_dir)
                return 0

            # === PHASE 2: CLASSIFYING ===
            self.state.transition(State.CLASSIFYING, reason="Classifying entities")
            self.state.save(self.run_dir)

            entities = self.classify_entities(changes)
            self.state.add_evidence('entities.json')

            # === PHASE 3: RESOLVING ===
            self.state.transition(State.RESOLVING, reason="Resolving identities")
            self.state.save(self.run_dir)

            resolutions = self.resolve_identities(entities)
            self.state.add_evidence('resolutions.json')

            # Check for manual intervention required
            if any(r.get('requires_manual') for r in resolutions):
                self.state.transition(State.MANUAL_REQUIRED, reason="Ambiguous identities detected")
                self.state.save(self.run_dir)
                self.generate_override_template(resolutions)
                return 1

            # === PHASE 4: REMEDIATING (with snapshot) ===
            snapshot_id = self.rollback_mgr.create_snapshot(self.context.name)
            print(f"Created snapshot: {snapshot_id}")

            # Snapshot registries before modification
            self.rollback_mgr.snapshot_registries()

            self.state.transition(State.REMEDIATING, reason="Applying remediations")
            self.state.save(self.run_dir)

            success = self.apply_remediations(resolutions)
            self.state.add_evidence('remediations.json')

            if not success:
                self.state.transition(State.ROLLBACK, reason="Remediation failed")
                self.state.save(self.run_dir)
                self.rollback_mgr.rollback()
                return 1

            # === PHASE 5: VALIDATING ===
            self.state.transition(State.VALIDATING, reason="Running validators")
            self.state.save(self.run_dir)

            reports = self.run_validators()

            # Check if all validators passed
            all_passed = all(r.get('status') == 'pass' for r in reports)

            if not all_passed:
                self.state.transition(State.ROLLBACK, reason="Validation failed")
                self.state.save(self.run_dir)
                self.rollback_mgr.rollback()
                return 1

            # === PHASE 6: AGGREGATING ===
            self.state.transition(State.AGGREGATING, reason="Aggregating gate results")
            self.state.save(self.run_dir)

            gate = self.aggregate_gate(reports)
            self.state.add_evidence('gate.json')

            # === PHASE 7: GATE DECISION ===
            self.state.transition(State.GATE_DECISION, reason="Making gate decision")
            self.state.save(self.run_dir)

            if gate.get('status') == 'pass':
                self.state.transition(State.COMMIT, reason="Gate passed")
                self.state.save(self.run_dir)

                # Commit snapshot (success)
                self.rollback_mgr.commit_snapshot()

                self.state.transition(State.SUCCESS, reason="Completed successfully")
                self.state.save(self.run_dir)

                print("✓ Orchestration completed successfully")
                return 0
            else:
                self.state.transition(State.BLOCK, reason="Gate failed")
                self.state.save(self.run_dir)

                self.display_violations(gate)
                self.rollback_mgr.rollback()

                self.state.transition(State.FAILED, reason="Gate blocked commit")
                self.state.save(self.run_dir)

                print("✗ Orchestration failed - gate blocked")
                return 1

        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()

            self.state.transition(State.ROLLBACK, reason=f"Exception: {e}")
            self.state.save(self.run_dir)

            if self.rollback_mgr.current_snapshot:
                self.rollback_mgr.rollback()

            return 1

    def detect_changes(self) -> List[dict]:
        """Detect changes based on context

        Returns:
            List of change objects
        """
        # TODO: Implement ChangeDetector
        # For now, return mock data
        print("  Detecting changes...")
        return []

    def classify_entities(self, changes: List[dict]) -> List[dict]:
        """Classify changes into entities

        Args:
            changes: List of detected changes

        Returns:
            List of classified entities
        """
        # TODO: Implement EntityClassifier
        print("  Classifying entities...")
        return []

    def resolve_identities(self, entities: List[dict]) -> List[dict]:
        """Resolve entity identities

        Args:
            entities: List of classified entities

        Returns:
            List of identity resolutions
        """
        # TODO: Implement IdentityResolver
        print("  Resolving identities...")
        return []

    def apply_remediations(self, resolutions: List[dict]) -> bool:
        """Apply remediations atomically

        Args:
            resolutions: List of identity resolutions

        Returns:
            True if all remediations succeeded
        """
        # TODO: Implement RemediationEngine
        print("  Applying remediations...")
        return True

    def run_validators(self) -> List[dict]:
        """Run all applicable validators

        Returns:
            List of validation reports
        """
        # TODO: Implement ValidatorRunner
        print("  Running validators...")
        return [{'status': 'pass', 'validator_id': 'mock'}]

    def aggregate_gate(self, reports: List[dict]) -> dict:
        """Aggregate validation reports

        Args:
            reports: List of validation reports

        Returns:
            Gate result
        """
        # TODO: Implement GateAggregator
        print("  Aggregating gate...")

        all_pass = all(r.get('status') == 'pass' for r in reports)

        return {
            'status': 'pass' if all_pass else 'fail',
            'total_reports': len(reports),
            'passed': sum(1 for r in reports if r.get('status') == 'pass'),
            'failed': sum(1 for r in reports if r.get('status') == 'fail'),
        }

    def generate_override_template(self, resolutions: List[dict]):
        """Generate manual override template

        Args:
            resolutions: List of resolutions with ambiguities
        """
        print("Manual intervention required - see .id_overrides.json")
        # TODO: Generate actual template

    def display_violations(self, gate: dict):
        """Display gate violations

        Args:
            gate: Gate result
        """
        print(f"\n✗ Gate FAILED")
        print(f"  Passed: {gate.get('passed', 0)}")
        print(f"  Failed: {gate.get('failed', 0)}")


__doc_id__ = 'DOC-CORE-ORCHESTRATOR-MAIN-005'
