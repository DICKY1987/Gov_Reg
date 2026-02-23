#!/usr/bin/env python3
"""
Schema validation tests for doc_id removal.
"""

import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")


def test_schema_rejects_doc_id():
    """Ensure FileRecord rejects doc_id field."""
    repo_root = Path(__file__).parent.parent
    schema_path = repo_root / "REGISTRY" / "01999000042260124012_governance_registry_schema.v3.json"

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    file_record_schema = schema["definitions"]["FileRecord"]

    valid_record = {
        "file_id": "12345678901234567890",
        "relative_path": "test.py",
        "repo_root_id": "AI_PROD_PIPELINE",
        "governance_domain": "SRC",
        "artifact_kind": "PYTHON_MODULE",
        "layer": "CORE",
        "canonicality": "CANONICAL",
        "has_tests": False,
    }

    invalid_record = dict(valid_record)
    invalid_record["doc_id"] = "1234567890123456"

    jsonschema.validate(instance=valid_record, schema=file_record_schema)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=invalid_record, schema=file_record_schema)
