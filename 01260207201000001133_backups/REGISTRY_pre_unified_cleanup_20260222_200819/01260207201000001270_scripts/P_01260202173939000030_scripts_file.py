import argparse
import json
import sys
from pathlib import Path


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def collect_py_columns(column_dict: dict) -> list[str]:
    headers = column_dict.get("headers", {})
    return sorted([name for name in headers.keys() if name.startswith("py_")])


def summarize_missing(py_cols: list[str], available: set[str]) -> list[str]:
    return [col for col in py_cols if col not in available]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate py_* column integration across dictionary, schema, and registry."
    )
    parser.add_argument(
        "--column-dictionary",
        default="2026012816000001_COLUMN_DICTIONARY.json",
        help="Path to Column Dictionary JSON",
    )
    parser.add_argument(
        "--schema",
        default="01999000042260124012_governance_registry_schema.v3.json",
        help="Path to registry schema JSON",
    )
    parser.add_argument(
        "--registry",
        default="01999000042260124503_governance_registry_unified.json",
        help="Path to unified registry JSON",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail if PYTHON_MODULE file records are missing py_* values.",
    )
    args = parser.parse_args()

    column_dict = load_json(Path(args.column_dictionary))
    schema = load_json(Path(args.schema))
    registry = load_json(Path(args.registry))

    py_cols = collect_py_columns(column_dict)
    errors: list[str] = []

    if len(py_cols) != 37:
        errors.append(f"Column Dictionary py_* count expected 37, found {len(py_cols)}.")

    schema_props = (
        schema.get("definitions", {})
        .get("FileRecord", {})
        .get("properties", {})
    )
    missing_in_schema = summarize_missing(py_cols, set(schema_props.keys()))
    if missing_in_schema:
        errors.append(
            f"Schema missing py_* properties: {', '.join(missing_in_schema)}."
        )

    registry_headers = registry.get("column_headers", {})
    missing_in_registry = summarize_missing(py_cols, set(registry_headers.keys()))
    if missing_in_registry:
        errors.append(
            f"Registry column_headers missing py_* columns: {', '.join(missing_in_registry)}."
        )

    py_files = [
        file_rec
        for file_rec in registry.get("files", [])
        if file_rec.get("artifact_kind") == "PYTHON_MODULE"
    ]
    if py_files:
        missing_values = {}
        for col in py_cols:
            missing_values[col] = sum(1 for file_rec in py_files if col not in file_rec)
        missing_summary = {k: v for k, v in missing_values.items() if v > 0}
        if missing_summary:
            print("PYTHON_MODULE records missing py_* fields (counts):")
            for col, count in sorted(missing_summary.items()):
                print(f"  {col}: {count}")
            if args.strict:
                errors.append("PYTHON_MODULE records are missing py_* values in strict mode.")
    else:
        print("No PYTHON_MODULE records found; skipping py_* value checks.")

    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("py_* column integration checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
