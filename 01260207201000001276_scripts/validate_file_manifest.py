#!/usr/bin/env python3
"""
Validate File Manifest
Validate a manifest JSON file against schemas/file_manifest_schema_v1.json.
"""
import argparse
import json
import sys
from pathlib import Path

import jsonschema


DEFAULT_SCHEMA_PATH = (
    Path(__file__).resolve().parents[1]
    / "schemas"
    / "file_manifest_schema_v1.json"
)


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def format_error(error: jsonschema.ValidationError) -> str:
    if error.path:
        path = ".".join(str(part) for part in error.path)
    else:
        path = "<root>"
    return f"{path}: {error.message}"


def validate_manifest(manifest_path: Path, schema_path: Path) -> dict:
    schema = load_json(schema_path)
    manifest = load_json(manifest_path)
    validator = jsonschema.Draft7Validator(schema)
    errors = sorted(validator.iter_errors(manifest), key=lambda e: list(e.path))

    return {
        "manifest_path": str(manifest_path),
        "schema_path": str(schema_path),
        "valid": not errors,
        "error_count": len(errors),
        "errors": [format_error(error) for error in errors],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="validate-file-manifest",
        description="Validate a file manifest JSON against the v1 schema",
    )
    parser.add_argument("manifest", type=Path, help="Path to manifest JSON")
    parser.add_argument(
        "--schema",
        type=Path,
        default=DEFAULT_SCHEMA_PATH,
        help="Path to schema JSON (default: schemas/file_manifest_schema_v1.json)",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="Optional path to write JSON validation report",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress stdout output (exit code only)",
    )
    args = parser.parse_args()

    try:
        result = validate_manifest(args.manifest, args.schema)
    except FileNotFoundError as exc:
        if not args.quiet:
            print(f"File not found: {exc.filename}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        if not args.quiet:
            print(f"Invalid JSON: {exc}", file=sys.stderr)
        return 2
    except jsonschema.SchemaError as exc:
        if not args.quiet:
            print(f"Invalid schema: {exc}", file=sys.stderr)
        return 2

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with open(args.report, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

    if not args.quiet:
        status = "VALID" if result["valid"] else "INVALID"
        print(f"Manifest validation: {status}")
        print(f"Manifest: {args.manifest}")
        print(f"Schema: {args.schema}")
        if result["errors"]:
            print("Errors:")
            for error in result["errors"]:
                print(f"- {error}")

    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
