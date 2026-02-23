"""
Phase 6: Validation and Final Checks
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime


def validate_migration():
    """Perform final validation checks."""

    print("="*70)
    print("PHASE 6: VALIDATION")
    print("="*70)

    results = {
        'checks': [],
        'all_passed': True,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }

    # Check 1: All directories created
    print("\nCheck 1: Verify directories...")
    with open('.migration/reports/PHASE_1_2_RESULTS.json', 'r') as f:
        phase12 = json.load(f)

    dirs_ok = True
    for dir_path in phase12['directories_created']:
        if not Path(dir_path).exists():
            print(f"  ✗ Missing: {dir_path}")
            dirs_ok = False

    results['checks'].append({
        'check': 'directories_created',
        'passed': dirs_ok,
        'message': f"{len(phase12['directories_created'])} directories verified"
    })
    print(f"  {'✓' if dirs_ok else '✗'} Directories: {len(phase12['directories_created'])}")

    # Check 2: All files copied
    print("\nCheck 2: Verify file copies...")
    files_ok = True
    missing_files = []

    for file_info in phase12['files_copied']:
        if not Path(file_info['target']).exists():
            missing_files.append(file_info['target'])
            files_ok = False

    results['checks'].append({
        'check': 'files_copied',
        'passed': files_ok,
        'message': f"{len(phase12['files_copied'])} files verified",
        'missing_files': missing_files
    })
    print(f"  {'✓' if files_ok else '✗'} Files copied: {len(phase12['files_copied'])}")
    if missing_files:
        for missing in missing_files[:5]:
            print(f"    Missing: {missing}")

    # Check 3: Registry count
    print("\nCheck 3: Verify registry count...")
    registry_path = Path('REGISTRY/01999000042260124503_governance_registry_unified.json')
    with open(registry_path, 'r') as f:
        registry = json.load(f)

    expected_count = 9 + 85  # baseline + new files
    actual_count = len(registry.get('files', []))
    registry_ok = abs(actual_count - expected_count) <= 10

    results['checks'].append({
        'check': 'registry_count',
        'passed': registry_ok,
        'expected': expected_count,
        'actual': actual_count,
        'message': f"Registry has {actual_count} files (expected ~{expected_count})"
    })
    print(f"  {'✓' if registry_ok else '✗'} Registry count: {actual_count} (expected ~{expected_count})")

    # Check 4: No duplicate file IDs
    print("\nCheck 4: Check for duplicate file IDs...")
    file_ids = [f['file_id'] for f in registry.get('files', [])]
    duplicates = [id for id in file_ids if file_ids.count(id) > 1]
    duplicates_ok = len(set(duplicates)) == 0

    results['checks'].append({
        'check': 'no_duplicate_ids',
        'passed': duplicates_ok,
        'duplicates': list(set(duplicates)),
        'message': f"{'No' if duplicates_ok else len(set(duplicates))} duplicate IDs found"
    })
    print(f"  {'✓' if duplicates_ok else '✗'} Duplicate IDs: {len(set(duplicates))}")

    # Check 5: Schema version
    print("\nCheck 5: Verify schema version...")
    schema_ok = registry.get('schema_version') == '4.0'

    results['checks'].append({
        'check': 'schema_version',
        'passed': schema_ok,
        'version': registry.get('schema_version'),
        'message': f"Schema version: {registry.get('schema_version')}"
    })
    print(f"  {'✓' if schema_ok else '✗'} Schema version: {registry.get('schema_version')}")

    # Check 6: path_index.yaml updated
    print("\nCheck 6: Verify path_index.yaml...")
    import yaml
    with open('PATH_FILES/config/path_index.yaml', 'r') as f:
        path_index = yaml.safe_load(f)

    expected_keys = ['REGISTRY_WRITER_SERVICE', 'REPO_AUTOOPS_ORCHESTRATOR']
    path_index_ok = all(key in path_index for key in expected_keys)

    results['checks'].append({
        'check': 'path_index_updated',
        'passed': path_index_ok,
        'message': f"path_index.yaml has key entries"
    })
    print(f"  {'✓' if path_index_ok else '✗'} path_index.yaml updated")

    # Check 7: File integrity (sample)
    print("\nCheck 7: File integrity check (sample)...")
    sample_files = phase12['files_copied'][:10]
    integrity_ok = True

    for file_info in sample_files:
        target_path = Path(file_info['target'])
        if target_path.exists():
            # Just check size > 0
            if target_path.stat().st_size == 0:
                integrity_ok = False
                break

    results['checks'].append({
        'check': 'file_integrity',
        'passed': integrity_ok,
        'message': f"Sampled {len(sample_files)} files"
    })
    print(f"  {'✓' if integrity_ok else '✗'} File integrity check")

    # Overall result
    results['all_passed'] = all(check['passed'] for check in results['checks'])

    # Save results
    with open('.migration/reports/PHASE_6_VALIDATION.json', 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n" + "="*70)
    print("VALIDATION COMPLETE")
    print("="*70)
    print(f"Status: {'✓ ALL CHECKS PASSED' if results['all_passed'] else '✗ SOME CHECKS FAILED'}")
    print(f"Passed: {sum(1 for c in results['checks'] if c['passed'])}/{len(results['checks'])}")
    print(f"\nResults saved to: .migration/reports/PHASE_6_VALIDATION.json")

    return results


if __name__ == '__main__':
    validate_migration()
