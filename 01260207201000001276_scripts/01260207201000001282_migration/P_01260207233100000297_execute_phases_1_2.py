"""
Phase 1: Create target directories and Phase 2: Copy files with IDs
"""
import json
import shutil
from pathlib import Path
from datetime import datetime


def execute_phases_1_and_2():
    """Execute directory creation and file copying."""

    print("="*70)
    print("PHASE 1: CREATE TARGET DIRECTORIES")
    print("="*70)

    # Load allocation
    with open('.migration/mapping/id_allocation.json', 'r') as f:
        allocation = json.load(f)

    # Collect unique target directories
    target_dirs = set()
    for alloc in allocation['allocations']:
        target_path = Path(alloc['target_path'])
        if str(target_path).startswith('Gov_Reg/'):
            target_path = Path(str(target_path).replace('Gov_Reg/', '', 1))
        target_dir = target_path.parent
        target_dirs.add(target_dir)

    # Create directories
    created_dirs = []
    for target_dir in sorted(target_dirs):
        target_dir.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(target_dir))
        print(f"  ✓ Created: {target_dir}")

    print(f"\n✓ Created {len(created_dirs)} directories")

    # Phase 2: Copy files
    print("\n" + "="*70)
    print("PHASE 2: COPY FILES WITH 20-DIGIT IDS")
    print("="*70)

    copied_files = []
    created_inits = []
    errors = []

    for i, alloc in enumerate(allocation['allocations'], 1):
        try:
            target_path = Path(alloc['target_path'])
            if str(target_path).startswith('Gov_Reg/'):
                target_path = Path(str(target_path).replace('Gov_Reg/', '', 1))

            if alloc.get('is_new_init'):
                # Create __init__.py
                target_path.parent.mkdir(parents=True, exist_ok=True)

                # Create with FILE_ID header
                content = f'''"""
Package initialization.
FILE_ID: {alloc['allocated_id']}
"""
'''
                with open(target_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                created_inits.append({
                    'path': str(target_path),
                    'id': alloc['allocated_id']
                })
                print(f"  [{i}/{len(allocation['allocations'])}] ✓ CREATE: {target_path.name} -> {target_path.parent}")

            else:
                # Copy file with new name
                source_path = Path(alloc['source_path'])

                if not source_path.exists():
                    errors.append({
                        'file': str(source_path),
                        'error': 'Source file not found'
                    })
                    print(f"  [{i}/{len(allocation['allocations'])}] ✗ MISSING: {source_path}")
                    continue

                # New filename with 20-digit ID prefix
                original_name = source_path.name
                new_name = f"{alloc['allocated_id']}_{original_name}"
                new_path = target_path.parent / new_name

                # Copy file
                shutil.copy2(source_path, new_path)

                copied_files.append({
                    'source': str(source_path),
                    'target': str(new_path),
                    'id': alloc['allocated_id'],
                    'original_name': original_name
                })

                if i % 10 == 0 or i == len(allocation['allocations']):
                    print(f"  [{i}/{len(allocation['allocations'])}] ✓ COPY: {original_name}")

        except Exception as e:
            errors.append({
                'file': alloc.get('source_path', alloc.get('target_path')),
                'error': str(e)
            })
            print(f"  [{i}/{len(allocation['allocations'])}] ✗ ERROR: {e}")

    print(f"\n✓ Copied {len(copied_files)} files")
    print(f"✓ Created {len(created_inits)} __init__.py files")

    if errors:
        print(f"\n⚠️  {len(errors)} errors encountered:")
        for error in errors:
            print(f"  - {error['file']}: {error['error']}")

    # Save results
    result = {
        'phase': 'phases_1_and_2',
        'directories_created': created_dirs,
        'files_copied': copied_files,
        'inits_created': created_inits,
        'errors': errors,
        'total_operations': len(copied_files) + len(created_inits),
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }

    with open('.migration/reports/PHASE_1_2_RESULTS.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Phase 1 & 2 complete")
    print(f"  Total operations: {result['total_operations']}")
    print(f"  Results saved to: .migration/reports/PHASE_1_2_RESULTS.json")

    return result


if __name__ == '__main__':
    execute_phases_1_and_2()
