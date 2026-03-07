#!/usr/bin/env python3
# DOC_LINK: DOC-SCANNER-TRIGGER-ID-001
# DOC_ID: DOC-SCANNER-TRIGGER-ID-001
"""
doc_id: DOC-SCANNER-TRIGGER-ID-001
Trigger ID Scanner

PURPOSE: Scan automation hooks for trigger definitions and generate inventory
PATTERN: PATTERN-TRIGGER-ID-SCAN-001

USAGE:
    python trigger_id_scanner.py scan
    python trigger_id_scanner.py stats
    python trigger_id_scanner.py report --format markdown
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


class TriggerIDScanner:
    """Scan repository for automation triggers."""

    def __init__(self, repo_root: Path = REPO_ROOT):
        self.repo_root = repo_root
        self.inventory: List[Dict] = []
        self.automation_dir = repo_root / "SUB_DOC_ID" / "3_AUTOMATION_HOOKS"

    def scan_python_trigger(self, file_path: Path) -> Optional[Dict]:
        """Extract trigger metadata from Python file."""
        try:
            content = file_path.read_text(encoding='utf-8')

            # Look for TRIGGER_ID in header
            trigger_id_match = re.search(r'TRIGGER_ID:\s*(TRIGGER-[A-Z0-9-]+)', content[:500])

            # Detect trigger type
            trigger_type = self._detect_trigger_type(file_path, content)
            if not trigger_type:
                return None

            # Extract metadata
            trigger_meta = {
                'file_path': str(file_path.relative_to(self.repo_root)),
                'trigger_type': trigger_type,
                'trigger_id': trigger_id_match.group(1) if trigger_id_match else None,
                'name': file_path.stem,
                'status': 'active',
                'discovered': datetime.utcnow().isoformat() + 'Z'
            }

            # Extract doc_id if present
            doc_id_match = re.search(r'DOC_(?:ID|LINK):\s*(DOC-[A-Z0-9-]+)', content[:500])
            if doc_id_match:
                trigger_meta['file_doc_id'] = doc_id_match.group(1)

            # Extract additional metadata based on type
            if trigger_type == 'watcher':
                trigger_meta.update(self._extract_watcher_config(content))
            elif trigger_type == 'hook':
                trigger_meta.update(self._extract_hook_config(content))
            elif trigger_type == 'scheduled':
                trigger_meta.update(self._extract_scheduled_config(content))

            return trigger_meta

        except Exception as e:
            print(f"⚠️ Error scanning {file_path}: {e}")
            return None

    def _detect_trigger_type(self, file_path: Path, content: str) -> Optional[str]:
        """Detect trigger type from filename and content."""
        name_lower = file_path.name.lower()

        if 'watcher' in name_lower or 'watch' in name_lower:
            return 'watcher'
        elif 'hook' in name_lower or 'pre_commit' in name_lower or 'pre-commit' in name_lower:
            return 'hook'
        elif 'scheduled' in name_lower or 'cron' in name_lower or 'nightly' in name_lower:
            return 'scheduled'
        elif 'runner' in name_lower or 'automation' in name_lower:
            return 'runner'

        # Check content
        if 'watchdog' in content.lower() or 'Observer()' in content:
            return 'watcher'
        if 'git' in content.lower() and 'hook' in content.lower():
            return 'hook'

        return None

    def _extract_watcher_config(self, content: str) -> Dict:
        """Extract file watcher configuration."""
        config = {}

        # Look for patterns
        pattern_match = re.search(r'patterns?\s*=\s*\[([^\]]+)\]', content)
        if pattern_match:
            config['patterns'] = pattern_match.group(1).strip()

        # Look for exclude patterns
        exclude_match = re.search(r'ignore_patterns?\s*=\s*\[([^\]]+)\]', content)
        if exclude_match:
            config['exclude_patterns'] = exclude_match.group(1).strip()

        return config

    def _extract_hook_config(self, content: str) -> Dict:
        """Extract git hook configuration."""
        config = {}

        # Check if it's pre-commit
        if 'pre-commit' in content.lower() or 'pre_commit' in content.lower():
            config['hook_type'] = 'pre-commit'

        # Look for validation commands
        if 'validate' in content.lower():
            config['action'] = 'validate'

        return config

    def _extract_scheduled_config(self, content: str) -> Dict:
        """Extract scheduled task configuration."""
        config = {}

        # Look for schedule patterns
        schedule_match = re.search(r'schedule\s*=\s*["\']([^"\']+)["\']', content)
        if schedule_match:
            config['schedule'] = schedule_match.group(1)

        # Look for task name
        task_match = re.search(r'task_name\s*=\s*["\']([^"\']+)["\']', content)
        if task_match:
            config['task_name'] = task_match.group(1)

        return config

    def scan_all_triggers(self) -> List[Dict]:
        """Scan all automation files for triggers."""
        self.inventory = []

        if not self.automation_dir.exists():
            print(f"⚠️ Automation directory not found: {self.automation_dir}")
            return []

        # Scan Python files
        for py_file in self.automation_dir.glob("*.py"):
            trigger = self.scan_python_trigger(py_file)
            if trigger:
                self.inventory.append(trigger)

        # Scan subdirectories
        for subdir in self.automation_dir.iterdir():
            if subdir.is_dir() and not subdir.name.startswith('.'):
                for py_file in subdir.glob("*.py"):
                    trigger = self.scan_python_trigger(py_file)
                    if trigger:
                        self.inventory.append(trigger)

        # Scan PowerShell scripts
        for ps_file in self.automation_dir.glob("*.ps1"):
            trigger = self._scan_powershell_trigger(ps_file)
            if trigger:
                self.inventory.append(trigger)

        # Scan batch files
        for bat_file in self.automation_dir.glob("*.bat"):
            trigger = self._scan_batch_trigger(bat_file)
            if trigger:
                self.inventory.append(trigger)

        return self.inventory

    def _scan_powershell_trigger(self, file_path: Path) -> Optional[Dict]:
        """Scan PowerShell trigger file."""
        try:
            content = file_path.read_text(encoding='utf-8')

            trigger_id_match = re.search(r'TRIGGER_ID:\s*(TRIGGER-[A-Z0-9-]+)', content[:500])

            return {
                'file_path': str(file_path.relative_to(self.repo_root)),
                'trigger_type': 'runner',
                'trigger_id': trigger_id_match.group(1) if trigger_id_match else None,
                'name': file_path.stem,
                'language': 'powershell',
                'status': 'active',
                'discovered': datetime.utcnow().isoformat() + 'Z'
            }
        except Exception:
            return None

    def _scan_batch_trigger(self, file_path: Path) -> Optional[Dict]:
        """Scan batch file trigger."""
        try:
            content = file_path.read_text(encoding='utf-8')

            trigger_id_match = re.search(r'TRIGGER_ID:\s*(TRIGGER-[A-Z0-9-]+)', content[:500])

            return {
                'file_path': str(file_path.relative_to(self.repo_root)),
                'trigger_type': 'runner',
                'trigger_id': trigger_id_match.group(1) if trigger_id_match else None,
                'name': file_path.stem,
                'language': 'batch',
                'status': 'active',
                'discovered': datetime.utcnow().isoformat() + 'Z'
            }
        except Exception:
            return None

    def save_inventory(self, output_path: Path = None):
        """Save inventory to JSONL file."""
        if output_path is None:
            output_path = self.repo_root / "SUB_DOC_ID" / "trigger_id" / "5_REGISTRY_DATA" / "triggers_inventory.jsonl"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            for item in self.inventory:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')

        print(f"✅ Saved inventory: {output_path} ({len(self.inventory)} triggers)")

    def print_stats(self):
        """Print scan statistics."""
        total = len(self.inventory)
        by_type = {}
        assigned = 0

        for trigger in self.inventory:
            t_type = trigger['trigger_type']
            by_type[t_type] = by_type.get(t_type, 0) + 1
            if trigger.get('trigger_id'):
                assigned += 1

        print(f"\n📊 Trigger Scan Statistics")
        print(f"{'='*50}")
        print(f"Total triggers found: {total}")
        print(f"Triggers with IDs: {assigned}")
        print(f"Triggers without IDs: {total - assigned}")
        print(f"\nBy Type:")
        for t_type, count in sorted(by_type.items()):
            print(f"  {t_type}: {count}")


def main():
    parser = argparse.ArgumentParser(description="Scan automation triggers")
    parser.add_argument('command', choices=['scan', 'stats', 'report'],
                       help="Command to execute")
    parser.add_argument('--format', choices=['text', 'json', 'markdown'],
                       default='text', help="Output format")

    args = parser.parse_args()

    scanner = TriggerIDScanner()

    if args.command == 'scan':
        print("🔍 Scanning for automation triggers...")
        scanner.scan_all_triggers()
        scanner.save_inventory()
        scanner.print_stats()

    elif args.command == 'stats':
        # Load existing inventory
        inventory_path = REPO_ROOT / "SUB_DOC_ID" / "trigger_id" / "5_REGISTRY_DATA" / "triggers_inventory.jsonl"
        if inventory_path.exists():
            with open(inventory_path, 'r', encoding='utf-8') as f:
                scanner.inventory = [json.loads(line) for line in f]
            scanner.print_stats()
        else:
            print("⚠️ No inventory found. Run 'scan' first.")

    elif args.command == 'report':
        # Load and generate report
        inventory_path = REPO_ROOT / "SUB_DOC_ID" / "trigger_id" / "5_REGISTRY_DATA" / "triggers_inventory.jsonl"
        if inventory_path.exists():
            with open(inventory_path, 'r', encoding='utf-8') as f:
                scanner.inventory = [json.loads(line) for line in f]

            if args.format == 'markdown':
                print("# Automation Trigger Inventory\n")
                print(f"**Generated:** {datetime.utcnow().isoformat()}Z\n")
                print(f"**Total Triggers:** {len(scanner.inventory)}\n")
                print("## Triggers\n")
                for trigger in scanner.inventory:
                    print(f"### {trigger['name']}")
                    print(f"- **Type:** {trigger['trigger_type']}")
                    print(f"- **ID:** {trigger.get('trigger_id', 'UNASSIGNED')}")
                    print(f"- **Path:** `{trigger['file_path']}`")
                    print()
        else:
            print("⚠️ No inventory found. Run 'scan' first.")


if __name__ == '__main__':
    main()
