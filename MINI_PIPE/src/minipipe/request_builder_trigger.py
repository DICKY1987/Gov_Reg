#!/usr/bin/env python3
"""
Auto-trigger Request Builder
Implements WS1-003: Auto-trigger Request Builder on PLANNING_COMPLETE

Watches for PLANNING_COMPLETE flag and automatically invokes request builder.
"""

# DOC_ID: DOC-CORE-AUTOMATION-REQUEST-BUILDER-TRIGGER-001

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional


def check_planning_complete(flag_file: Path = Path(".state/PLANNING_COMPLETE")) -> bool:
    """Check if PLANNING_COMPLETE flag exists"""
    return flag_file.exists()


def get_planning_metadata(flag_file: Path = Path(".state/PLANNING_COMPLETE")) -> dict:
    """Read metadata from PLANNING_COMPLETE flag file"""
    if not flag_file.exists():
        return {}

    try:
        with open(flag_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except:
        # Flag file might be empty marker
        return {}


def trigger_request_builder(
    plan_id: Optional[str] = None, run_id: Optional[str] = None
) -> int:
    """Trigger request builder execution"""
    print(f"[AUTO-TRIGGER] Invoking request builder...")

    cmd = [sys.executable, "-m", "core.engine.execution_request_builder"]

    if plan_id:
        cmd.extend(["--plan-id", plan_id])

    if run_id:
        cmd.extend(["--run-id", run_id])

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=False, timeout=1800
        )

        if result.stdout:
            print(result.stdout)

        if result.returncode == 0:
            print(f"[OK] Request builder completed successfully")

            # Log execution
            log_execution(plan_id, run_id, "success")
            return 0
        else:
            print(
                f"[ERROR] Request builder failed with exit code {result.returncode}",
                file=sys.stderr,
            )
            if result.stderr:
                print(result.stderr, file=sys.stderr)

            log_execution(plan_id, run_id, "failed", result.stderr)
            return 1

    except Exception as e:
        print(f"[ERROR] Failed to invoke request builder: {e}", file=sys.stderr)
        log_execution(plan_id, run_id, "error", str(e))
        return 2


def log_execution(
    plan_id: Optional[str],
    run_id: Optional[str],
    status: str,
    error: Optional[str] = None,
):
    """Log auto-trigger execution to JSONL"""
    log_file = Path("logs/request_builder.jsonl")
    log_file.parent.mkdir(parents=True, exist_ok=True)

    log_entry = {
        "timestamp": time.time(),
        "plan_id": plan_id,
        "run_id": run_id,
        "status": status,
        "error": error,
        "trigger": "auto",
    }

    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"[WARN] Failed to log execution: {e}", file=sys.stderr)


def clear_planning_flag(flag_file: Path = Path(".state/PLANNING_COMPLETE")):
    """Clear PLANNING_COMPLETE flag after processing"""
    try:
        if flag_file.exists():
            flag_file.unlink()
            print(f"[OK] Cleared PLANNING_COMPLETE flag")
    except Exception as e:
        print(f"[WARN] Failed to clear flag: {e}", file=sys.stderr)


def watch_mode(interval: int = 5, clear_flag: bool = True):
    """Watch for PLANNING_COMPLETE flag in continuous mode"""
    print(f"[WATCH] Monitoring for PLANNING_COMPLETE flag (interval: {interval}s)")
    print("[WATCH] Press Ctrl+C to stop")

    try:
        while True:
            if check_planning_complete():
                print(f"\n[DETECTED] PLANNING_COMPLETE flag found")

                metadata = get_planning_metadata()
                plan_id = metadata.get("plan_id")
                run_id = metadata.get("run_id")

                result = trigger_request_builder(plan_id, run_id)

                if clear_flag:
                    clear_planning_flag()

                if result != 0:
                    print(f"[ERROR] Auto-trigger failed, continuing watch...")

            time.sleep(interval)

    except KeyboardInterrupt:
        print(f"\n[STOP] Watch mode stopped")
        return 0


def main():
    """Main CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Auto-trigger request builder on PLANNING_COMPLETE",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # One-shot check and trigger
  python -m core.automation.request_builder_trigger

  # Watch mode (continuous)
  python -m core.automation.request_builder_trigger --watch

  # Custom interval
  python -m core.automation.request_builder_trigger --watch --interval 10
        """,
    )

    parser.add_argument(
        "--watch", action="store_true", help="Run in watch mode (continuous monitoring)"
    )

    parser.add_argument(
        "--interval", type=int, default=5, help="Watch interval in seconds (default: 5)"
    )

    parser.add_argument(
        "--no-clear",
        action="store_true",
        help="Don't clear PLANNING_COMPLETE flag after processing",
    )

    args = parser.parse_args()

    if args.watch:
        return watch_mode(args.interval, not args.no_clear)
    else:
        # One-shot mode
        if check_planning_complete():
            print(f"[DETECTED] PLANNING_COMPLETE flag found")

            metadata = get_planning_metadata()
            plan_id = metadata.get("plan_id")
            run_id = metadata.get("run_id")

            result = trigger_request_builder(plan_id, run_id)

            if not args.no_clear:
                clear_planning_flag()

            return result
        else:
            print(f"[INFO] No PLANNING_COMPLETE flag detected")
            return 0


if __name__ == "__main__":
    sys.exit(main())
