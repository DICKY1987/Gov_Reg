"""
Schema Validation Utilities for ACMS

Provides validation helpers for all ACMS data structures.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

try:
    import jsonschema
    from jsonschema import validate, ValidationError

    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    print("⚠️  jsonschema not installed. Install with: pip install jsonschema")


class SchemaValidator:
    """Validates JSON data against schemas"""

    def __init__(self, schema_dir: Optional[Path] = None):
        self.schema_dir = schema_dir or (
            Path(__file__).parent.parent.parent / "schemas"
        )
        self.schemas = {}
        self._load_schemas()

    def _load_schemas(self) -> None:
        """Load all schemas from schema directory"""
        if not self.schema_dir.exists():
            print(f"⚠️  Schema directory not found: {self.schema_dir}")
            return

        for schema_file in self.schema_dir.glob("**/*.schema.json"):
            # schema_name should be like "acms/gap_record"
            relative_path = schema_file.relative_to(self.schema_dir)
            schema_name = str(relative_path.parent / relative_path.stem).replace(
                ".schema", ""
            )
            try:
                with open(schema_file, "r", encoding="utf-8") as f:
                    self.schemas[schema_name] = json.load(f)
            except Exception as e:
                print(f"⚠️  Failed to load schema {schema_file.name}: {e}")

    def validate(
        self, data: Dict[str, Any], schema_name: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate data against a schema

        Returns:
            (is_valid, error_message)
        """
        if not JSONSCHEMA_AVAILABLE:
            return True, "jsonschema not available - skipping validation"

        schema = self.schemas.get(schema_name)
        if not schema:
            return False, f"Schema '{schema_name}' not found"

        try:
            validate(instance=data, schema=schema)
            return True, None
        except ValidationError as e:
            return (
                False,
                f"Validation error: {e.message} at {'.'.join(str(p) for p in e.path)}",
            )
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def validate_file(
        self, file_path: Path, schema_name: str
    ) -> Tuple[bool, Optional[str]]:
        """Validate a JSON file against a schema"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return self.validate(data, schema_name)
        except Exception as e:
            return False, f"Failed to load file: {str(e)}"

    def get_schema_names(self) -> list:
        """Get list of available schema names"""
        return list(self.schemas.keys())


# Convenience functions
_validator = None


def get_validator() -> SchemaValidator:
    """Get singleton schema validator"""
    global _validator
    if _validator is None:
        _validator = SchemaValidator()
    return _validator


def validate_gap_record(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate a gap record"""
    return get_validator().validate(data, "acms/gap_record")


def validate_workstream(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate a workstream definition"""
    return get_validator().validate(data, "workstreams/workstream_definition")


def validate_execution_plan(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate a MINI_PIPE execution plan"""
    return get_validator().validate(data, "execution/minipipe_execution_plan")


def validate_run_status(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate a run status"""
    return get_validator().validate(data, "acms/run_status")


if __name__ == "__main__":
    # Test schema loading
    validator = SchemaValidator()
    print(f"\nLoaded {len(validator.schemas)} schemas:")
    for name in validator.get_schema_names():
        print(f"  ✓ {name}")

    # Test validation with sample data
    print("\nTesting validation:")

    sample_gap = {
        "gap_id": "GAP_TEST_001",
        "title": "Test gap",
        "description": "This is a test gap for validation",
        "category": "testing",
        "severity": "low",
        "status": "discovered",
        "file_paths": ["test.py"],
    }

    is_valid, error = validate_gap_record(sample_gap)
    if is_valid:
        print("  ✓ Sample gap record is valid")
    else:
        print(f"  ✗ Sample gap record is invalid: {error}")
