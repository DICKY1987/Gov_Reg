#!/usr/bin/env python3
"""Prune registry to only files that exist on disk."""
import json
from pathlib import Path
from datetime import datetime

def main():
    registry_path = Path('01999000042260124503_REGISTRY_file.json')
    gov_reg = Path(r'C:\Users\richg\Gov_Reg')
    
    print("Loading registry...")
    with open(registry_path, encoding='utf-8') as f:
        reg = json.load(f)
    
    original_count = len(reg['files'])
    print(f"Original file count: {original_count}")
    
    # Filter to existing files only
    print("Checking file existence...")
    existing_files = []
    missing_files = []
    
    for idx, file_rec in enumerate(reg['files']):
        if (idx + 1) % 100 == 0:
            print(f"  Progress: {idx + 1}/{original_count}", end='\r')
        
        rel_path = file_rec.get('relative_path', '')
        if (gov_reg / rel_path).exists():
            existing_files.append(file_rec)
        else:
            missing_files.append(file_rec)
    
    print()  # Clear progress line
    
    reg['files'] = existing_files
    pruned_count = len(missing_files)
    
    # Add metadata about pruning
    if 'entries_metadata' not in reg:
        reg['entries_metadata'] = {}
    
    reg['entries_metadata']['pruned_at'] = datetime.now().isoformat()
    reg['entries_metadata']['pruned_count'] = pruned_count
    reg['entries_metadata']['pruning_reason'] = 'removed non-existent file references'
    reg['entries_metadata']['remaining_files'] = len(existing_files)
    
    # Write pruned registry
    output_path = Path('01999000042260124503_REGISTRY_file.pruned.json')
    print(f"Writing pruned registry to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(reg, f, indent=2, ensure_ascii=False)
    
    print()
    print("=== PRUNING SUMMARY ===")
    print(f"Original files: {original_count}")
    print(f"Pruned (missing): {pruned_count} ({100*pruned_count/original_count:.1f}%)")
    print(f"Remaining (exist): {len(existing_files)} ({100*len(existing_files)/original_count:.1f}%)")
    print(f"Output: {output_path}")
    print()
    
    # Show sample of what was kept
    print("Sample of files KEPT (first 5):")
    for f in existing_files[:5]:
        print(f"  ✓ {f.get('relative_path', '<no path>')[:70]}")
    
    print()
    print("Sample of files REMOVED (first 5):")
    for f in missing_files[:5]:
        print(f"  ✗ {f.get('relative_path', '<no path>')[:70]}")

if __name__ == '__main__':
    main()
