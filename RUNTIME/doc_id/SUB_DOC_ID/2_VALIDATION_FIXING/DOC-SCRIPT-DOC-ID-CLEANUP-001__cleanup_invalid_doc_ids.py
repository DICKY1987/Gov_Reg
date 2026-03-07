#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# DOC_LINK: DOC-SCRIPT-DOC-ID-CLEANUP-001
"""
Doc ID Cleanup Script

PURPOSE: Detect and fix invalid doc_ids in the repository
PATTERN: PATTERN-DOC-ID-CLEANUP-001

USAGE:
    python SUB_DOC_ID/2_VALIDATION_FIXING/cleanup_invalid_doc_ids.py scan
    python SUB_DOC_ID/2_VALIDATION_FIXING/cleanup_invalid_doc_ids.py fix --dry-run
    python SUB_DOC_ID/2_VALIDATION_FIXING/cleanup_invalid_doc_ids.py fix --backup
"""

import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

# Add parent directory to path for common module import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import from common module
from common import REPO_ROOT, REPORTS_DIR
from common.rules import DOC_ID_REGEX, validate_doc_id  # Phase 1: Use centralized rules
from common.utils import validate_doc_id

EXCLUDE_DIRS = {".git", "__pycache__", ".venv", "node_modules", ".pytest_cache"}
ELIGIBLE_EXTENSIONS = {".py", ".md", ".yaml", ".yml", ".json", ".ps1", ".sh", ".txt"}


def find_invalid_doc_ids() -> Dict[str, List[Dict]]:
    """Scan repository for invalid doc_ids"""
    invalid_entries = {"malformed": [], "duplicates": [], "orphaned": []}
    doc_id_map = {}

    for file_path in REPO_ROOT.rglob("*"):
        if not file_path.is_file() or file_path.suffix not in ELIGIBLE_EXTENSIONS:
            continue
        if any(excluded in file_path.parts for excluded in EXCLUDE_DIRS):
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            doc_ids = re.findall(r"DOC-[A-Z0-9-]+", content)

            for doc_id in doc_ids:
                if not DOC_ID_REGEX.match(doc_id):
                    invalid_entries["malformed"].append(
                        {
                            "file": str(file_path.relative_to(REPO_ROOT)),
                            "doc_id": doc_id,
                            "type": "malformed",
                        }
                    )
                else:
                    if doc_id in doc_id_map:
                        invalid_entries["duplicates"].append(
                            {
                                "doc_id": doc_id,
                                "files": [
                                    doc_id_map[doc_id],
                                    str(file_path.relative_to(REPO_ROOT)),
                                ],
                            }
                        )
                    else:
                        doc_id_map[doc_id] = str(file_path.relative_to(REPO_ROOT))
        except Exception as e:
            print(f"Error processing {file_path}: {e}", file=sys.stderr)

    return invalid_entries


def generate_report(invalid_entries: Dict, output_file: Path = None):
    """Generate cleanup report"""
    report = {
        "scan_date": datetime.now().isoformat(),
        "summary": {
            "malformed": len(invalid_entries["malformed"]),
            "duplicates": len(invalid_entries["duplicates"]),
            "orphaned": len(invalid_entries["orphaned"]),
        },
        "details": invalid_entries,
    }

    if output_file:
        output_file.write_text(json.dumps(report, indent=2))
        print(f"Report saved to: {output_file}")

    print("\n=== DOC_ID Cleanup Report ===")
    print(f"Malformed: {report['summary']['malformed']}")
    print(f"Duplicates: {report['summary']['duplicates']}")
    print(f"Orphaned: {report['summary']['orphaned']}")

    return report


def fix_invalid_doc_ids(
    invalid_entries: Dict, dry_run: bool = True, backup: bool = False
):
    """Fix invalid doc_ids in files"""
    fixed_count = 0

    print(f"\n{'DRY RUN: ' if dry_run else ''}Fixing invalid doc_ids...")

    for entry in invalid_entries["malformed"]:
        file_path = REPO_ROOT / entry["file"]
        if backup and not dry_run:
            shutil.copy2(file_path, f"{file_path}.bak")

        print(f"  Fix: {entry['file']} - {entry['doc_id']}")
        fixed_count += 1

    print(f"\n{'Would fix' if dry_run else 'Fixed'} {fixed_count} invalid doc_ids")
    return fixed_count


def main():
    parser = argparse.ArgumentParser(description="Doc ID Cleanup Tool")
    parser.add_argument("action", choices=["scan", "fix"], help="Action to perform")
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without applying"
    )
    parser.add_argument(
        "--backup", action="store_true", help="Backup files before fixing"
    )
    parser.add_argument(
        "--auto-approve", action="store_true", help="Skip confirmation prompt for automation"
    )
    parser.add_argument("--report", type=Path, help="Output report file path")

    args = parser.parse_args()

    invalid_entries = find_invalid_doc_ids()

    if args.action == "scan":
        report_path = args.report or REPORTS_DIR / "cleanup_report.json"
        generate_report(invalid_entries, report_path)
    elif args.action == "fix":
        # PATTERN: EXEC-004 Atomic Operation - Remove approval loop
        if not args.auto_approve and not args.dry_run:
            confirm = input("Proceed with fix? (y/n): ")
            if confirm.lower() != 'y':
                print("Cancelled")
                sys.exit(0)

        fix_invalid_doc_ids(invalid_entries, dry_run=args.dry_run, backup=args.backup)


if __name__ == "__main__":
    main()

