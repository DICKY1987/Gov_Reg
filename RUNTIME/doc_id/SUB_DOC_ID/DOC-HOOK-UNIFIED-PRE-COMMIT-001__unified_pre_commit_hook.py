#!/usr/bin/env python3
# DOC_LINK: DOC-HOOK-UNIFIED-PRE-COMMIT-001
# DOC_ID: DOC-HOOK-UNIFIED-PRE-COMMIT-001
"""
doc_id: DOC-HOOK-UNIFIED-PRE-COMMIT-001
Enhanced pre-commit hook for all stable ID types
"""

import sys
import subprocess
from pathlib import Path

def run_validator(script_path, name):
    """Run a validator script"""
    try:
        result = subprocess.run(
            ['python', str(script_path)],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=30
        )
        return {
            'name': name,
            'passed': result.returncode == 0,
            'output': result.stdout + result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            'name': name,
            'passed': False,
            'output': 'Validator timed out (>30s)'
        }
    except Exception as e:
        return {
            'name': name,
            'passed': False,
            'output': f'Error running validator: {e}'
        }

def main():
    """Run all validators for production ID types"""
    base_dir = Path(__file__).parent

    validators = [
        # doc_id validators (production)
        (base_dir / '2_VALIDATION_FIXING' / 'validate_doc_id_format.py', 'doc_id format'),
        (base_dir / '2_VALIDATION_FIXING' / 'validate_doc_id_uniqueness.py', 'doc_id uniqueness'),
        (base_dir / '2_VALIDATION_FIXING' / 'validate_doc_id_sync.py', 'doc_id sync'),
        (base_dir / '2_VALIDATION_FIXING' / 'validate_doc_id_coverage.py', 'doc_id coverage'),
        (base_dir / '2_VALIDATION_FIXING' / 'validate_doc_id_references.py', 'doc_id references'),

        # trigger_id validators (production)
        (base_dir / 'trigger_id' / '2_VALIDATION_FIXING' / 'validate_trigger_id_format.py', 'trigger_id format'),
        (base_dir / 'trigger_id' / '2_VALIDATION_FIXING' / 'validate_trigger_id_uniqueness.py', 'trigger_id uniqueness'),
        (base_dir / 'trigger_id' / '2_VALIDATION_FIXING' / 'validate_trigger_id_sync.py', 'trigger_id sync'),
        (base_dir / 'trigger_id' / '2_VALIDATION_FIXING' / 'validate_trigger_id_references.py', 'trigger_id references'),
        (base_dir / 'trigger_id' / '2_VALIDATION_FIXING' / 'validate_trigger_coverage.py', 'trigger_id coverage'),

        # pattern_id validators (production)
        (base_dir / 'pattern_id' / '2_VALIDATION_FIXING' / 'validate_pattern_id_format.py', 'pattern_id format'),
        (base_dir / 'pattern_id' / '2_VALIDATION_FIXING' / 'validate_pattern_id_uniqueness.py', 'pattern_id uniqueness'),
        (base_dir / 'pattern_id' / '2_VALIDATION_FIXING' / 'validate_pattern_id_sync.py', 'pattern_id sync'),
        (base_dir / 'pattern_id' / '2_VALIDATION_FIXING' / 'validate_pattern_id_coverage.py', 'pattern_id coverage'),
        (base_dir / 'pattern_id' / '2_VALIDATION_FIXING' / 'validate_pattern_id_references.py', 'pattern_id references'),

        # meta-registry validator
        (base_dir / 'validate_id_type_registry.py', 'ID type registry'),
    ]

    print("\n" + "="*80)
    print("UNIFIED PRE-COMMIT VALIDATION")
    print("="*80 + "\n")

    results = []
    for validator_path, name in validators:
        if not validator_path.exists():
            print(f"⚠️  Skipping {name} (not found)")
            continue

        print(f"Running {name}...", end=' ', flush=True)
        result = run_validator(validator_path, name)
        results.append(result)

        if result['passed']:
            print("✅")
        else:
            print("❌")

    # Summary
    passed = sum(1 for r in results if r['passed'])
    total = len(results)

    print("\n" + "="*80)
    print(f"SUMMARY: {passed}/{total} validators passed")
    print("="*80 + "\n")

    # Show failures
    failures = [r for r in results if not r['passed']]
    if failures:
        print("FAILURES:\n")
        for failure in failures:
            print(f"❌ {failure['name']}")
            print(f"   {failure['output'][:200]}")
            print()

        print("\n⛔ Pre-commit check FAILED")
        print("Fix the above issues and try again.\n")
        return 1

    print("✅ All validators passed - commit allowed\n")
    return 0

if __name__ == '__main__':
    sys.exit(main())
