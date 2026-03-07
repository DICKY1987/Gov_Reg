#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# DOC_LINK: DOC-TEST-DOC-ID-SYSTEM-TESTS-001
"""
Comprehensive DOC_ID System Tests

PURPOSE: Test all aspects of doc_id system for bugs and edge cases
PATTERN: PATTERN-TEST-DOC-ID-COMPREHENSIVE-001
"""

import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).parent.parent
DOC_ID_DIR = REPO_ROOT / "5_REGISTRY_DATA"
REGISTRY_PATH = DOC_ID_DIR / "DOC_ID_REGISTRY.yaml"
INVENTORY_PATH = DOC_ID_DIR / "docs_inventory.jsonl"

# Valid doc_id pattern
VALID_DOC_ID_PATTERN = re.compile(r"^DOC-[A-Z0-9]+-[A-Z0-9]+(-[A-Z0-9]+)*-[0-9]{3}$")


class TestDocIDFormat:
    """Test doc_id format compliance."""

    def test_registry_exists(self):
        """Registry file should exist."""
        assert REGISTRY_PATH.exists(), f"Registry not found: {REGISTRY_PATH}"

    def test_inventory_exists(self):
        """Inventory file should exist."""
        assert INVENTORY_PATH.exists(), f"Inventory not found: {INVENTORY_PATH}"

    def test_valid_doc_id_pattern(self):
        """Test valid doc_id pattern matching."""
        valid_ids = [
            "DOC-CORE-TEST-001",
            "DOC-GUIDE-README-123",
            "DOC-PATTERN-BATCH-MINT-337",
            "DOC-SCRIPT-SCANNER-046",
        ]

        for doc_id in valid_ids:
            assert VALID_DOC_ID_PATTERN.match(doc_id), f"Valid ID rejected: {doc_id}"

    def test_invalid_doc_id_pattern(self):
        """Test invalid doc_id pattern rejection."""
        invalid_ids = [
            "DOC-TEST",  # Missing suffix
            "DOC-TEST-",  # Trailing dash
            "DOC-TEST-1",  # Single digit
            "DOC-TEST-12",  # Two digits
            "doc-test-001",  # Lowercase
            "DOC_TEST-001",  # Underscore instead of dash
            "TEST-001",  # Missing DOC prefix
        ]

        for doc_id in invalid_ids:
            assert not VALID_DOC_ID_PATTERN.match(doc_id), f"Invalid ID accepted: {doc_id}"

    def test_no_invalid_doc_ids_in_inventory(self):
        """Inventory should not contain invalid doc_ids."""
        invalid_count = 0
        invalid_entries = []

        with open(INVENTORY_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                entry = json.loads(line.strip())
                if entry.get('status') == 'invalid':
                    invalid_count += 1
                    invalid_entries.append(entry)

        if invalid_count > 0:
            print(f"\n⚠️  Found {invalid_count} invalid doc_ids:")
            for entry in invalid_entries[:10]:  # Show first 10
                print(f"  - {entry['path']}: {entry.get('doc_id')}")

        assert invalid_count == 0, f"Found {invalid_count} files with invalid doc_ids"


class TestDocIDUniqueness:
    """Test doc_id uniqueness across system."""

    def test_registry_doc_ids_unique(self):
        """Registry should not contain duplicate doc_ids."""
        registry = yaml.safe_load(REGISTRY_PATH.read_text(encoding='utf-8'))

        doc_ids = [doc['doc_id'] for doc in registry.get('docs', []) if 'doc_id' in doc]
        duplicates = [doc_id for doc_id, count in Counter(doc_ids).items() if count > 1]

        assert len(duplicates) == 0, f"Duplicate doc_ids in registry: {duplicates}"

    def test_inventory_doc_ids_unique(self):
        """Inventory should not contain duplicate doc_ids."""
        doc_ids = []

        with open(INVENTORY_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                entry = json.loads(line.strip())
                if entry.get('doc_id') and entry.get('status') == 'registered':
                    doc_ids.append(entry['doc_id'])

        duplicates = [doc_id for doc_id, count in Counter(doc_ids).items() if count > 1]

        assert len(duplicates) == 0, f"Duplicate doc_ids in inventory: {duplicates}"


class TestDocIDCategorization:
    """Test doc_id categorization."""

    def test_no_unknown_categories(self):
        """Registry should not contain 'unknown' categories."""
        registry = yaml.safe_load(REGISTRY_PATH.read_text(encoding='utf-8'))

        unknown_count = 0
        for doc in registry.get('docs', []):
            if doc.get('category') == 'unknown':
                unknown_count += 1

        assert unknown_count == 0, f"Found {unknown_count} entries with 'unknown' category"

    def test_category_counts_accurate(self):
        """Registry metadata should match actual category counts."""
        registry = yaml.safe_load(REGISTRY_PATH.read_text(encoding='utf-8'))

        # Count actual occurrences
        actual_counts = Counter()
        for doc in registry.get('docs', []):
            category = doc.get('category', 'unknown')
            actual_counts[category] += 1

        # Compare with metadata
        mismatches = []
        for category, category_data in registry.get('categories', {}).items():
            if isinstance(category_data, dict):
                claimed_count = category_data.get('count', 0)
                actual_count = actual_counts.get(category, 0)

                if claimed_count != actual_count:
                    mismatches.append(
                        f"{category}: claimed {claimed_count}, actual {actual_count}"
                    )

        assert len(mismatches) == 0, f"Category count mismatches: {mismatches}"

    def test_total_docs_accurate(self):
        """Registry total_docs should match actual count."""
        registry = yaml.safe_load(REGISTRY_PATH.read_text(encoding='utf-8'))

        claimed_total = registry.get('metadata', {}).get('total_docs', 0)
        actual_total = len(registry.get('docs', []))

        assert claimed_total == actual_total, \
            f"Total docs mismatch: claimed {claimed_total}, actual {actual_total}"


class TestRegistrySync:
    """Test registry and inventory synchronization."""

    def test_sync_check_runs(self):
        """Sync check should execute successfully."""
        result = subprocess.run(
            [sys.executable, str(DOC_ID_DIR / "sync_registries.py"), "check"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )

        assert result.returncode == 0, f"Sync check failed: {result.stderr}"

    def test_sync_status_valid_json(self):
        """Sync check should output valid JSON."""
        result = subprocess.run(
            [sys.executable, str(DOC_ID_DIR / "sync_registries.py"), "check"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )

        try:
            status = json.loads(result.stdout)
            assert 'in_both' in status
            assert 'only_registry' in status
            assert 'only_inventory' in status
        except json.JSONDecodeError:
            pytest.fail(f"Sync check output is not valid JSON: {result.stdout}")

    def test_minimal_drift_between_sources(self):
        """Registry and inventory should be mostly synchronized."""
        result = subprocess.run(
            [sys.executable, str(DOC_ID_DIR / "sync_registries.py"), "check"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )

        status = json.loads(result.stdout)

        only_registry = len(status.get('only_registry', []))
        only_inventory = len(status.get('only_inventory', []))
        total = status.get('total_registry', 0) + status.get('total_inventory', 0)

        if total > 0:
            drift_percent = ((only_registry + only_inventory) / total) * 100

            # Allow up to 10% drift
            assert drift_percent < 10, \
                f"High drift detected: {drift_percent:.1f}% ({only_registry} + {only_inventory} out of {total})"


class TestDocIDScanner:
    """Test doc_id scanner functionality."""

    def test_scanner_exists(self):
        """Scanner script should exist."""
        scanner_path = DOC_ID_DIR / "doc_id_scanner.py"
        assert scanner_path.exists(), f"Scanner not found: {scanner_path}"

    def test_scanner_runs(self):
        """Scanner should execute successfully."""
        result = subprocess.run(
            [sys.executable, str(DOC_ID_DIR / "doc_id_scanner.py"), "stats"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )

        assert result.returncode == 0, f"Scanner failed: {result.stderr}"

    def test_scanner_stats_output(self):
        """Scanner stats should show coverage information."""
        result = subprocess.run(
            [sys.executable, str(DOC_ID_DIR / "doc_id_scanner.py"), "stats"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )

        output = result.stdout
        assert "Total eligible files:" in output
        assert "Files with doc_id:" in output
        assert "Coverage:" in output


class TestCategoryFixer:
    """Test category fix script."""

    def test_category_fixer_exists(self):
        """Category fixer script should exist."""
        fixer_path = DOC_ID_DIR / "fix_registry_categories.py"
        assert fixer_path.exists(), f"Category fixer not found: {fixer_path}"

    def test_category_fixer_dry_run(self):
        """Category fixer should support dry run."""
        result = subprocess.run(
            [sys.executable, str(DOC_ID_DIR / "fix_registry_categories.py"), "--dry-run"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )

        # Should succeed even if nothing to fix
        assert result.returncode == 0


class TestInvalidIDFixer:
    """Test invalid doc_id fixer."""

    def test_invalid_id_fixer_exists(self):
        """Invalid ID fixer script should exist."""
        fixer_path = DOC_ID_DIR / "fix_invalid_doc_ids.py"
        assert fixer_path.exists(), f"Invalid ID fixer not found: {fixer_path}"

    def test_invalid_id_fixer_dry_run(self):
        """Invalid ID fixer should support dry run."""
        fixer_path = DOC_ID_DIR / "fix_invalid_doc_ids.py"
        if not fixer_path.exists():
            pytest.skip("Invalid ID fixer not yet created")

        result = subprocess.run(
            [sys.executable, str(fixer_path), "--dry-run"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )

        assert result.returncode == 0


class TestDocIDCoverage:
    """Test doc_id coverage metrics."""

    def test_high_coverage(self):
        """Repository should have >90% doc_id coverage."""
        with open(INVENTORY_PATH, 'r', encoding='utf-8') as f:
            total = 0
            with_doc_id = 0

            for line in f:
                entry = json.loads(line.strip())
                total += 1
                if entry.get('doc_id') and entry.get('status') in ['registered', 'invalid']:
                    with_doc_id += 1

        if total > 0:
            coverage = (with_doc_id / total) * 100
            assert coverage >= 90, f"Low doc_id coverage: {coverage:.1f}%"

    def test_coverage_by_file_type(self):
        """Track coverage by file type."""
        by_type = {}

        with open(INVENTORY_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                entry = json.loads(line.strip())
                file_type = entry.get('file_type', 'unknown')

                if file_type not in by_type:
                    by_type[file_type] = {'total': 0, 'with_id': 0}

                by_type[file_type]['total'] += 1
                if entry.get('doc_id'):
                    by_type[file_type]['with_id'] += 1

        # Just track, don't fail
        print("\n📊 Coverage by file type:")
        for file_type, stats in sorted(by_type.items()):
            if stats['total'] > 0:
                coverage = (stats['with_id'] / stats['total']) * 100
                print(f"  {file_type:8s}: {stats['with_id']:4d}/{stats['total']:4d} ({coverage:5.1f}%)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
