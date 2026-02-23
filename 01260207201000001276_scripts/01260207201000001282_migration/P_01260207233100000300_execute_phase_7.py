"""
Phase 7: Delete source files after successful migration
"""
import json
import shutil
from pathlib import Path
from datetime import datetime


def delete_source_files():
    """Delete source files that were successfully migrated."""

    print("="*70)
    print("PHASE 7: DELETE SOURCE FILES")
    print("="*70)

    # Load Phase 1&2 results to get source file list
    with open('.migration/reports/PHASE_1_2_RESULTS.json', 'r') as f:
        phase12 = json.load(f)

    deleted_files = []
    deleted_dirs = []
    errors = []

    # Delete individual files
    print("\nDeleting source files...")
    for file_info in phase12['files_copied']:
        source_path = Path(file_info['source'])

        try:
            if source_path.exists():
                source_path.unlink()
                deleted_files.append(str(source_path))
                print(f"  ✓ Deleted: {source_path.name}")
            else:
                print(f"  ⚠️  Already gone: {source_path}")
        except Exception as e:
            errors.append({
                'file': str(source_path),
                'error': str(e)
            })
            print(f"  ✗ Error deleting {source_path}: {e}")

    # Delete now-empty directories (from specific source locations only)
    print("\nDeleting empty source directories...")

    # Directories to clean up
    cleanup_dirs = [
        Path(r'C:\Users\richg\eafix-modular\repo_autoops'),
        Path(r'C:\Users\richg\eafix-modular\services\registry_writer'),
        Path(r'C:\Users\richg\eafix-modular\services\data-validator'),
        Path(r'C:\Users\richg\eafix-modular\services\generator'),
        Path(r'C:\Users\richg\eafix-modular\services\flow-orchestrator'),
        Path(r'C:\Users\richg\eafix-modular\services\signal-generator'),
        Path(r'C:\Users\richg\ALL_AI\mapp_py'),
        Path(r'C:\Users\richg\eafix-modular\scripts'),
        Path(r'C:\Users\richg\eafix-modular\Directory management system\03_IMPLEMENTATION')
    ]

    for dir_path in cleanup_dirs:
        if not dir_path.exists():
            print(f"  ⚠️  Directory doesn't exist: {dir_path}")
            continue

        try:
            # Check if directory is empty or only has __pycache__
            contents = list(dir_path.iterdir())
            pycache_only = all(item.name == '__pycache__' for item in contents)

            if len(contents) == 0 or pycache_only:
                # Remove __pycache__ if present
                for item in contents:
                    if item.name == '__pycache__':
                        shutil.rmtree(item)

                # Remove the directory itself
                dir_path.rmdir()
                deleted_dirs.append(str(dir_path))
                print(f"  ✓ Removed empty directory: {dir_path.name}")
            else:
                # Check if only subdirectories remain (and they're empty)
                all_empty = True
                for item in contents:
                    if item.is_file():
                        all_empty = False
                        break
                    if item.is_dir() and any(item.iterdir()):
                        all_empty = False
                        break

                if all_empty:
                    shutil.rmtree(dir_path)
                    deleted_dirs.append(str(dir_path))
                    print(f"  ✓ Removed directory tree: {dir_path.name}")
                else:
                    print(f"  ℹ️  Directory not empty, skipping: {dir_path.name}")

        except Exception as e:
            errors.append({
                'directory': str(dir_path),
                'error': str(e)
            })
            print(f"  ✗ Error with {dir_path}: {e}")

    # Save cleanup results
    result = {
        'phase': 'phase_7_cleanup',
        'deleted_files': deleted_files,
        'deleted_directories': deleted_dirs,
        'errors': errors,
        'total_files_deleted': len(deleted_files),
        'total_dirs_deleted': len(deleted_dirs),
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }

    with open('.migration/reports/PHASE_7_CLEANUP.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print("\n" + "="*70)
    print("PHASE 7 COMPLETE")
    print("="*70)
    print(f"Files deleted: {len(deleted_files)}")
    print(f"Directories removed: {len(deleted_dirs)}")

    if errors:
        print(f"\n⚠️  {len(errors)} errors encountered")
        for error in errors[:5]:
            print(f"  - {error.get('file') or error.get('directory')}: {error['error']}")

    print(f"\nResults saved to: .migration/reports/PHASE_7_CLEANUP.json")
    print("\n✅ Source cleanup complete")
    print("   Backups remain at: .migration/backups/sources/")

    return result


if __name__ == '__main__':
    delete_source_files()
