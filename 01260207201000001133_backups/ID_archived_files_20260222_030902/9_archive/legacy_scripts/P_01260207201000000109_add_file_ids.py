#!/usr/bin/env python3
"""Add 20-digit IDs to files in current directory that need them."""

import os
import sys
from pathlib import Path

# Import the ID allocator
sys.path.insert(0, str(Path(__file__).parent))
from govreg_core.P_01999000042260124031_unified_id_allocator import UnifiedIDAllocator

def main():
    # Find the counter store (may have ID prefix already)
    counter_store_files = list(Path('.').glob('*COUNTER_STORE.json'))
    counter_store_files = [f for f in counter_store_files if not f.name.endswith('.lock')]
    
    if not counter_store_files:
        print("ERROR: COUNTER_STORE.json not found")
        return
    
    counter_store = counter_store_files[0]
    print(f"Using counter store: {counter_store.name}")
    allocator = UnifiedIDAllocator(counter_store)
    
    # Files that need IDs in current directory
    target_extensions = {'.md', '.txt', '.py', '.ps1', '.yaml', '.json'}
    current_dir = Path('.')
    
    files_to_rename = []
    for file_path in current_dir.glob('*'):
        if not file_path.is_file():
            continue
        if file_path.suffix not in target_extensions:
            continue
        # Skip files that already have IDs
        name = file_path.name
        if name.startswith('P_') and len(name) > 22 and name[2:22].isdigit():
            continue
        if len(name) > 20 and name[:20].isdigit():
            continue
        
        files_to_rename.append(file_path)
    
    print(f"Found {len(files_to_rename)} files needing IDs")
    
    for file_path in sorted(files_to_rename):
        # Get new ID
        new_id = allocator.allocate_single_id(purpose="file_id_assignment", allocated_by="batch_script")
        
        # Determine prefix based on extension
        if file_path.suffix == '.py':
            prefix = f"P_{new_id}_"
        else:
            prefix = f"{new_id}_"
        
        new_name = prefix + file_path.name
        new_path = file_path.parent / new_name
        
        try:
            file_path.rename(new_path)
            print(f"✓ {file_path.name} → {new_name}")
        except Exception as e:
            print(f"✗ Failed to rename {file_path.name}: {e}")
    
    print(f"\nRenamed {len(files_to_rename)} files")

if __name__ == '__main__':
    main()
