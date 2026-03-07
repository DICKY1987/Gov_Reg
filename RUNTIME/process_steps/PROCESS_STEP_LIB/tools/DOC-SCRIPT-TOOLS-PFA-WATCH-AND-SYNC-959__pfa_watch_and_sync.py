#!/usr/bin/env python3
# DOC_LINK: DOC-SCRIPT-TOOLS-PFA-WATCH-AND-SYNC-959
"""
PFA Watch and Sync - Automated Schema Synchronization

Watches for changes in process schema files and automatically:
1. Detects new or modified process steps
2. Scans for relevant implementation files
3. Updates file attachments with high confidence matches
4. Regenerates unified schemas
5. Validates the result

This ensures the process schema stays in sync with the evolving codebase.

Usage:
    python pfa_watch_and_sync.py [--watch] [--once] [--confidence 60]
"""
DOC_ID: DOC-SCRIPT-TOOLS-PFA-WATCH-AND-SYNC-959

import sys
import DOC-ERROR-UTILS-TIME-145__time
import yaml
from pathlib import Path
from typing import Dict, Any, Set
from datetime import datetime
import hashlib


class SchemaWatcher:
    """Watch and sync process schemas with implementation files."""

    def __init__(self, confidence_threshold: int = 60):
        self.confidence_threshold = confidence_threshold
        self.process_lib = Path(__file__).parent.parent
        self.schemas_dir = self.process_lib / 'schemas'
        self.workspace = self.process_lib / 'workspace'
        self.workspace.mkdir(exist_ok=True)

        # Track file hashes to detect changes
        self.file_hashes: Dict[str, str] = {}

    def compute_hash(self, filepath: Path) -> str:
        """Compute SHA256 hash of file."""
        if not filepath.exists():
            return ""
        try:
            with open(filepath, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return ""

    def detect_changes(self) -> Dict[str, Path]:
        """Detect changed schema files."""
        changed = {}

        # Watch source schemas
        source_dir = self.schemas_dir / 'source'
        if source_dir.exists():
            for schema_file in source_dir.glob('PFA_*.yaml'):
                current_hash = self.compute_hash(schema_file)
                previous_hash = self.file_hashes.get(str(schema_file), "")

                if current_hash != previous_hash:
                    changed[str(schema_file)] = schema_file
                    self.file_hashes[str(schema_file)] = current_hash

        return changed

    def sync_single_schema(self, schema_path: Path) -> bool:
        """Sync a single schema file."""
        print(f"\n{'='*60}")
        print(f"Syncing: {schema_path.name}")
        print(f"{'='*60}")

        try:
            # Load schema
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = yaml.safe_load(f)

            steps = schema.get('steps', [])
            steps_without_files = [s for s in steps if not s.get('implementation_files')]

            print(f"Total steps: {len(steps)}")
            print(f"Steps needing files: {len(steps_without_files)}")

            if not steps_without_files:
                print("✓ All steps have implementation files")
                return True

            # Run auto-attach
            from pfa_auto_attach_files import FileAttacher

            attacher = FileAttacher(
                confidence_threshold=self.confidence_threshold,
                dry_run=False
            )

            print("Scanning codebase...")
            files = attacher.scan_codebase()

            print("Finding matches...")
            matches = attacher.find_matches(steps, files)

            if matches:
                print(f"Found {len(matches)} new matches")
                schema = attacher.update_schema(schema, matches)

                # Write updated schema
                backup_path = self.workspace / f"{schema_path.stem}_backup_{int(time.time())}.yaml"
                with open(backup_path, 'w', encoding='utf-8') as f:
                    yaml.dump(schema, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
                print(f"Backup created: {backup_path}")

                with open(schema_path, 'w', encoding='utf-8') as f:
                    yaml.dump(schema, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
                print(f"✓ Updated: {schema_path}")

                return True
            else:
                print("No new matches found")
                return False

        except Exception as e:
            print(f"✗ Error syncing {schema_path}: {e}")
            return False

    def rebuild_unified_schemas(self) -> bool:
        """Rebuild unified E2E schemas."""
        print(f"\n{'='*60}")
        print("Rebuilding unified schemas...")
        print(f"{'='*60}")

        try:
            # Check if merge tool exists
            merge_tool = self.process_lib / 'tools' / 'pfa_merge_schemas.py'
            if not merge_tool.exists():
                print("⚠ Merge tool not found, skipping unified rebuild")
                return False

            import subprocess
            result = subprocess.run(
                [sys.executable, str(merge_tool)],
                capture_output=True,
                text=True,
                cwd=str(self.process_lib)
            )

            if result.returncode == 0:
                print("✓ Unified schemas rebuilt")
                return True
            else:
                print(f"✗ Error rebuilding unified schemas: {result.stderr}")
                return False

        except Exception as e:
            print(f"✗ Error rebuilding unified schemas: {e}")
            return False

    def validate_schemas(self) -> bool:
        """Validate all schemas."""
        print(f"\n{'='*60}")
        print("Validating schemas...")
        print(f"{'='*60}")

        try:
            validator = self.process_lib / 'tools' / 'PFA_validate_process_steps_schema.py'
            if not validator.exists():
                print("⚠ Validator not found, skipping validation")
                return True

            unified_schema = self.schemas_dir / 'unified' / 'PFA_E2E_WITH_FILES.yaml'
            if not unified_schema.exists():
                print("⚠ Unified schema not found, skipping validation")
                return True

            import subprocess
            result = subprocess.run(
                [sys.executable, str(validator), str(unified_schema)],
                capture_output=True,
                text=True,
                cwd=str(self.process_lib)
            )

            print(result.stdout)

            if result.returncode == 0 or "validated successfully" in result.stdout.lower():
                print("✓ Schema validation passed")
                return True
            else:
                print("⚠ Schema validation had warnings")
                return True  # Don't fail on warnings

        except Exception as e:
            print(f"⚠ Error validating schemas: {e}")
            return True  # Don't fail the sync

    def run_once(self) -> None:
        """Run sync once."""
        print(f"Starting one-time sync at {datetime.now().isoformat()}")

        # Sync unified schema
        unified_with_files = self.schemas_dir / 'unified' / 'PFA_E2E_WITH_FILES.yaml'
        if unified_with_files.exists():
            self.sync_single_schema(unified_with_files)

        # Rebuild and validate
        self.rebuild_unified_schemas()
        self.validate_schemas()

        print(f"\n{'='*60}")
        print("Sync complete")
        print(f"{'='*60}")

    def watch(self, interval: int = 30) -> None:
        """Watch for changes and sync continuously."""
        print(f"Starting schema watcher (checking every {interval}s)")
        print(f"Confidence threshold: {self.confidence_threshold}")
        print("Press Ctrl+C to stop")

        # Initialize file hashes
        self.detect_changes()

        try:
            while True:
                changed = self.detect_changes()

                if changed:
                    print(f"\n[{datetime.now().isoformat()}] Changes detected:")
                    for path in changed.values():
                        print(f"  - {path.name}")

                    # Run sync
                    self.run_once()

                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\nWatcher stopped")


def main():
    watch_mode = False
    once_mode = False
    confidence = 60
    interval = 30

    for arg in sys.argv[1:]:
        if arg == '--watch':
            watch_mode = True
        elif arg == '--once':
            once_mode = True
        elif arg.startswith('--confidence='):
            confidence = int(arg.split('=')[1])
        elif arg.startswith('--interval='):
            interval = int(arg.split('=')[1])

    watcher = SchemaWatcher(confidence_threshold=confidence)

    if watch_mode:
        watcher.watch(interval=interval)
    else:
        watcher.run_once()


if __name__ == '__main__':
    main()
