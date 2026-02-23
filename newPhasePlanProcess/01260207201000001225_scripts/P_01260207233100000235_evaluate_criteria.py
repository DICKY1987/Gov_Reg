#!/usr/bin/env python3
"""
Criteria Evaluator for v3.0.0 Plans

Evaluates typed criteria for step preconditions and postconditions:
- exists: File/directory exists
- not_exists: File/directory does not exist
- json_valid: File contains valid JSON
- schema_valid: JSON validates against schema
- hash_equals: File hash matches expected value
- diff_empty: Diff between two paths is empty
- contains: File/string contains substring
- custom: Custom validation logic
"""

import json
import os
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Any, Tuple
from datetime import datetime

try:
    import jsonschema

    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False


def evaluate_criteria(
    criteria: Dict[str, Any], context: Dict[str, Any] = None
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Evaluate a single criteria object.

    Args:
        criteria: Criteria object with type, statement, evidence_path
        context: Optional context (e.g., base paths, variable substitutions)

    Returns:
        Tuple of (passed: bool, message: str, evidence: dict)
    """
    if context is None:
        context = {}

    criteria_type = criteria.get("type")
    statement = criteria.get("statement", "")
    evidence_path = criteria.get("evidence_path")

    timestamp = datetime.utcnow().isoformat() + "Z"

    # Dispatch to appropriate evaluator
    evaluators = {
        "exists": evaluate_exists,
        "not_exists": evaluate_not_exists,
        "json_valid": evaluate_json_valid,
        "schema_valid": evaluate_schema_valid,
        "hash_equals": evaluate_hash_equals,
        "diff_empty": evaluate_diff_empty,
        "contains": evaluate_contains,
        "custom": evaluate_custom,
    }

    evaluator = evaluators.get(criteria_type)
    if not evaluator:
        return (
            False,
            f"Unknown criteria type: {criteria_type}",
            {
                "timestamp": timestamp,
                "criteria_type": criteria_type,
                "statement": statement,
                "passed": False,
                "error": f"Unknown criteria type: {criteria_type}",
            },
        )

    try:
        passed, message = evaluator(criteria, context)
        evidence = {
            "timestamp": timestamp,
            "criteria_type": criteria_type,
            "statement": statement,
            "passed": passed,
            "message": message,
        }

        # Write evidence to file if path provided
        if evidence_path:
            write_evidence(evidence_path, evidence)

        return passed, message, evidence

    except Exception as e:
        error_message = f"Criteria evaluation failed: {str(e)}"
        evidence = {
            "timestamp": timestamp,
            "criteria_type": criteria_type,
            "statement": statement,
            "passed": False,
            "error": error_message,
        }

        if evidence_path:
            write_evidence(evidence_path, evidence)

        return False, error_message, evidence


def evaluate_exists(
    criteria: Dict[str, Any], context: Dict[str, Any]
) -> Tuple[bool, str]:
    """Evaluate if file/directory exists."""
    # Extract path from statement (assumes format: "Path /path/to/file exists")
    statement = criteria.get("statement", "")

    # Try to extract path from context or statement
    path = context.get("target_path")
    if not path:
        # Simple heuristic: extract path-like strings from statement
        parts = statement.split()
        for part in parts:
            if "/" in part or "\\" in part or part.startswith("."):
                path = part
                break

    if not path:
        return False, f"No path specified in criteria: {statement}"

    if os.path.exists(path):
        return True, f"Path exists: {path}"
    else:
        return False, f"Path does not exist: {path}"


def evaluate_not_exists(
    criteria: Dict[str, Any], context: Dict[str, Any]
) -> Tuple[bool, str]:
    """Evaluate if file/directory does not exist."""
    passed, message = evaluate_exists(criteria, context)
    return not passed, message.replace(
        "exists", "does not exist"
    ) if passed else message.replace("does not exist", "exists")


def evaluate_json_valid(
    criteria: Dict[str, Any], context: Dict[str, Any]
) -> Tuple[bool, str]:
    """Evaluate if file contains valid JSON."""
    statement = criteria.get("statement", "")

    # Extract path
    path = context.get("target_path")
    if not path:
        parts = statement.split()
        for part in parts:
            if "/" in part or "\\" in part or part.endswith(".json"):
                path = part
                break

    if not path:
        return False, f"No path specified in criteria: {statement}"

    if not os.path.exists(path):
        return False, f"Path does not exist: {path}"

    try:
        with open(path, "r", encoding="utf-8") as f:
            json.load(f)
        return True, f"Valid JSON: {path}"
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON in {path}: {str(e)}"
    except Exception as e:
        return False, f"Error reading {path}: {str(e)}"


def evaluate_schema_valid(
    criteria: Dict[str, Any], context: Dict[str, Any]
) -> Tuple[bool, str]:
    """Evaluate if JSON validates against schema."""
    if not JSONSCHEMA_AVAILABLE:
        return False, "jsonschema package not installed (pip install jsonschema)"

    statement = criteria.get("statement", "")
    data_path = context.get("target_path")
    schema_path = context.get("schema_path")

    if not data_path or not schema_path:
        return False, f"schema_valid requires target_path and schema_path in context"

    if not os.path.exists(data_path):
        return False, f"Data file does not exist: {data_path}"

    if not os.path.exists(schema_path):
        return False, f"Schema file does not exist: {schema_path}"

    try:
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        jsonschema.validate(instance=data, schema=schema)
        return True, f"Valid against schema: {data_path}"

    except jsonschema.ValidationError as e:
        return False, f"Schema validation failed: {e.message}"
    except Exception as e:
        return False, f"Error validating schema: {str(e)}"


def evaluate_hash_equals(
    criteria: Dict[str, Any], context: Dict[str, Any]
) -> Tuple[bool, str]:
    """Evaluate if file hash matches expected value."""
    statement = criteria.get("statement", "")
    path = context.get("target_path")
    expected_hash = context.get("expected_hash")
    hash_algo = context.get("hash_algo", "sha256")

    if not path or not expected_hash:
        return False, "hash_equals requires target_path and expected_hash in context"

    if not os.path.exists(path):
        return False, f"Path does not exist: {path}"

    try:
        hasher = hashlib.new(hash_algo)
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)

        actual_hash = hasher.hexdigest()

        if actual_hash == expected_hash:
            return True, f"Hash matches ({hash_algo}): {path}"
        else:
            return (
                False,
                f"Hash mismatch for {path}: expected {expected_hash}, got {actual_hash}",
            )

    except Exception as e:
        return False, f"Error computing hash: {str(e)}"


def evaluate_diff_empty(
    criteria: Dict[str, Any], context: Dict[str, Any]
) -> Tuple[bool, str]:
    """Evaluate if diff between two paths is empty."""
    path1 = context.get("path1")
    path2 = context.get("path2")

    if not path1 or not path2:
        return False, "diff_empty requires path1 and path2 in context"

    if not os.path.exists(path1):
        return False, f"Path does not exist: {path1}"

    if not os.path.exists(path2):
        return False, f"Path does not exist: {path2}"

    try:
        # Use diff command or file comparison
        result = subprocess.run(
            ["diff", "-q", path1, path2], capture_output=True, text=True, timeout=30
        )

        if result.returncode == 0:
            return True, f"Files are identical: {path1} vs {path2}"
        else:
            return False, f"Files differ: {path1} vs {path2}"

    except FileNotFoundError:
        # Fallback to Python comparison if diff not available
        try:
            with open(path1, "rb") as f1, open(path2, "rb") as f2:
                if f1.read() == f2.read():
                    return True, f"Files are identical: {path1} vs {path2}"
                else:
                    return False, f"Files differ: {path1} vs {path2}"
        except Exception as e:
            return False, f"Error comparing files: {str(e)}"

    except Exception as e:
        return False, f"Error running diff: {str(e)}"


def evaluate_contains(
    criteria: Dict[str, Any], context: Dict[str, Any]
) -> Tuple[bool, str]:
    """Evaluate if file/string contains substring."""
    statement = criteria.get("statement", "")
    path = context.get("target_path")
    substring = context.get("substring")

    if not substring:
        # Try to extract from statement
        if "contains" in statement.lower():
            parts = statement.split("contains", 1)
            if len(parts) == 2:
                substring = parts[1].strip().strip('"').strip("'")

    if not path or not substring:
        return False, "contains requires target_path and substring in context"

    if not os.path.exists(path):
        return False, f"Path does not exist: {path}"

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        if substring in content:
            return True, f"File contains '{substring}': {path}"
        else:
            return False, f"File does not contain '{substring}': {path}"

    except Exception as e:
        return False, f"Error reading file: {str(e)}"


def evaluate_custom(
    criteria: Dict[str, Any], context: Dict[str, Any]
) -> Tuple[bool, str]:
    """Evaluate custom criteria."""
    statement = criteria.get("statement", "")

    # Custom criteria require a custom_evaluator function in context
    custom_evaluator = context.get("custom_evaluator")

    if not custom_evaluator:
        return False, "custom criteria requires custom_evaluator function in context"

    try:
        result = custom_evaluator(criteria, context)
        if isinstance(result, tuple) and len(result) == 2:
            return result
        elif isinstance(result, bool):
            return result, f"Custom criteria: {statement}"
        else:
            return False, f"Invalid custom evaluator return type"

    except Exception as e:
        return False, f"Custom evaluator failed: {str(e)}"


def write_evidence(evidence_path: str, evidence: Dict[str, Any]) -> None:
    """Write evidence to JSON file."""
    try:
        # Create parent directories if needed
        Path(evidence_path).parent.mkdir(parents=True, exist_ok=True)

        with open(evidence_path, "w", encoding="utf-8") as f:
            json.dump(evidence, f, indent=2)

    except Exception as e:
        print(f"Warning: Failed to write evidence to {evidence_path}: {e}")


def evaluate_all_criteria(
    criteria_list: list, context: Dict[str, Any] = None
) -> Tuple[bool, list]:
    """
    Evaluate a list of criteria.

    Returns:
        Tuple of (all_passed: bool, results: list of evidence dicts)
    """
    results = []
    all_passed = True

    for criteria in criteria_list:
        passed, message, evidence = evaluate_criteria(criteria, context)
        results.append(evidence)
        if not passed:
            all_passed = False

    return all_passed, results


if __name__ == "__main__":
    # Example usage
    print("Criteria Evaluator v3.0.0")
    print("=" * 50)

    # Test exists
    test_criteria = {
        "type": "exists",
        "statement": "Schema file exists",
        "evidence_path": ".state/evidence/test/exists.json",
    }

    passed, message, evidence = evaluate_criteria(
        test_criteria,
        context={"target_path": "schemas/01260207233100000675_NEWPHASEPLANPROCESS_plan.schema.v3.0.0.json"},
    )

    print(f"Test 'exists': {passed} - {message}")

    # Test json_valid
    test_criteria = {
        "type": "json_valid",
        "statement": "Schema is valid JSON",
        "evidence_path": ".state/evidence/test/json_valid.json",
    }

    passed, message, evidence = evaluate_criteria(
        test_criteria,
        context={"target_path": "schemas/01260207233100000675_NEWPHASEPLANPROCESS_plan.schema.v3.0.0.json"},
    )

    print(f"Test 'json_valid': {passed} - {message}")
