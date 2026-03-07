#!/usr/bin/env python3
"""
E2E Pipeline Validation Suite
Validates the complete E2E process map pipeline from schema → index → docs.

Tests:
1. Schema integrity (no duplicates, valid phases, acyclic dependencies)
2. Index completeness (all steps indexed, workflows valid)
3. Documentation accuracy (all steps documented, links valid)
4. Cross-reference consistency (schema ↔ index ↔ docs)
5. Data quality (no orphans, no missing fields)

Usage:
    python pfa_validate_e2e_pipeline.py --schema unified.yaml --index master_index.json --docs-dir docs/e2e/ --report validation_report.json

DOC_ID: DOC-SCRIPT-TOOLS-PFA-VALIDATE-E2E-PIPELINE-955
"""

import json
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple, Set
from collections import defaultdict
import sys
import re

# Add parent directory to path for pfa_common import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from DOC-SCRIPT-TOOLS-PFA-COMMON-944__pfa_common import (
    load_yaml, save_yaml, load_json, save_json,
    print_success, print_error, print_warning, print_info
)

class E2EPipelineValidator:
    """Validates E2E pipeline integrity and data quality"""

    def __init__(self, schema_path: Path, index_path: Path, docs_dir: Path):
        self.schema_path = schema_path
        self.index_path = index_path
        self.docs_dir = docs_dir

        # Load data
        self.schema = self._load_yaml(schema_path)
        self.index = self._load_json(index_path)

        # Extract core data
        self.meta = self.schema.get('meta', {})
        self.steps = self.schema.get('steps', [])
        self.universal_phases = self.schema.get('universal_phases', [])

        # Validation results
        self.errors = []
        self.warnings = []
        self.info = []

        print(f"Loaded schema: {self.meta.get('schema_id', 'Unknown')}")
        print(f"  Steps: {len(self.steps)}")
        print(f"  Phases: {len(self.universal_phases)}")
        print(f"  Index types: {len(self.index)}")

    def _load_yaml(self, path: Path) -> Dict:
        """Load YAML file"""
        return load_yaml(path)

    def _load_json(self, path: Path) -> Dict:
        """Load JSON file"""
        return load_json(path)

    def _error(self, message: str):
        """Record error"""
        self.errors.append(message)
        print(f"  ❌ ERROR: {message}")

    def _warning(self, message: str):
        """Record warning"""
        self.warnings.append(message)
        print(f"  ⚠️  WARNING: {message}")

    def _info(self, message: str):
        """Record info"""
        self.info.append(message)
        print(f"  ℹ️  INFO: {message}")

    def _success(self, message: str):
        """Print success"""
        print(f"  ✅ {message}")

    # ============================================================================
    # SCHEMA VALIDATION
    # ============================================================================

    def validate_schema(self) -> bool:
        """Validate schema integrity"""
        print("\n=== Schema Validation ===\n")

        passed = True

        # Test 1: No duplicate step IDs
        passed &= self._validate_no_duplicate_step_ids()

        # Test 2: All steps have required fields
        passed &= self._validate_required_fields()

        # Test 3: All phases are valid
        passed &= self._validate_phase_references()

        # Test 4: Dependencies are valid
        passed &= self._validate_dependencies()

        # Test 5: Dependency graph is acyclic
        passed &= self._validate_acyclic_dependencies()

        return passed

    def _validate_no_duplicate_step_ids(self) -> bool:
        """Validate no duplicate step IDs"""
        step_ids = [s.get('step_id') for s in self.steps]
        duplicates = [sid for sid in step_ids if step_ids.count(sid) > 1]

        if duplicates:
            self._error(f"Duplicate step IDs found: {set(duplicates)}")
            return False

        self._success(f"No duplicate step IDs ({len(step_ids)} unique)")
        return True

    def _validate_required_fields(self) -> bool:
        """Validate all steps have required fields"""
        required = ['step_id', 'name', 'universal_phase', 'operation_kind', 'responsible_component']
        missing = []

        for step in self.steps:
            for field in required:
                if not step.get(field):
                    missing.append(f"{step.get('step_id', 'Unknown')}: missing '{field}'")

        if missing:
            for m in missing[:10]:  # Show first 10
                self._error(m)
            if len(missing) > 10:
                self._error(f"... and {len(missing) - 10} more missing fields")
            return False

        self._success(f"All {len(self.steps)} steps have required fields")
        return True

    def _validate_phase_references(self) -> bool:
        """Validate all phase references are valid"""
        invalid = []

        for step in self.steps:
            phase = step.get('universal_phase')
            if phase and phase not in self.universal_phases:
                invalid.append(f"{step.get('step_id')}: invalid phase '{phase}'")

        if invalid:
            for i in invalid[:10]:
                self._error(i)
            if len(invalid) > 10:
                self._error(f"... and {len(invalid) - 10} more invalid phases")
            return False

        self._success(f"All phase references valid (9 phases)")
        return True

    def _validate_dependencies(self) -> bool:
        """Validate all dependency references exist"""
        step_ids = {s.get('step_id') for s in self.steps}
        invalid = []

        for step in self.steps:
            depends_on = step.get('depends_on', [])
            if isinstance(depends_on, str):
                depends_on = [depends_on]

            for dep in depends_on:
                if dep and dep not in step_ids:
                    invalid.append(f"{step.get('step_id')} → {dep}: dependency not found")

        if invalid:
            for i in invalid[:10]:
                self._warning(i)
            if len(invalid) > 10:
                self._warning(f"... and {len(invalid) - 10} more invalid dependencies")
            return False

        self._success("All dependency references valid")
        return True

    def _validate_acyclic_dependencies(self) -> bool:
        """Validate dependency graph is acyclic"""
        # Build adjacency list
        graph = defaultdict(list)
        for step in self.steps:
            step_id = step.get('step_id')
            depends_on = step.get('depends_on', [])
            if isinstance(depends_on, str):
                depends_on = [depends_on]
            graph[step_id] = [d for d in depends_on if d]

        # Detect cycles using DFS
        visited = set()
        rec_stack = set()

        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for step in self.steps:
            step_id = step.get('step_id')
            if step_id not in visited:
                if has_cycle(step_id):
                    self._error("Dependency graph contains cycles")
                    return False

        self._success("Dependency graph is acyclic")
        return True

    # ============================================================================
    # INDEX VALIDATION
    # ============================================================================

    def validate_index(self) -> bool:
        """Validate master index completeness"""
        print("\n=== Index Validation ===\n")

        passed = True

        # Test 1: All steps are indexed
        passed &= self._validate_all_steps_indexed()

        # Test 2: Index types are complete
        passed &= self._validate_index_types()

        # Test 3: Workflows are valid
        passed &= self._validate_workflows()

        # Test 4: No orphaned entries
        passed &= self._validate_no_orphans()

        return passed

    def _validate_all_steps_indexed(self) -> bool:
        """Validate all steps appear in at least one index"""
        step_ids = {s.get('step_id') for s in self.steps}

        # Collect all indexed step IDs
        indexed_ids = set()
        # Handle nested indices structure
        indices = self.index.get('indices', self.index)
        for index_type, index_data in indices.items():
            if isinstance(index_data, dict):
                for key, values in index_data.items():
                    if isinstance(values, list):
                        indexed_ids.update(values)
                    elif isinstance(values, dict) and 'step_id' in values:
                        indexed_ids.add(values['step_id'])

        missing = step_ids - indexed_ids

        if missing:
            self._error(f"{len(missing)} steps not indexed: {list(missing)[:5]}")
            return False

        self._success(f"All {len(step_ids)} steps indexed")
        return True

    def _validate_index_types(self) -> bool:
        """Validate expected index types exist"""
        expected = ['by_phase', 'by_component', 'by_operation', 'by_workflow', 'dependencies']
        # Handle nested indices structure
        indices = self.index.get('indices', self.index)
        missing = [e for e in expected if e not in indices]

        if missing:
            self._error(f"Missing index types: {missing}")
            return False

        self._success(f"All {len(expected)} expected index types present")
        return True

    def _validate_workflows(self) -> bool:
        """Validate workflow definitions"""
        indices = self.index.get('indices', self.index)
        workflows = indices.get('by_workflow', {})

        if not workflows:
            self._warning("No workflows defined")
            return False

        step_ids = {s.get('step_id') for s in self.steps}
        invalid = []

        for workflow_name, step_list in workflows.items():
            for step_id in step_list:
                if step_id not in step_ids:
                    invalid.append(f"Workflow '{workflow_name}' references invalid step: {step_id}")

        if invalid:
            for i in invalid[:10]:
                self._error(i)
            return False

        self._success(f"{len(workflows)} workflows validated")
        return True

    def _validate_no_orphans(self) -> bool:
        """Validate no orphaned index entries"""
        step_ids = {s.get('step_id') for s in self.steps}
        orphans = []

        # Handle nested indices structure
        indices = self.index.get('indices', self.index)
        for index_type, index_data in indices.items():
            if index_type in ['by_phase', 'by_component', 'by_operation', 'by_workflow']:
                if isinstance(index_data, dict):
                    for key, values in index_data.items():
                        if isinstance(values, list):
                            for val in values:
                                if val not in step_ids:
                                    orphans.append(f"Index '{index_type}' → '{key}' contains orphan: {val}")

        if orphans:
            for o in orphans[:10]:
                self._warning(o)
            if len(orphans) > 10:
                self._warning(f"... and {len(orphans) - 10} more orphans")
            return False

        self._success("No orphaned index entries")
        return True

    # ============================================================================
    # DOCUMENTATION VALIDATION
    # ============================================================================

    def validate_documentation(self) -> bool:
        """Validate generated documentation"""
        print("\n=== Documentation Validation ===\n")

        passed = True

        # Test 1: Required files exist
        passed &= self._validate_required_files()

        # Test 2: All phases documented
        passed &= self._validate_phase_docs()

        # Test 3: Markdown links are valid
        passed &= self._validate_markdown_links()

        # Test 4: HTML renders correctly
        passed &= self._validate_html()

        return passed

    def _validate_required_files(self) -> bool:
        """Validate required documentation files exist"""
        required = [
            'README.md',
            'index.html',
            'components.md',
            'operations.md',
        ]

        missing = []
        for req in required:
            if not (self.docs_dir / req).exists():
                missing.append(req)

        if missing:
            self._error(f"Missing documentation files: {missing}")
            return False

        self._success(f"All {len(required)} required files present")
        return True

    def _validate_phase_docs(self) -> bool:
        """Validate all phases have documentation"""
        phases_dir = self.docs_dir / 'phases'

        if not phases_dir.exists():
            self._error("phases/ directory not found")
            return False

        missing = []
        for phase_id in self.universal_phases:
            phase_file = phases_dir / f"{phase_id}.md"
            if not phase_file.exists():
                missing.append(phase_id)

        if missing:
            self._error(f"Missing phase documentation: {missing}")
            return False

        self._success(f"All {len(self.universal_phases)} phases documented")
        return True

    def _validate_markdown_links(self) -> bool:
        """Validate markdown internal links"""
        readme_path = self.docs_dir / 'README.md'

        if not readme_path.exists():
            self._error("README.md not found")
            return False

        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract markdown links [text](path)
        link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
        links = re.findall(link_pattern, content)

        broken = []
        for text, path in links:
            # Skip external links
            if path.startswith('http'):
                continue

            # Resolve relative path
            target = self.docs_dir / path
            if not target.exists():
                broken.append(f"{text} → {path}")

        if broken:
            for b in broken[:10]:
                self._warning(f"Broken link: {b}")
            if len(broken) > 10:
                self._warning(f"... and {len(broken) - 10} more broken links")
            return False

        self._success(f"{len(links)} internal links validated")
        return True

    def _validate_html(self) -> bool:
        """Validate HTML file structure"""
        html_path = self.docs_dir / 'index.html'

        if not html_path.exists():
            self._error("index.html not found")
            return False

        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for required elements
        required = ['<div id="app">', 'Vue.js', 'steps:', 'filterSteps']
        missing = [r for r in required if r not in content]

        if missing:
            self._error(f"HTML missing required elements: {missing}")
            return False

        self._success("HTML structure valid")
        return True

    # ============================================================================
    # CROSS-REFERENCE VALIDATION
    # ============================================================================

    def validate_cross_references(self) -> bool:
        """Validate consistency across schema, index, and docs"""
        print("\n=== Cross-Reference Validation ===\n")

        passed = True

        # Test 1: Schema ↔ Index consistency
        passed &= self._validate_schema_index_consistency()

        # Test 2: Index ↔ Docs consistency
        passed &= self._validate_index_docs_consistency()

        return passed

    def _validate_schema_index_consistency(self) -> bool:
        """Validate schema and index have same steps"""
        schema_ids = {s.get('step_id') for s in self.steps}

        index_ids = set()
        indices = self.index.get('indices', self.index)
        by_phase = indices.get('by_phase', {})
        for step_list in by_phase.values():
            if isinstance(step_list, list):
                index_ids.update(step_list)

        missing_in_index = schema_ids - index_ids
        missing_in_schema = index_ids - schema_ids

        if missing_in_index:
            self._error(f"{len(missing_in_index)} steps in schema but not in index: {list(missing_in_index)[:5]}")
            return False

        if missing_in_schema:
            self._error(f"{len(missing_in_schema)} steps in index but not in schema: {list(missing_in_schema)[:5]}")
            return False

        self._success("Schema ↔ Index consistency validated")
        return True

    def _validate_index_docs_consistency(self) -> bool:
        """Validate index and docs reference same components"""
        # This is a simplified check - could be expanded
        components_file = self.docs_dir / 'components.md'

        if not components_file.exists():
            self._warning("components.md not found, skipping consistency check")
            return False

        with open(components_file, 'r', encoding='utf-8') as f:
            content = f.read()

        indices = self.index.get('indices', self.index)
        index_components = set(indices.get('by_component', {}).keys())

        # Count how many components are mentioned in docs
        mentioned = sum(1 for comp in index_components if comp in content)

        coverage = mentioned / len(index_components) if index_components else 0

        if coverage < 0.8:
            self._warning(f"Only {coverage:.1%} of components documented")
            return False

        self._success(f"Index ↔ Docs consistency validated ({coverage:.1%} coverage)")
        return True

    # ============================================================================
    # MAIN VALIDATION RUNNER
    # ============================================================================

    def run_all_validations(self) -> Tuple[bool, Dict]:
        """Run all validation tests"""
        print("=" * 80)
        print("E2E PIPELINE VALIDATION SUITE")
        print("=" * 80)

        schema_pass = self.validate_schema()
        index_pass = self.validate_index()
        docs_pass = self.validate_documentation()
        cross_ref_pass = self.validate_cross_references()

        all_pass = schema_pass and index_pass and docs_pass and cross_ref_pass

        # Generate report
        report = {
            'timestamp': '2025-12-18',
            'schema_path': str(self.schema_path),
            'index_path': str(self.index_path),
            'docs_dir': str(self.docs_dir),
            'results': {
                'schema_validation': schema_pass,
                'index_validation': index_pass,
                'documentation_validation': docs_pass,
                'cross_reference_validation': cross_ref_pass,
                'overall': all_pass
            },
            'statistics': {
                'total_steps': len(self.steps),
                'total_phases': len(self.universal_phases),
                'total_components': len(self.index.get('by_component', {})),
                'total_workflows': len(self.index.get('by_workflow', {}))
            },
            'errors': self.errors,
            'warnings': self.warnings,
            'info': self.info
        }

        return all_pass, report

    def print_summary(self, all_pass: bool):
        """Print validation summary"""
        print("\n" + "=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        print(f"\nErrors: {len(self.errors)}")
        print(f"Warnings: {len(self.warnings)}")
        print(f"Info: {len(self.info)}")
        print()

        if all_pass:
            print("✅ ALL VALIDATIONS PASSED")
        else:
            print("❌ SOME VALIDATIONS FAILED")
            print("\nReview errors above and fix issues before proceeding.")

        print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description='Validate E2E pipeline integrity')
    parser.add_argument('--schema', type=Path, required=True, help='Path to unified schema YAML')
    parser.add_argument('--index', type=Path, required=True, help='Path to master index JSON')
    parser.add_argument('--docs-dir', type=Path, required=True, help='Path to documentation directory')
    parser.add_argument('--report', type=Path, help='Output path for validation report JSON')

    args = parser.parse_args()

    # Validate inputs
    if not args.schema.exists():
        print(f"Error: Schema file not found: {args.schema}")
        sys.exit(1)

    if not args.index.exists():
        print(f"Error: Index file not found: {args.index}")
        sys.exit(1)

    if not args.docs_dir.exists():
        print(f"Error: Documentation directory not found: {args.docs_dir}")
        sys.exit(1)

    # Run validation
    validator = E2EPipelineValidator(args.schema, args.index, args.docs_dir)
    all_pass, report = validator.run_all_validations()
    validator.print_summary(all_pass)

    # Save report
    if args.report:
        save_json(report, Path(args.report))
        print(f"\nValidation report saved: {args.report}")

    sys.exit(0 if all_pass else 1)


if __name__ == '__main__':
    main()
