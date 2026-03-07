#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# TRIGGER_ID: TRIGGER-WATCHER-FILE-WATCHER-HARDENED-001
# DOC_LINK: DOC-SCRIPT-DOC-ID-FILE-WATCHER-HARDENED-010
"""
DOC_ID File Watcher - HARDENED VERSION with Precision Detection

ENHANCEMENTS v2:
1. Segment-based matching (not substrings) to avoid false positives
2. File stability checks (avoid writing to files mid-save)
3. Assignment limits (--max-assign-per-scan)
4. Dry-run mode (--dry-run)
5. Real end-to-end testing
6. Registry non-destructive updates

PATTERN: EXEC-003 Tool Availability Guards
Ground Truth: Watcher process running, precise categorization, safe assignment

USAGE:
    python file_watcher_v2_hardened.py                    # Production
    python file_watcher_v2_hardened.py --dry-run          # Simulation
    python file_watcher_v2_hardened.py --max-assign 50    # Limit blast radius
"""

import argparse
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Tuple

# PATTERN: Tool availability guard
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("❌ watchdog not installed")
    print("Run: pip install watchdog")
    sys.exit(1)

# Add parent directory to path for common module import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import from common module
from common import REPO_ROOT, MODULE_ROOT

SCANNER_SCRIPT = MODULE_ROOT / "1_CORE_OPERATIONS" / "doc_id_scanner.py"
ASSIGNER_SCRIPT = MODULE_ROOT / "1_CORE_OPERATIONS" / "doc_id_assigner.py"
ELIGIBLE_EXTENSIONS = {'.py', '.md', '.yaml', '.yml', '.json', '.ps1', '.sh', '.txt'}
EXCLUDE_DIRS = {'.git', '__pycache__', '.venv', 'node_modules', '.pytest_cache',
                'UTI_Archives', 'Backups', '.acms_runs', 'envs'}

# File stability check constants
FILE_STABILITY_CHECKS = 2
FILE_STABILITY_DELAY_MS = 300  # milliseconds
FILE_MIN_AGE_SECONDS = 2  # Don't process files modified within last 2 seconds

# MONITORED_FOLDERS: Explicit high-priority mappings
MONITORED_FOLDERS = {
    'glossary': {
        'path': REPO_ROOT / 'SUB_GLOSSARY',
        'patterns': ['.yaml', '.yml', '.md', '.py'],
        'category': 'glossary',
        'exclude': ['config', '__pycache__', '.glossary-metadata.yaml']
    },
    'process_schemas': {
        'path': REPO_ROOT / 'PROCESS_STEP_LIB' / 'schemas' / 'source',
        'patterns': ['.yaml', '.yml'],
        'category': 'spec',
        'exclude': []
    },
    'process_tools': {
        'path': REPO_ROOT / 'PROCESS_STEP_LIB' / 'tools',
        'patterns': ['.py'],
        'category': 'script',
        'exclude': ['__pycache__', '__init__.py']
    },
    'runtime': {
        'path': REPO_ROOT / 'RUNTIME',
        'patterns': ['.py', '.yaml', '.yml', '.md', '.json'],
        'category': 'runtime',
        'exclude': ['__pycache__']
    },
    'governance': {
        'path': REPO_ROOT / 'GOVERNANCE',
        'patterns': ['.md', '.yaml', '.yml', '.json'],
        'category': 'policy',
        'exclude': []
    },
    'context': {
        'path': REPO_ROOT / 'CONTEXT',
        'patterns': ['.md', '.yaml', '.yml', '.json'],
        'category': 'guide',
        'exclude': []
    },
    'scripts': {
        'path': REPO_ROOT / 'scripts',
        'patterns': ['.py', '.ps1', '.sh'],
        'category': 'script',
        'exclude': ['__pycache__']
    },
    'tests': {
        'path': REPO_ROOT / 'tests',
        'patterns': ['.py'],
        'category': 'test',
        'exclude': ['__pycache__', '__init__.py']
    },
    'uti_tools': {
        'path': REPO_ROOT / 'UTI_TOOLS',
        'patterns': ['.py', '.ps1'],
        'category': 'script',
        'exclude': ['__pycache__']
    },
    'automation': {
        'path': REPO_ROOT / 'automation',
        'patterns': ['.py'],
        'category': 'script',
        'exclude': ['__pycache__', '__init__.py']
    },
    'modules': {
        'path': REPO_ROOT / 'modules',
        'patterns': ['.py'],
        'category': 'module',
        'exclude': ['__pycache__', '__init__.py']
    },
    'docs': {
        'path': REPO_ROOT / 'docs',
        'patterns': ['.md', '.yaml', '.yml'],
        'category': 'guide',
        'exclude': []
    },
    'contracts': {
        'path': REPO_ROOT / 'CONTRACTS',
        'patterns': ['.md', '.yaml', '.yml', '.json'],
        'category': 'contract',
        'exclude': []
    },
    'workflows': {
        'path': REPO_ROOT / 'WORKFLOWS',
        'patterns': ['.yaml', '.yml', '.json', '.md'],
        'category': 'workflow',
        'exclude': []
    },
    'config': {
        'path': REPO_ROOT / 'config',
        'patterns': ['.yaml', '.yml', '.json'],
        'category': 'config',
        'exclude': []
    },
    'data': {
        'path': REPO_ROOT / 'data',
        'patterns': ['.json', '.yaml', '.yml'],
        'category': 'data',
        'exclude': []
    },
    'specs': {
        'path': REPO_ROOT / 'specs',
        'patterns': ['.yaml', '.yml', '.md'],
        'category': 'spec',
        'exclude': []
    },
    'benchmarks': {
        'path': REPO_ROOT / 'benchmarks',
        'patterns': ['.py', '.yaml', '.yml'],
        'category': 'benchmark',
        'exclude': ['__pycache__']
    },
}


