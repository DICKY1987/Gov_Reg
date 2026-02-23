"""
Schema Adapter

Loads and validates against column dictionary schema.

Features:
1. Load column dictionary JSON
2. Extract field validation rules
3. Validate field values against schema
4. Check presence rules (REQUIRED, OPTIONAL, CONDITIONAL)
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class FieldValidationResult:
    """Result of field validation."""

    field_name: str
    is_valid: bool
    issues: List[str]
    value: Any


class ColumnDictionary:
    """
    Column dictionary adapter for registry validation.

    Usage:
        col_dict = ColumnDictionary.load(Path("column_dict.json"))
        result = col_dict.validate_field("file_id", "01999000042260124003")
        if not result.is_valid:
            print(result.issues)
    """

    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self.headers = data.get("headers", {})

    @classmethod
    def load(cls, path: Path) -> "ColumnDictionary":
        """Load column dictionary from JSON file."""
        if not path.exists():
            raise FileNotFoundError(f"Column dictionary not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return cls(data)

    def get_field_schema(self, field_name: str) -> Optional[Dict[str, Any]]:
        """Get schema definition for a field."""
        return self.headers.get(field_name)

    def validate_field(
        self, field_name: str, value: Any, record: Optional[Dict[str, Any]] = None
    ) -> FieldValidationResult:
        """
        Validate a field value against column dictionary rules.

        Args:
            field_name: Name of field to validate
            value: Value to validate
            record: Full record (needed for conditional rules)

        Returns:
            FieldValidationResult with validation status
        """
        issues = []
        schema = self.get_field_schema(field_name)

        if not schema:
            # Field not in dictionary
            return FieldValidationResult(
                field_name=field_name,
                is_valid=True,  # Unknown fields are allowed
                issues=[],
                value=value,
            )

        # Extract validation rules
        value_schema = schema.get("value_schema", {})
        presence = schema.get("presence", {})

        # Check type
        expected_types = value_schema.get("type", [])
        if isinstance(expected_types, str):
            expected_types = [expected_types]

        if value is None:
            if "null" not in expected_types:
                # Check if field is required
                presence_policy = presence.get("policy")
                if presence_policy == "REQUIRED":
                    issues.append(f"Field '{field_name}' is REQUIRED but is null")
        else:
            # Type check
            actual_type = type(value).__name__
            type_map = {
                "str": "string",
                "int": "integer",
                "float": "number",
                "bool": "boolean",
                "list": "array",
                "dict": "object",
            }

            mapped_type = type_map.get(actual_type, actual_type)

            if mapped_type not in expected_types and expected_types:
                issues.append(f"Expected type {expected_types}, got {mapped_type}")

            # Pattern check (for strings)
            if isinstance(value, str):
                pattern = value_schema.get("pattern")
                if pattern:
                    if not re.match(pattern, value):
                        issues.append(
                            f"Value '{value}' does not match pattern '{pattern}'"
                        )

            # Array item validation
            if isinstance(value, list):
                items_schema = value_schema.get("items", {})
                item_type = items_schema.get("type")
                if item_type:
                    for i, item in enumerate(value):
                        item_actual_type = type_map.get(
                            type(item).__name__, type(item).__name__
                        )
                        if item_actual_type != item_type:
                            issues.append(
                                f"Array item {i} has type {item_actual_type}, expected {item_type}"
                            )

        # Conditional presence rules
        if presence.get("policy") == "CONDITIONAL" and record:
            rules = presence.get("rules", [])
            for rule in rules:
                # Check if condition is met
                when_cond = rule.get("when", {})
                if when_cond.get("op") == "exists":
                    check_path = when_cond.get("path", "").strip("/")
                    if check_path in record and record[check_path]:
                        # Condition met, check must clause
                        must_cond = rule.get("must", {})
                        if must_cond.get("op") == "exists":
                            must_path = must_cond.get("path", "").strip("/")
                            if must_path == field_name:
                                if value is None:
                                    issues.append(
                                        f"Field '{field_name}' is required when '{check_path}' exists"
                                    )

        return FieldValidationResult(
            field_name=field_name, is_valid=len(issues) == 0, issues=issues, value=value
        )

    def validate_record(
        self, record: Dict[str, Any]
    ) -> Dict[str, FieldValidationResult]:
        """
        Validate all fields in a record.

        Args:
            record: Record to validate

        Returns:
            Dict mapping field_name → FieldValidationResult
        """
        results = {}

        # Validate present fields
        for field_name, value in record.items():
            result = self.validate_field(field_name, value, record)
            if not result.is_valid:
                results[field_name] = result

        # Check for missing required fields
        for field_name, schema in self.headers.items():
            if field_name not in record:
                presence = schema.get("presence", {})
                if presence.get("policy") == "REQUIRED":
                    results[field_name] = FieldValidationResult(
                        field_name=field_name,
                        is_valid=False,
                        issues=[f"Required field '{field_name}' is missing"],
                        value=None,
                    )

        return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python schema_adapter.py <column_dict_path>")
        sys.exit(1)

    col_dict_path = Path(sys.argv[1])

    print(f"Loading column dictionary: {col_dict_path}")
    col_dict = ColumnDictionary.load(col_dict_path)

    print(f"✓ Loaded {len(col_dict.headers)} field definitions")

    # Test field validation
    print("\nTesting field validations:")

    # Test file_id
    test_cases = [
        ("file_id", "01999000042260124003", True),
        ("file_id", "1999000042260124003", False),  # 19 digits
        ("file_id", 123, False),  # Wrong type
        ("geu_ids", ["GEU-1", "GEU-2"], True),  # Array
        ("geu_ids", "GEU-1", False),  # String (should be array)
        ("geu_ids", None, True),  # Null is OK
    ]

    for field_name, value, expected_valid in test_cases:
        result = col_dict.validate_field(field_name, value)
        status = "✓" if result.is_valid == expected_valid else "✗"
        print(
            f"  {status} {field_name} = {value!r} → {'valid' if result.is_valid else 'invalid'}"
        )
        if result.issues:
            for issue in result.issues:
                print(f"      Issue: {issue}")
