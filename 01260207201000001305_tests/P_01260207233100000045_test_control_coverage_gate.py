#!/usr/bin/env python3
"""
Test Suite for G-CTRL-001 Control Coverage Gate

Tests all error codes and happy path scenarios per specification.
"""

import pytest
import json
import shutil
from pathlib import Path
from validators.validate_control_coverage import ControlCoverageValidator


@pytest.fixture
def temp_test_dir(tmp_path):
    """Create temporary test directory with fixture files"""
    test_dir = tmp_path / "test_fixtures"
    test_dir.mkdir()
    
    # Create minimal sections directory
    sections_dir = test_dir / "sections"
    sections_dir.mkdir()
    
    return test_dir


def create_sec_021(test_dir: Path, controls: dict):
    """Helper: Create SEC-021 with given controls"""
    sec_021 = {
        "section_id": "sec_021_quality_controls_catalog",
        "title": "Quality Controls Catalog",
        "required": True,
        "instructions_file": "sec_021_quality_controls_catalog.inst.md",
        "quality_controls_catalog": {
            "version": "1.0.0",
            "controls": controls
        }
    }
    
    path = test_dir / "sections" / "sec_021.json"
    with open(path, 'w') as f:
        json.dump(sec_021, f, indent=2)
    
    return path


def create_sec_012(test_dir: Path, gates: list):
    """Helper: Create SEC-012 with given gates"""
    sec_012 = {
        "section_id": "sec_012_validation_gates",
        "validation_gates": {
            "gates": gates
        }
    }
    
    path = test_dir / "sections" / "sec_012.json"
    with open(path, 'w') as f:
        json.dump(sec_012, f, indent=2)
    
    return path


def create_evidence_policy(test_dir: Path):
    """Helper: Create evidence_path_policy.json"""
    policy = {
        "path_formulas": {
            "gate": {
                "formula": "evidence/{plan_id}/{run_id}/gates/{gate_id}/"
            }
        }
    }
    
    policies_dir = test_dir / "policies"
    policies_dir.mkdir(exist_ok=True)
    path = policies_dir / "evidence_path_policy.json"
    with open(path, 'w') as f:
        json.dump(policy, f, indent=2)
    
    return path


def test_missing_satisfying_gate(temp_test_dir):
    """Test CTRL001_MISSING_SATISFYING_GATE error"""
    
    # Control required but no gate satisfies it
    controls = {
        "CTRL-TEST-001": {
            "control_id": "CTRL-TEST-001",
            "title": "Test Control",
            "required": True,
            "required_gates": ["GATE-TEST-001"],
            "required_artifacts": [],
            "test_requirements": {}
        }
    }
    
    gates = []  # No gates defined
    
    sec_021_path = create_sec_021(temp_test_dir, controls)
    sec_012_path = create_sec_012(temp_test_dir, gates)
    evidence_policy_path = create_evidence_policy(temp_test_dir)
    
    # Create dummy SEC-011 and SEC-016
    (temp_test_dir / "sections" / "sec_011.json").write_text('{"artifact_manifest":{"manifest_table":{"entries":[]}}}')
    (temp_test_dir / "sections" / "sec_016.json").write_text('{"testing_strategy":{}}')
    
    validator = ControlCoverageValidator(
        sec_021_path,
        sec_012_path,
        temp_test_dir / "sections" / "sec_011.json",
        temp_test_dir / "sections" / "sec_016.json",
        evidence_policy_path
    )
    
    report = validator.validate()
    
    assert report['all_required_controls_satisfied'] == False
    assert report['violated_controls_count'] == 1
    assert len(report['errors']) == 1
    assert report['errors'][0]['code'] == "CTRL001_MISSING_SATISFYING_GATE"
    assert report['errors'][0]['control_id'] == "CTRL-TEST-001"


