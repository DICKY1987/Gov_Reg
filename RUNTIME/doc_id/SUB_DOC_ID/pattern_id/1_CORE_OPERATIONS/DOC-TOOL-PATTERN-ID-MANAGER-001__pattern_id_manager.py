#!/usr/bin/env python3
# DOC_LINK: DOC-TOOL-PATTERN-ID-MANAGER-001
# DOC_ID: DOC-TOOL-PATTERN-ID-MANAGER-001
"""
doc_id: DOC-TOOL-PATTERN-ID-MANAGER-001
Pattern ID Manager

PURPOSE: Create and manage execution pattern identities
PATTERN: PATTERN-PATTERN-ID-MANAGE-002

A pattern is a multi-file concept consisting of:
- Specification (optional): Pattern documentation
- Executor: Implementation file(s)
- Tests (optional): Test coverage

USAGE:
    # Create new pattern
    python pattern_id_manager.py create --name "Batch Doc ID Minting" --category exec

    # Link file to pattern
    python pattern_id_manager.py link --pattern-id PATTERN-EXEC-DOC-ID-SCANNING-001 --file path/to/file.py --role executor

    # List patterns
    python pattern_id_manager.py list

    # Show pattern details
    python pattern_id_manager.py show --pattern-id PATTERN-EXEC-DOC-ID-SCANNING-001
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import yaml

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from common import REPO_ROOT


class PatternIDManager:
    """Manage pattern identities and relationships."""

    def __init__(self, repo_root: Path = REPO_ROOT):
        self.repo_root = repo_root
        self.registry_path = repo_root / "SUB_DOC_ID" / "pattern_id" / "5_REGISTRY_DATA" / "PAT_ID_REGISTRY.yaml"
        self.registry = self._load_registry()

    def _load_registry(self) -> Dict:
        """Load pattern registry."""
        if self.registry_path.exists():
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return None

    def _save_registry(self):
        """Save updated registry."""
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.registry, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    def mint_pattern_id(self, category: str) -> str:
        """Mint a new pattern_id."""
        cat_info = self.registry['categories'].get(category)
        if not cat_info:
            raise ValueError(f"Unknown category: {category}")

        prefix = cat_info['prefix']
        seq = cat_info['next_id']

        pattern_id = f"PATTERN-{prefix}-{seq:03d}"

        # Increment counter
        cat_info['next_id'] = seq + 1

        return pattern_id

    def create_pattern(self, name: str, category: str, description: str = None) -> str:
        """Create a new pattern entry."""
        pattern_id = self.mint_pattern_id(category)

        pattern_entry = {
            'pattern_id': pattern_id,
            'category': category,
            'name': name,
            'description': description or f"{name} execution pattern",
            'status': 'active',
            'files': {},
            'first_seen': datetime.now().replace(microsecond=0).isoformat() + 'Z',
            'last_seen': datetime.now().replace(microsecond=0).isoformat() + 'Z'
        }

        self.registry['patterns'].append(pattern_entry)
        self.registry['meta']['total_patterns'] += 1
        self.registry['meta']['updated_utc'] = datetime.now().replace(microsecond=0).isoformat() + 'Z'

        self._save_registry()

        print(f"✅ Created pattern {pattern_id}: {name}")
        return pattern_id

    def link_file_to_pattern(self, pattern_id: str, file_path: str, role: str, doc_id: str = None):
        """Link a file to a pattern with a specific role (spec/executor/test)."""
        # Find pattern
        pattern = None
        for p in self.registry['patterns']:
            if p['pattern_id'] == pattern_id:
                pattern = p
                break

        if not pattern:
            print(f"❌ Pattern not found: {pattern_id}")
            return False

        # Valid roles
        valid_roles = ['spec', 'executor', 'test']
        if role not in valid_roles:
            print(f"❌ Invalid role: {role}. Must be one of: {', '.join(valid_roles)}")
            return False

        # Add file to pattern
        if role not in pattern['files']:
            pattern['files'][role] = []

        # Support multiple files per role (e.g., multiple executors)
        if isinstance(pattern['files'][role], str):
            pattern['files'][role] = [pattern['files'][role]]

        file_entry = file_path
        if doc_id:
            file_entry = {'path': file_path, 'doc_id': doc_id}

        pattern['files'][role].append(file_entry)
        pattern['last_seen'] = datetime.now().replace(microsecond=0).isoformat() + 'Z'

        self._save_registry()

        print(f"✅ Linked {role} file to {pattern_id}: {file_path}")
        return True

    def list_patterns(self, category: str = None):
        """List all patterns, optionally filtered by category."""
        patterns = self.registry['patterns']

        if category:
            patterns = [p for p in patterns if p['category'] == category]

        if not patterns:
            print("No patterns found.")
            return

        print(f"\n📋 Pattern Inventory ({len(patterns)} patterns)")
        print("=" * 60)

        for pattern in patterns:
            status_icon = "✅" if pattern['status'] == 'active' else "⚠️"
            print(f"\n{status_icon} {pattern['pattern_id']}: {pattern['name']}")
            print(f"   Category: {pattern['category']}")

            if pattern.get('files'):
                print(f"   Files:")
                for role, files in pattern['files'].items():
                    if isinstance(files, list):
                        for f in files:
                            if isinstance(f, dict):
                                print(f"     - {role}: {f['path']} ({f['doc_id']})")
                            else:
                                print(f"     - {role}: {f}")
                    else:
                        print(f"     - {role}: {files}")
            else:
                print(f"   Files: None (pattern defined but not linked)")

    def show_pattern(self, pattern_id: str):
        """Show detailed information about a pattern."""
        pattern = None
        for p in self.registry['patterns']:
            if p['pattern_id'] == pattern_id:
                pattern = p
                break

        if not pattern:
            print(f"❌ Pattern not found: {pattern_id}")
            return

        print(f"\n📋 Pattern Details: {pattern_id}")
        print("=" * 60)
        print(f"Name: {pattern['name']}")
        print(f"Category: {pattern['category']}")
        print(f"Status: {pattern['status']}")
        print(f"Description: {pattern.get('description', 'N/A')}")
        print(f"First Seen: {pattern['first_seen']}")
        print(f"Last Seen: {pattern['last_seen']}")

        print(f"\nLinked Files:")
        if pattern.get('files'):
            for role, files in pattern['files'].items():
                print(f"  {role}:")
                if isinstance(files, list):
                    for f in files:
                        if isinstance(f, dict):
                            print(f"    - {f['path']}")
                            print(f"      doc_id: {f['doc_id']}")
                        else:
                            print(f"    - {f}")
                else:
                    print(f"    - {files}")
        else:
            print("  None")

        print()

    def validate_pattern_completeness(self) -> Dict[str, List[str]]:
        """Check which patterns are missing spec/executor/tests."""
        issues = {
            'missing_executor': [],
            'missing_tests': [],
            'missing_spec': []
        }

        for pattern in self.registry['patterns']:
            files = pattern.get('files', {})

            if not files.get('executor'):
                issues['missing_executor'].append(pattern['pattern_id'])
            if not files.get('test'):
                issues['missing_tests'].append(pattern['pattern_id'])
            if not files.get('spec'):
                issues['missing_spec'].append(pattern['pattern_id'])

        return issues


def main():
    parser = argparse.ArgumentParser(description="Manage execution patterns")

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # create command
    create_parser = subparsers.add_parser('create', help='Create new pattern')
    create_parser.add_argument('--name', required=True, help='Pattern name')
    create_parser.add_argument('--category', required=True,
                              choices=['exec', 'doc', 'test', 'validation'],
                              help='Pattern category')
    create_parser.add_argument('--description', help='Pattern description')

    # link command
    link_parser = subparsers.add_parser('link', help='Link file to pattern')
    link_parser.add_argument('--pattern-id', required=True, help='Pattern ID')
    link_parser.add_argument('--file', required=True, help='File path')
    link_parser.add_argument('--role', required=True,
                            choices=['spec', 'executor', 'test'],
                            help='File role')
    link_parser.add_argument('--doc-id', help='File doc_id')

    # list command
    list_parser = subparsers.add_parser('list', help='List patterns')
    list_parser.add_argument('--category',
                            choices=['exec', 'doc', 'test', 'validation'],
                            help='Filter by category')

    # show command
    show_parser = subparsers.add_parser('show', help='Show pattern details')
    show_parser.add_argument('--pattern-id', required=True, help='Pattern ID')

    # validate command
    validate_parser = subparsers.add_parser('validate', help='Validate pattern completeness')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    manager = PatternIDManager()

    if args.command == 'create':
        manager.create_pattern(args.name, args.category, args.description)

    elif args.command == 'link':
        manager.link_file_to_pattern(args.pattern_id, args.file, args.role, args.doc_id)

    elif args.command == 'list':
        manager.list_patterns(args.category)

    elif args.command == 'show':
        manager.show_pattern(args.pattern_id)

    elif args.command == 'validate':
        issues = manager.validate_pattern_completeness()

        print("\n🔍 Pattern Completeness Validation")
        print("=" * 60)

        all_good = True

        if issues['missing_executor']:
            all_good = False
            print(f"\n❌ Patterns missing executor ({len(issues['missing_executor'])}):")
            for pid in issues['missing_executor']:
                print(f"  - {pid}")

        if issues['missing_tests']:
            print(f"\n⚠️  Patterns missing tests ({len(issues['missing_tests'])}):")
            for pid in issues['missing_tests']:
                print(f"  - {pid}")

        if issues['missing_spec']:
            print(f"\n⚠️  Patterns missing spec ({len(issues['missing_spec'])}):")
            for pid in issues['missing_spec']:
                print(f"  - {pid}")

        if all_good:
            print("\n✅ All patterns have executors!")

        print()


if __name__ == '__main__':
    main()
