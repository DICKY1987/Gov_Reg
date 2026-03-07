#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# DOC_LINK: DOC-SCRIPT-DOC-ID-REGISTRY-CLI-001
"""
DOC_ID Registry CLI

PURPOSE: Manage doc_id assignments across the repository
USAGE:
    python doc_id/doc_id_registry_cli.py mint --category CORE --name SCHEDULER
    python doc_id/doc_id_registry_cli.py validate
    python doc_id/doc_id_registry_cli.py search --pattern "CORE-.*"
    python doc_id/doc_id_registry_cli.py stats
"""

import argparse
import io
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# Add grandparent directory to path for common module import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Import from common module
from common import REPO_ROOT, REGISTRY_PATH, DOC_ID_REGEX
from common.utils import load_yaml, save_yaml


class DocIDRegistry:
    """Manage the central DOC_ID registry."""

    def __init__(self, registry_path: Path = REGISTRY_PATH):
        self.registry_path = registry_path
        self.data = self._load_registry()

    def _load_registry(self) -> dict:
        """Load registry from YAML file."""
        if not self.registry_path.exists():
            print(f"[ERROR] Registry not found: {self.registry_path}")
            sys.exit(1)

        with open(self.registry_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _save_registry(self):
        """Save registry back to YAML file."""
        self.data["metadata"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")

        with open(self.registry_path, "w", encoding="utf-8") as f:
            yaml.dump(self.data, f, default_flow_style=False, sort_keys=False)

        print(f"[OK] Registry updated: {self.registry_path}")

    def mint_doc_id(
        self,
        category: str,
        name: str,
        title: str = None,
        artifacts: List[Dict] = None,
        tags: List[str] = None,
    ) -> str:
        """
        Mint a new doc_id.

        Args:
            category: Category prefix (e.g., 'core', 'error', 'patterns')
            name: Name segments (e.g., 'orchestrator', 'python-ruff')
            title: Human-readable title
            artifacts: List of artifact dicts with 'type' and 'path'
            tags: List of tags

        Returns:
            The new doc_id
        """
        category_lower = category.lower()

        if category_lower not in self.data["categories"]:
            print(f"[ERROR] Unknown category: {category}")
            print(f"Available: {', '.join(self.data['categories'].keys())}")
            sys.exit(1)

        cat_data = self.data["categories"][category_lower]
        prefix = cat_data["prefix"]
        next_num = cat_data["next_id"]
        existing = [d.get("doc_id") for d in self.data["docs"] if "doc_id" in d]
        used_numbers = {
            int(match.group(1))
            for doc in self.data["docs"]
            if doc.get("category") == category_lower
            for match in [re.search(r"-(\d{3})$", doc.get("doc_id", ""))]
            if match
        }

        def find_available(start: int) -> int:
            """Find the next unused slot within the category (up to 9999)."""
            for candidate in range(start, 10000):
                if candidate not in used_numbers:
                    return candidate
            for candidate in range(1, 10000):
                if candidate not in used_numbers:
                    return candidate
            print(f"[ERROR] No available doc_id slots for category: {category_lower}")
            sys.exit(1)

        next_num = find_available(next_num)

        # Convert name to uppercase with dashes
        name_upper = name.upper().replace("_", "-").replace(" ", "-")

        # Construct doc_id with 3 or 4 digits (4 digits if >= 1000)
        suffix_width = 4 if next_num >= 1000 else 3
        doc_id = f"DOC-{prefix}-{name_upper}-{next_num:0{suffix_width}d}"

        # Validate format
        if not DOC_ID_REGEX.match(doc_id):
            print(f"[ERROR] Generated doc_id failed validation: {doc_id}")
            sys.exit(1)

        # Check for duplicates (should be prevented by find_available but guard anyway)
        if doc_id in existing:
            next_num = find_available(next_num + 1)
            doc_id = f"DOC-{prefix}-{name_upper}-{next_num:03d}"
            if doc_id in existing:
                print(f"[ERROR] doc_id already exists: {doc_id}")
                sys.exit(1)

        used_numbers.add(next_num)

        # Create doc entry
        doc_entry = {
            "doc_id": doc_id,
            "category": category_lower,
            "name": name.lower().replace("-", "_"),
            "title": title or name,
            "status": "active",
            "artifacts": artifacts or [],
            "created": datetime.now().strftime("%Y-%m-%d"),
            "last_modified": datetime.now().strftime("%Y-%m-%d"),
            "tags": tags or [],
        }

        # Add to registry
        self.data["docs"].append(doc_entry)
        cat_data["next_id"] = find_available(next_num + 1)
        cat_data["count"] = cat_data["count"] + 1
        self.data["metadata"]["total_docs"] = len(self.data["docs"])

        self._save_registry()

        print(f"\n[OK] Minted new doc_id: {doc_id}")
        print(f"   Category: {category_lower}")
        print(f"   Name: {name}")
        if title:
            print(f"   Title: {title}")

        return doc_id

    def validate_format(self, doc_id: str) -> bool:
        """Validate doc_id format."""
        return DOC_ID_REGEX.match(doc_id) is not None

    def search(
        self, pattern: str = None, category: str = None, status: str = None
    ) -> List[Dict]:
        """
        Search for doc_ids.

        Args:
            pattern: Regex pattern to match doc_id
            category: Filter by category
            status: Filter by status

        Returns:
            List of matching doc entries
        """
        results = self.data["docs"]

        if category:
            results = [d for d in results if d["category"] == category.lower()]

        if status:
            results = [d for d in results if d["status"] == status]

        if pattern:
            regex = re.compile(pattern)
            results = [d for d in results if regex.search(d["doc_id"])]

        return results

    def get_stats(self) -> Dict:
        """Get registry statistics."""
        return {
            "total_docs": len(self.data["docs"]),
            "total_categories": len(self.data["categories"]),
            "by_category": {
                cat: cat_data["count"]
                for cat, cat_data in self.data["categories"].items()
            },
            "by_status": self._count_by_field("status"),
            "last_updated": self.data["metadata"]["last_updated"],
        }

    def _count_by_field(self, field: str) -> Dict[str, int]:
        """Count docs by field value."""
        counts = {}
        for doc in self.data["docs"]:
            value = doc.get(field, "unknown")
            counts[value] = counts.get(value, 0) + 1
        return counts

    def validate_all(self) -> Dict:
        """
        Validate all doc_ids in registry.

        Returns:
            Validation report with errors and warnings
        """
        errors = []
        warnings = []

        seen_ids = set()

        for doc in self.data["docs"]:
            doc_id = doc["doc_id"]

            # Check format
            if not self.validate_format(doc_id):
                errors.append(f"Invalid format: {doc_id}")

            # Check duplicates
            if doc_id in seen_ids:
                errors.append(f"Duplicate doc_id: {doc_id}")
            seen_ids.add(doc_id)

            # Check artifacts exist
            for artifact in doc.get("artifacts", []):
                path = REPO_ROOT / artifact["path"]
                if not path.exists():
                    warnings.append(
                        f"Missing artifact: {artifact['path']} for {doc_id}"
                    )

        return {
            "total_docs": len(self.data["docs"]),
            "errors": errors,
            "warnings": warnings,
            "valid": len(errors) == 0,
        }

    def add_existing(
        self,
        doc_id: str,
        category: str,
        name: str,
        path: str,
        title: str = None,
        tags: List[str] = None,
    ) -> None:
        """
        Add an existing doc_id to registry without incrementing counters.
        Used for importing doc_ids that already exist in files.

        Args:
            doc_id: Existing doc_id (e.g., 'DOC-CORE-SCHEDULER-001')
            category: Category name (e.g., 'core')
            name: Logical name
            path: File path
            title: Optional title
            tags: Optional tags
        """
        # Check if already exists
        existing_ids = {d["doc_id"] for d in self.data["docs"]}
        if doc_id in existing_ids:
            return  # Skip duplicates silently during import

        doc_entry = {
            "doc_id": doc_id,
            "category": category.lower(),
            "name": name.lower().replace("-", "_"),
            "title": title or name,
            "status": "active",
            "artifacts": [{"type": "source", "path": path}],
            "created": datetime.now().strftime("%Y-%m-%d"),
            "last_modified": datetime.now().strftime("%Y-%m-%d"),
            "tags": tags or [],
        }

        self.data["docs"].append(doc_entry)

    def recompute_next_id_counters(self) -> None:
        """
        Recompute next_id counters for all categories based on existing doc_ids.
        Call this after importing existing doc_ids to sync counters.
        """
        for cat_name, cat_data in self.data["categories"].items():
            cat_docs = [d for d in self.data["docs"] if d["category"] == cat_name]

            if cat_docs:
                # Extract numeric suffix from each doc_id
                max_num = 0
                for doc in cat_docs:
                    doc_id = doc["doc_id"]
                    # Extract last segment after final dash
                    parts = doc_id.split("-")
                    if parts and parts[-1].isdigit():
                        num = int(parts[-1])
                        max_num = max(max_num, num)

                cat_data["next_id"] = max_num + 1
                cat_data["count"] = len(cat_docs)
            else:
                cat_data["next_id"] = 1
                cat_data["count"] = 0


def cmd_mint(args):
    """Mint a new doc_id."""
    registry = DocIDRegistry()

    artifacts = []
    if args.artifact:
        for artifact_spec in args.artifact:
            atype, path = artifact_spec.split(":", 1)
            artifacts.append({"type": atype, "path": path})

    tags = args.tags.split(",") if args.tags else []

    doc_id = registry.mint_doc_id(
        category=args.category,
        name=args.name,
        title=args.title,
        artifacts=artifacts,
        tags=tags,
    )

    print(f"\n📋 Next steps:")
    print(f"   1. Add 'doc_id: {doc_id}' or 'DOC_LINK: {doc_id}' to your files")
    print(f"   2. Run validation: python scripts/doc_id_registry_cli.py validate")


def cmd_search(args):
    """Search for doc_ids."""
    registry = DocIDRegistry()

    results = registry.search(
        pattern=args.pattern, category=args.category, status=args.status
    )

    if not results:
        print("[ERROR] No matching doc_ids found")
        return

    print(f"\n📋 Found {len(results)} doc_id(s):\n")

    for doc in results:
        print(f"  {doc['doc_id']}")
        print(f"    Category: {doc['category']}")
        print(f"    Name: {doc['name']}")
        print(f"    Status: {doc['status']}")
        if doc.get("title"):
            print(f"    Title: {doc['title']}")
        if doc.get("artifacts"):
            print(f"    Artifacts: {len(doc['artifacts'])}")
        print()


def cmd_validate(args):
    """Validate all doc_ids."""
    registry = DocIDRegistry()

    print("🔍 Validating DOC_ID registry...\n")

    report = registry.validate_all()

    print(f"Total docs: {report['total_docs']}")

    if report["errors"]:
        print(f"\n[ERROR] Errors ({len(report['errors'])}):")
        for err in report["errors"]:
            print(f"   - {err}")

    if report["warnings"]:
        print(f"\n[WARN]  Warnings ({len(report['warnings'])}):")
        for warn in report["warnings"]:
            print(f"   - {warn}")

    if report["valid"] and not report["warnings"]:
        print("\n[OK] All doc_ids are valid!")
        return 0
    elif report["valid"]:
        print("\n[OK] Format valid, but warnings present")
        return 0
    else:
        print("\n[ERROR] Validation failed")
        return 1


def cmd_stats(args):
    """Show registry statistics."""
    registry = DocIDRegistry()

    stats = registry.get_stats()

    print("\n[STATS] DOC_ID Registry Statistics\n")
    print(f"Total docs: {stats['total_docs']}")
    print(f"Total categories: {stats['total_categories']}")
    print(f"Last updated: {stats['last_updated']}")

    print(f"\nBy category:")
    for cat, count in sorted(stats["by_category"].items()):
        print(f"  {cat:12} {count:4d}")

    print(f"\nBy status:")
    for status, count in sorted(stats["by_status"].items()):
        print(f"  {status:12} {count:4d}")


def cmd_list(args):
    """List all doc_ids."""
    registry = DocIDRegistry()

    docs = registry.data["docs"]

    if args.category:
        docs = [d for d in docs if d["category"] == args.category.lower()]

    print(f"\n📋 {len(docs)} doc_id(s):\n")

    for doc in sorted(docs, key=lambda d: d["doc_id"]):
        print(f"  {doc['doc_id']:<40} {doc['category']:10} {doc['status']:10}")


def cmd_batch_mint(args):
    """Batch mint doc_ids from a batch spec file."""
    import json

    registry = DocIDRegistry(args.registry)

    # Load batch spec
    batch_spec_path = Path(args.batch)
    if not batch_spec_path.exists():
        print(f"[ERROR] Batch spec not found: {batch_spec_path}")
        sys.exit(1)

    with open(batch_spec_path, "r", encoding="utf-8") as f:
        batch_spec = yaml.safe_load(f)

    batch_id = batch_spec.get("batch_id", "UNKNOWN")
    items = batch_spec.get("items", [])

    print(f"\n[INFO] Processing batch: {batch_id}")
    print(f"[INFO] Items: {len(items)}")
    print(f"[INFO] Mode: {args.mode}")

    deltas = []

    for item in items:
        logical_name = item["logical_name"]
        title = item["title"]
        artifacts = item.get("artifacts", [])
        category = batch_spec.get("category", "docs")
        tags = batch_spec.get("tags", [])

        # Generate doc_id (normalize: replace _ with -)
        logical_name_normalized = logical_name.upper().replace("_", "-")
        doc_id = f"DOC-{category.upper()}-{logical_name_normalized}-001"

        delta_entry = {
            "doc_id": doc_id,
            "category": category,
            "name": logical_name.lower(),
            "title": title,
            "status": "active",
            "artifacts": artifacts,
            "created": datetime.now().strftime("%Y-%m-%d"),
            "last_modified": datetime.now().strftime("%Y-%m-%d"),
            "tags": tags,
        }

        deltas.append(delta_entry)

        if args.mode == "dry-run":
            print(f"  [DRY-RUN] Would mint: {doc_id}")

    # Handle output based on mode
    if args.mode == "dry-run":
        if args.dry_run_report:
            report_path = Path(args.dry_run_report)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(f"# Dry-Run Report: {batch_id}\n\n")
                f.write(f"Total items: {len(deltas)}\n\n")
                for delta in deltas:
                    f.write(f"- {delta['doc_id']}: {delta['title']}\n")
            print(f"\n[OK] Dry-run report: {report_path}")

    elif args.mode == "deltas-only":
        if args.delta_out:
            delta_path = Path(args.delta_out)
            delta_path.parent.mkdir(parents=True, exist_ok=True)
            with open(delta_path, "w", encoding="utf-8") as f:
                for delta in deltas:
                    f.write(json.dumps(delta) + "\n")
            print(f"\n[OK] Delta file created: {delta_path}")
            print(f"[INFO] Run merge-deltas on control checkout to apply")

        if not args.no_registry:
            print(
                "[WARN] --no-registry not specified; use it to prevent registry writes from worktrees"
            )


def cmd_merge_deltas(args):
    """Merge delta JSONL files into the registry."""
    import json

    registry = DocIDRegistry(args.registry)

    delta_files = args.delta_files

    print(f"\n[INFO] Merging {len(delta_files)} delta file(s)")

    total_merged = 0

    for delta_file in delta_files:
        delta_path = Path(delta_file)
        if not delta_path.exists():
            print(f"[WARN] Delta file not found, skipping: {delta_path}")
            continue

        with open(delta_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    delta = json.loads(line)
                    registry.data["docs"].append(delta)
                    total_merged += 1
                    print(f"  [+] {delta['doc_id']}")

    registry.data["metadata"]["total_docs"] = len(registry.data["docs"])
    registry._save_registry()

    print(f"\n[OK] Merged {total_merged} doc_id(s)")

    # Generate merge report
    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# Merge Report\n\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"Total merged: {total_merged}\n\n")
            f.write(f"Delta files:\n")
            for df in delta_files:
                f.write(f"- {df}\n")
        print(f"[OK] Merge report: {report_path}")


def cmd_generate_index(args):
    """Generate index files from registry."""
    registry = DocIDRegistry(args.registry)

    # Generate by-category index
    by_category = {}
    for doc in registry.data["docs"]:
        cat = doc["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(doc)

    index_path = REPO_ROOT / "CODEBASE_INDEX.yaml"
    print(f"\n[INFO] Generating index: {index_path}")

    # Simple index structure
    index = {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_docs": len(registry.data["docs"]),
        "by_category": {},
    }

    for cat, docs in by_category.items():
        index["by_category"][cat] = {
            "count": len(docs),
            "doc_ids": [d["doc_id"] for d in docs],
        }

    with open(index_path, "w", encoding="utf-8") as f:
        yaml.dump(index, f, default_flow_style=False)

    print(f"[OK] Index generated: {index_path}")


def cmd_import_from_inventory(args):
    """Import existing doc_ids from docs_inventory.jsonl into registry."""
    import json

    registry = DocIDRegistry(args.registry)

    inventory_path = REPO_ROOT / "docs_inventory.jsonl"
    if not inventory_path.exists():
        print(f"[ERROR] Inventory file not found: {inventory_path}")
        print(f"        Run: python doc_id/doc_id_scanner.py scan")
        sys.exit(1)

    print(f"\n[INFO] Importing from: {inventory_path}")

    imported = 0
    skipped = 0
    errors = []

    # Load existing registry IDs
    existing_ids = {d["doc_id"] for d in registry.data["docs"]}

    with open(inventory_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                entry = json.loads(line)
            except json.JSONDecodeError as e:
                errors.append(f"Line {line_num}: JSON decode error: {e}")
                continue

            # Only import valid doc_ids
            if entry.get("status") != "registered":
                continue

            doc_id = entry.get("doc_id")
            if not doc_id:
                continue

            # Skip if already in registry
            if doc_id in existing_ids:
                skipped += 1
                continue

            # Parse doc_id to extract category
            parts = doc_id.split("-")
            if len(parts) < 3:
                errors.append(f"Invalid doc_id format: {doc_id}")
                continue

            # Category is second segment (DOC-CATEGORY-NAME-NUM)
            category_prefix = parts[1]

            # Map prefix to category
            category = None
            for cat_name, cat_data in registry.data["categories"].items():
                if cat_data["prefix"].upper() == category_prefix.upper():
                    category = cat_name
                    break

            if not category:
                errors.append(
                    f"Unknown category prefix '{category_prefix}' in {doc_id}"
                )
                continue

            # Extract name from path
            path = entry.get("path", "")
            name = Path(path).stem if path else "unknown"
            title = entry.get("title", path)
            tags = [entry.get("file_type", "unknown")]

            # Add to registry
            registry.add_existing(
                doc_id=doc_id,
                category=category,
                name=name,
                path=path,
                title=title,
                tags=tags,
            )
            imported += 1

            if imported % 100 == 0:
                print(f"[INFO] Imported {imported} doc_ids...")

    # Recompute counters
    print(f"\n[INFO] Recomputing category counters...")
    registry.recompute_next_id_counters()

    # Update metadata
    registry.data["metadata"]["total_docs"] = len(registry.data["docs"])

    # Save registry
    registry._save_registry()

    print(f"\n[OK] Import complete:")
    print(f"   Imported:  {imported}")
    print(f"   Skipped:   {skipped} (already in registry)")

    if errors:
        print(f"\n[WARN] Errors encountered: {len(errors)}")
        if args.error_log:
            error_log = Path(args.error_log)
            error_log.parent.mkdir(parents=True, exist_ok=True)
            with open(error_log, "w", encoding="utf-8") as f:
                for err in errors:
                    f.write(f"{err}\n")
            print(f"[INFO] Error log written to: {error_log}")
        else:
            for err in errors[:10]:
                print(f"   - {err}")
            if len(errors) > 10:
                print(f"   ... and {len(errors) - 10} more")

    return 0 if not errors else 1


def main():
    parser = argparse.ArgumentParser(
        description="DOC_ID Registry CLI - Manage repository documentation identifiers"
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=REGISTRY_PATH,
        help="Path to DOC_ID_REGISTRY.yaml",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Mint command
    mint_parser = subparsers.add_parser("mint", help="Mint a new doc_id")
    mint_parser.add_argument(
        "--category", required=True, help="Category (core, error, patterns, etc.)"
    )
    mint_parser.add_argument(
        "--name", required=True, help="Name segments (e.g., orchestrator)"
    )
    mint_parser.add_argument("--title", help="Human-readable title")
    mint_parser.add_argument(
        "--artifact", action="append", help="Artifact spec (type:path)"
    )
    mint_parser.add_argument("--tags", help="Comma-separated tags")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search for doc_ids")
    search_parser.add_argument("--pattern", help="Regex pattern to match")
    search_parser.add_argument("--category", help="Filter by category")
    search_parser.add_argument("--status", help="Filter by status")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate all doc_ids")

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show statistics")

    # List command
    list_parser = subparsers.add_parser("list", help="List all doc_ids")
    list_parser.add_argument("--category", help="Filter by category")

    # Batch-mint command (Phase 3)
    batch_mint_parser = subparsers.add_parser(
        "batch-mint", help="Batch mint doc_ids from spec file"
    )
    batch_mint_parser.add_argument(
        "--batch", required=True, help="Path to batch spec YAML"
    )
    batch_mint_parser.add_argument(
        "--mode",
        choices=["dry-run", "deltas-only", "direct"],
        default="dry-run",
        help="Execution mode",
    )
    batch_mint_parser.add_argument(
        "--dry-run-report", help="Output path for dry-run report"
    )
    batch_mint_parser.add_argument("--delta-out", help="Output path for delta JSONL")
    batch_mint_parser.add_argument(
        "--no-registry",
        action="store_true",
        help="Do not write to registry (deltas-only mode)",
    )

    # Merge-deltas command (Phase 3)
    merge_deltas_parser = subparsers.add_parser(
        "merge-deltas", help="Merge delta files into registry"
    )
    merge_deltas_parser.add_argument(
        "delta_files", nargs="+", help="Delta JSONL file(s) to merge"
    )
    merge_deltas_parser.add_argument("--report", help="Output path for merge report")

    # Generate-index command (Phase 3)
    generate_index_parser = subparsers.add_parser(
        "generate-index", help="Generate index from registry"
    )

    # Import-from-inventory command (NEW - CRITICAL MIGRATION TOOL)
    import_parser = subparsers.add_parser(
        "import-from-inventory",
        help="Import existing doc_ids from docs_inventory.jsonl into registry",
    )
    import_parser.add_argument("--error-log", help="Path to write import error log")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        "mint": cmd_mint,
        "search": cmd_search,
        "validate": cmd_validate,
        "stats": cmd_stats,
        "list": cmd_list,
        "batch-mint": cmd_batch_mint,
        "merge-deltas": cmd_merge_deltas,
        "generate-index": cmd_generate_index,
        "import-from-inventory": cmd_import_from_inventory,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main() or 0)
