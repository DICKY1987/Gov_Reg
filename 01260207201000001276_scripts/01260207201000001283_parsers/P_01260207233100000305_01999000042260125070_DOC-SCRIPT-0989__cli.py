#!/usr/bin/env python3
"""
FILE_ID: 01999000042260125070
Migrated from: C:\Users\richg\ALL_AI\mapp_py\DOC-SCRIPT-0989__cli.py
"""

# DOC_ID: DOC-SCRIPT-0989
"""
MAPP-PY CLI - Command-line interface for Python file comparison.

Work ID: WORK-MAPP-PY-001
Module: cli.py
"""
import sys
import argparse
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from DOC-SCRIPT-0994__file_comparator import FileComparator


def main():
    parser = argparse.ArgumentParser(
        description="MAPP-PY: Compare Python files for similarity detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare two files
  python cli.py file1.py file2.py

  # Save evidence to JSON
  python cli.py file1.py file2.py --output evidence.json

  # Use custom weights
  python cli.py file1.py file2.py --weight-structural 0.4 --weight-semantic 0.3

  # Quiet mode (JSON only)
  python cli.py file1.py file2.py --quiet
"""
    )

    parser.add_argument("file_a", type=Path, help="First Python file to compare")
    parser.add_argument("file_b", type=Path, help="Second Python file to compare")

    parser.add_argument("-o", "--output", type=Path, help="Output JSON file for evidence")
    parser.add_argument("-q", "--quiet", action="store_true", help="Quiet mode (JSON output only)")

    # Weight customization
    parser.add_argument("--weight-structural", type=float, help="Weight for structural similarity (default: 0.35)")
    parser.add_argument("--weight-semantic", type=float, help="Weight for semantic similarity (default: 0.30)")
    parser.add_argument("--weight-dependency", type=float, help="Weight for dependency overlap (default: 0.20)")
    parser.add_argument("--weight-io-surface", type=float, help="Weight for I/O surface overlap (default: 0.15)")

    # Observability
    parser.add_argument("--trace-id", help="Trace ID for distributed tracing")
    parser.add_argument("--run-id", help="Run ID for execution tracking")

    args = parser.parse_args()

    # Validate files exist
    if not args.file_a.exists():
        print(f"Error: File not found: {args.file_a}", file=sys.stderr)
        return 1

    if not args.file_b.exists():
        print(f"Error: File not found: {args.file_b}", file=sys.stderr)
        return 1

    # Build custom weights if provided
    weights = None
    if any([args.weight_structural, args.weight_semantic, args.weight_dependency, args.weight_io_surface]):
        weights = {
            "structural": args.weight_structural or 0.35,
            "semantic": args.weight_semantic or 0.30,
            "dependency": args.weight_dependency or 0.20,
            "io_surface": args.weight_io_surface or 0.15
        }

    # Create comparator
    comparator = FileComparator(
        weights=weights,
        trace_id=args.trace_id,
        run_id=args.run_id
    )

    # Compare files
    try:
        result = comparator.compare(args.file_a, args.file_b)
    except Exception as e:
        print(f"Error during comparison: {e}", file=sys.stderr)
        return 1

    # Handle errors
    if result.has_errors:
        print(f"Comparison Error: {result.error_message}", file=sys.stderr)
        if not args.quiet:
            print("\nPartial results may be available in JSON output.", file=sys.stderr)

    # Output results
    if args.quiet:
        # JSON only
        print(result.to_json())
    else:
        # Human-readable output
        print(f"=== MAPP-PY Comparison Report ===\n")
        print(f"File A: {result.file_a}")
        print(f"File B: {result.file_b}\n")

        print(f"Aggregate Score: {result.aggregate_score:.4f}")
        print(f"Decision: {result.decision}")
        print(f"Confidence: {result.decision_confidence:.4f}\n")

        print("Dimension Breakdown:")
        for name, dim in result.dimensions.items():
            print(f"  {name:14s}: {dim.score:.4f} × {dim.weight:.2f} = {dim.weighted_score:.4f}")

        print(f"\nComponents:")
        print(f"  File A: {result.components.get('file_a_count', 0)} components")
        print(f"  File B: {result.components.get('file_b_count', 0)} components")
        print(f"  Common: {result.components.get('common_components', 0)} components")

        if result.trace_id:
            print(f"\nTrace ID: {result.trace_id}")
        if result.run_id:
            print(f"Run ID: {result.run_id}")

    # Save to file if requested
    if args.output:
        try:
            args.output.write_text(result.to_json())
            if not args.quiet:
                print(f"\nEvidence saved to: {args.output}")
        except Exception as e:
            print(f"Error saving output: {e}", file=sys.stderr)
            return 1

    # Exit code based on decision
    if result.has_errors:
        return 2
    elif result.decision == "SIMILAR":
        return 0
    elif result.decision == "REVIEW_NEEDED":
        return 0
    else:  # DIFFERENT
        return 0


if __name__ == "__main__":
    sys.exit(main())
