# DOC_LINK: DOC-CORE-3-AUTOMATION-HOOKS-V3-FILE-WATCHER-521
# TRIGGER_ID: TRIGGER-WATCHER-V3-FILE-WATCHER-002
"""
Registry V3 File Watcher
DOC_LINK: A-REGV3-FILEWATCHER-008
Work ID: WORK-REGV3-002

Monitors file system for changes and triggers V3 scans automatically.
"""

import sys
import time
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class V3FileHandler(FileSystemEventHandler):
    """Handler for file system events triggering V3 scans"""

    def __init__(self, v3_db_path: str, repo_root: str, debounce_seconds: int = 5):
        self.v3_db_path = Path(v3_db_path)
        self.repo_root = Path(repo_root)
        self.debounce_seconds = debounce_seconds
        self.pending_files = set()
        self.last_trigger = time.time()

    def on_modified(self, event):
        if event.is_directory:
            return

        # Filter: only Python, JSON, YAML files
        if not event.src_path.endswith(('.py', '.json', '.yaml', '.yml')):
            return

        self.pending_files.add(event.src_path)

        # Debounce: wait for quiet period before triggering
        current_time = time.time()
        if current_time - self.last_trigger > self.debounce_seconds:
            self.trigger_v3_scan()

    def trigger_v3_scan(self):
        """Trigger V3 scan for pending files"""
        if not self.pending_files:
            return

        run_id = str(uuid.uuid4())
        trace_id = f"FILEWATCHER-{time.strftime('%Y%m%d-%H%M%S')}"

        logger.info(f"Triggering V3 scan for {len(self.pending_files)} files (trace_id={trace_id})")

        # Call backfill script for changed files
        backfill_script = self.repo_root / "SUB_DOC_ID" / "migration_v3" / "tools" / "backfill_tier2_tier3.py"

        if backfill_script.exists():
            try:
                cmd = [
                    sys.executable,
                    str(backfill_script),
                    "--db", str(self.v3_db_path),
                    "--repo-root", str(self.repo_root),
                    "--batch-size", "50",
                    "--run-id", run_id,
                    "--trace-id", trace_id
                ]

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

                if result.returncode == 0:
                    logger.info(f"V3 scan completed successfully (trace_id={trace_id})")
                else:
                    logger.error(f"V3 scan failed: {result.stderr}")

            except subprocess.TimeoutExpired:
                logger.error(f"V3 scan timed out after 300 seconds")
            except Exception as e:
                logger.error(f"Error triggering V3 scan: {e}")
        else:
            logger.warning(f"Backfill script not found: {backfill_script}")
            # Log the files that would be scanned
            for file_path in self.pending_files:
                logger.info(f"  - {file_path}")

        self.pending_files.clear()
        self.last_trigger = time.time()


def start_file_watcher(watch_path: str, v3_db_path: str, repo_root: str):
    """Start file system watcher"""
    event_handler = V3FileHandler(v3_db_path, repo_root)
    observer = Observer()
    observer.schedule(event_handler, watch_path, recursive=True)
    observer.start()

    logger.info(f"V3 File Watcher started: watching {watch_path}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python v3_file_watcher.py <watch_path> <v3_db_path> <repo_root>")
        sys.exit(1)

    start_file_watcher(sys.argv[1], sys.argv[2], sys.argv[3])
