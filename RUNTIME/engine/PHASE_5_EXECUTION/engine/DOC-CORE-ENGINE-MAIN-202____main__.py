# DOC_LINK: DOC-CORE-ENGINE-MAIN-202
"""CLI entry point for orchestrator plan execution."""

# DOC_ID: DOC-CORE-ENGINE-MAIN-202

import argparse
import sys
from pathlib import Path

from core.engine.orchestrator import Orchestrator


def main():
    """Execute a JSON plan file."""
    parser = argparse.ArgumentParser(
        description="Execute a JSON orchestration plan",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m core.engine.orchestrator plans/safe_merge.json --var BRANCH=main
  python -m core.engine.orchestrator plans/test_gate.json --var COMMIT_MSG="fix: bug"
        """,
    )

    parser.add_argument("plan_path", help="Path to JSON plan file")

    parser.add_argument(
        "--var",
        action="append",
        dest="variables",
        help="Variable for substitution (KEY=VALUE). Can be specified multiple times.",
    )

    parser.add_argument(
        "--db",
        default=".ledger/framework.db",
        help="Database path (default: .ledger/framework.db)",
    )

    args = parser.parse_args()

    # Parse variables
    variables = {}
    if args.variables:
        for var_str in args.variables:
            if "=" not in var_str:
                print(
                    f"Error: Invalid variable format '{var_str}'. Use KEY=VALUE",
                    file=sys.stderr,
                )
                sys.exit(2)
            key, value = var_str.split("=", 1)
            variables[key] = value

    # Validate plan file exists
    if not Path(args.plan_path).exists():
        print(f"Error: Plan file not found: {args.plan_path}", file=sys.stderr)
        sys.exit(2)

    try:
        # Execute plan
        orch = Orchestrator()
        run_id = orch.execute_plan(args.plan_path, variables)

        print("✅ Plan execution completed")
        print(f"Run ID: {run_id}")
        print(f"Database: {args.db}")

        # Get final status
        run = orch.get_run_status(run_id)
        if run and run.get("state") == "succeeded":
            sys.exit(0)
        else:
            sys.exit(1)

    except Exception as e:
        print(f"❌ Plan execution failed: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
