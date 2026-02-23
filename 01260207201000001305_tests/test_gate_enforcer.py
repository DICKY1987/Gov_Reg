"""
Unit tests for GateEnforcer - Phase D

Tests gate enforcement, checker registration, and evidence generation.

FILE_ID: 01999000042260125149
"""

import pytest
import json
import sys
import tempfile
from pathlib import Path

# Add govreg_core to path
sys.path.insert(0, str(Path(__file__).parent.parent / "01260207201000001173_govreg_core"))

from P_01999000042260125143_gate_enforcer import GateEnforcer, GateResult
from P_01999000042260125141_telemetry_emitter import TelemetryEmitter


@pytest.fixture
def gate_catalog():
    """Create temporary gate catalog."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        catalog = {
            "gates": [
                {
                    "gate_id": "TEST-G1",
                    "phase": "pre_execution",
                    "severity": "BLOCK",
                    "description": "Test gate 1"
                },
                {
                    "gate_id": "TEST-G2",
                    "phase": "post_execution",
                    "severity": "WARN",
                    "description": "Test gate 2"
                }
            ]
        }
        json.dump(catalog, f)
        path = Path(f.name)
    
    yield path
    path.unlink()


def test_gate_enforcer_register_checker(gate_catalog):
    """Test checker registration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        telemetry = TelemetryEmitter(fallback_dir=Path(tmpdir))
        enforcer = GateEnforcer(gate_catalog, telemetry)
        
        def mock_checker(context):
            return GateResult(
                gate_id="TEST-G1",
                passed=True,
                severity="info",
                violations=[]
            )
        
        enforcer.register_checker("TEST-G1", mock_checker)
        
        assert "TEST-G1" in enforcer.checkers


def test_gate_enforcer_single_gate_pass(gate_catalog):
    """Test enforcing single gate that passes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        telemetry = TelemetryEmitter(fallback_dir=Path(tmpdir))
        enforcer = GateEnforcer(gate_catalog, telemetry)
        
        def passing_checker(context):
            return GateResult(
                gate_id="TEST-G1",
                passed=True,
                severity="info",
                violations=[]
            )
        
        enforcer.register_checker("TEST-G1", passing_checker)
        result = enforcer.enforce_single_gate("TEST-G1", {})
        
        assert result.passed == True
        assert result.gate_id == "TEST-G1"


def test_gate_enforcer_single_gate_fail(gate_catalog):
    """Test enforcing single gate that fails."""
    with tempfile.TemporaryDirectory() as tmpdir:
        telemetry = TelemetryEmitter(fallback_dir=Path(tmpdir))
        enforcer = GateEnforcer(gate_catalog, telemetry)
        
        def failing_checker(context):
            return GateResult(
                gate_id="TEST-G1",
                passed=False,
                severity="error",
                violations=[{"issue": "test violation"}]
            )
        
        enforcer.register_checker("TEST-G1", failing_checker)
        result = enforcer.enforce_single_gate("TEST-G1", {})
        
        assert result.passed == False
        assert len(result.violations) == 1


def test_gate_enforcer_telemetry_emission(gate_catalog):
    """Test that gate results emit telemetry."""
    with tempfile.TemporaryDirectory() as tmpdir:
        telemetry = TelemetryEmitter(fallback_dir=Path(tmpdir))
        enforcer = GateEnforcer(gate_catalog, telemetry)
        
        def checker(context):
            return GateResult(
                gate_id="TEST-G1",
                passed=False,
                severity="error",
                violations=[{"issue": "test"}]
            )
        
        enforcer.register_checker("TEST-G1", checker)
        enforcer.enforce_single_gate("TEST-G1", {})
        
        # Check telemetry was written
        telemetry_path = Path(tmpdir) / "events.jsonl"
        assert telemetry_path.exists()
        
        with open(telemetry_path) as f:
            events = [json.loads(line) for line in f]
        
        assert len(events) == 1
        assert events[0]["event_type"] == "gate_result"


def test_gate_enforcer_pre_execution_gates(gate_catalog):
    """Test enforcing pre-execution gates."""
    with tempfile.TemporaryDirectory() as tmpdir:
        telemetry = TelemetryEmitter(fallback_dir=Path(tmpdir))
        enforcer = GateEnforcer(gate_catalog, telemetry)
        
        def checker(context):
            return GateResult(
                gate_id="TEST-G1",
                passed=True,
                severity="info",
                violations=[]
            )
        
        enforcer.register_checker("TEST-G1", checker)
        all_passed, results = enforcer.enforce_pre_execution_gates({})
        
        assert all_passed == True
        assert len(results) == 1


def test_gate_enforcer_block_severity_fails(gate_catalog):
    """Test BLOCK severity gate failure prevents execution."""
    with tempfile.TemporaryDirectory() as tmpdir:
        telemetry = TelemetryEmitter(fallback_dir=Path(tmpdir))
        enforcer = GateEnforcer(gate_catalog, telemetry)
        
        def failing_checker(context):
            return GateResult(
                gate_id="TEST-G1",
                passed=False,
                severity="error",
                violations=[{"issue": "blocking issue"}]
            )
        
        enforcer.register_checker("TEST-G1", failing_checker)
        all_passed, results = enforcer.enforce_pre_execution_gates({})
        
        # BLOCK severity + failed = should not pass
        assert all_passed == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