def smart_category_detection(path: Path) -> str:
    """
    HARDENED v2: Segment-based category detection with precedence layers.

    Precedence (high to low):
    1. Filename pattern matching (e.g., test_*.py, *_test.py) - HIGHEST
    2. Path segment matching (e.g., /tests/, /docs/)
    3. Directory name heuristics
    4. File extension fallback
    5. 'general' default

    Args:
        path: Path object of the file

    Returns:
        Category string (e.g., 'test', 'script', 'guide', 'general')
    """
    try:
        rel_path = path.relative_to(REPO_ROOT)
        path_str = str(rel_path).replace('\\', '/')
        parts = path_str.split('/')
        filename = path.name.lower()
    except ValueError:
        # Path not under REPO_ROOT
        return 'general'

    # Layer 1: Filename pattern matching (PRECISE - regex boundaries, HIGHEST PRIORITY)
    # This must come FIRST to override segment matching
    filename_patterns = {
        'test': [
            r'^test_.*\.py$',
            r'.*_test\.py$',
            r'^test.*\.py$',
        ],
        'script': [
            r'.*\.(ps1|sh)$',
        ],
        'config': [
            r'.*config.*\.(yaml|yml|json)$',
            r'.*settings.*\.(yaml|yml|json)$',
        ],
    }

    for category, patterns in filename_patterns.items():
        if any(re.match(pattern, filename) for pattern in patterns):
            return category

    # Layer 2: Path segment matching (PRECISE - no false positives)
    segment_map = {
        'test': ['tests', 'test'],
        'script': ['scripts', 'automation'],
        'guide': ['docs', 'doc', 'documentation'],
        'policy': ['governance', 'policies', 'policy'],
        'spec': ['specs', 'spec', 'schemas', 'schema'],
        'runtime': ['runtime'],
        'workflow': ['workflows', 'workflow'],
        'config': ['config', 'configuration'],
        'contract': ['contracts', 'contract'],
        'module': ['modules', 'module'],
        'data': ['data'],
        'benchmark': ['benchmarks', 'benchmark'],
        'template': ['templates', 'template'],
        'prompt': ['prompts', 'prompt'],
    }

    # Check each path segment
    for category, segment_names in segment_map.items():
        if any(seg.lower() in segment_names for seg in parts):
            return category

    # Layer 3: Directory name heuristics (parent directory)
    # Layer 3: Directory name heuristics (parent directory)
    if len(parts) > 1:
        parent_dir = parts[-2].lower()
        # Direct mapping (avoid substring issues)
        if parent_dir in ['tests', 'test']:
            return 'test'
        elif parent_dir in ['scripts', 'script', 'automation']:
            return 'script'
        elif parent_dir in ['docs', 'doc', 'documentation']:
            return 'guide'
        elif parent_dir in ['governance', 'policies']:
            return 'policy'

    # Layer 4: File extension fallback
    ext = path.suffix.lower()
    if ext == '.py':
        # Avoid misclassifying all .py as 'script'
        # Already checked test patterns above
        # Default to module for uncategorized .py files
        return 'module'
    elif ext in ['.md', '.txt']:
        return 'guide'
    elif ext in ['.yaml', '.yml', '.json']:
        return 'config'
    elif ext in ['.ps1', '.sh']:
        return 'script'

    # Layer 5: Default
    return 'general'


