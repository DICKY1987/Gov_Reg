"""JSON schema validation helpers with a minimal fallback."""

from __future__ import annotations

from typing import Any, Dict, List

try:
    from jsonschema import Draft202012Validator
except Exception:  # pragma: no cover - fallback for missing deps
    Draft202012Validator = None


def validate_input(instance: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if Draft202012Validator is None:
        return _fallback_validate(instance, schema)

    validator = Draft202012Validator(schema)
    for err in validator.iter_errors(instance):
        errors.append(err.message)
    return errors


def _fallback_validate(instance: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if schema.get("type") == "object" and not isinstance(instance, dict):
        return ["input must be an object"]

    required = schema.get("required", [])
    for key in required:
        if key not in instance:
            errors.append(f"missing required field: {key}")

    properties = schema.get("properties", {})
    for key, prop in properties.items():
        if key not in instance:
            continue
        expected = prop.get("type")
        value = instance[key]
        if expected == "string" and not isinstance(value, str):
            errors.append(f"{key} must be a string")
        elif expected == "integer" and not isinstance(value, int):
            errors.append(f"{key} must be an integer")
        elif expected == "boolean" and not isinstance(value, bool):
            errors.append(f"{key} must be a boolean")
        elif expected == "array" and not isinstance(value, list):
            errors.append(f"{key} must be an array")
        elif expected == "object" and not isinstance(value, dict):
            errors.append(f"{key} must be an object")

    return errors
