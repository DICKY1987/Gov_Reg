#!/usr/bin/env python3
# DOC_LINK: DOC-CORE-SSOT-SYS-TOOLS-ID-REGISTRY-1105
"""
ID Registry - Stable ID Allocation and Management

Provides:
- Stable, never-reused IDs for directories/components
- Path updates and renames without ID changes
- Forward lookup: path → ID
- Reverse lookup: ID → path
- JSON-backed persistent storage

Requirements from SSOT: R-ENF-002
"""
# DOC_ID: DOC-CORE-SSOT-SYS-TOOLS-ID-REGISTRY-1105

import json
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
import hashlib


class IdRegistry:
    """
    Manages stable IDs for directories and components.

    IDs are allocated once and never reused, even if paths change.
    """

    def __init__(self, registry_path: Path):
        """
        Initialize ID registry.

        Args:
            registry_path: Path to registry JSON file
        """
        self.registry_path = Path(registry_path)
        self.registry: Dict = self._load_registry()

    def _load_registry(self) -> Dict:
        """Load registry from disk or create new."""
        if self.registry_path.exists():
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {
                "meta": {
                    "version": "1.0.0",
                    "created_utc": datetime.utcnow().isoformat() + "Z",
                    "last_updated_utc": datetime.utcnow().isoformat() + "Z"
                },
                "entries": {},  # id → entry
                "path_index": {}  # normalized_path → id
            }

    def _save_registry(self):
        """Save registry to disk."""
        self.registry["meta"]["last_updated_utc"] = datetime.utcnow().isoformat() + "Z"
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(self.registry, f, indent=2, sort_keys=True)

    def _normalize_path(self, path: str) -> str:
        """Normalize path for consistent lookup."""
        return str(Path(path).as_posix()).lower()

    def _generate_id(self, path: str, prefix: str = "DIR") -> str:
        """
        Generate stable ID for a path.

        Uses monotonic counter to ensure uniqueness.
        """
        # Get next ID number
        existing_ids = [
            int(entry["id"].split("-")[-1])
            for entry in self.registry["entries"].values()
            if entry["id"].startswith(f"{prefix}-")
        ]
        next_num = max(existing_ids, default=0) + 1

        return f"{prefix}-{next_num:05d}"

    def allocate_id(self, path: str, prefix: str = "DIR",
                   metadata: Optional[Dict] = None) -> str:
        """
        Allocate a new stable ID for a path.

        Args:
            path: Path to allocate ID for
            prefix: ID prefix (default: DIR)
            metadata: Optional metadata dict

        Returns:
            Allocated ID

        Raises:
            ValueError: If path already has an ID
        """
        norm_path = self._normalize_path(path)

        # Check if path already has ID
        if norm_path in self.registry["path_index"]:
            existing_id = self.registry["path_index"][norm_path]
            raise ValueError(f"Path {path} already has ID: {existing_id}")

        # Generate new ID
        new_id = self._generate_id(path, prefix)

        # Create entry
        entry = {
            "id": new_id,
            "current_path": path,
            "normalized_path": norm_path,
            "allocated_utc": datetime.utcnow().isoformat() + "Z",
            "path_history": [
                {
                    "path": path,
                    "from_utc": datetime.utcnow().isoformat() + "Z"
                }
            ],
            "metadata": metadata or {}
        }

        # Store entry
        self.registry["entries"][new_id] = entry
        self.registry["path_index"][norm_path] = new_id

        self._save_registry()

        return new_id

    def get_id(self, path: str) -> Optional[str]:
        """
        Get ID for a path (forward lookup).

        Args:
            path: Path to lookup

        Returns:
            ID if found, None otherwise
        """
        norm_path = self._normalize_path(path)
        return self.registry["path_index"].get(norm_path)

    def get_path(self, id: str) -> Optional[str]:
        """
        Get current path for an ID (reverse lookup).

        Args:
            id: ID to lookup

        Returns:
            Current path if found, None otherwise
        """
        entry = self.registry["entries"].get(id)
        return entry["current_path"] if entry else None

    def update_path(self, id: str, new_path: str) -> bool:
        """
        Update path for an existing ID (handles renames/moves).

        Args:
            id: ID to update
            new_path: New path

        Returns:
            True if updated, False if ID not found
        """
        entry = self.registry["entries"].get(id)
        if not entry:
            return False

        old_norm_path = entry["normalized_path"]
        new_norm_path = self._normalize_path(new_path)

        # Update entry
        entry["current_path"] = new_path
        entry["normalized_path"] = new_norm_path
        entry["path_history"].append({
            "path": new_path,
            "from_utc": datetime.utcnow().isoformat() + "Z"
        })

        # Update path index
        if old_norm_path in self.registry["path_index"]:
            del self.registry["path_index"][old_norm_path]
        self.registry["path_index"][new_norm_path] = id

        self._save_registry()

        return True

    def get_entry(self, id: str) -> Optional[Dict]:
        """Get complete entry for an ID."""
        return self.registry["entries"].get(id)

    def list_all_ids(self) -> List[str]:
        """Get list of all allocated IDs."""
        return list(self.registry["entries"].keys())

    def get_path_history(self, id: str) -> List[Dict]:
        """Get path history for an ID."""
        entry = self.registry["entries"].get(id)
        return entry["path_history"] if entry else []

    def search_by_prefix(self, prefix: str) -> List[Dict]:
        """
        Search entries by ID prefix.

        Args:
            prefix: ID prefix to match (e.g., "DIR-")

        Returns:
            List of matching entries
        """
        return [
            entry for entry in self.registry["entries"].values()
            if entry["id"].startswith(prefix)
        ]

    def validate_integrity(self) -> Dict:
        """
        Validate registry integrity.

        Returns:
            Dict with validation results
        """
        errors = []
        warnings = []

        # Check for duplicate paths
        path_counts = {}
        for id, entry in self.registry["entries"].items():
            norm_path = entry["normalized_path"]
            if norm_path in path_counts:
                errors.append(f"Duplicate path {norm_path}: IDs {path_counts[norm_path]} and {id}")
            else:
                path_counts[norm_path] = id

        # Check path_index consistency
        for norm_path, id in self.registry["path_index"].items():
            if id not in self.registry["entries"]:
                errors.append(f"Path index references non-existent ID: {id}")
            elif self.registry["entries"][id]["normalized_path"] != norm_path:
                errors.append(f"Path index mismatch for {id}: index={norm_path}, entry={self.registry['entries'][id]['normalized_path']}")

        # Check for orphaned entries
        for id, entry in self.registry["entries"].items():
            norm_path = entry["normalized_path"]
            if norm_path not in self.registry["path_index"]:
                warnings.append(f"Entry {id} not in path index")

        return {
            "valid": len(errors) == 0,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "errors": errors,
            "warnings": warnings,
            "total_entries": len(self.registry["entries"]),
            "total_paths_indexed": len(self.registry["path_index"])
        }