def check_file_stable(file_path: Path) -> bool:
    """
    HARDENED v2: Check if file is stable (not being written).

    Returns True if:
    - File exists
    - Size unchanged across multiple checks
    - mtime is older than threshold

    Args:
        file_path: Path to check

    Returns:
        bool: True if file is stable
    """
    if not file_path.exists():
        return False

    try:
        # Check 1: File must be at least FILE_MIN_AGE_SECONDS old
        stat1 = file_path.stat()
        age = time.time() - stat1.st_mtime
        if age < FILE_MIN_AGE_SECONDS:
            return False

        # Check 2: Size must be stable across multiple checks
        size1 = stat1.st_size
        for _ in range(FILE_STABILITY_CHECKS - 1):
            time.sleep(FILE_STABILITY_DELAY_MS / 1000.0)
            if not file_path.exists():
                return False
            size2 = file_path.stat().st_size
            if size1 != size2:
                return False
            size1 = size2

        return True
    except (OSError, IOError):
        return False


class DocIDEventHandler(FileSystemEventHandler):
    """Handle file system events for DOC_ID scanning"""

    def __init__(self, debounce_seconds=300, dry_run=False, max_assign_per_scan=100):
        self.last_scan = datetime.min
        self.debounce = timedelta(seconds=debounce_seconds)
        self.pending_scan = False
        self.modified_files = set()
        self.dry_run = dry_run
        self.max_assign_per_scan = max_assign_per_scan
        self.stats = {
            'files_detected': 0,
            'files_stable': 0,
            'files_unstable': 0,
            'doc_ids_assigned': 0,
            'doc_ids_skipped_limit': 0,
            'explicit_matches': 0,
            'smart_detections': 0,
            'scan_triggers': 0,
            'category_distribution': {}
        }

    def should_process(self, path: Path) -> bool:
        """Check if file should trigger scan"""
        # Skip directories
        if path.is_dir():
            return False

        # Check extension
        if path.suffix not in ELIGIBLE_EXTENSIONS:
            return False

        # Check excluded directories
        if any(excluded in path.parts for excluded in EXCLUDE_DIRS):
            return False

        return True

    def get_folder_category(self, path: Path) -> Tuple[str, str]:
        """
        HARDENED v2: Determine doc_id category with detection method.

        Returns:
            Tuple[category, method] where method is 'explicit' or 'smart'
        """
        try:
            # Try explicit mapping first
            for folder_name, folder_config in MONITORED_FOLDERS.items():
                folder_path = folder_config['path']
                if not folder_path.exists():
                    continue

                # Check if file is under this folder
                try:
                    rel_path = path.relative_to(folder_path)

                    # Check file extension matches patterns
                    if path.suffix not in folder_config['patterns']:
                        continue

                    # Check exclusions
                    if any(excl in str(rel_path) for excl in folder_config['exclude']):
                        continue

                    self.stats['explicit_matches'] += 1
                    return folder_config['category'], 'explicit'
                except ValueError:
                    # Not relative to this folder
                    continue

            # Fall back to smart detection
            category = smart_category_detection(path)
            if category:
                self.stats['smart_detections'] += 1
                return category, 'smart'

        except Exception as e:
            print(f"⚠️  Error determining category for {path}: {e}")

        return 'general', 'fallback'

    def has_doc_id(self, file_path: Path) -> bool:
        """Check if file already has a doc_id."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            return bool(re.search(r'DOC-[A-Z]+-[A-Z0-9-]+-[0-9]+', content))
        except Exception:
            return False

    def on_modified(self, event):
        """Trigger scan on file modification"""
        if event.is_directory:
            return

        path = Path(event.src_path)

        if not self.should_process(path):
            return

        # Track modified file
        self.modified_files.add(str(path.relative_to(REPO_ROOT)))
        self.stats['files_detected'] += 1

        # Debounce
        now = datetime.now()
        if now - self.last_scan < self.debounce:
            self.pending_scan = True
            return

        # Trigger scan
        self.trigger_scan()

    def on_created(self, event):
        """Handle new files"""
        self.on_modified(event)

    def on_moved(self, event):
        """Handle moved/renamed files (atomic save pattern)"""
        if not event.is_directory:
            # Treat destination as new file
            path = Path(event.dest_path)
            if self.should_process(path):
                self.modified_files.add(str(path.relative_to(REPO_ROOT)))
                self.stats['files_detected'] += 1
                self.pending_scan = True

    def trigger_scan(self):
        """Execute scanner and assign doc_ids to new files"""
        if not self.modified_files:
            return

        print(f"\n[{datetime.now():%Y-%m-%d %H:%M:%S}] Files changed: {len(self.modified_files)}")
        if self.dry_run:
            print("🔍 DRY RUN MODE - No files will be modified")
        self.stats['scan_triggers'] += 1

        # Group files by category and check stability
        files_by_category = {}
        for file_str in list(self.modified_files):
            file_path = REPO_ROOT / file_str
            if not file_path.exists():
                continue

            # HARDENED v2: Check file stability
            if not check_file_stable(file_path):
                print(f"⏳ Unstable: {file_str} (skipping)")
                self.stats['files_unstable'] += 1
                continue

            self.stats['files_stable'] += 1

            # Get category
            category, method = self.get_folder_category(file_path)
            if category:
                files_by_category.setdefault(category, []).append((file_path, method))

                # Track category distribution
                self.stats['category_distribution'][category] = \
                    self.stats['category_distribution'].get(category, 0) + 1

        # Assign doc_ids by category (with limit)
        if files_by_category:
            total_files = sum(len(files) for files in files_by_category.values())
            assigned_count = 0

            print(f"\n🔍 Checking {total_files} stable files across {len(files_by_category)} categories for doc_ids...")
            if self.max_assign_per_scan < total_files:
                print(f"⚠️  Assignment limit: {self.max_assign_per_scan} files per scan")

            for category, file_method_list in files_by_category.items():
                print(f"\n   Category: {category}")
                for file_path, method in file_method_list:
                    # Check assignment limit
                    if assigned_count >= self.max_assign_per_scan:
                        print(f"  ⏸️  Limit reached ({self.max_assign_per_scan}), deferring remaining files")
                        self.stats['doc_ids_skipped_limit'] += 1
                        break

                    # Check if file already has doc_id
                    if self.has_doc_id(file_path):
                        continue

                    rel_path_str = str(file_path.relative_to(REPO_ROOT))
                    print(f"  📝 [{method}] {rel_path_str} → {category}")

                    if self.dry_run:
                        print(f"     [DRY RUN] Would assign DOC-{category.upper()}-*")
                        continue

                    # Invoke assigner in single mode
                    try:
                        result = subprocess.run(
                            [sys.executable, str(ASSIGNER_SCRIPT),
                             'single', '--file', str(file_path), '--category', category],
                            capture_output=True,
                            text=True,
                            cwd=REPO_ROOT,
                            timeout=60
                        )

                        if result.returncode == 0:
                            self.stats['doc_ids_assigned'] += 1
                            assigned_count += 1
                            # Extract doc_id from output
                            for line in result.stdout.split('\n'):
                                if 'DOC-' in line:
                                    print(f"     ✅ {line.strip()}")
                                    break
                        else:
                            print(f"     ❌ Assignment failed: {result.stderr[:100]}")
                    except subprocess.TimeoutExpired:
                        print(f"     ❌ Timeout (60s exceeded)")
                    except Exception as e:
                        print(f"     ❌ Error: {e}")

        # Run scanner (unless dry-run)
        if not self.dry_run:
            print(f"\n📊 Triggering scan...")

            result = subprocess.run(
                [sys.executable, str(SCANNER_SCRIPT), 'scan'],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
                timeout=120
            )

            if result.returncode == 0:
                print("✅ Scan completed successfully")
                # Parse and display coverage
                if 'Coverage:' in result.stdout:
                    for line in result.stdout.split('\n'):
                        if 'Coverage:' in line or 'Scanned:' in line:
                            print(f"   {line.strip()}")
            else:
                print(f"❌ Scan failed (exit code: {result.returncode})")
                if result.stderr:
                    print(f"Error: {result.stderr[:200]}")

        # Display stats
        print(f"\n📈 Session Stats:")
        print(f"   Files detected: {self.stats['files_detected']}")
        print(f"   Files stable: {self.stats['files_stable']}")
        print(f"   Files unstable (skipped): {self.stats['files_unstable']}")
        print(f"   Doc IDs assigned: {self.stats['doc_ids_assigned']}")
        print(f"   Doc IDs deferred (limit): {self.stats['doc_ids_skipped_limit']}")
        print(f"   Explicit matches: {self.stats['explicit_matches']}")
        print(f"   Smart detections: {self.stats['smart_detections']}")
        print(f"   Scan triggers: {self.stats['scan_triggers']}")

        if self.stats['category_distribution']:
            print(f"\n📊 Category Distribution:")
            for cat, count in sorted(self.stats['category_distribution'].items(),
                                     key=lambda x: x[1], reverse=True):
                print(f"   {cat}: {count}")

        self.last_scan = datetime.now()
        self.modified_files.clear()
        self.pending_scan = False


def main():
    parser = argparse.ArgumentParser(
        description="DOC_ID File Watcher - HARDENED VERSION with Precision Detection"
    )
    parser.add_argument('--debounce', type=int, default=300,
                       help='Debounce interval in seconds (default: 300)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Simulate without modifying files')
    parser.add_argument('--max-assign', type=int, default=100,
                       help='Max files to assign per scan (default: 100)')
    args = parser.parse_args()

    print("═══════════════════════════════════════════════════════════════")
    print("   DOC_ID FILE WATCHER - HARDENED v2")
    print("═══════════════════════════════════════════════════════════════")
    print(f"Watching: {REPO_ROOT}")
    print(f"Scanner: {SCANNER_SCRIPT}")
    print(f"Debounce: {args.debounce} seconds")
    print(f"Max assign per scan: {args.max_assign}")
    print(f"Dry run: {args.dry_run}")
    print(f"Monitored folders: {len(MONITORED_FOLDERS)} explicit + smart detection")
    print(f"Enhancements: Segment matching, stability checks, assignment limits")
    print("Press Ctrl+C to stop")
    print("═══════════════════════════════════════════════════════════════\n")

    # Verify scanner exists
    if not SCANNER_SCRIPT.exists():
        print(f"❌ Scanner not found: {SCANNER_SCRIPT}")
        sys.exit(1)

    # Verify assigner exists (unless dry-run)
    if not args.dry_run and not ASSIGNER_SCRIPT.exists():
        print(f"❌ Assigner not found: {ASSIGNER_SCRIPT}")
        sys.exit(1)

    # Create handler and observer
    handler = DocIDEventHandler(
        debounce_seconds=args.debounce,
        dry_run=args.dry_run,
        max_assign_per_scan=args.max_assign
    )
    observer = Observer()
    observer.schedule(handler, str(REPO_ROOT), recursive=True)
    observer.start()

    print("✅ Watcher started - monitoring for changes across all directories...\n")

    try:
        while True:
            time.sleep(1)
            # Check for pending scans
            if handler.pending_scan:
                now = datetime.now()
                if now - handler.last_scan >= handler.debounce:
                    handler.trigger_scan()
    except KeyboardInterrupt:
        print("\n\nStopping watcher...")
        observer.stop()

    observer.join()
    print("✅ Watcher stopped")

    # Final stats
    print("\n" + "="*60)
    print("FINAL SESSION STATS:")
    print("="*60)
    for key, value in handler.stats.items():
        if key != 'category_distribution':
            print(f"  {key}: {value}")
    if handler.stats['category_distribution']:
        print("\n  Category Distribution:")
        for cat, count in sorted(handler.stats['category_distribution'].items(),
                                 key=lambda x: x[1], reverse=True):
            print(f"    {cat}: {count}")
    print("="*60)

    sys.exit(0)


if __name__ == '__main__':
    main()