def test_missing_evidence_mapping(temp_test_dir):
    """Test CTRL001_MISSING_EVIDENCE_MAPPING error"""
    
    controls = {
        "CTRL-TEST-001": {
            "control_id": "CTRL-TEST-001",
            "required": True,
            "required_gates": ["GATE-TEST-001"],
            "required_artifacts": [],
            "test_requirements": {}
        }
    }
    
    # Gate satisfies control but has no evidence_outputs
    gates = [
        {
            "gate_id": "GATE-TEST-001",
            "controls_satisfied": ["CTRL-TEST-001"]
            # Missing: evidence_outputs
        }
    ]
    
    sec_021_path = create_sec_021(temp_test_dir, controls)
    sec_012_path = create_sec_012(temp_test_dir, gates)
    evidence_policy_path = create_evidence_policy(temp_test_dir)
    
    (temp_test_dir / "sections" / "sec_011.json").write_text('{"artifact_manifest":{"manifest_table":{"entries":[]}}}')
    (temp_test_dir / "sections" / "sec_016.json").write_text('{"testing_strategy":{}}')
    
    validator = ControlCoverageValidator(
        sec_021_path,
        sec_012_path,
        temp_test_dir / "sections" / "sec_011.json",
        temp_test_dir / "sections" / "sec_016.json",
        evidence_policy_path
    )
    
    report = validator.validate()
    
    assert report['all_required_controls_satisfied'] == False
    assert len(report['errors']) == 1
    assert report['errors'][0]['code'] == "CTRL001_MISSING_EVIDENCE_MAPPING"


def test_nondeterministic_path(temp_test_dir):
    """Test CTRL001_NONDETERMINISTIC_PATH error"""
    
    controls = {
        "CTRL-TEST-001": {
            "control_id": "CTRL-TEST-001",
            "required": True,
            "required_gates": ["GATE-TEST-001"],
            "required_artifacts": [],
            "test_requirements": {}
        }
    }
    
    # Gate has evidence_outputs but path is not deterministic
    gates = [
        {
            "gate_id": "GATE-TEST-001",
            "controls_satisfied": ["CTRL-TEST-001"],
            "evidence_outputs": ["/tmp/random_path.log"]  # Nondeterministic
        }
    ]
    
    sec_021_path = create_sec_021(temp_test_dir, controls)
    sec_012_path = create_sec_012(temp_test_dir, gates)
    evidence_policy_path = create_evidence_policy(temp_test_dir)
    
    (temp_test_dir / "sections" / "sec_011.json").write_text('{"artifact_manifest":{"manifest_table":{"entries":[]}}}')
    (temp_test_dir / "sections" / "sec_016.json").write_text('{"testing_strategy":{}}')
    
    validator = ControlCoverageValidator(
        sec_021_path,
        sec_012_path,
        temp_test_dir / "sections" / "sec_011.json",
        temp_test_dir / "sections" / "sec_016.json",
        evidence_policy_path
    )
    
    report = validator.validate()
    
    assert report['all_required_controls_satisfied'] == False
    assert len(report['errors']) == 1
    assert report['errors'][0]['code'] == "CTRL001_NONDETERMINISTIC_PATH"


def test_all_controls_satisfied(temp_test_dir):
    """Test happy path: all controls satisfied"""
    
    controls = {
        "CTRL-TEST-001": {
            "control_id": "CTRL-TEST-001",
            "required": True,
            "required_gates": ["GATE-TEST-001"],
            "required_artifacts": [],
            "test_requirements": {}
        }
    }
    
    # Gate properly satisfies control with deterministic evidence
    gates = [
        {
            "gate_id": "GATE-TEST-001",
            "controls_satisfied": ["CTRL-TEST-001"],
            "evidence_outputs": [".state/evidence/PH-01/test.log"]  # Deterministic pattern
        }
    ]
    
    sec_021_path = create_sec_021(temp_test_dir, controls)
    sec_012_path = create_sec_012(temp_test_dir, gates)
    evidence_policy_path = create_evidence_policy(temp_test_dir)
    
    (temp_test_dir / "sections" / "sec_011.json").write_text('{"artifact_manifest":{"manifest_table":{"entries":[]}}}')
    (temp_test_dir / "sections" / "sec_016.json").write_text('{"testing_strategy":{}}')
    
    validator = ControlCoverageValidator(
        sec_021_path,
        sec_012_path,
        temp_test_dir / "sections" / "sec_011.json",
        temp_test_dir / "sections" / "sec_016.json",
        evidence_policy_path
    )
    
    report = validator.validate()
    
    assert report['all_required_controls_satisfied'] == True
    assert report['satisfied_controls_count'] == 1
    assert report['violated_controls_count'] == 0
    assert len(report['errors']) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
