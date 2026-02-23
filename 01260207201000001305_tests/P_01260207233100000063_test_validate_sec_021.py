#!/usr/bin/env python3
"""
Tests for validate_sec_021.py validator

Comprehensive tests to achieve >= 90% coverage
"""

import pytest
import json
from pathlib import Path
from validators.validate_sec_021 import validate_sec_021_file


@pytest.fixture
def temp_test_dir(tmp_path):
    """Create temporary test directory"""
    test_dir = tmp_path / "test_sec_021"
    test_dir.mkdir()
    return test_dir


def create_valid_sec_021(test_dir: Path) -> Path:
    """Create a minimal valid SEC-021 file"""
    sec_021 = {
        "section_id": "sec_021_quality_controls_catalog",
        "title": "Quality Controls Catalog",
        "required": True,
        "instructions_file": "sec_021_quality_controls_catalog.inst.md",
        "quality_controls_catalog": {
            "version": "1.0.0",
            "controls": [
                {
                    "control_id": "CTRL-TEST-001",
                    "title": "Test Control",
                    "control_class": "security",
                    "required": True,
                    "intent": "Test intent",
                    "required_gates": ["GATE-001"],
                    "evidence_requirements": {
                        "type": "command_output",
                        "output_path_pattern": ".state/evidence/test/"
                    },
                    "required_artifacts": [],
                    "test_requirements": {},
                    "tools": ["pytest"]
                }
            ]
        }
    }
    
    path = test_dir / "sec_021_valid.json"
    with open(path, 'w') as f:
        json.dump(sec_021, f, indent=2)
    
    return path


def test_valid_sec_021(temp_test_dir):
    """Test validation of a valid SEC-021 file"""
    sec_path = create_valid_sec_021(temp_test_dir)
    
    result = validate_sec_021_file(sec_path)
    
    assert result['control_id_uniqueness'] == True
    assert result['all_required_fields_present'] == True
    assert result['status'] == 'pass'


def test_duplicate_control_ids(temp_test_dir):
    """Test detection of duplicate control IDs"""
    sec_021 = {
        "section_id": "sec_021_quality_controls_catalog",
        "title": "Quality Controls Catalog",
        "required": True,
        "instructions_file": "sec_021.inst.md",
        "quality_controls_catalog": {
            "version": "1.0.0",
            "controls": [
                {
                    "control_id": "CTRL-DUPLICATE",
                    "title": "Control 1",
                    "control_class": "security",
                    "required": False,
                    "intent": "Test",
                    "required_gates": [],
                    "evidence_requirements": {},
                    "required_artifacts": [],
                    "test_requirements": {},
                    "tools": []
                },
                {
                    "control_id": "CTRL-DUPLICATE",
                    "title": "Control 2",
                    "control_class": "testing",
                    "required": False,
                    "intent": "Test",
                    "required_gates": [],
                    "evidence_requirements": {},
                    "required_artifacts": [],
                    "test_requirements": {},
                    "tools": []
                }
            ]
        }
    }
    
    path = temp_test_dir / "sec_021_duplicate.json"
    with open(path, 'w') as f:
        json.dump(sec_021, f)
    
    result = validate_sec_021_file(path)
    
    assert result['control_id_uniqueness'] == False
    assert result['status'] == 'fail'
    assert 'duplicate_control_ids' in result


def test_missing_required_fields(temp_test_dir):
    """Test detection of missing required fields"""
    sec_021 = {
        "section_id": "sec_021_quality_controls_catalog",
        "title": "Quality Controls Catalog",
        "required": True,
        "instructions_file": "sec_021.inst.md",
        "quality_controls_catalog": {
            "version": "1.0.0",
            "controls": [
                {
                    "control_id": "CTRL-INCOMPLETE",
                    "title": "Incomplete Control"
                    # Missing required fields: control_class, required, intent, etc.
                }
            ]
        }
    }
    
    path = temp_test_dir / "sec_021_incomplete.json"
    with open(path, 'w') as f:
        json.dump(sec_021, f)
    
    result = validate_sec_021_file(path)
    
    assert result['all_required_fields_present'] == False
    assert result['status'] == 'fail'


def test_invalid_json(temp_test_dir):
    """Test handling of invalid JSON"""
    path = temp_test_dir / "sec_021_invalid.json"
    with open(path, 'w') as f:
        f.write("{ invalid json }")
    
    result = validate_sec_021_file(path)
    
    assert result['status'] == 'error'
    assert 'error' in result


def test_evidence_paths_deterministic(temp_test_dir):
    """Test evidence path determinism check"""
    sec_021 = {
        "section_id": "sec_021_quality_controls_catalog",
        "title": "Quality Controls Catalog",
        "required": True,
        "instructions_file": "sec_021.inst.md",
        "quality_controls_catalog": {
            "version": "1.0.0",
            "controls": [
                {
                    "control_id": "CTRL-TEST-001",
                    "title": "Test",
                    "control_class": "security",
                    "required": True,
                    "intent": "Test",
                    "required_gates": [],
                    "evidence_requirements": {
                        "type": "command_output",
                        "output_path_pattern": ".state/evidence/{phase}/test/"
                    },
                    "required_artifacts": [],
                    "test_requirements": {},
                    "tools": []
                }
            ]
        }
    }
    
    path = temp_test_dir / "sec_021_deterministic.json"
    with open(path, 'w') as f:
        json.dump(sec_021, f)
    
    result = validate_sec_021_file(path)
    
    assert result['status'] == 'pass'


def test_empty_controls_array(temp_test_dir):
    """Test empty controls array"""
    sec_021 = {
        "section_id": "sec_021_quality_controls_catalog",
        "title": "Quality Controls Catalog",
        "required": True,
        "instructions_file": "sec_021.inst.md",
        "quality_controls_catalog": {
            "version": "1.0.0",
            "controls": []
        }
    }
    
    path = temp_test_dir / "sec_021_empty.json"
    with open(path, 'w') as f:
        json.dump(sec_021, f)
    
    result = validate_sec_021_file(path)
    
    assert result['status'] == 'pass'
    assert result['control_count'] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
