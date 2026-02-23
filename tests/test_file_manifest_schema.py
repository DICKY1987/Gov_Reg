"""
File Manifest Schema Tests
"""
import json
from pathlib import Path

import jsonschema


SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "file_manifest_schema_v1.json"


def load_schema() -> dict:
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_manifest(data: dict) -> list:
    validator = jsonschema.Draft7Validator(load_schema())
    return list(validator.iter_errors(data))


def minimal_manifest() -> dict:
    return {
        "manifest_metadata": {
            "schema_version": "1.0.0",
            "scan_timestamp": "2026-02-21T21:12:00Z",
            "scanner_version": "1.0.0",
            "root_path": "C:\\Users\\richg\\Gov_Reg",
            "scan_host": "TEST_HOST",
            "collision_handling": "error",
        },
        "files": {
            "FID_001": {
                "file_id": "FID_001",
                "relative_path": "examples/sample.txt",
                "filename": "sample.txt",
                "derivation_method": "auto",
                "file_size_bytes": 12,
                "file_type": "text/plain",
                "modified_timestamp": 1700000000.0,
            }
        },
    }


def test_minimal_manifest_valid():
    errors = validate_manifest(minimal_manifest())
    assert errors == []


def test_missing_manifest_metadata_fails():
    data = minimal_manifest()
    data.pop("manifest_metadata")
    errors = validate_manifest(data)
    assert errors


def test_missing_file_id_fails():
    data = minimal_manifest()
    data["files"] = {
        "FID_001": {
            "relative_path": "examples/sample.txt",
            "filename": "sample.txt",
            "derivation_method": "auto",
            "file_size_bytes": 12,
            "file_type": "text/plain",
            "modified_timestamp": 1700000000.0,
        }
    }
    errors = validate_manifest(data)
    assert errors
