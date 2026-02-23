#!/usr/bin/env python3
"""
Tests for validate_command_spec.py validator

Comprehensive tests to achieve >= 90% coverage
"""

import pytest
import json
from pathlib import Path
from validators.validate_command_spec import check_command_field, validate_section_file


@pytest.fixture
def temp_test_dir(tmp_path):
    """Create temporary test directory"""
    test_dir = tmp_path / "test_command_spec"
    test_dir.mkdir()
    return test_dir


def test_check_command_field_string_command():
    """Test detection of string command"""
    data = {"command": "python script.py"}
    violations = []
    
    check_command_field(data, "", violations)
    
    assert len(violations) == 1
    assert violations[0]['type'] == 'free_form_command'


def test_check_command_field_structured_command():
    """Test valid structured command"""
    data = {"command": {"exe": "python", "args": ["script.py"]}}
    violations = []
    
    check_command_field(data, "", violations)
    
    assert len(violations) == 0


def test_check_command_field_incomplete_command():
    """Test incomplete command spec"""
    data = {"command": {"exe": "python"}}  # Missing args
    violations = []
    
    check_command_field(data, "", violations)
    
    assert len(violations) == 1
    assert violations[0]['type'] == 'incomplete_command_spec'


def test_check_command_field_invalid_args_type():
    """Test invalid args type"""
    data = {"command": {"exe": "python", "args": "not_an_array"}}
    violations = []
    
    check_command_field(data, "", violations)
    
    assert len(violations) == 1
    assert violations[0]['type'] == 'invalid_args_type'


def test_check_command_field_nested():
    """Test nested command detection"""
    data = {
        "gates": [
            {"gate_id": "G1", "command": "python test.py"},
            {"gate_id": "G2", "command": {"exe": "python", "args": ["test2.py"]}}
        ]
    }
    violations = []
    
    check_command_field(data, "", violations)
    
    assert len(violations) == 1  # Only first gate has violation


def test_validate_section_file_valid(temp_test_dir):
    """Test validation of section with valid commands"""
    section = {
        "section_id": "test",
        "gates": [
            {"command": {"exe": "python", "args": ["test.py"]}}
        ]
    }
    
    path = temp_test_dir / "valid.json"
    with open(path, 'w') as f:
        json.dump(section, f)
    
    is_valid, violations = validate_section_file(path)
    
    assert is_valid == True
    assert len(violations) == 0


def test_validate_section_file_violations(temp_test_dir):
    """Test validation of section with violations"""
    section = {
        "section_id": "test",
        "gates": [
            {"command": "python test.py"}  # String command
        ]
    }
    
    path = temp_test_dir / "violations.json"
    with open(path, 'w') as f:
        json.dump(section, f)
    
    is_valid, violations = validate_section_file(path)
    
    assert is_valid == False
    assert len(violations) == 1


def test_validate_section_file_invalid_json(temp_test_dir):
    """Test handling of invalid JSON"""
    path = temp_test_dir / "invalid.json"
    with open(path, 'w') as f:
        f.write("{ invalid json }")
    
    is_valid, violations = validate_section_file(path)
    
    assert is_valid == False
    assert len(violations) > 0
    assert violations[0]['type'] == 'json_parse_error'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
