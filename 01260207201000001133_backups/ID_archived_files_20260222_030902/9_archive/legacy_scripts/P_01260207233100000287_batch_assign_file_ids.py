#!/usr/bin/env python3
"""
Batch File ID Assignment - Add file IDs to existing files and register them

Scans directory for .py, .yaml, .yml, and .json files without file IDs,
allocates IDs for them, renames files, updates JSON content, and adds to registry.

Usage:
    python batch_assign_file_ids.py --root /path/to/scan --registry registry.json
    python batch_assign_file_ids.py --root . --dry-run
"""

import json
import shutil
import sys
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime
from dataclasses import dataclass

# Import the ID allocator
sys.path.insert(0, str(Path(__file__).parent))
from P_01999000042260124027_id_allocator import IDAllocator


@dataclass
class FileToProcess:
    """Represents a file that needs a file ID assigned."""
    original_path: Path
    file_name: str
    extension: str
    is_python: bool
    needs_id: bool
    reason: str


class BatchFileIDAssigner:
    """Batch assign file IDs to existing files without them."""

    def __init__(
        self,
        counter_path: Path,
        registry_path: Path = None,
        dry_run: bool = False
    ):
        self.allocator = IDAllocator(counter_path)
        self.registry_path = registry_path
        self.dry_run = dry_run
        self.files_to_process: List[FileToProcess] = []
        self.assignments: List[Dict] = []

    def scan_directory(self, root_path: Path, exclude_dirs: List[str] = None) -> int:
        """
        Scan directory for files without file IDs.

        Args:
            root_path: Root directory to scan
            exclude_dirs: Directories to exclude from scan

        Returns:
            Number of files found needing IDs
        """
        exclude_dirs = exclude_dirs or [
            'backups', 'BACKUP_FILES', '.git', '.pytest_cache',
            '__pycache__', 'node_modules', 'venv', '.venv'
        ]

        print(f"\n{'='*70}")
        print("SCANNING FOR FILES WITHOUT FILE IDs")
        print(f"{'='*70}\n")
        print(f"Root: {root_path}")
        print(f"Excluding: {', '.join(exclude_dirs)}\n")

        # Target extensions
        extensions = ['*.py', '*.ps1', '*.yaml', '*.yml', '*.json']
        files_found = []

        for ext in extensions:
            files_found.extend(root_path.rglob(ext))

        # Filter excluded directories
        files_to_check = [
            f for f in files_found
            if not any(excluded in str(f) for excluded in exclude_dirs)
        ]

        print(f"Found {len(files_to_check)} files to check\n")

        # Check each file
        for file_path in files_to_check:
            file_info = self._check_file(file_path)
            if file_info and file_info.needs_id:
                self.files_to_process.append(file_info)

        print(f"✅ Found {len(self.files_to_process)} files needing file IDs\n")
        return len(self.files_to_process)

    def _check_file(self, file_path: Path) -> FileToProcess:
        """Check if a file needs a file ID."""
        file_name = file_path.name
        extension = file_path.suffix
        is_python = extension == '.py'

        # Check if file already has an ID
        # Python: P_{20-digit}_name.py
        # Others: {20-digit}_name.ext
        import re

        if is_python:
            pattern = r'^P_(\d{20})_'
        else:
            pattern = r'^(\d{20})_'

        match = re.match(pattern, file_name)

        if match:
            # File already has an ID
            return None

        # File needs an ID
        reason = "No file ID in filename"
        return FileToProcess(
            original_path=file_path,
            file_name=file_name,
            extension=extension,
            is_python=is_python,
            needs_id=True,
            reason=reason
        )

    def assign_ids(self, purpose: str = "Batch assign file IDs to existing files") -> int:
        """
        Assign file IDs to all scanned files.

        Args:
            purpose: Purpose string for allocation tracking

        Returns:
            Number of files processed
        """
        if not self.files_to_process:
            print("⚠️  No files to process")
            return 0

        count = len(self.files_to_process)
        print(f"\n{'='*70}")
        print(f"ASSIGNING {count} FILE IDs")
        print(f"{'='*70}\n")

        if self.dry_run:
            print("🔍 DRY RUN MODE - No files will be modified\n")

        # Allocate IDs in batch
        try:
            allocated_ids = self.allocator.allocate_batch_ids(count, purpose)
        except Exception as e:
            print(f"❌ Failed to allocate IDs: {e}")
            return 0

        # Process each file
        for i, file_info in enumerate(self.files_to_process):
            file_id = allocated_ids[i]
            self._process_file(file_info, file_id)

        print(f"\n✅ Processed {len(self.assignments)} files")
        return len(self.assignments)

    def _process_file(self, file_info: FileToProcess, file_id: str):
        """Process a single file: rename, update content if JSON, track assignment."""
        original_path = file_info.original_path
        original_name = file_info.file_name

        # Generate new filename
        if file_info.is_python:
            # Remove .py, add P_{ID}_ prefix
            base_name = original_name[:-3]  # Remove .py
            new_name = f"P_{file_id}_{base_name}.py"
        else:
            # Add {ID}_ prefix
            new_name = f"{file_id}_{original_name}"

        new_path = original_path.parent / new_name

        print(f"📝 {original_name}")
        print(f"   → {new_name}")
        print(f"   ID: {file_id}")

        if not self.dry_run:
            try:
                # If JSON file, update content with file_id field
                if file_info.extension == '.json':
                    self._update_json_file_id(original_path, new_path, file_id)
                else:
                    # Just rename
                    shutil.move(str(original_path), str(new_path))

                print(f"   ✅ Success\n")

            except Exception as e:
                print(f"   ❌ Error: {e}\n")
                return

        # Track assignment
        assignment = {
            'file_id': file_id,
            'original_name': original_name,
            'new_name': new_name,
            'path': str(original_path.parent),
            'file_type': file_info.extension,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        self.assignments.append(assignment)

    def _update_json_file_id(self, original_path: Path, new_path: Path, file_id: str):
        """Update JSON file to include file_id field and rename."""
        try:
            # Read existing JSON
            with open(original_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Add file_id field (don't overwrite if exists)
            if 'file_id' not in data:
                data['file_id'] = file_id
            else:
                print(f"   ⚠️  file_id already exists in content: {data['file_id']}")

            # Write to new path
            with open(new_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            # Remove original
            original_path.unlink()

        except json.JSONDecodeError as e:
            # If JSON is invalid, just rename file
            print(f"   ⚠️  Invalid JSON, just renaming: {e}")
            shutil.move(str(original_path), str(new_path))

    def update_registry(self) -> bool:
        """
        Update registry file with new assignments.

        Returns:
            True if registry updated successfully
        """
        if not self.registry_path or not self.assignments:
            return False

        if self.dry_run:
            print("\n🔍 DRY RUN: Would update registry with assignments")
            return True

        print(f"\n{'='*70}")
        print("UPDATING REGISTRY")
        print(f"{'='*70}\n")

        try:
            # Load existing registry
            if self.registry_path.exists():
                with open(self.registry_path, 'r', encoding='utf-8') as f:
                    registry = json.load(f)
            else:
                registry = {'entities': [], 'edges': []}

            # Add new entities
            if 'entities' not in registry:
                registry['entities'] = []

            for assignment in self.assignments:
                entity = {
                    'record_kind': 'entity',
                    'entity_kind': 'file',
                    'file_id': assignment['file_id'],
                    'artifact_path': f"{assignment['path']}/{assignment['new_name']}",
                    'added_to_registry_at': assignment['timestamp'],
                    'batch_assigned': True
                }
                registry['entities'].append(entity)

            # Save registry
            with open(self.registry_path, 'w', encoding='utf-8') as f:
                json.dump(registry, f, indent=2)

            print(f"✅ Registry updated: {self.registry_path}")
            print(f"   Added {len(self.assignments)} entities\n")
            return True

        except Exception as e:
            print(f"❌ Failed to update registry: {e}\n")
            return False

    def generate_report(self, output_path: Path = None):
        """Generate assignment report."""
        report = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'total_assigned': len(self.assignments),
            'dry_run': self.dry_run,
            'assignments': self.assignments
        }

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            print(f"📄 Report saved to: {output_path}")

        return report


def main():
    """CLI interface."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Batch assign file IDs to existing files'
    )
    parser.add_argument(
        '--root', type=Path, required=True,
        help='Root directory to scan'
    )
    parser.add_argument(
        '--counter', type=Path,
        default=Path('01999000042260124026_ID_COUNTER.json'),
        help='Path to ID counter file'
    )
    parser.add_argument(
        '--registry', type=Path,
        help='Path to registry file to update'
    )
    parser.add_argument(
        '--exclude', nargs='*',
        help='Additional directories to exclude'
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Preview changes without modifying files'
    )
    parser.add_argument(
        '--report', type=Path,
        help='Path to save assignment report'
    )
    parser.add_argument(
        '--purpose', type=str,
        default='Batch assign file IDs to existing files',
        help='Purpose for allocation tracking'
    )

    args = parser.parse_args()

    # Validate inputs
    if not args.root.exists():
        print(f"❌ Root directory not found: {args.root}")
        sys.exit(1)

    if not args.counter.exists():
        print(f"❌ ID counter not found: {args.counter}")
        sys.exit(1)

    # Create assigner
    assigner = BatchFileIDAssigner(
        counter_path=args.counter,
        registry_path=args.registry,
        dry_run=args.dry_run
    )

    # Scan directory
    found_count = assigner.scan_directory(args.root, args.exclude)

    if found_count == 0:
        print("✅ No files need file IDs")
        sys.exit(0)

    # Show preview
    print("Files to process:")
    for i, file_info in enumerate(assigner.files_to_process[:10], 1):
        print(f"  {i}. {file_info.file_name} ({file_info.reason})")

    if len(assigner.files_to_process) > 10:
        print(f"  ... and {len(assigner.files_to_process) - 10} more")

    # Confirm if not dry run
    if not args.dry_run:
        print(f"\n⚠️  This will rename {found_count} files and allocate IDs.")
        response = input("Continue? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("❌ Aborted")
            sys.exit(0)

    # Assign IDs
    processed = assigner.assign_ids(args.purpose)

    # Update registry
    if args.registry:
        assigner.update_registry()

    # Generate report
    if args.report:
        assigner.generate_report(args.report)

    print(f"\n{'='*70}")
    print("COMPLETE")
    print(f"{'='*70}\n")
    print(f"Files processed: {processed}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")


if __name__ == '__main__':
    main()
