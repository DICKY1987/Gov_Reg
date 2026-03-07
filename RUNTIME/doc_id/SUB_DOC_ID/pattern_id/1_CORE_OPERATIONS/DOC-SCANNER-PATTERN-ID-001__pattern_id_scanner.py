#!/usr/bin/env python3
# DOC_LINK: DOC-SCANNER-PATTERN-ID-001
# DOC_ID: DOC-SCANNER-PATTERN-ID-001
"""
doc_id: DOC-SCANNER-PATTERN-ID-001
Pattern ID Scanner

PURPOSE: Scan repository for pattern references and definitions
PATTERN: PATTERN-PATTERN-ID-SCAN-001

USAGE:
    python pattern_id_scanner.py scan
    python pattern_id_scanner.py stats
    python pattern_id_scanner.py report --format markdown
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
import yaml

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from common import REPO_ROOT


class PatternIDScanner:
    """Scan repository for pattern definitions and references."""

    def __init__(self, repo_root: Path = REPO_ROOT):
        self.repo_root = repo_root
        self.inventory: List[Dict] = []
        self.pattern_references: Dict[str, List[str]] = {}  # pattern_name -> [file_paths]

    def scan_file_for_patterns(self, file_path: Path) -> Optional[Dict]:
        """Extract pattern metadata from file."""
        try:
            content = file_path.read_text(encoding='utf-8')

            # Look for PATTERN_ID in header
            pattern_id_match = re.search(r'PATTERN_ID:\s*(PATTERN-[A-Z0-9-]+)', content[:500])

            # Look for PATTERN: references
            pattern_refs = re.findall(r'PATTERN:\s*([A-Z0-9-]+)', content)

            # Look for PATTERN- prefixed patterns
            pat_refs = re.findall(r'PATTERN-([A-Z0-9-]+)', content)

            # Check if this file defines a pattern (has pattern_id)
            if pattern_id_match:
                pattern_id = pattern_id_match.group(1)

                # Extract pattern metadata
                pattern_meta = {
                    'pattern_id': pattern_id,
                    'file_path': str(file_path.relative_to(self.repo_root)),
                    'type': 'definition',
                    'status': 'active',
                    'discovered': datetime.now().replace(microsecond=0).isoformat() + 'Z'
                }

                # Extract doc_id if present
                doc_id_match = re.search(r'DOC_(?:ID|LINK):\s*(DOC-[A-Z0-9-]+)', content[:500])
                if doc_id_match:
                    pattern_meta['file_doc_id'] = doc_id_match.group(1)

                # Extract pattern name from docstring
                name_match = re.search(r'"""([^"]+)', content[500:1000])
                if name_match:
                    pattern_meta['name'] = name_match.group(1).strip()

                return pattern_meta

            # Track pattern references even if not a definition
            if pattern_refs or pat_refs:
                all_refs = set(pattern_refs + [f"PATTERN-{r}" for r in pat_refs])
                for ref in all_refs:
                    if ref not in self.pattern_references:
                        self.pattern_references[ref] = []
                    self.pattern_references[ref].append(str(file_path.relative_to(self.repo_root)))

            return None

        except Exception as e:
            print(f"⚠️ Error scanning {file_path}: {e}")
            return None

    def scan_all_patterns(self) -> List[Dict]:
        """Scan all Python files for pattern definitions and references."""
        self.inventory = []
        self.pattern_references = {}

        # Scan SUB_DOC_ID directory
        doc_id_dir = self.repo_root / "SUB_DOC_ID"
        if not doc_id_dir.exists():
            print(f"⚠️ SUB_DOC_ID directory not found")
            return []

        print(f"🔍 Scanning for patterns in {doc_id_dir}...")

        # Scan Python files
        for py_file in doc_id_dir.rglob("*.py"):
            # Skip test cache and pycache
            if '__pycache__' in str(py_file) or '.pytest_cache' in str(py_file):
                continue

            pattern = self.scan_file_for_patterns(py_file)
            if pattern:
                self.inventory.append(pattern)

        # Also scan markdown files for pattern specifications
        for md_file in doc_id_dir.rglob("*.md"):
            self._scan_markdown_patterns(md_file)

        return self.inventory

    def _scan_markdown_patterns(self, file_path: Path):
        """Scan markdown files for pattern specifications."""
        try:
            content = file_path.read_text(encoding='utf-8')

            # Look for pattern specifications in markdown
            # Pattern: ## Pattern Name or # Pattern: XXX
            pattern_headers = re.findall(r'(?:^|\n)##?\s+Pattern[:\s]+([^\n]+)', content, re.IGNORECASE)

            if pattern_headers:
                for header in pattern_headers:
                    # This is likely a pattern spec document
                    spec_meta = {
                        'type': 'specification',
                        'file_path': str(file_path.relative_to(self.repo_root)),
                        'pattern_name': header.strip(),
                        'status': 'specified',
                        'discovered': datetime.now().replace(microsecond=0).isoformat() + 'Z'
                    }

                    # Look for doc_id in YAML frontmatter
                    if content.startswith('---'):
                        frontmatter_match = re.search(r'doc_id:\s*["\']?(DOC-[A-Z0-9-]+)', content[:500])
                        if frontmatter_match:
                            spec_meta['file_doc_id'] = frontmatter_match.group(1)

                    self.inventory.append(spec_meta)

        except Exception as e:
            pass  # Silently skip markdown parsing errors

    def save_inventory(self, output_path: Path = None):
        """Save inventory to JSONL file."""
        if output_path is None:
            output_path = self.repo_root / "SUB_DOC_ID" / "pattern_id" / "5_REGISTRY_DATA" / "patterns_inventory.jsonl"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            for item in self.inventory:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')

        print(f"✅ Saved inventory: {output_path} ({len(self.inventory)} patterns)")

        # Also save pattern references
        refs_path = output_path.parent / "pattern_references.json"
        with open(refs_path, 'w', encoding='utf-8') as f:
            json.dump(self.pattern_references, f, indent=2, ensure_ascii=False)

        print(f"✅ Saved references: {refs_path} ({len(self.pattern_references)} unique patterns referenced)")

    def print_stats(self):
        """Print scan statistics."""
        total = len(self.inventory)
        by_type = {}
        assigned = 0

        for pattern in self.inventory:
            p_type = pattern.get('type', 'unknown')
            by_type[p_type] = by_type.get(p_type, 0) + 1
            if pattern.get('pattern_id'):
                assigned += 1

        print(f"\n📊 Pattern Scan Statistics")
        print(f"{'='*50}")
        print(f"Total patterns found: {total}")
        print(f"Patterns with IDs: {assigned}")
        print(f"Patterns without IDs: {total - assigned}")
        print(f"\nBy Type:")
        for p_type, count in sorted(by_type.items()):
            print(f"  {p_type}: {count}")

        print(f"\nPattern References:")
        print(f"  Unique patterns referenced: {len(self.pattern_references)}")

        # Show top referenced patterns
        if self.pattern_references:
            sorted_refs = sorted(self.pattern_references.items(),
                               key=lambda x: len(x[1]), reverse=True)
            print(f"\n  Top Referenced Patterns:")
            for pattern_name, files in sorted_refs[:5]:
                print(f"    {pattern_name}: {len(files)} files")


def main():
    parser = argparse.ArgumentParser(description="Scan execution patterns")
    parser.add_argument('command', choices=['scan', 'stats', 'report'],
                       help="Command to execute")
    parser.add_argument('--format', choices=['text', 'json', 'markdown'],
                       default='text', help="Output format")

    args = parser.parse_args()

    scanner = PatternIDScanner()

    if args.command == 'scan':
        print("🔍 Scanning for execution patterns...")
        scanner.scan_all_patterns()
        scanner.save_inventory()
        scanner.print_stats()

    elif args.command == 'stats':
        # Load existing inventory
        inventory_path = REPO_ROOT / "SUB_DOC_ID" / "pattern_id" / "5_REGISTRY_DATA" / "patterns_inventory.jsonl"
        if inventory_path.exists():
            with open(inventory_path, 'r', encoding='utf-8') as f:
                scanner.inventory = [json.loads(line) for line in f]

            refs_path = inventory_path.parent / "pattern_references.json"
            if refs_path.exists():
                with open(refs_path, 'r', encoding='utf-8') as f:
                    scanner.pattern_references = json.load(f)

            scanner.print_stats()
        else:
            print("⚠️ No inventory found. Run 'scan' first.")

    elif args.command == 'report':
        # Load and generate report
        inventory_path = REPO_ROOT / "SUB_DOC_ID" / "pattern_id" / "5_REGISTRY_DATA" / "patterns_inventory.jsonl"
        if inventory_path.exists():
            with open(inventory_path, 'r', encoding='utf-8') as f:
                scanner.inventory = [json.loads(line) for line in f]

            if args.format == 'markdown':
                print("# Execution Pattern Inventory\n")
                print(f"**Generated:** {datetime.now().replace(microsecond=0).isoformat()}Z\n")
                print(f"**Total Patterns:** {len(scanner.inventory)}\n")
                print("## Patterns\n")
                for pattern in scanner.inventory:
                    name = pattern.get('name', pattern.get('pattern_name', 'Unnamed'))
                    print(f"### {name}")
                    print(f"- **ID:** {pattern.get('pattern_id', 'UNASSIGNED')}")
                    print(f"- **Type:** {pattern.get('type', 'unknown')}")
                    print(f"- **Path:** `{pattern['file_path']}`")
                    print()
        else:
            print("⚠️ No inventory found. Run 'scan' first.")


if __name__ == '__main__':
    main()
