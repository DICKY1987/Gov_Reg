#!/usr/bin/env python3
# DOC_LINK: DOC-TOOL-TRIGGER-ID-ASSIGNER-001
# DOC_ID: DOC-TOOL-TRIGGER-ID-ASSIGNER-001
"""
doc_id: DOC-TOOL-TRIGGER-ID-ASSIGNER-001
Trigger ID Assigner

PURPOSE: Assign trigger_ids to automation files and update registry
PATTERN: PATTERN-TRIGGER-ID-ASSIGN-002

USAGE:
    python trigger_id_assigner.py auto-assign
    python trigger_id_assigner.py assign --file path/to/trigger.py --category watcher
    python trigger_id_assigner.py inject --trigger-id TRIGGER-WATCHER-FILE-WATCHER-001
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import yaml

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from common import REPO_ROOT


class TriggerIDAssigner:
    """Assign trigger_ids to automation files."""

    def __init__(self, repo_root: Path = REPO_ROOT):
        self.repo_root = repo_root
        self.registry_path = repo_root / "SUB_DOC_ID" / "trigger_id" / "5_REGISTRY_DATA" / "TRG_ID_REGISTRY.yaml"
        self.inventory_path = repo_root / "SUB_DOC_ID" / "trigger_id" / "5_REGISTRY_DATA" / "triggers_inventory.jsonl"
        self.registry = self._load_registry()

    def _load_registry(self) -> Dict:
        """Load trigger registry."""
        if self.registry_path.exists():
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return None

    def _save_registry(self):
        """Save updated registry."""
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.registry, f, default_flow_style=False, sort_keys=False)

    def _load_inventory(self) -> List[Dict]:
        """Load triggers inventory."""
        if not self.inventory_path.exists():
            return []

        with open(self.inventory_path, 'r', encoding='utf-8') as f:
            return [json.loads(line) for line in f]

    def mint_trigger_id(self, category: str) -> str:
        """Mint a new trigger_id."""
        cat_info = self.registry['categories'].get(category)
        if not cat_info:
            raise ValueError(f"Unknown category: {category}")

        prefix = cat_info['prefix']
        seq = cat_info['next_id']

        trigger_id = f"TRIGGER-{prefix}-{seq:03d}"

        # Increment counter
        cat_info['next_id'] = seq + 1

        return trigger_id

    def inject_trigger_id(self, file_path: Path, trigger_id: str) -> bool:
        """Inject trigger_id into file header."""
        try:
            content = file_path.read_text(encoding='utf-8')

            # Determine file type
            if file_path.suffix == '.py':
                return self._inject_python(file_path, content, trigger_id)
            elif file_path.suffix == '.ps1':
                return self._inject_powershell(file_path, content, trigger_id)
            elif file_path.suffix == '.bat':
                return self._inject_batch(file_path, content, trigger_id)
            else:
                print(f"⚠️ Unsupported file type: {file_path.suffix}")
                return False

        except Exception as e:
            print(f"❌ Error injecting into {file_path}: {e}")
            return False

    def _inject_python(self, file_path: Path, content: str, trigger_id: str) -> bool:
        """Inject TRIGGER_ID into Python file."""
        lines = content.split('\n')

        # Check if already has TRIGGER_ID
        if any('TRIGGER_ID:' in line for line in lines[:10]):
            print(f"⚠️ File already has TRIGGER_ID: {file_path.name}")
            return False

        # Find insertion point (after shebang and encoding)
        insert_idx = 0
        for i, line in enumerate(lines[:5]):
            if line.startswith('#!') or 'coding:' in line or 'coding=' in line:
                insert_idx = i + 1

        # Insert TRIGGER_ID line
        lines.insert(insert_idx, f"# TRIGGER_ID: {trigger_id}")

        # Write back
        file_path.write_text('\n'.join(lines), encoding='utf-8')
        print(f"✅ Injected {trigger_id} into {file_path.name}")
        return True

    def _inject_powershell(self, file_path: Path, content: str, trigger_id: str) -> bool:
        """Inject TRIGGER_ID into PowerShell file."""
        lines = content.split('\n')

        # Check if already has TRIGGER_ID
        if any('TRIGGER_ID:' in line for line in lines[:10]):
            print(f"⚠️ File already has TRIGGER_ID: {file_path.name}")
            return False

        # Insert at top
        lines.insert(0, f"# TRIGGER_ID: {trigger_id}")

        # Write back
        file_path.write_text('\n'.join(lines), encoding='utf-8')
        print(f"✅ Injected {trigger_id} into {file_path.name}")
        return True

    def _inject_batch(self, file_path: Path, content: str, trigger_id: str) -> bool:
        """Inject TRIGGER_ID into batch file."""
        lines = content.split('\n')

        # Check if already has TRIGGER_ID
        if any('TRIGGER_ID:' in line for line in lines[:10]):
            print(f"⚠️ File already has TRIGGER_ID: {file_path.name}")
            return False

        # Insert at top
        lines.insert(0, f"REM TRIGGER_ID: {trigger_id}")

        # Write back
        file_path.write_text('\n'.join(lines), encoding='utf-8')
        print(f"✅ Injected {trigger_id} into {file_path.name}")
        return True

    def register_trigger(self, trigger_id: str, trigger_meta: Dict):
        """Add trigger to registry."""
        entry = {
            'trigger_id': trigger_id,
            'category': trigger_meta['trigger_type'],
            'name': trigger_meta['name'],
            'file_path': trigger_meta['file_path'],
            'enabled': True,
            'first_seen': datetime.now().replace(microsecond=0).isoformat() + 'Z',
            'last_seen': datetime.now().replace(microsecond=0).isoformat() + 'Z',
            'status': 'active'
        }

        # Add optional fields
        if 'file_doc_id' in trigger_meta:
            entry['file_doc_id'] = trigger_meta['file_doc_id']
        if 'patterns' in trigger_meta:
            entry['patterns'] = trigger_meta['patterns']
        if 'schedule' in trigger_meta:
            entry['schedule'] = trigger_meta['schedule']

        self.registry['triggers'].append(entry)
        self.registry['meta']['total_triggers'] += 1
        self.registry['meta']['updated_utc'] = datetime.now().replace(microsecond=0).isoformat() + 'Z'

    def auto_assign_all(self, dry_run: bool = False):
        """Auto-assign trigger_ids to all unassigned triggers."""
        inventory = self._load_inventory()
        unassigned = [t for t in inventory if not t.get('trigger_id')]

        print(f"\n🎯 Auto-Assigning Trigger IDs")
        print(f"{'='*50}")
        print(f"Total triggers: {len(inventory)}")
        print(f"Unassigned: {len(unassigned)}")

        if dry_run:
            print("\n🔍 DRY RUN - No changes will be made\n")

        assigned_count = 0

        for trigger in unassigned:
            # Map trigger_type to category
            category_map = {
                'watcher': 'watcher',
                'hook': 'hook',
                'scheduled': 'scheduled',
                'runner': 'runner'
            }

            category = category_map.get(trigger['trigger_type'])
            if not category:
                print(f"⚠️ Unknown trigger type: {trigger['trigger_type']}")
                continue

            # Mint ID
            trigger_id = self.mint_trigger_id(category)

            if dry_run:
                print(f"Would assign {trigger_id} to {trigger['file_path']}")
            else:
                # Inject into file
                file_path = self.repo_root / trigger['file_path']
                if self.inject_trigger_id(file_path, trigger_id):
                    # Register
                    self.register_trigger(trigger_id, trigger)
                    assigned_count += 1

        if not dry_run and assigned_count > 0:
            self._save_registry()
            print(f"\n✅ Assigned {assigned_count} trigger IDs")
            print(f"📝 Registry updated: {self.registry_path}")

        return assigned_count


def main():
    parser = argparse.ArgumentParser(description="Assign trigger IDs")
    parser.add_argument('command', choices=['auto-assign', 'assign', 'inject'],
                       help="Command to execute")
    parser.add_argument('--file', type=str, help="Target file path")
    parser.add_argument('--category', type=str,
                       choices=['watcher', 'hook', 'scheduled', 'runner'],
                       help="Trigger category")
    parser.add_argument('--trigger-id', type=str, help="Specific trigger ID")
    parser.add_argument('--dry-run', action='store_true',
                       help="Show what would be done without making changes")

    args = parser.parse_args()

    assigner = TriggerIDAssigner()

    if args.command == 'auto-assign':
        assigner.auto_assign_all(dry_run=args.dry_run)

    elif args.command == 'assign':
        if not args.file or not args.category:
            print("❌ --file and --category required for 'assign' command")
            sys.exit(1)

        trigger_id = assigner.mint_trigger_id(args.category)
        file_path = REPO_ROOT / args.file

        if assigner.inject_trigger_id(file_path, trigger_id):
            print(f"✅ Assigned {trigger_id}")

    elif args.command == 'inject':
        if not args.file or not args.trigger_id:
            print("❌ --file and --trigger-id required for 'inject' command")
            sys.exit(1)

        file_path = REPO_ROOT / args.file
        assigner.inject_trigger_id(file_path, args.trigger_id)


if __name__ == '__main__':
    main()
