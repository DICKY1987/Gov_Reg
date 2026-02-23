#!/usr/bin/env python3
"""
Generate 20-digit file IDs and register all .py, .yaml, .json, .ps1 files
"""

import json
import pathlib
from datetime import datetime
import hashlib

def generate_file_id():
    """Generate 20-digit file ID based on timestamp"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')[:20]
    return timestamp

def find_all_target_files():
    """Find all .py, .yaml, .json, .ps1 files"""
    root = pathlib.Path('.')
    extensions = ['.py', '.yaml', '.yml', '.json', '.ps1', '.psh']
    
    files = []
    for ext in extensions:
        files.extend(root.rglob(f'*{ext}'))
    
    # Filter out .git, .venv, __pycache__, etc.
    excluded_dirs = {'.git', '.venv', '__pycache__', 'node_modules', '.pytest_cache'}
    
    filtered = []
    for f in files:
        if not any(excluded in f.parts for excluded in excluded_dirs):
            filtered.append(f)
    
    return sorted(filtered)

def main():
    print('=' * 80)
    print('FILE ID ASSIGNMENT AND REGISTRY UPDATE')
    print('=' * 80)
    print(f'Timestamp: {datetime.now().isoformat()}')
    print()

    # Find all target files
    target_files = find_all_target_files()
    print(f'Found {len(target_files)} files requiring file IDs')
    print()

    # Check if registry exists
    registry_path = pathlib.Path('REGISTRY/master_registry.json')
    registry_path.parent.mkdir(parents=True, exist_ok=True)

    if registry_path.exists():
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
        existing_count = len(registry.get('files', []))
        print(f'✓ Loaded existing registry with {existing_count} entries')
    else:
        registry = {
            'version': '1.0.0',
            'created_at': datetime.now().isoformat(),
            'description': 'Master registry of all code, config, and script files',
            'files': []
        }
        print('✓ Created new registry')

    print()

    # Create file ID mapping
    existing_files = {f['path']: f for f in registry.get('files', [])}
    added = 0
    skipped = 0

    new_entries = []

    for file_path in target_files:
        rel_path = str(file_path.relative_to('.'))
        
        # Check if file already in registry
        if rel_path in existing_files:
            entry = existing_files[rel_path]
            # Update hash and size
            try:
                content = file_path.read_bytes()
                new_hash = hashlib.sha256(content).hexdigest()[:16]
                entry['hash'] = new_hash
                entry['size'] = file_path.stat().st_size
                entry['last_verified'] = datetime.now().isoformat()
            except:
                pass
            skipped += 1
        else:
            # Generate new file ID
            file_id = generate_file_id()
            
            # Calculate file hash for integrity
            try:
                content = file_path.read_bytes()
                file_hash = hashlib.sha256(content).hexdigest()[:16]
            except:
                file_hash = 'unreadable'
            
            # Determine file type
            if file_path.suffix == '.py':
                ftype = 'code'
            elif file_path.suffix in ['.yaml', '.yml', '.json']:
                ftype = 'config'
            elif file_path.suffix in ['.ps1', '.psh']:
                ftype = 'script'
            else:
                ftype = 'unknown'
            
            entry = {
                'file_id': file_id,
                'path': rel_path,
                'extension': file_path.suffix,
                'size': file_path.stat().st_size,
                'hash': file_hash,
                'registered_at': datetime.now().isoformat(),
                'type': ftype
            }
            added += 1
            print(f'✓ NEW: {file_id} -> {rel_path}')
        
        new_entries.append(entry)

    # Update registry metadata
    registry['files'] = new_entries
    registry['last_updated'] = datetime.now().isoformat()
    registry['total_files'] = len(new_entries)

    # Save registry
    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2)

    print()
    print('=' * 80)
    print('SUMMARY')
    print('=' * 80)
    print(f'Total files processed:  {len(target_files)}')
    print(f'New file IDs assigned:  {added}')
    print(f'Existing entries kept:  {skipped}')
    print()
    print(f'Registry saved to: {registry_path}')
    print(f'Total registry entries: {len(new_entries)}')
    print()

    # Show breakdown by type
    by_type = {}
    for entry in new_entries:
        ftype = entry['type']
        by_type[ftype] = by_type.get(ftype, 0) + 1

    print('Files by type:')
    for ftype, count in sorted(by_type.items()):
        print(f'  {ftype}: {count}')

    print()
    
    # Show breakdown by extension
    by_ext = {}
    for entry in new_entries:
        ext = entry['extension']
        by_ext[ext] = by_ext.get(ext, 0) + 1
    
    print('Files by extension:')
    for ext, count in sorted(by_ext.items()):
        print(f'  {ext}: {count}')

    print()
    print('✓ Registry update complete!')
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
