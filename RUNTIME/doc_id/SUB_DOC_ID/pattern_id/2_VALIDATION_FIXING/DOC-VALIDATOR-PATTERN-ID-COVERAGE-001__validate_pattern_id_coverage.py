#!/usr/bin/env python3
# DOC_LINK: DOC-VALIDATOR-PATTERN-ID-COVERAGE-001
# DOC_ID: DOC-VALIDATOR-PATTERN-ID-COVERAGE-001
"""
doc_id: DOC-VALIDATOR-PATTERN-ID-COVERAGE-001
Validate pattern_id triad completeness (spec, executor, test)
"""

import sys
from pathlib import Path
import yaml

def validate_coverage():
    """Validate pattern triads are complete"""
    registry_path = Path(__file__).parent.parent / "5_REGISTRY_DATA" / "PAT_ID_REGISTRY.yaml"

    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = yaml.safe_load(f)

    incomplete_patterns = []
    complete_patterns = []

    for pattern in registry.get('patterns', []):
        files = pattern.get('files', {})
        has_executor = 'executor' in files and files['executor']
        has_spec = 'spec' in files and files['spec']
        has_test = 'test' in files and files['test']

        completeness = {
            'pattern_id': pattern['pattern_id'],
            'name': pattern.get('name'),
            'has_executor': has_executor,
            'has_spec': has_spec,
            'has_test': has_test,
            'complete': has_executor and has_spec and has_test
        }

        if completeness['complete']:
            complete_patterns.append(completeness)
        else:
            incomplete_patterns.append(completeness)

    total = len(complete_patterns) + len(incomplete_patterns)
    coverage_pct = (len(complete_patterns) / total * 100) if total > 0 else 0

    return {
        'passed': coverage_pct >= 75.0,  # Target: 75% complete triads
        'incomplete_patterns': incomplete_patterns,
        'complete_patterns': complete_patterns,
        'coverage_pct': coverage_pct,
        'total_patterns': total
    }

if __name__ == '__main__':
    result = validate_coverage()

    print("\n=== Pattern ID Coverage Validation ===")
    print(f"Total patterns: {result['total_patterns']}")
    print(f"Complete triads: {len(result['complete_patterns'])}")
    print(f"Incomplete triads: {len(result['incomplete_patterns'])}")
    print(f"Coverage: {result['coverage_pct']:.1f}%")
    print(f"Target: 75%")

    if result['incomplete_patterns']:
        print("\n⚠️  Incomplete patterns (missing spec/executor/test):")
        for pattern in result['incomplete_patterns']:
            missing = []
            if not pattern['has_spec']: missing.append('spec')
            if not pattern['has_executor']: missing.append('executor')
            if not pattern['has_test']: missing.append('test')
            print(f"  - {pattern['pattern_id']}: missing {', '.join(missing)}")

    if result['passed']:
        print("\n✅ Coverage meets target (≥75%)")
        sys.exit(0)
    else:
        print(f"\n⚠️  Coverage below target ({result['coverage_pct']:.1f}% < 75%)")
        sys.exit(0)  # Warning only, not a failure
