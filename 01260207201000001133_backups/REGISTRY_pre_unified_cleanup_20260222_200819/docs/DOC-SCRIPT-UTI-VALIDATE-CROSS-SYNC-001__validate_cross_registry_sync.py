#!/usr/bin/env python3
# DOC_LINK: DOC-SCRIPT-UTI-VALIDATE-CROSS-SYNC-001
"""
Cross-Registry Synchronization Validator

Validates consistency across three registries:
1. SUB_GLOSSARY/.glossary-metadata.yaml (term registry)
2. SUB_DOC_ID/5_REGISTRY_DATA/DOC_ID_REGISTRY.yaml (doc_id registry)
3. PROCESS_STEP_LIB/indices/master_index.json (process index)

Checks:
- Doc_id coverage for glossary files
- Glossary term usage in process schemas
- Implementation files have doc_ids
- Category definitions match across systems

Usage:
    python validate_cross_registry_sync.py --report
    python validate_cross_registry_sync.py --report --output custom_report.json
"""
# DOC_ID: DOC-SCRIPT-UTI-VALIDATE-CROSS-SYNC-001

import json
import yaml
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class SyncReport:
    """Cross-registry sync validation report."""
    timestamp: str
    glossary_files_with_doc_ids: int = 0
    glossary_files_without_doc_ids: int = 0
    schema_terms_in_glossary: int = 0
    schema_terms_not_in_glossary: int = 0
    impl_files_with_doc_ids: int = 0
    impl_files_without_doc_ids: int = 0
    category_mismatches: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def doc_id_coverage(self) -> float:
        """Calculate doc_id coverage percentage."""
        total = self.glossary_files_with_doc_ids + self.glossary_files_without_doc_ids
        if total == 0:
            return 100.0
        return (self.glossary_files_with_doc_ids / total) * 100

    @property
    def term_coverage(self) -> float:
        """Calculate term coverage percentage."""
        total = self.schema_terms_in_glossary + self.schema_terms_not_in_glossary
        if total == 0:
            return 100.0
        return (self.schema_terms_in_glossary / total) * 100

    @property
    def impl_coverage(self) -> float:
        """Calculate implementation file coverage."""
        total = self.impl_files_with_doc_ids + self.impl_files_without_doc_ids
        if total == 0:
            return 100.0
        return (self.impl_files_with_doc_ids / total) * 100