def main():
    """CLI entry point for testing."""
    import argparse

    parser = argparse.ArgumentParser(description='ID Registry CLI')
    parser.add_argument('--registry', default='data/id_registry.json', help='Registry file path')

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # allocate command
    allocate_parser = subparsers.add_parser('allocate', help='Allocate new ID')
    allocate_parser.add_argument('path', help='Path to allocate ID for')
    allocate_parser.add_argument('--prefix', default='DIR', help='ID prefix')

    # lookup command
    lookup_parser = subparsers.add_parser('lookup', help='Lookup ID or path')
    lookup_parser.add_argument('value', help='ID or path to lookup')

    # update command
    update_parser = subparsers.add_parser('update', help='Update path for ID')
    update_parser.add_argument('id', help='ID to update')
    update_parser.add_argument('new_path', help='New path')

    # list command
    list_parser = subparsers.add_parser('list', help='List all IDs')

    # validate command
    validate_parser = subparsers.add_parser('validate', help='Validate registry integrity')

    args = parser.parse_args()

    registry = IdRegistry(args.registry)

    if args.command == 'allocate':
        try:
            id = registry.allocate_id(args.path, args.prefix)
            print(f"Allocated ID: {id} for path: {args.path}")
        except ValueError as e:
            print(f"Error: {e}")

    elif args.command == 'lookup':
        # Try as path first
        id = registry.get_id(args.value)
        if id:
            print(f"Path: {args.value} → ID: {id}")
        else:
            # Try as ID
            path = registry.get_path(args.value)
            if path:
                print(f"ID: {args.value} → Path: {path}")
            else:
                print(f"Not found: {args.value}")

    elif args.command == 'update':
        if registry.update_path(args.id, args.new_path):
            print(f"Updated ID {args.id} to path: {args.new_path}")
        else:
            print(f"ID not found: {args.id}")

    elif args.command == 'list':
        ids = registry.list_all_ids()
        print(f"Total IDs: {len(ids)}")
        for id in sorted(ids):
            entry = registry.get_entry(id)
            print(f"  {id}: {entry['current_path']}")

    elif args.command == 'validate':
        result = registry.validate_integrity()
        print(f"Valid: {result['valid']}")
        print(f"Errors: {result['error_count']}")
        print(f"Warnings: {result['warning_count']}")
        print(f"Entries: {result['total_entries']}")
        if result['errors']:
            print("\nErrors:")
            for err in result['errors']:
                print(f"  - {err}")
        if result['warnings']:
            print("\nWarnings:")
            for warn in result['warnings']:
                print(f"  - {warn}")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()

