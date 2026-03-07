#!/usr/bin/env python3
# DOC_LINK: DOC-SCRIPT-TOOLS-PFA-ANALYZE-COVERAGE-940
"""
Coverage Analyzer for E2E Unified Process Steps Schema
Analyzes file attachment coverage and implementation references
"""
DOC_ID: DOC-SCRIPT-TOOLS-PFA-ANALYZE-COVERAGE-940

import yaml
import json
import argparse
from pathlib import Path
from typing import Dict, List, Set, Any
from collections import defaultdict

class CoverageAnalyzer:
    """Analyzes coverage of file attachments and implementation references"""

    def __init__(self, schema_path: Path):
        self.schema_path = schema_path
        self.schema_data = None
        self.steps = []

    def load_schema(self):
        """Load unified schema"""
        with open(self.schema_path, 'r', encoding='utf-8') as f:
            self.schema_data = yaml.safe_load(f)
        self.steps = self.schema_data.get('steps', [])

    def analyze_file_coverage(self) -> Dict[str, Any]:
        """Analyze which steps have file attachments"""
        coverage = {
            'total_steps': len(self.steps),
            'steps_with_files': 0,
            'steps_without_files': 0,
            'steps_with_impl': 0,
            'steps_without_impl': 0,
            'file_type_distribution': defaultdict(int),
            'missing_files': [],
            'missing_impl': [],
            'coverage_by_phase': defaultdict(lambda: {'total': 0, 'with_files': 0, 'with_impl': 0}),
            'coverage_by_source': defaultdict(lambda: {'total': 0, 'with_files': 0, 'with_impl': 0})
        }

        for step in self.steps:
            step_id = step.get('step_id', 'UNKNOWN')
            universal_phase = step.get('universal_phase', 'UNKNOWN')
            source_schema = step.get('source_schema', 'UNKNOWN')

            # Track by phase and source
            coverage['coverage_by_phase'][universal_phase]['total'] += 1
            coverage['coverage_by_source'][source_schema]['total'] += 1

            # Check for file attachments
            has_files = False
            files = step.get('files', [])
            if files and len(files) > 0:
                has_files = True
                coverage['steps_with_files'] += 1
                coverage['coverage_by_phase'][universal_phase]['with_files'] += 1
                coverage['coverage_by_source'][source_schema]['with_files'] += 1

                # Track file types
                for file_path in files:
                    ext = Path(file_path).suffix or 'no_extension'
                    coverage['file_type_distribution'][ext] += 1
            else:
                coverage['steps_without_files'] += 1
                coverage['missing_files'].append({
                    'step_id': step_id,
                    'name': step.get('name', ''),
                    'phase': universal_phase,
                    'source': source_schema
                })

            # Check for implementation references
            has_impl = False
            responsible_component = step.get('responsible_component', '')
            if responsible_component and responsible_component != 'TBD':
                has_impl = True
                coverage['steps_with_impl'] += 1
                coverage['coverage_by_phase'][universal_phase]['with_impl'] += 1
                coverage['coverage_by_source'][source_schema]['with_impl'] += 1
            else:
                coverage['steps_without_impl'] += 1
                coverage['missing_impl'].append({
                    'step_id': step_id,
                    'name': step.get('name', ''),
                    'phase': universal_phase,
                    'source': source_schema
                })

        # Calculate percentages
        if coverage['total_steps'] > 0:
            coverage['file_coverage_percent'] = round(
                (coverage['steps_with_files'] / coverage['total_steps']) * 100, 2
            )
            coverage['impl_coverage_percent'] = round(
                (coverage['steps_with_impl'] / coverage['total_steps']) * 100, 2
            )

        return coverage

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive coverage report"""
        self.load_schema()

        report = {
            'schema_path': str(self.schema_path),
            'analysis_date': '2025-12-18',
            'schema_version': self.schema_data.get('meta', {}).get('version', 'UNKNOWN'),
            'coverage': self.analyze_file_coverage()
        }

        return report

    def print_summary(self, report: Dict[str, Any]):
        """Print human-readable summary"""
        cov = report['coverage']

        print(f"\n{'='*80}")
        print(f"E2E UNIFIED SCHEMA COVERAGE ANALYSIS")
        print(f"{'='*80}")
        print(f"Schema: {report['schema_path']}")
        print(f"Version: {report['schema_version']}")
        print(f"Total Steps: {cov['total_steps']}")
        print(f"\n{'FILE ATTACHMENT COVERAGE':-^80}")
        print(f"Steps WITH files: {cov['steps_with_files']} ({cov.get('file_coverage_percent', 0)}%)")
        print(f"Steps WITHOUT files: {cov['steps_without_files']}")

        print(f"\n{'IMPLEMENTATION REFERENCE COVERAGE':-^80}")
        print(f"Steps WITH impl: {cov['steps_with_impl']} ({cov.get('impl_coverage_percent', 0)}%)")
        print(f"Steps WITHOUT impl: {cov['steps_without_impl']}")

        print(f"\n{'FILE TYPE DISTRIBUTION':-^80}")
        for ext, count in sorted(cov['file_type_distribution'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {ext}: {count}")

        print(f"\n{'COVERAGE BY PHASE':-^80}")
        for phase, stats in sorted(cov['coverage_by_phase'].items()):
            file_pct = (stats['with_files'] / stats['total'] * 100) if stats['total'] > 0 else 0
            impl_pct = (stats['with_impl'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"  {phase}: {stats['total']} steps | Files: {file_pct:.1f}% | Impl: {impl_pct:.1f}%")

        print(f"\n{'COVERAGE BY SOURCE SCHEMA':-^80}")
        for source, stats in sorted(cov['coverage_by_source'].items()):
            file_pct = (stats['with_files'] / stats['total'] * 100) if stats['total'] > 0 else 0
            impl_pct = (stats['with_impl'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"  {source}: {stats['total']} steps | Files: {file_pct:.1f}% | Impl: {impl_pct:.1f}%")

        if cov['missing_files']:
            print(f"\n{'STEPS MISSING FILE ATTACHMENTS (First 10)':-^80}")
            for item in cov['missing_files'][:10]:
                print(f"  {item['step_id']}: {item['name'][:60]}")
            if len(cov['missing_files']) > 10:
                print(f"  ... and {len(cov['missing_files']) - 10} more")

        print(f"\n{'='*80}\n")

def main():
    parser = argparse.ArgumentParser(description='Analyze E2E schema file coverage')
    parser.add_argument('--schema', required=True, help='Path to unified schema YAML')
    parser.add_argument('--report', help='Output JSON report path')
    parser.add_argument('--summary', action='store_true', help='Print summary to console')

    args = parser.parse_args()

    analyzer = CoverageAnalyzer(Path(args.schema))
    report = analyzer.generate_report()

    if args.report:
        with open(args.report, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        print(f"Coverage report saved to: {args.report}")

    if args.summary or not args.report:
        analyzer.print_summary(report)

if __name__ == '__main__':
    main()