class CrossRegistryValidator:
    """Validate synchronization across registries."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.glossary_root = repo_root / 'SUB_GLOSSARY'
        self.doc_id_root = repo_root / 'SUB_DOC_ID'
        self.process_root = repo_root / 'PROCESS_STEP_LIB'

        self.glossary_terms: Dict[str, Dict] = {}
        self.doc_id_registry: Dict = {}
        self.process_index: Dict = {}

        self.report = SyncReport(timestamp=datetime.now().isoformat())

    def load_registries(self):
        """Load all three registries."""
        print("📚 Loading registries...")

        # Load glossary metadata
        glossary_meta = self.glossary_root / '.glossary-metadata.yaml'
        if glossary_meta.exists():
            try:
                with open(glossary_meta, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {}
                    self.glossary_terms = data.get('terms', {})
                print(f"   ✓ Glossary: {len(self.glossary_terms)} terms")
            except Exception as e:
                self.report.errors.append(f"Failed to load glossary metadata: {e}")
                print(f"   ❌ Glossary load failed: {e}")
        else:
            print(f"   ⚠️  Glossary metadata not found")

        # Load doc_id registry
        doc_id_reg = self.doc_id_root / '5_REGISTRY_DATA' / 'DOC_ID_REGISTRY.yaml'
        if doc_id_reg.exists():
            try:
                with open(doc_id_reg, 'r', encoding='utf-8') as f:
                    self.doc_id_registry = yaml.safe_load(f) or {}
                doc_count = len(self.doc_id_registry.get('docs', []))
                print(f"   ✓ Doc ID: {doc_count} docs")
            except Exception as e:
                self.report.errors.append(f"Failed to load doc_id registry: {e}")
                print(f"   ❌ Doc ID load failed: {e}")
        else:
            print(f"   ⚠️  Doc ID registry not found")

        # Load process index
        process_idx = self.process_root / 'indices' / 'master_index.json'
        if process_idx.exists():
            try:
                with open(process_idx, 'r', encoding='utf-8') as f:
                    self.process_index = json.load(f)
                step_count = self.process_index.get('total_steps', 0)
                print(f"   ✓ Process: {step_count} steps")
            except Exception as e:
                self.report.errors.append(f"Failed to load process index: {e}")
                print(f"   ❌ Process load failed: {e}")
        else:
            print(f"   ⚠️  Process index not found")

    def validate_glossary_doc_ids(self):
        """Check doc_id coverage for glossary files."""
        print("\n🔍 Validating glossary file doc_ids...")

        # Find all glossary files
        glossary_files = []
        for pattern in ['*.yaml', '*.yml', '*.md', '*.py']:
            glossary_files.extend(self.glossary_root.rglob(pattern))

        # Exclude certain files
        exclude_patterns = ['.glossary-metadata.yaml', '__pycache__', 'config/', '.git/']
        glossary_files = [f for f in glossary_files
                         if not any(p in str(f) for p in exclude_patterns)]

        for file_path in glossary_files:
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                if re.search(r'DOC-[A-Z]+-[A-Z0-9-]+-[0-9]+', content):
                    self.report.glossary_files_with_doc_ids += 1
                else:
                    self.report.glossary_files_without_doc_ids += 1
                    rel_path = file_path.relative_to(self.repo_root)
                    self.report.warnings.append(f"Missing doc_id: {rel_path}")
            except Exception as e:
                self.report.errors.append(f"Could not read {file_path}: {e}")

        coverage = self.report.doc_id_coverage
        print(f"   📊 Doc_id coverage: {coverage:.1f}%")
        print(f"   ✓ With doc_ids: {self.report.glossary_files_with_doc_ids}")
        print(f"   ⚠️  Without doc_ids: {self.report.glossary_files_without_doc_ids}")

    def validate_schema_term_usage(self):
        """Check if terms used in schemas exist in glossary."""
        print("\n🔍 Validating schema term usage...")

        # Get all terms referenced in process steps
        schema_terms = set()

        # Scan unified schema for term references
        unified_schema = self.process_root / 'schemas' / 'unified' / 'PFA_E2E_UNIFIED_PROCESS_STEPS_SCHEMA.yaml'
        if unified_schema.exists():
            try:
                with open(unified_schema, 'r', encoding='utf-8') as f:
                    schema_data = yaml.safe_load(f) or {}
                    steps = schema_data.get('steps', [])

                    for step in steps:
                        # Extract terms from operation_kind
                        op_kind = step.get('operation_kind', '')
                        if 'term' in op_kind.lower():
                            schema_terms.add(op_kind)

                        # Extract from description
                        desc = step.get('description', '')
                        if 'TERM-' in desc:
                            # Extract TERM-XXX-NNN references
                            term_refs = re.findall(r'TERM-[A-Z]+-[0-9]+', desc)
                            schema_terms.update(term_refs)
            except Exception as e:
                self.report.errors.append(f"Failed to scan unified schema: {e}")

        # Check against glossary
        glossary_term_names = {t.get('name', '').lower() for t in self.glossary_terms.values()}

        for term in schema_terms:
            if term.lower() in glossary_term_names or term in self.glossary_terms:
                self.report.schema_terms_in_glossary += 1
            else:
                self.report.schema_terms_not_in_glossary += 1
                self.report.warnings.append(f"Schema term not in glossary: {term}")

        if schema_terms:
            coverage = self.report.term_coverage
            print(f"   📊 Term coverage: {coverage:.1f}%")
            print(f"   ✓ In glossary: {self.report.schema_terms_in_glossary}")
            print(f"   ⚠️  Not in glossary: {self.report.schema_terms_not_in_glossary}")
        else:
            print("   ℹ️  No term references found in schemas")

    def validate_implementation_files(self):
        """Check if implementation files have doc_ids."""
        print("\n🔍 Validating implementation file doc_ids...")

        # Get implementation files from process index
        impl_files = set()

        if 'by_phase' in self.process_index:
            for phase_steps in self.process_index['by_phase'].values():
                for step in phase_steps:
                    files = step.get('implementation_files', [])
                    for file_info in files:
                        if isinstance(file_info, dict):
                            file_path = file_info.get('file', '')
                        else:
                            file_path = str(file_info)

                        if file_path:
                            impl_files.add(file_path)

        # Check doc_id coverage
        for file_path_str in impl_files:
            file_path = self.repo_root / file_path_str

            if not file_path.exists():
                continue

            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                if re.search(r'DOC-[A-Z]+-[A-Z0-9-]+-[0-9]+', content):
                    self.report.impl_files_with_doc_ids += 1
                else:
                    self.report.impl_files_without_doc_ids += 1
                    self.report.warnings.append(f"Implementation file missing doc_id: {file_path_str}")
            except Exception as e:
                self.report.errors.append(f"Could not read {file_path_str}: {e}")

        if impl_files:
            coverage = self.report.impl_coverage
            print(f"   📊 Implementation coverage: {coverage:.1f}%")
            print(f"   ✓ With doc_ids: {self.report.impl_files_with_doc_ids}")
            print(f"   ⚠️  Without doc_ids: {self.report.impl_files_without_doc_ids}")
        else:
            print("   ℹ️  No implementation files tracked")

    def validate_category_consistency(self):
        """Check if categories match across systems."""
        print("\n🔍 Validating category consistency...")

        # Get doc_id categories
        doc_id_categories = set(self.doc_id_registry.get('categories', {}).keys())

        # Get glossary categories
        glossary_categories = set()
        for term_data in self.glossary_terms.values():
            cat = term_data.get('category', '')
            if cat:
                glossary_categories.add(cat.lower())

        # Check for mismatches (informational only)
        print(f"   📋 Doc_id categories: {len(doc_id_categories)}")
        print(f"   📋 Glossary categories: {len(glossary_categories)}")

        # Categories unique to each system
        only_in_doc_id = doc_id_categories - glossary_categories
        only_in_glossary = glossary_categories - doc_id_categories

        if only_in_doc_id:
            print(f"   ℹ️  Only in doc_id: {', '.join(only_in_doc_id)}")
        if only_in_glossary:
            print(f"   ℹ️  Only in glossary: {', '.join(only_in_glossary)}")

    def generate_report(self) -> Dict:
        """Generate validation report."""
        return {
            'timestamp': self.report.timestamp,
            'doc_id_coverage': {
                'percentage': round(self.report.doc_id_coverage, 2),
                'files_with': self.report.glossary_files_with_doc_ids,
                'files_without': self.report.glossary_files_without_doc_ids
            },
            'term_coverage': {
                'percentage': round(self.report.term_coverage, 2),
                'terms_in_glossary': self.report.schema_terms_in_glossary,
                'terms_not_in_glossary': self.report.schema_terms_not_in_glossary
            },
            'implementation_coverage': {
                'percentage': round(self.report.impl_coverage, 2),
                'files_with': self.report.impl_files_with_doc_ids,
                'files_without': self.report.impl_files_without_doc_ids
            },
            'warnings': self.report.warnings[:20],  # Limit to first 20
            'warning_count': len(self.report.warnings),
            'errors': self.report.errors,
            'status': self._determine_status()
        }

    def _determine_status(self) -> str:
        """Determine overall status."""
        if self.report.errors:
            return 'ERROR'
        elif self.report.doc_id_coverage < 70:
            return 'FAIL'
        elif self.report.doc_id_coverage < 85:
            return 'WARN'
        else:
            return 'PASS'

    def save_report(self, output_path: Path):
        """Save report to JSON."""
        report_data = self.generate_report()

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)

        print(f"\n✅ Report saved: {output_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Validate cross-registry synchronization")
    parser.add_argument('--report', action='store_true', help='Generate sync report')
    parser.add_argument('--output', type=str, default='logs/cross_sync_report.json',
                       help='Output report path (default: logs/cross_sync_report.json)')

    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent
    validator = CrossRegistryValidator(repo_root)

    print("="*70)
    print("  CROSS-REGISTRY SYNCHRONIZATION VALIDATOR")
    print("="*70)

    validator.load_registries()
    validator.validate_glossary_doc_ids()
    validator.validate_schema_term_usage()
    validator.validate_implementation_files()
    validator.validate_category_consistency()

    # Save report
    output_path = repo_root / args.output
    validator.save_report(output_path)

    # Print summary
    report = validator.generate_report()
    print("\n" + "="*70)
    print("  SUMMARY")
    print("="*70)
    print(f"  Doc_id Coverage:     {report['doc_id_coverage']['percentage']}%")
    print(f"  Term Coverage:       {report['term_coverage']['percentage']}%")
    print(f"  Impl Coverage:       {report['implementation_coverage']['percentage']}%")
    print(f"  Warnings:            {report['warning_count']}")
    print(f"  Errors:              {len(report['errors'])}")
    print(f"  Status:              {report['status']}")
    print("="*70)

    # Exit code based on status
    if report['status'] == 'ERROR':
        return 2
    elif report['status'] == 'FAIL':
        return 1
    else:
        return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
