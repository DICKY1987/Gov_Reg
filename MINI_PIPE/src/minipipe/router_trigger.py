#!/usr/bin/env python3
"""
Auto-trigger Router
Implements WS1-004: Auto-trigger Router on task_queue.json changes

Watches for task_queue.json changes and automatically invokes router.
"""

# DOC_ID: DOC-CORE-AUTOMATION-ROUTER-TRIGGER-001

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional


def get_file_mtime(file_path: Path) -> float:
    """Get file modification time"""
    try:
        return file_path.stat().st_mtime if file_path.exists() else 0
    except:
        return 0


def trigger_router(queue_file: Path) -> int:
    """Trigger router execution"""
    print(f"[AUTO-TRIGGER] Invoking router...")

    cmd = [sys.executable, "-m", "core.engine.router", "--queue", str(queue_file)]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=False, timeout=1800
        )

        if result.stdout:
            print(result.stdout)

        if result.returncode == 0:
            print(f"[OK] Router completed successfully")
            log_execution("success")
            return 0
        else:
            print(
                f"[ERROR] Router failed with exit code {result.returncode}",
                file=sys.stderr,
            )
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            log_execution("failed", result.stderr)
            return 1

    except Exception as e:
        print(f"[ERROR] Failed to invoke router: {e}", file=sys.stderr)
        log_execution("error", str(e))
        return 2


def log_execution(status: str, error: Optional[str] = None):
    """Log auto-trigger execution to JSONL"""
    log_file = Path("logs/router_trigger.jsonl")
    log_file.parent.mkdir(parents=True, exist_ok=True)

    log_entry = {
        "timestamp": time.time(),
        "status": status,
        "error": error,
        "trigger": "auto",
    }

    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"[WARN] Failed to log execution: {e}", file=sys.stderr)


def watch_mode(queue_file: Path, interval: int = 2):
    """Watch for task_queue.json changes in continuous mode"""
    print(f"[WATCH] Monitoring {queue_file} for changes (interval: {interval}s)")
    print("[WATCH] Press Ctrl+C to stop")

    last_mtime = get_file_mtime(queue_file)

    try:
        while True:
            current_mtime = get_file_mtime(queue_file)

            if current_mtime > last_mtime and current_mtime > 0:
                print(f"\n[DETECTED] {queue_file} modified")

                result = trigger_router(queue_file)

                if result != 0:
                    print(f"[ERROR] Auto-trigger failed, continuing watch...")

                last_mtime = current_mtime

            time.sleep(interval)

    except KeyboardInterrupt:
        print(f"\n[STOP] Watch mode stopped")
        return 0


def main():
    """Main CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Auto-trigger router on task_queue.json changes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Watch mode (continuous)
  python -m core.automation.router_trigger --watch

  # Custom queue file
  python -m core.automation.router_trigger --watch --queue .state/custom_queue.json

  # Custom interval
  python -m core.automation.router_trigger --watch --interval 5
        """,
    )

    parser.add_argument(
        "--watch", action="store_true", help="Run in watch mode (continuous monitoring)"
    )

    parser.add_argument(
        "--queue",
        type=Path,
        default=Path(".state/task_queue.json"),
        help="Path to task queue file (default: .state/task_queue.json)",
    )

    parser.add_argument(
        "--interval", type=int, default=2, help="Watch interval in seconds (default: 2)"
    )

    args = parser.parse_args()

    if args.watch:
        return watch_mode(args.queue, args.interval)
    else:
        # One-shot mode
        if args.queue.exists():
            print(f"[DETECTED] {args.queue} exists")
            return trigger_router(args.queue)
        else:
            print(f"[INFO] Queue file not found: {args.queue}")
            return 0


if __name__ == "__main__":
    sys.exit(main())
