# DOC_LINK: DOC-TEST-ORCHESTRATOR-INTEGRATION-008
"""Integration tests for Orchestrator

Tests end-to-end orchestrator flow with mocked components.

DOC_ID: DOC-TEST-ORCHESTRATOR-INTEGRATION-008
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from RUNTIME.doc_id.SUB_DOC_ID.orchestrator.orchestrator import (
    Orchestrator,
    Context
)
from RUNTIME.doc_id.SUB_DOC_ID.orchestrator.state.state_machine import State


class TestOrchestratorIntegration:
    """Integration tests for Orchestrator"""

    def test_orchestrator_initialization(self):
        """Test orchestrator initializes correctly"""
        with TemporaryDirectory() as tmpdir:
            context = Context(
                name='test',
                mode='safe_only',
                repo_root=Path(tmpdir)
            )

            orch = Orchestrator(context)

            assert orch.context.name == 'test'
            assert orch.state.current_state == State.INITIAL
            assert orch.run_dir.exists()
            assert orch.rollback_mgr is not None

    def test_orchestrator_no_changes_path(self):
        """Test orchestrator with no changes detected"""
        with TemporaryDirectory() as tmpdir:
            context = Context(
                name='test',
                mode='safe_only',
                repo_root=Path(tmpdir)
            )

            orch = Orchestrator(context)

            # Mock detect_changes to return empty list
            orch.detect_changes = lambda: []

            # Run orchestrator
            exit_code = orch.run()

            # Should succeed with no changes
            assert exit_code == 0
            assert orch.state.current_state == State.SUCCESS

            # State should have transitioned: INITIAL -> DETECTING -> SUCCESS
            assert len(orch.state.transitions) == 2
            assert orch.state.transitions[0].to_state == State.DETECTING
            assert orch.state.transitions[1].to_state == State.SUCCESS

    def test_orchestrator_state_persistence(self):
        """Test state is persisted to run directory"""
        with TemporaryDirectory() as tmpdir:
            context = Context(
                name='test',
                mode='safe_only',
                repo_root=Path(tmpdir)
            )

            orch = Orchestrator(context)
            orch.detect_changes = lambda: []

            orch.run()

            # Verify state.json was created
            state_file = orch.run_dir / 'state.json'
            assert state_file.exists()

            # Verify content
            import json
            with open(state_file, 'r') as f:
                state_data = json.load(f)

            assert state_data['current_state'] == 'SUCCESS'
            assert state_data['context'] == 'test'
            assert len(state_data['transitions']) >= 2

    def test_orchestrator_evidence_tracking(self):
        """Test orchestrator tracks evidence files"""
        with TemporaryDirectory() as tmpdir:
            context = Context(
                name='test',
                mode='safe_only',
                repo_root=Path(tmpdir)
            )

            orch = Orchestrator(context)

            # Mock to return empty changes
            orch.detect_changes = lambda: []

            orch.run()

            # Should have tracked changes.json as evidence
            assert 'changes.json' in orch.state.evidence_files

    def test_orchestrator_snapshot_creation(self):
        """Test orchestrator creates snapshot before remediation"""
        with TemporaryDirectory() as tmpdir:
            context = Context(
                name='test',
                mode='safe_only',
                repo_root=Path(tmpdir)
            )

            orch = Orchestrator(context)

            # Mock components to simulate normal workflow
            orch.detect_changes = lambda: [{'type': 'FILE_ADDED', 'path': 'test.txt'}]
            orch.classify_entities = lambda changes: [{'type': 'DOC', 'path': 'test.txt'}]
            orch.resolve_identities = lambda entities: [{'action': 'MINT', 'id': 'DOC-TEST-001'}]
            orch.apply_remediations = lambda resolutions: True
            orch.run_validators = lambda: [{'status': 'pass'}]

            orch.run()

            # Snapshot should have been created and committed
            snapshots_dir = orch.rollback_mgr.snapshot_dir
            # After success, snapshot should be removed (committed)
            assert len(list(snapshots_dir.iterdir())) == 0

    def test_orchestrator_success_path(self):
        """Test complete successful orchestrator execution"""
        with TemporaryDirectory() as tmpdir:
            context = Context(
                name='test',
                mode='safe_only',
                repo_root=Path(tmpdir)
            )

            orch = Orchestrator(context)

            # Mock all components for success path
            orch.detect_changes = lambda: [{'type': 'FILE_ADDED'}]
            orch.classify_entities = lambda changes: [{'type': 'DOC'}]
            orch.resolve_identities = lambda entities: [{'action': 'MINT'}]
            orch.apply_remediations = lambda resolutions: True
            orch.run_validators = lambda: [{'status': 'pass'}]
            orch.aggregate_gate = lambda reports: {'status': 'pass'}

            exit_code = orch.run()

            assert exit_code == 0
            assert orch.state.current_state == State.SUCCESS

            # Verify complete workflow
            states = [t.to_state for t in orch.state.transitions]
            assert State.DETECTING in states
            assert State.CLASSIFYING in states
            assert State.RESOLVING in states
            assert State.REMEDIATING in states
            assert State.VALIDATING in states
            assert State.AGGREGATING in states
            assert State.GATE_DECISION in states
            assert State.COMMIT in states
            assert State.SUCCESS in states

    def test_orchestrator_manual_intervention_path(self):
        """Test orchestrator handles manual intervention required"""
        with TemporaryDirectory() as tmpdir:
            context = Context(
                name='test',
                mode='safe_only',
                repo_root=Path(tmpdir)
            )

            orch = Orchestrator(context)

            # Mock to require manual intervention
            orch.detect_changes = lambda: [{'type': 'FILE_RENAMED'}]
            orch.classify_entities = lambda changes: [{'type': 'DOC'}]
            orch.resolve_identities = lambda entities: [
                {'action': 'AMBIGUOUS', 'requires_manual': True}
            ]

            exit_code = orch.run()

            assert exit_code == 1
            assert orch.state.current_state == State.MANUAL_REQUIRED

    def test_orchestrator_validation_failure_rollback(self):
        """Test orchestrator rolls back on validation failure"""
        with TemporaryDirectory() as tmpdir:
            context = Context(
                name='test',
                mode='safe_only',
                repo_root=Path(tmpdir)
            )

            orch = Orchestrator(context)

            # Mock to fail at validation
            orch.detect_changes = lambda: [{'type': 'FILE_ADDED'}]
            orch.classify_entities = lambda changes: [{'type': 'DOC'}]
            orch.resolve_identities = lambda entities: [{'action': 'MINT'}]
            orch.apply_remediations = lambda resolutions: True
            orch.run_validators = lambda: [{'status': 'fail'}]

            # Create a test file to verify rollback
            test_file = Path(tmpdir) / 'test.txt'
            test_file.write_text('original')

            exit_code = orch.run()

            assert exit_code == 1
            # Should end in FAILED after ROLLBACK
            assert orch.state.current_state == State.FAILED

            # Verify rollback transition occurred
            states = [t.to_state for t in orch.state.transitions]
            assert State.ROLLBACK in states

    def test_orchestrator_gate_failure_path(self):
        """Test orchestrator handles gate failure"""
        with TemporaryDirectory() as tmpdir:
            context = Context(
                name='test',
                mode='safe_only',
                repo_root=Path(tmpdir)
            )

            orch = Orchestrator(context)

            # Mock to fail at gate
            orch.detect_changes = lambda: [{'type': 'FILE_ADDED'}]
            orch.classify_entities = lambda changes: [{'type': 'DOC'}]
            orch.resolve_identities = lambda entities: [{'action': 'MINT'}]
            orch.apply_remediations = lambda resolutions: True
            orch.run_validators = lambda: [{'status': 'pass'}]
            orch.aggregate_gate = lambda reports: {'status': 'fail'}

            exit_code = orch.run()

            assert exit_code == 1
            assert orch.state.current_state == State.FAILED

            # Verify workflow went through BLOCK
            states = [t.to_state for t in orch.state.transitions]
            assert State.GATE_DECISION in states
            assert State.BLOCK in states
            assert State.FAILED in states

    def test_orchestrator_exception_handling(self):
        """Test orchestrator handles exceptions gracefully"""
        with TemporaryDirectory() as tmpdir:
            context = Context(
                name='test',
                mode='safe_only',
                repo_root=Path(tmpdir)
            )

            orch = Orchestrator(context)

            # Mock to raise exception
            def raise_error():
                raise RuntimeError("Simulated error")

            orch.detect_changes = raise_error

            exit_code = orch.run()

            assert exit_code == 1
            # Should have attempted rollback
            states = [t.to_state for t in orch.state.transitions]
            assert State.ROLLBACK in states


__doc_id__ = 'DOC-TEST-ORCHESTRATOR-INTEGRATION-008'
