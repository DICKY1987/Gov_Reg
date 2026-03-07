#!/usr/bin/env python3
# DOC_LINK: DOC-SCRIPT-TOOLS-PFA-WATCH-958
"""
File Watcher - Auto-run pipeline when source schemas change

Watches the schemas/source/ directory for changes and automatically
runs the pipeline regeneration when YAML files are modified.

Usage:
    python pfa_watch.py                    # Watch with default settings
    python pfa_watch.py --quick            # Quick rebuild only
    python pfa_watch.py --debounce 5       # Wait 5 seconds after change
    python pfa_watch.py --dry-run          # Dry-run mode
"""
DOC_ID: DOC-SCRIPT-TOOLS-PFA-WATCH-958

import sys
import DOC-ERROR-UTILS-TIME-145__time
from pathlib import Path
from datetime import datetime
import threading

# Try to import watchdog, install if not available
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("❌ watchdog not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "watchdog"])
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

# Add parent to path for imports
.parent.parent))
from DOC-SCRIPT-TOOLS-PFA-COMMON-944__pfa_common import print_success, print_error, print_warning, print_info

class SchemaChangeHandler(FileSystemEventHandler):
    """Handles file system events for schema changes"""

    def __init__(self, orchestrator, debounce_seconds=2, quick=False, dry_run=False):
        super().__init__()
        self.orchestrator = orchestrator
        self.debounce_seconds = debounce_seconds
        self.quick = quick
        self.dry_run = dry_run
        self.last_modified = {}
        self.timer = None
        self.lock = threading.Lock()

    def on_modified(self, event):
        """Called when a file is modified"""
        if event.is_directory:
            return

        # Only watch YAML files
        if not event.src_path.endswith('.yaml'):
            return

        # Ignore temporary files
        if '~' in event.src_path or event.src_path.endswith('.swp'):
            return

        file_path = Path(event.src_path)
        filename = file_path.name

        # Debounce: ignore if modified very recently
        now = time.time()
        last_time = self.last_modified.get(filename, 0)

        if now - last_time < 1:  # Less than 1 second ago
            return

        self.last_modified[filename] = now

        # Cancel previous timer if exists
        with self.lock:
            if self.timer:
                self.timer.cancel()

            # Start new timer for debounced execution
            self.timer = threading.Timer(
                self.debounce_seconds,
                self._run_pipeline,
                args=(filename,)
            )
            self.timer.start()

    def _run_pipeline(self, filename):
        """Run the pipeline after debounce period"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print()
        print("=" * 70)
        print(f"[{timestamp}] 📝 Detected change: {filename}")
        print("=" * 70)
        print()

        # Import here to avoid circular dependency
        from pfa_run_pipeline import PipelineOrchestrator

        try:
            orchestrator = PipelineOrchestrator(self.orchestrator)
            success = orchestrator.run_full_pipeline(
                dry_run=self.dry_run,
                quick=self.quick
            )

            if success:
                print()
                print_success("✅ Auto-rebuild complete!")
            else:
                print()
                print_warning("⚠️  Auto-rebuild completed with errors")

        except Exception as e:
            print_error(f"❌ Auto-rebuild failed: {e}")

        print()
        print("👀 Watching for next change...")
        print()

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Watch source schemas and auto-run pipeline on changes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pfa_watch.py                # Watch with defaults
  python pfa_watch.py --quick        # Quick rebuilds only
  python pfa_watch.py --debounce 5   # Wait 5s after changes
  python pfa_watch.py --dry-run      # Preview mode

Press Ctrl+C to stop watching.
        """
    )

    parser.add_argument('--quick', action='store_true',
                        help='Only rebuild if source schemas changed')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview changes without modifying files')
    parser.add_argument('--debounce', type=int, default=2,
                        help='Seconds to wait after change before rebuilding (default: 2)')

    args = parser.parse_args()

    # Get base directory
    base_dir = Path(__file__).parent.parent
    watch_dir = base_dir / 'schemas' / 'source'

    if not watch_dir.exists():
        print_error(f"Watch directory not found: {watch_dir}")
        sys.exit(1)

    # Create event handler
    event_handler = SchemaChangeHandler(
        orchestrator=base_dir,
        debounce_seconds=args.debounce,
        quick=args.quick,
        dry_run=args.dry_run
    )

    # Create and start observer
    observer = Observer()
    observer.schedule(event_handler, str(watch_dir), recursive=False)
    observer.start()

    print("=" * 70)
    print("👀 SCHEMA WATCHER - Auto-rebuild on changes")
    print("=" * 70)
    print()
    print(f"Watching: {watch_dir}")
    print(f"Debounce: {args.debounce} seconds")
    print(f"Mode: {'Quick' if args.quick else 'Full'} rebuild")
    if args.dry_run:
        print_warning("Dry-run mode enabled")
    print()
    print("Press Ctrl+C to stop watching...")
    print()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print()
        print_info("Stopping watcher...")
        observer.stop()

    observer.join()
    print_success("✅ Watcher stopped")

if __name__ == '__main__':
    main()
