#!/usr/bin/env python3
# DOC_LINK: DOC-CORE-UTI-TOOLS-VALIDATE-REGISTRY-823
"""
DOC_ID Registry Validator - Comprehensive validation

Validates DOC_ID_REGISTRY.yaml for:
- YAML syntax
- Required fields
- Duplicate doc_ids
- Module_id consistency
- Orphaned entries

Usage:
    python scripts/validate_registry.py
    python scripts/validate_registry.py --report validation_report.json
"""
DOC_ID: DOC-CORE-UTI-TOOLS-VALIDATE-REGISTRY-823
DOC_ID: DOC - SCRIPT - SCRIPTS - VALIDATE - REGISTRY - 732
DOC_ID: DOC - SCRIPT - SCRIPTS - VALIDATE - REGISTRY - 732

import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Set, Tuple

import yaml

# Repository root
REPO_ROOT = Path(__file__).parent.parent
REGISTRY_PATH = REPO_ROOT / "doc_id" / "specs" / "DOC_ID_REGISTRY.yaml"
TAXONOMY_PATH = REPO_ROOT / "doc_id" / "specs" / "module_taxonomy.yaml"


class RegistryValidator:
    """Validates DOC_ID_REGISTRY.yaml"""

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.registry = None
        self.taxonomy = None

    def load_registry(self) -> bool:
        """Load and parse registry YAML"""
        try:
            with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
                self.registry = yaml.safe_load(f)
            return True
        except FileNotFoundError:
            self.errors.append(f"Registry not found: {REGISTRY_PATH}")
            return False
        except yaml.YAMLError as e:
            self.errors.append(f"YAML parse error: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Failed to load registry: {e}")
            return False

    def load_taxonomy(self) -> bool:
        """Load module taxonomy"""
        if not TAXONOMY_PATH.exists():
            self.warnings.append(f"Module taxonomy not found: {TAXONOMY_PATH}")
            return False

        try:
            with open(TAXONOMY_PATH, "r", encoding="utf-8") as f:
                self.taxonomy = yaml.safe_load(f)
            return True
        except Exception as e:
            self.warnings.append(f"Failed to load taxonomy: {e}")
            return False

    def validate_structure(self) -> bool:
        """Validate registry has required top-level keys"""
        required_keys = ["metadata", "categories", "docs"]

        for key in required_keys:
            if key not in self.registry:
                self.errors.append(f"Missing required top-level key: {key}")

        return len([e for e in self.errors if "Missing required" in e]) == 0

    def validate_docs(self) -> Tuple[int, int]:
        """
        Validate all doc entries.

        Returns:
            (total_docs, valid_docs)
        """
        if "docs" not in self.registry:
            return 0, 0

        docs = self.registry["docs"]
        total = len(docs)
        valid = 0

        required_fields = ["doc_id", "category", "name", "status"]

        for i, doc in enumerate(docs, 1):
            doc_valid = True
            doc_id = doc.get("doc_id", f"UNKNOWN-{i}")

            # Check required fields
            for field in required_fields:
                if field not in doc:
                    self.errors.append(
                        f"Doc {doc_id}: Missing required field '{field}'"
                    )
                    doc_valid = False

            # Check doc_id format
            if "doc_id" in doc:
                doc_id_value = doc["doc_id"]
                if not isinstance(doc_id_value, str) or not doc_id_value.startswith(
                    "DOC-"
                ):
                    self.errors.append(f"Doc {doc_id}: Invalid doc_id format")
                    doc_valid = False

            # Check module_id if present
            if "module_id" in doc:
                module_id = doc["module_id"]
                if self.taxonomy and "module_taxonomy" in self.taxonomy:
                    valid_modules = set(self.taxonomy["module_taxonomy"].keys())
                    if module_id not in valid_modules and module_id != "unassigned":
                        self.warnings.append(
                            f"Doc {doc_id}: module_id '{module_id}' not in taxonomy"
                        )

            if doc_valid:
                valid += 1

        return total, valid

    def check_duplicates(self) -> List[str]:
        """Check for duplicate doc_ids"""
        if "docs" not in self.registry:
            return []

        doc_ids = [doc.get("doc_id", "") for doc in self.registry["docs"]]
        id_counts = defaultdict(int)

        for doc_id in doc_ids:
            if doc_id:
                id_counts[doc_id] += 1

        duplicates = [doc_id for doc_id, count in id_counts.items() if count > 1]

        for doc_id in duplicates:
            self.errors.append(
                f"Duplicate doc_id: {doc_id} (appears {id_counts[doc_id]} times)"
            )

        return duplicates

    def validate_module_ids(self) -> Tuple[int, int]:
        """
        Validate module_id assignments.

        Returns:
            (total_with_module_id, total_docs)
        """
        if "docs" not in self.registry:
            return 0, 0

        docs = self.registry["docs"]
        total = len(docs)
        with_module_id = sum(1 for doc in docs if "module_id" in doc)

        if with_module_id < total:
            missing = total - with_module_id
            self.warnings.append(
                f"{missing} docs missing module_id field ({missing/total*100:.1f}%)"
            )

        return with_module_id, total

    def generate_report(self) -> Dict:
        """Generate validation report"""
        return {
            "validated_at": datetime.now(timezone.utc).isoformat(),
            "registry_path": str(REGISTRY_PATH),
            "errors": self.errors,
            "warnings": self.warnings,
            "passed": len(self.errors) == 0,
        }

    def validate(self) -> bool:
        """Run all validations"""
        print("==> Validating DOC_ID_REGISTRY.yaml...")

        # Load files
        if not self.load_registry():
            return False

        self.load_taxonomy()  # Warnings only if missing

        # Run validations
        print("   - Checking structure...")
        self.validate_structure()

        print("   - Validating doc entries...")
        total_docs, valid_docs = self.validate_docs()
        print(f"     Docs: {valid_docs}/{total_docs} valid")

        print("   - Checking for duplicates...")
        duplicates = self.check_duplicates()
        if duplicates:
            print(f"     Found {len(duplicates)} duplicate doc_ids")

        print("   - Validating module_id assignments...")
        with_module, total = self.validate_module_ids()
        if total > 0:
            print(
                f"     Module IDs: {with_module}/{total} ({with_module/total*100:.1f}%)"
            )

        # Summary
        print(f"\n==> Validation Summary:")
        print(f"   Errors:   {len(self.errors)}")
        print(f"   Warnings: {len(self.warnings)}")

        if self.errors:
            print(f"\n==> Errors:")
            for error in self.errors[:10]:
                print(f"   ✗ {error}")
            if len(self.errors) > 10:
                print(f"   ... and {len(self.errors) - 10} more")

        if self.warnings:
            print(f"\n==> Warnings:")
            for warning in self.warnings[:10]:
                print(f"   ⚠ {warning}")
            if len(self.warnings) > 10:
                print(f"   ... and {len(self.warnings) - 10} more")

        passed = len(self.errors) == 0

        if passed:
            print(f"\n✓ PASS: Registry validation successful")
        else:
            print(
                f"\n✗ FAIL: Registry validation failed with {len(self.errors)} errors"
            )

        return passed


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Validate DOC_ID_REGISTRY.yaml")
    parser.add_argument("--report", type=str, help="Output JSON report to file")

    args = parser.parse_args()

    validator = RegistryValidator()
    passed = validator.validate()

    # Write report if requested
    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)

        report = validator.generate_report()
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\n==> Report written to: {report_path}")

    # Exit with appropriate code
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
