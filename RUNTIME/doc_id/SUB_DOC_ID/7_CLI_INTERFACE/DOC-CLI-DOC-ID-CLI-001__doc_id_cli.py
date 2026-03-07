#!/usr/bin/env python3
# DOC_LINK: DOC-CLI-DOC-ID-CLI-001
"""
Unified DOC_ID CLI - Single entry point for all doc_id operations.

Phase 5 optimization - consolidates all doc_id commands into one interface
with consistent output and CI-friendly reporting.

USAGE:
    doc_id_cli.py scan [--incremental] [--emit missing.json]
    doc_id_cli.py assign --input missing.json [--stage]
    doc_id_cli.py validate --run-id RUN-ID
    doc_id_cli.py commit --run-id RUN-ID
    doc_id_cli.py verify [--baseline 0.55]
    doc_id_cli.py stats [--format json]
"""
# DOC_ID: DOC-CLI-DOC-ID-CLI-001

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common import REPO_ROOT, INVENTORY_PATH
from common.index_store import IndexStore
from common.staging import StagingArea
from common.validators import ValidatorFactory
from common.rules import validate_doc_id


class DocIDCLI:
    """Unified CLI for doc_id operations."""

    def __init__(self):
        self.repo_root = REPO_ROOT
        self.cache_dir = self.repo_root / ".cache"
        self.staging_dir = self.repo_root / ".staging"

    def cmd_scan(self, args) -> int:
        """Scan repository for doc_ids."""
        from RUNTIME.doc_id.ONE_CORE_OPERATIONS.doc_id_scanner import DocIDScanner

        scanner = DocIDScanner()

        # Determine scan mode
        use_incremental = not args.full

        if use_incremental:
            # Incremental scan with cache
            index_store = IndexStore(self.cache_dir / "doc_id_index.sqlite")
            run_id = f"RUN-SCAN-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

            scanner.scan_repository_incremental(index_store, run_id)

            # Emit missing.json if requested
            if args.emit:
                missing_files = index_store.get_files_missing_doc_id()
                missing_data = {
                    "run_id": run_id,
                    "scan_completed_utc": datetime.utcnow().isoformat(),
                    "total_missing": len(missing_files),
                    "files": missing_files
                }
                args.emit.parent.mkdir(parents=True, exist_ok=True)
                args.emit.write_text(json.dumps(missing_data, indent=2))
                print(f"[OK] Missing files: {args.emit}")
        else:
            # Full scan
            scanner.scan_repository()

        scanner.save_inventory(INVENTORY_PATH)
        scanner.print_stats()

        return 0

    def cmd_assign(self, args) -> int:
        """Assign doc_ids to files."""
        if args.stage:
            # Staged assignment (Phase 3)
            from RUNTIME.doc_id.ONE_CORE_OPERATIONS.doc_id_assigner import auto_assign_staged

            staging = StagingArea(self.staging_dir)
            run_id = f"RUN-ASSIGN-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

            result = auto_assign_staged(
                args.input,
                staging,
                run_id,
                batch_size=args.batch_size
            )

            print(f"[OK] Staged {result['staged']} assignments")
            print(f"     Run ID: {result['run_id']}")
            print(f"     Next: doc_id_cli.py validate --run-id {result['run_id']}")

            return 0
        else:
            # Direct assignment (legacy)
            from RUNTIME.doc_id.ONE_CORE_OPERATIONS.doc_id_assigner import auto_assign

            result = auto_assign(
                dry_run=args.dry_run,
                limit=args.limit
            )

            print(f"[OK] Assigned {len(result.get('assignments', []))} doc_ids")
            return 0

    def cmd_validate(self, args) -> int:
        """Validate staged operations."""
        staging = StagingArea(self.staging_dir)

        # Get validators
        validators = []
        for ext, validator in ValidatorFactory.get_all_validators().items():
            validators.append(validator)

        # Validate
        results = staging.validate_staged(args.run_id, validators)

        if results["summary"]["failed"] > 0:
            print(f"[ERROR] Validation failed:")
            print(f"        Passed: {results['summary']['passed']}")
            print(f"        Failed: {results['summary']['failed']}")

            for failure in results["failed"][:5]:
                print(f"        - {failure['file']}: {failure['error']}")

            return 1

        print(f"[OK] Validation passed ({results['summary']['passed']} checks)")
        print(f"     Next: doc_id_cli.py commit --run-id {args.run_id}")

        return 0

    def cmd_commit(self, args) -> int:
        """Commit staged operations."""
        staging = StagingArea(self.staging_dir)

        if not args.force:
            # Validate first
            validators = list(ValidatorFactory.get_all_validators().values())
            results = staging.validate_staged(args.run_id, validators)

            if results["summary"]["failed"] > 0:
                print(f"[ERROR] Validation failed - commit blocked")
                print(f"        Use --force to override (not recommended)")
                return 1

        # Commit
        result = staging.commit_staged(
            args.run_id,
            self.repo_root,
            dry_run=args.dry_run
        )

        if args.dry_run:
            print(f"[DRY RUN] Would commit {result['count']} files")
        else:
            print(f"[OK] Committed {result['count']} files")

            # Cleanup staging
            staging.rollback(args.run_id)

        return 0

    def cmd_verify(self, args) -> int:
        """Verify doc_id integrity."""
        from RUNTIME.doc_id.TWO_VALIDATION_FIXING.validate_doc_id_coverage import (
            scan_repository,
            calculate_coverage
        )

        # Scan and calculate coverage
        files_with_id, total_files = scan_repository(self.repo_root)
        coverage = calculate_coverage(files_with_id, total_files)

        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_files": total_files,
            "files_with_doc_id": files_with_id,
            "coverage_pct": coverage * 100,
            "baseline": args.baseline * 100,
            "status": "PASS" if coverage >= args.baseline else "FAIL"
        }

        if args.format == "json":
            print(json.dumps(report, indent=2))
        else:
            print(f"Coverage: {coverage:.1%}")
            print(f"Baseline: {args.baseline:.1%}")
            print(f"Status: {report['status']}")

        return 0 if coverage >= args.baseline else 1

    def cmd_stats(self, args) -> int:
        """Show doc_id statistics."""
        index_store = IndexStore(self.cache_dir / "doc_id_index.sqlite")
        stats = index_store.get_stats()

        if args.format == "json":
            print(json.dumps(stats, indent=2))
        else:
            print(f"Total files: {stats['total_files']}")
            print(f"With doc_id: {stats['files_with_doc_id']} ({stats['coverage_pct']:.1f}%)")
            print(f"\nTop extensions:")
            for ext, count in list(stats['top_extensions'].items())[:5]:
                print(f"  {ext}: {count}")

        return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Unified DOC_ID CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Scan repository")
    scan_parser.add_argument("--full", action="store_true", help="Full scan (no cache)")
    scan_parser.add_argument("--emit", type=Path, help="Emit missing.json")

    # Assign command
    assign_parser = subparsers.add_parser("assign", help="Assign doc_ids")
    assign_parser.add_argument("--input", type=Path, required=True, help="Input missing.json")
    assign_parser.add_argument("--stage", action="store_true", default=True, help="Use staging")
    assign_parser.add_argument("--batch-size", type=int, default=50, help="Batch size")
    assign_parser.add_argument("--dry-run", action="store_true", help="Dry run")
    assign_parser.add_argument("--limit", type=int, help="Limit files")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate staged")
    validate_parser.add_argument("--run-id", required=True, help="Run ID")

    # Commit command
    commit_parser = subparsers.add_parser("commit", help="Commit staged")
    commit_parser.add_argument("--run-id", required=True, help="Run ID")
    commit_parser.add_argument("--dry-run", action="store_true", help="Dry run")
    commit_parser.add_argument("--force", action="store_true", help="Skip validation")

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify integrity")
    verify_parser.add_argument("--baseline", type=float, default=0.55, help="Coverage baseline")
    verify_parser.add_argument("--format", choices=["text", "json"], default="text")

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show statistics")
    stats_parser.add_argument("--format", choices=["text", "json"], default="text")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    cli = DocIDCLI()

    # Route to command
    cmd_map = {
        "scan": cli.cmd_scan,
        "assign": cli.cmd_assign,
        "validate": cli.cmd_validate,
        "commit": cli.cmd_commit,
        "verify": cli.cmd_verify,
        "stats": cli.cmd_stats,
    }

    return cmd_map[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
