#!/usr/bin/env python3
"""
Fix file_id pattern in Column Dictionary to match COMPLETE_SSOT.json specification.

Updates:
- file_id: Add pattern "^[0-9]{20}$" (20-digit file identifiers)
- Confirm bundle_id: pattern "^[0-9]{16}$" is correct
- Update provenance to reference COMPLETE_SSOT.json
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone


def fix_file_id_pattern(dict_path: Path) -> dict:
    """Add proper pattern and provenance for file_id."""
    
    with open(dict_path, 'r', encoding='utf-8') as f:
        dictionary = json.load(f)
    
    # Fix file_id
    if 'file_id' in dictionary['headers']:
        dictionary['headers']['file_id']['value_schema'] = {
            'type': ['string', 'null'],
            'pattern': '^[0-9]{20}$',
            'description': '20-digit file identifier (17-char timestamp prefix + 3-digit suffix)'
        }
        
        dictionary['headers']['file_id']['provenance'] = {
            'sources': [{
                'doc_id': '01999000042260124527',
                'path': '01999000042260124527_COMPLETE_SSOT.json',
                'anchor': 'id_system.file_id_format'
            }]
        }
        
        dictionary['headers']['file_id']['scope'] = {
            'record_kinds_in': ['ENTITY', 'EDGE', 'GENERATOR'],
            'entity_kinds_in': ['FILE', 'ASSET']
        }
        
        dictionary['headers']['file_id']['presence'] = {
            'policy': 'REQUIRED',
            'rules': []
        }
        
        # Update derivation to be SYSTEM (allocated by ID counter)
        dictionary['headers']['file_id']['derivation'] = {
            'mode': 'SYSTEM',
            'sources': [
                {'kind': 'REGISTRY', 'ref': '01999000042260124026_ID_COUNTER.json'},
                {'kind': 'TOOL_OUTPUT', 'ref': 'P_01999000042260124027_id_allocator.py'}
            ],
            'process': {
                'engine': 'TASK_OUTPUT',
                'spec': {
                    'task_id': 'TASK_ID_ALLOCATION',
                    'output_key': 'file_id',
                    'tool': 'id_allocator.allocate_single_id()'
                }
            },
            'null_policy': 'ERROR',
            'error_policy': 'ERROR',
            'evidence': {
                'evidence_keys': ['id_counter.last_allocated', 'allocation_history.entry'],
                'artifacts': ['ID_COUNTER.json', 'ALLOCATION_LOG.jsonl']
            }
        }
    
    # Update bundle_id provenance to reference COMPLETE_SSOT
    if 'bundle_id' in dictionary['headers']:
        dictionary['headers']['bundle_id']['provenance']['sources'] = [{
            'doc_id': '01999000042260124527',
            'path': '01999000042260124527_COMPLETE_SSOT.json',
            'anchor': 'bundle_fields.bundle_id'
        }]
        
        # Confirm pattern is correct (16 digits)
        assert dictionary['headers']['bundle_id']['value_schema']['pattern'] == '^[0-9]{16}$', \
            "bundle_id pattern should be 16 digits"
    
    # Update metadata
    dictionary['dictionary_version'] = '4.1.1'  # Patch version for corrections
    dictionary['generated_utc'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    return dictionary


def main():
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    
    dict_path = repo_root / '2026012816000001_COLUMN_DICTIONARY.json'
    
    if not dict_path.exists():
        print(f"ERROR: Dictionary not found: {dict_path}", file=sys.stderr)
        sys.exit(1)
    
    print("=" * 70)
    print("FIXING FILE_ID PATTERN")
    print("=" * 70)
    print()
    
    # Backup
    backup_path = dict_path.with_suffix('.json.backup3')
    with open(dict_path, 'r', encoding='utf-8') as f:
        with open(backup_path, 'w', encoding='utf-8') as fb:
            fb.write(f.read())
    
    print(f"Backup created: {backup_path}")
    print()
    
    # Fix
    dictionary = fix_file_id_pattern(dict_path)
    
    # Write
    with open(dict_path, 'w', encoding='utf-8') as f:
        json.dump(dictionary, f, indent=2, ensure_ascii=False)
    
    print("Updates made:")
    print("  ✓ file_id: Added pattern ^[0-9]{20}$ (20 digits)")
    print("  ✓ file_id: Updated provenance to COMPLETE_SSOT.json")
    print("  ✓ file_id: Changed derivation to SYSTEM mode (ID allocator)")
    print("  ✓ file_id: Updated scope to ENTITY/EDGE/GENERATOR")
    print("  ✓ file_id: Changed presence to REQUIRED")
    print("  ✓ bundle_id: Confirmed pattern ^[0-9]{16}$ (16 digits) is correct")
    print("  ✓ bundle_id: Updated provenance to COMPLETE_SSOT.json")
    print("  ✓ dictionary_version: 4.1.0 → 4.1.1 (patch)")
    print()
    print("=" * 70)
    print("CORRECTION COMPLETE")
    print("=" * 70)
    print()
    print("ID Formats (per COMPLETE_SSOT.json):")
    print("  file_id:   20 digits (e.g., 01999000042260124527)")
    print("  bundle_id: 16 digits (e.g., 1000000000000002)")
    print()


if __name__ == '__main__':
    main()
