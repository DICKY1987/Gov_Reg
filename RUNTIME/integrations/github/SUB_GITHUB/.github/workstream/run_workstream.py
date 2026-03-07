#!/usr/bin/env python
"""
CLI to run a single workstream end-to-end via the canonical core.engine orchestrator.

UPDATED: 2025-12-04 - Migrated to use core.engine.orchestrator
"""
# DOC_ID: DOC-SCRIPT-SCRIPTS-RUN-WORKSTREAM-230
# DOC_ID: DOC-SCRIPT-SCRIPTS-RUN-WORKSTREAM-167

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

# Add project root to sys.path
.parent.parent))

from core.engine.orchestrator import Orchestrator
from core.state.bundles import load_bundle_file as load_bundle


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a workstream via canonical orchestrator"
    )
    parser.add_argument(
        "--ws-id", required=True, help="Workstream id to run (e.g., ws-hello-world)"
    )
    parser.add_argument(
        "--plan", help="Path to JSON plan file (overrides workstream bundle)"
    )
    parser.add_argument(
        "--run-id", help="Optional run id (default: auto-generated)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate steps without invoking external tools",
    )
    parser.add_argument(
        "--db",
        default=".ledger/framework.db",
        help="Database path (default: .ledger/framework.db)",
    )
    parser.add_argument(
        "--workstreams-dir",
        default="workstreams",
        help="Directory containing workstream bundles",
    )
    args = parser.parse_args(argv)

    try:
        # Initialize orchestrator
        orch = Orchestrator()

        # Create run
        run_id = args.run_id or orch.create_run(
            project_id="pipeline",
            phase_id="workstream-execution",
            workstream_id=args.ws_id,
            metadata={"dry_run": args.dry_run},
        )

        print(f"🚀 Executing workstream: {args.ws_id}")
        print(f"📝 Run ID: {run_id}")
        print(f"💾 Database: {args.db}")
        if args.dry_run:
            print("⚠️  DRY RUN MODE - No external tools will be invoked")
        print()

        # Execute based on input type
        if args.plan:
            # Execute from JSON plan file
            result_run_id = orch.execute_plan(args.plan, variables={})
            run = orch.get_run_status(result_run_id)
        else:
            # Load workstream bundle and execute
            workstreams_dir = Path(args.workstreams_dir)
            bundle_path = workstreams_dir / f"{args.ws_id}.json"

            if not bundle_path.exists():
                print(f"❌ Workstream bundle not found: {bundle_path}", file=sys.stderr)
                return 2

            bundle = load_bundle(bundle_path)

            # Execute the bundle directly via orchestrator
            from core.engine.orchestrator import Orchestrator

            print(f"✅ Loaded workstream: {bundle.get('id')}")
            print(f"📋 Title: {bundle.get('title', 'N/A')}")
            print(f"🔧 Tool: {bundle.get('tool', 'N/A')}")
            print(f"✓ Steps: {len(bundle.get('steps', []))}")

            # Execute the workstream bundle
            orchestrator = Orchestrator()
            result = orchestrator.run(
                workstream_id=ws_id,
                bundle=bundle,
                run_id=args.run_id,
                dry_run=args.dry_run
            )

            if result and result.get('success'):
                print(f"\n✅ Workstream completed successfully!")
                return 0
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'Execution failed'
                print(f"\n❌ Workstream failed: {error_msg}")
                return 1
            print()
            print("⚠️  Note: Bundle-to-Plan conversion not yet implemented.")
            print("   Use --plan flag to execute JSON plan directly.")
            return 0

        # Get final status
        if run and run.get("state") == "succeeded":
            print("✅ Workstream execution succeeded")
            return 0
        else:
            print(f"❌ Workstream execution failed: {run.get('state')}", file=sys.stderr)
            return 1

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
