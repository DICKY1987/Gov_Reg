#!/usr/bin/env python3
"""Add 20-digit IDs to all files recursively that need them."""

import sys
from pathlib import Path
from collections import defaultdict

# Import the ID allocator
ALLOCATORS_ROOT = Path(__file__).resolve().parents[2] / "1_runtime" / "allocators"
if str(ALLOCATORS_ROOT) not in sys.path:
    sys.path.insert(0, str(ALLOCATORS_ROOT))
from P_01999000042260124031_unified_id_allocator import UnifiedIDAllocator

def get_file_id_from_name(filename: str) -> str | None:
    """Extract file_id from filename."""
    if filename.startswith('P_') and len(filename) > 22 and filename[2:22].isdigit():
        return filename[2:22]
    elif len(filename) > 20 and filename[:20].isdigit():
        return filename[:20]
    return None

def main():
    # Find counter store
    counter_store_files = list(Path('.').glob('*COUNTER_STORE.json'))
    counter_store_files = [f for f in counter_store_files if not f.name.endswith('.lock')]
    
    if not counter_store_files:
        print("ERROR: COUNTER_STORE.json not found")
        return 1
    
    counter_store = counter_store_files[0]
    print(f"Using counter store: {counter_store.name}\n")
    allocator = UnifiedIDAllocator(counter_store)
    
    # Find all files recursively that need IDs
    target_extensions = {'.md', '.txt', '.py', '.ps1', '.yaml', '.json'}
    files_to_rename = []
    
    for file_path in Path('.').rglob('*'):
        if not file_path.is_file():
            continue
        if file_path.suffix not in target_extensions:
            continue
        # Skip if already has ID
        if get_file_id_from_name(file_path.name):
            continue
        # Skip certain directories
        if any(x in file_path.parts for x in ['.git', '__pycache__', 'node_modules', '.pytest_cache']):
            continue
        
        files_to_rename.append(file_path)
    
    print(f"Found {len(files_to_rename)} files needing IDs (recursive)")
    
    # Group by directory for reporting
    by_dir = defaultdict(list)
    for f in files_to_rename:
        rel_dir = str(f.parent.relative_to('.'))
        by_dir[rel_dir].append(f)
    
    print(f"\nFiles by directory:")
    for dir_path in sorted(by_dir.keys())[:20]:
        print(f"  {dir_path}: {len(by_dir[dir_path])} files")
    if len(by_dir) > 20:
        print(f"  ... and {len(by_dir) - 20} more directories")
    
    # Confirm
    print(f"\n⚠ About to rename {len(files_to_rename)} files")
    response = input("Continue? (y/N): ")
    if response.lower() != 'y':
        print("Aborted.")
        return 0
    
    print("\nRenaming files...\n")
    
    # Rename files
    success_count = 0
    error_count = 0
    
    for i, file_path in enumerate(sorted(files_to_rename), 1):
        try:
            # Get new ID
            new_id = allocator.allocate_single_id(
                purpose="recursive_file_id_assignment", 
                allocated_by="batch_script"
            )
            
            # Determine prefix based on extension
            if file_path.suffix == '.py':
                prefix = f"P_{new_id}_"
            else:
                prefix = f"{new_id}_"
            
            new_name = prefix + file_path.name
            new_path = file_path.parent / new_name
            
            file_path.rename(new_path)
            success_count += 1
            
            # Show progress every 50 files
            if i % 50 == 0 or i == len(files_to_rename):
                print(f"  Progress: {i}/{len(files_to_rename)} ({success_count} success, {error_count} errors)")
        
        except Exception as e:
            error_count += 1
            print(f"  ✗ Failed: {file_path}: {e}")
    
    print(f"\n{'='*60}")
    print(f"Complete!")
    print(f"  ✓ Success: {success_count}")
    print(f"  ✗ Errors: {error_count}")
    print(f"{'='*60}\n")
    
    return 0 if error_count == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
