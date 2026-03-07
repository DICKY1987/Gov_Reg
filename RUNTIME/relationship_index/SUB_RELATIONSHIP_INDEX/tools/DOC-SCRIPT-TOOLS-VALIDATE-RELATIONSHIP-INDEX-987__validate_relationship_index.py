#!/usr/bin/env python3
# DOC_LINK: DOC-SCRIPT-TOOLS-VALIDATE-RELATIONSHIP-INDEX-987
"""
Validate Relationship Index

CLI tool to validate a relationship index against the JSON schema.

Usage:
    python validate_relationship_index.py --index data/RELATIONSHIP_INDEX.json
    python validate_relationship_index.py --index data/RELATIONSHIP_INDEX.json --schema schemas/relationship_index.schema.json
"""
# DOC_ID: DOC-SCRIPT-TOOLS-VALIDATE-RELATIONSHIP-INDEX-987

import argparse
import json
import sys
from pathlib import Path

try:
    import jsonschema
    from jsonschema import Draft202012Validator
except ImportError:
    print("Error: jsonschema library not found", file=sys.stderr)
    print("Install with: pip install jsonschema", file=sys.stderr)
    sys.exit(2)


def load_json(file_path: Path) -> dict:
    """Load JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_index(index: dict, schema: dict) -> tuple[bool, list[str]]:
    """
    Validate index against schema.

    Returns:
        Tuple of (is_valid, errors)
    """
    validator = Draft202012Validator(schema)
    errors = []

    for error in sorted(validator.iter_errors(index), key=str):
        # Format error message
        path = " -> ".join(str(p) for p in error.path)
        if path:
            msg = f"  {path}: {error.message}"
        else:
            msg = f"  {error.message}"
        errors.append(msg)

    return len(errors) == 0, errors


def main():
    parser = argparse.ArgumentParser(
        description="Validate relationship index against JSON schema",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate with default schema
  python validate_relationship_index.py --index data/RELATIONSHIP_INDEX.json

  # Validate with custom schema
  python validate_relationship_index.py --index data/test.json --schema schemas/custom.schema.json
"""
    )

    parser.add_argument(
        "--index",
        type=Path,
        required=True,
        help="Path to relationship index JSON file"
    )

    parser.add_argument(
        "--schema",
        type=Path,
        default=Path(__file__).parent.parent / "schemas" / "relationship_index.schema.json",
        help="Path to JSON schema file (default: schemas/relationship_index.schema.json)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed validation output"
    )

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("RELATIONSHIP INDEX VALIDATOR")
    print("=" * 60 + "\n")

    # Check files exist
    if not args.index.exists():
        print(f"❌ Error: Index file not found: {args.index}", file=sys.stderr)
        return 1

    if not args.schema.exists():
        print(f"❌ Error: Schema file not found: {args.schema}", file=sys.stderr)
        return 1

    print(f"Index file: {args.index}")
    print(f"Schema file: {args.schema}\n")

    try:
        # Load files
        print("[1/3] Loading index...")
        index = load_json(args.index)
        print(f"      Loaded {len(index.get('nodes', []))} nodes, {len(index.get('edges', []))} edges")

        print("[2/3] Loading schema...")
        schema = load_json(args.schema)
        print(f"      Schema version: {schema.get('$schema', 'unknown')}")

        # Validate
        print("[3/3] Validating index against schema...")
        is_valid, errors = validate_index(index, schema)

        print()
        print("=" * 60)
        print("VALIDATION RESULT")
        print("=" * 60)

        if is_valid:
            print("✅ VALID - Index conforms to schema")
            print()
            print("Statistics:")
            meta = index.get("meta", {})
            stats = index.get("statistics", {})

            print(f"  Total nodes: {meta.get('total_nodes', 0)}")
            print(f"  Total edges: {meta.get('total_edges', 0)}")
            print(f"  Generated at: {meta.get('generated_at', 'unknown')}")
            print(f"  Generator version: {meta.get('generator_version', 'unknown')}")

            if stats:
                print(f"\n  Edge types:")
                for edge_type, count in stats.get("edge_types", {}).items():
                    print(f"    {edge_type}: {count}")

                print(f"\n  Confidence distribution:")
                for conf, count in stats.get("confidence_distribution", {}).items():
                    print(f"    {conf}: {count}")

            print("=" * 60 + "\n")
            return 0

        else:
            print("❌ INVALID - Index does not conform to schema")
            print()
            print(f"Found {len(errors)} validation error(s):")
            print()

            # Show first 20 errors (or all if verbose)
            max_errors = None if args.verbose else 20
            for i, error in enumerate(errors[:max_errors], 1):
                print(f"{i}. {error}")

            if not args.verbose and len(errors) > 20:
                print(f"\n... and {len(errors) - 20} more errors")
                print("(use --verbose to see all errors)")

            print()
            print("=" * 60 + "\n")
            return 1

    except json.JSONDecodeError as e:
        print(f"\n❌ Error: Invalid JSON: {e}", file=sys.stderr)
        return 1

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
