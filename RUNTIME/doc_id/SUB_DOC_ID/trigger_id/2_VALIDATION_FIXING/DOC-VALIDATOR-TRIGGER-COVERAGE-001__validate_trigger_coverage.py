#!/usr/bin/env python3
# DOC_LINK: DOC-VALIDATOR-TRIGGER-COVERAGE-001
# DOC_ID: DOC-VALIDATOR-TRIGGER-COVERAGE-001
"""
doc_id: DOC-VALIDATOR-TRIGGER-COVERAGE-001
Validate Trigger ID Coverage

PURPOSE: Ensure all automation triggers have assigned IDs
PATTERN: PATTERN-TRIGGER-ID-VALIDATE-001

USAGE:
    python validate_trigger_coverage.py
    python validate_trigger_coverage.py --strict
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List
import yaml

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from common import REPO_ROOT


class TriggerCoverageValidator:
    """Validate trigger ID coverage."""

    def __init__(self, repo_root: Path = REPO_ROOT):
        self.repo_root = repo_root
        self.registry_path = repo_root / "SUB_DOC_ID" / "trigger_id" / "5_REGISTRY_DATA" / "TRG_ID_REGISTRY.yaml"
        self.inventory_path = repo_root / "SUB_DOC_ID" / "trigger_id" / "5_REGISTRY_DATA" / "triggers_inventory.jsonl"
        self.errors = []
        self.warnings = []

    def load_registry(self) -> Dict:
        """Load trigger registry."""
        if not self.registry_path.exists():
            self.errors.append(f"Registry not found: {self.registry_path}")
            return {}

        with open(self.registry_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def load_inventory(self) -> List[Dict]:
        """Load triggers inventory."""
        if not self.inventory_path.exists():
            self.errors.append(f"Inventory not found: {self.inventory_path}")
            return []

        with open(self.inventory_path, 'r', encoding='utf-8') as f:
            return [json.loads(line) for line in f]

    def validate_coverage(self) -> bool:
        """Validate that all triggers have IDs."""
        inventory = self.load_inventory()

        if not inventory:
            return False

        unassigned = [t for t in inventory if not t.get('trigger_id')]

        if unassigned:
            self.errors.append(f"Found {len(unassigned)} triggers without IDs:")
            for trigger in unassigned:
                self.errors.append(f"  - {trigger['file_path']} (type: {trigger['trigger_type']})")
            return False

        print(f"✅ Coverage: 100% ({len(inventory)}/{len(inventory)} triggers have IDs)")
        return True

    def validate_uniqueness(self) -> bool:
        """Validate that all trigger IDs are unique."""
        registry = self.load_registry()

        if not registry or 'triggers' not in registry:
            return False

        trigger_ids = [t['trigger_id'] for t in registry['triggers']]
        duplicates = set([tid for tid in trigger_ids if trigger_ids.count(tid) > 1])

        if duplicates:
            self.errors.append(f"Found duplicate trigger IDs:")
            for tid in duplicates:
                self.errors.append(f"  - {tid}")
            return False

        print(f"✅ Uniqueness: All {len(trigger_ids)} trigger IDs are unique")
        return True

    def validate_format(self) -> bool:
        """Validate trigger ID format."""
        import re

        registry = self.load_registry()

        if not registry or 'triggers' not in registry:
            return False

        pattern = re.compile(r'^TRIGGER-[A-Z]+-\d{3}$')
        invalid = []

        for trigger in registry['triggers']:
            tid = trigger['trigger_id']
            if not pattern.match(tid):
                invalid.append(tid)

        if invalid:
            self.errors.append(f"Found {len(invalid)} triggers with invalid ID format:")
            for tid in invalid:
                self.errors.append(f"  - {tid}")
            return False

        print(f"✅ Format: All trigger IDs follow TRIGGER-CATEGORY-### format")
        return True

    def validate_sync(self) -> bool:
        """Validate registry is synced with inventory."""
        registry = self.load_registry()
        inventory = self.load_inventory()

        if not registry or not inventory:
            return False

        registry_paths = set(t['file_path'] for t in registry['triggers'])
        inventory_paths = set(t['file_path'] for t in inventory)

        missing_in_registry = inventory_paths - registry_paths
        extra_in_registry = registry_paths - inventory_paths

        has_errors = False

        if missing_in_registry:
            self.errors.append(f"Found {len(missing_in_registry)} triggers in inventory but not registry:")
            for path in missing_in_registry:
                self.errors.append(f"  - {path}")
            has_errors = True

        if extra_in_registry:
            self.warnings.append(f"Found {len(extra_in_registry)} triggers in registry but not inventory:")
            for path in extra_in_registry:
                self.warnings.append(f"  - {path} (may have been deleted)")

        if not has_errors:
            print(f"✅ Sync: Registry and inventory are synchronized")

        return not has_errors

    def validate_all(self, strict: bool = False) -> bool:
        """Run all validations."""
        print("\n🔍 Validating Trigger ID Coverage")
        print("=" * 50)

        results = []

        results.append(("Coverage", self.validate_coverage()))
        results.append(("Uniqueness", self.validate_uniqueness()))
        results.append(("Format", self.validate_format()))
        results.append(("Sync", self.validate_sync()))

        # Print results
        print("\n📊 Validation Results")
        print("=" * 50)

        for name, passed in results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{name}: {status}")

        # Print errors
        if self.errors:
            print("\n❌ Errors:")
            for error in self.errors:
                print(error)

        # Print warnings
        if self.warnings:
            print("\n⚠️  Warnings:")
            for warning in self.warnings:
                print(warning)

        all_passed = all(result[1] for result in results)

        if all_passed and not self.warnings:
            print("\n✅ All validations passed!")
            return True
        elif all_passed and not strict:
            print("\n⚠️  All validations passed with warnings")
            return True
        else:
            print("\n❌ Validation failed")
            return False


def main():
    parser = argparse.ArgumentParser(description="Validate trigger ID coverage")
    parser.add_argument('--strict', action='store_true',
                       help="Fail on warnings")

    args = parser.parse_args()

    validator = TriggerCoverageValidator()
    success = validator.validate_all(strict=args.strict)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
