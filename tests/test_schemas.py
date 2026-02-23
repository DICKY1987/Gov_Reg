"""
Schema Validation Tests
"""
import pytest
import json
import jsonschema
from pathlib import Path


SCHEMA_DIR = Path(__file__).parent.parent / "schemas"


def test_all_schemas_valid_json():
    """All schema files should be valid JSON"""
    for schema_file in SCHEMA_DIR.glob("*.json"):
        with open(schema_file, 'r') as f:
            data = json.load(f)
        assert isinstance(data, dict)
        assert "$schema" in data or schema_file.name == "baseline_planning_policy.json"


def test_plan_schema_structure():
    """PLAN.schema.json should have correct structure"""
    with open(SCHEMA_DIR / "PLAN.schema.json", 'r') as f:
        schema = json.load(f)
    
    assert schema["type"] == "object"
    assert len(schema["required"]) == 14
    assert "plan_id" in schema["required"]
    assert "version" in schema["required"]
    assert "workstreams" in schema["required"]
    assert "declared_new_artifacts" in schema["required"]


def test_critic_report_schema_structure():
    """CRITIC_REPORT.schema.json should have correct structure"""
    with open(SCHEMA_DIR / "CRITIC_REPORT.schema.json", 'r') as f:
        schema = json.load(f)
    
    assert schema["type"] == "object"
    assert "hard_defects" in schema["required"]
    assert "soft_defects" in schema["required"]
    assert "summary" in schema["required"]


def test_patch_schema_rfc6902_compliance():
    """PATCH.schema.json should support RFC-6902 operations"""
    with open(SCHEMA_DIR / "PATCH.schema.json", 'r') as f:
        schema = json.load(f)
    
    ops_enum = schema["properties"]["operations"]["items"]["properties"]["op"]["enum"]
    rfc6902_ops = ["add", "remove", "replace", "move", "copy", "test"]
    
    for op in rfc6902_ops:
        assert op in ops_enum


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
