#!/usr/bin/env python3
# DOC_LINK: DOC-SCRIPT-TOOLS-BUILD-RELATIONSHIP-INDEX-986
"""
Build Relationship Index

CLI tool to generate the relationship index from doc_id-tagged repository files.

Usage:
    python build_relationship_index.py --output data/RELATIONSHIP_INDEX.json
    python build_relationship_index.py --output data/RELATIONSHIP_INDEX.json --run-id run_001 --trace-id trace-001
"""
# DOC_ID: DOC-SCRIPT-TOOLS-BUILD-RELATIONSHIP-INDEX-986

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.index_builder import RelationshipIndexBuilder


def main():
    parser = argparse.ArgumentParser(
        description="Build relationship index from doc_id-tagged repository files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build index with default output location
  python build_relationship_index.py

  # Build index with custom output location
  python build_relationship_index.py --output ../analysis/relationships.json

  # Build with observability IDs
  python build_relationship_index.py --run-id run_20250131 --trace-id trace-experiment-01
"""
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent.parent / "data" / "RELATIONSHIP_INDEX.json",
        help="Output path for relationship index JSON (default: data/RELATIONSHIP_INDEX.json)"
    )

    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Run ID for observability (default: auto-generated timestamp)"
    )

    parser.add_argument(
        "--trace-id",
        type=str,
        default=None,
        help="Trace ID for observability (default: derived from run-id)"
    )

    parser.add_argument(
        "--registry",
        type=Path,
        default=None,
        help="Path to doc_id inventory (default: SUB_DOC_ID/5_REGISTRY_DATA/docs_inventory.jsonl)"
    )

    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Use incremental build with caching (10x faster for small changes)"
    )

    parser.add_argument(
        "--force-full",
        action="store_true",
        help="Force full rebuild even in incremental mode"
    )

    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output (default: canonical format with sorted keys)"
    )

    args = parser.parse_args()

    # Build index
    print("\n" + "=" * 60)
    print("RELATIONSHIP INDEX BUILDER")
    print("=" * 60)

    try:
        # Create builder
        if args.incremental:
            from core.incremental_builder import IncrementalRelationshipIndexBuilder
            builder = IncrementalRelationshipIndexBuilder(
                run_id=args.run_id,
                trace_id=args.trace_id,
                registry_path=args.registry,
                force_full=args.force_full
            )
        else:
            builder = RelationshipIndexBuilder(
                run_id=args.run_id,
                trace_id=args.trace_id,
                registry_path=args.registry
            )

        # Build index
        index = builder.build()

        # Ensure output directory exists
        args.output.parent.mkdir(parents=True, exist_ok=True)

        # Write index to file
        print(f"\nWriting index to: {args.output}")

        with open(args.output, 'w', encoding='utf-8') as f:
            if args.pretty:
                json.dump(index, f, indent=2, sort_keys=True)
            else:
                # Canonical format: sorted keys, 2-space indent (for determinism)
                json.dump(index, f, indent=2, sort_keys=True)

        print(f"✅ Index written successfully!\n")

        # Print final summary
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Output file: {args.output}")
        print(f"File size: {args.output.stat().st_size:,} bytes")
        print(f"Total nodes: {index['meta']['total_nodes']}")
        print(f"Total edges: {index['meta']['total_edges']}")
        print(f"Run ID: {index['meta']['run_id']}")
        print(f"Trace ID: {index['meta']['trace_id']}")
        print("=" * 60 + "\n")

        return 0

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        print("\nMake sure SUB_DOC_ID/5_REGISTRY_DATA/docs_inventory.jsonl exists.", file=sys.stderr)
        print("Run SUB_DOC_ID scanner first:\n", file=sys.stderr)
        print("  cd SUB_DOC_ID/1_CORE_OPERATIONS", file=sys.stderr)
        print("  python doc_id_scanner.py scan\n", file=sys.stderr)
        return 1

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
