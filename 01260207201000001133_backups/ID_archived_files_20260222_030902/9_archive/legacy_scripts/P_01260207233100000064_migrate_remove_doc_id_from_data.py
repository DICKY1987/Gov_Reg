#!/usr/bin/env python3
"""
Data migration: remove doc_id from registry records.

Usage:
    python validators/migrate_remove_doc_id_from_data.py --dry-run
    python validators/migrate_remove_doc_id_from_data.py --apply
    python validators/migrate_remove_doc_id_from_data.py --scan-dir REGISTRY --pattern "*registry*.json" --apply

Exit codes:
    0: Success
    1: Validation failed
    2: Migration failed
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    import jsonschema
except ImportError:
    jsonschema = None


class DocIdMigrator:
    """Removes doc_id from registry records and validates file_id presence."""

    def __init__(
        self,
        repo_root: Path,
        dry_run: bool,
        backup_dir: Path,
        schema_path: Path,
        report_path: Optional[Path] = None,
        require_schema: bool = False,
    ):
        self.repo_root = repo_root
        self.dry_run = dry_run
        self.backup_dir = backup_dir
        self.schema_path = schema_path
        self.report_path = report_path
        self.require_schema = require_schema

        self.stats: Dict[str, Any] = {
            "files_processed": 0,
            "files_modified": 0,
            "records_seen": 0,
            "records_modified": 0,
            "doc_ids_removed": 0,
            "errors": [],
            "warnings": [],
        }

        self._schema = None

    def load_schema(self) -> None:
        if jsonschema is None:
            msg = "jsonschema not installed - skipping schema validation"
            if self.require_schema:
                self.stats["errors"].append(msg)
            else:
                self.stats["warnings"].append(msg)
            return

        if not self.schema_path.exists():
            msg = f"Schema file not found: {self.schema_path}"
            self.stats["errors"].append(msg)
            return

        with open(self.schema_path, "r", encoding="utf-8") as f:
            self._schema = json.load(f)

    def scan_files(self, scan_dirs: Iterable[Path], patterns: List[str]) -> List[Path]:
        files: List[Path] = []
        for scan_dir in scan_dirs:
            if not scan_dir.exists():
                self.stats["warnings"].append(f"Scan dir not found: {scan_dir}")
                continue
            for pattern in patterns:
                files.extend(scan_dir.rglob(pattern))
        unique_files = sorted({f.resolve() for f in files if f.is_file()})
        return unique_files

    def migrate_files(self, files: List[Path]) -> int:
        self.load_schema()

        for filepath in files:
            self.stats["files_processed"] += 1
            try:
                changed, record_count = self._migrate_file(filepath)
                self.stats["records_seen"] += record_count
                if changed:
                    self.stats["files_modified"] += 1
            except Exception as exc:
                self.stats["errors"].append(f"{filepath}: {exc}")

        return len(self.stats["errors"])

    def _migrate_file(self, filepath: Path) -> Tuple[bool, int]:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        changed = False
        record_count = 0

        if isinstance(data, dict) and isinstance(data.get("files"), list):
            changed, record_count = self._migrate_records(data["files"])
        elif isinstance(data, list):
            changed, record_count = self._migrate_records(data)
        else:
            return False, 0

        if changed:
            if not self.dry_run:
                self._create_backup(filepath)
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=True)
                    f.write("\n")
            self.stats["records_modified"] += record_count

        if self._schema and isinstance(data, dict) and "files" in data:
            self._validate_schema_records(filepath, data.get("files", []))

        return changed, record_count

    def _migrate_records(self, records: List[Any]) -> Tuple[bool, int]:
        changed = False
        count = 0
        for record in records:
            if not isinstance(record, dict):
                continue
            count += 1
            if "doc_id" in record:
                record.pop("doc_id", None)
                self.stats["doc_ids_removed"] += 1
                changed = True
            self._validate_record(record)
        return changed, count

    def _validate_record(self, record: Dict[str, Any]) -> None:
        if "file_id" not in record:
            self.stats["errors"].append(
                "Record missing file_id (cannot migrate safely)"
            )

    def _validate_schema_records(self, filepath: Path, records: List[Any]) -> None:
        if jsonschema is None or self._schema is None:
            return
        file_def = self._schema.get("definitions", {}).get("FileRecord")
        if not file_def:
            self.stats["warnings"].append(f"{filepath}: FileRecord definition missing")
            return

        for record in records:
            if not isinstance(record, dict):
                continue
            try:
                jsonschema.validate(instance=record, schema=file_def)
            except jsonschema.ValidationError as exc:
                self.stats["errors"].append(f"{filepath}: {exc.message}")

    def _create_backup(self, filepath: Path) -> None:
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        try:
            rel_path = filepath.resolve().relative_to(self.repo_root.resolve())
            backup_path = self.backup_dir / rel_path
        except ValueError:
            backup_path = self.backup_dir / filepath.name
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        backup_path.write_bytes(filepath.read_bytes())

    def write_report(self) -> None:
        if not self.report_path:
            return
        report = {
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "dry_run": self.dry_run,
            "stats": self.stats,
        }
        self.report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=True)
            f.write("\n")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Remove doc_id from registry records with backup and validation."
    )
    parser.add_argument(
        "--scan-dir",
        action="append",
        default=["REGISTRY"],
        help="Directory to scan for JSON files (repeatable). Default: REGISTRY",
    )
    parser.add_argument(
        "--pattern",
        action="append",
        default=["*.json"],
        help="Glob pattern to match JSON files (repeatable). Default: *.json",
    )
    parser.add_argument(
        "--backup-dir",
        default="backups/doc_id_migration",
        help="Backup directory root (relative to repo root by default).",
    )
    parser.add_argument(
        "--schema",
        default="REGISTRY/01999000042260124012_governance_registry_schema.v3.json",
        help="Registry schema path.",
    )
    parser.add_argument(
        "--report",
        default=None,
        help="Optional report output path (JSON).",
    )
    parser.add_argument(
        "--require-schema",
        action="store_true",
        help="Fail if jsonschema is missing or schema cannot be loaded.",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Scan and report only.")
    mode.add_argument("--apply", action="store_true", help="Apply changes.")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    repo_root = Path(__file__).parent.parent

    scan_dirs = [repo_root / Path(p) for p in args.scan_dir]
    backup_dir = repo_root / Path(args.backup_dir)
    schema_path = repo_root / Path(args.schema)
    report_path = (repo_root / Path(args.report)) if args.report else None

    migrator = DocIdMigrator(
        repo_root=repo_root,
        dry_run=args.dry_run,
        backup_dir=backup_dir,
        schema_path=schema_path,
        report_path=report_path,
        require_schema=args.require_schema,
    )

    files = migrator.scan_files(scan_dirs, args.pattern)
    error_count = migrator.migrate_files(files)
    migrator.write_report()

    print("doc_id migration report")
    print(f"  dry_run: {migrator.dry_run}")
    print(f"  files_processed: {migrator.stats['files_processed']}")
    print(f"  files_modified: {migrator.stats['files_modified']}")
    print(f"  records_seen: {migrator.stats['records_seen']}")
    print(f"  records_modified: {migrator.stats['records_modified']}")
    print(f"  doc_ids_removed: {migrator.stats['doc_ids_removed']}")
    if migrator.stats["warnings"]:
        print("  warnings:")
        for warning in migrator.stats["warnings"]:
            print(f"    - {warning}")
    if migrator.stats["errors"]:
        print("  errors:")
        for error in migrator.stats["errors"]:
            print(f"    - {error}")

    if migrator.require_schema and migrator.stats["errors"]:
        return 1

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
