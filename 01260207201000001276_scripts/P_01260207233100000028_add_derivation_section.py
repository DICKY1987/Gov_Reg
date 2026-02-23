#!/usr/bin/env python3
"""
Add derivation section to all headers in COLUMN_DICTIONARY.json

This script adds a 6th section to each header definition that specifies
how the value is produced/derived/calculated in a machine-enforceable way.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

def classify_header_derivation(header_name: str, header_def: dict) -> dict:
    """
    Intelligently determine derivation mode based on header semantics.
    
    Returns a complete derivation object with sensible defaults.
    """
    
    # System-generated timestamps and IDs
    if header_name in ['allocated_at', 'generated_utc', 'created_at', 'updated_at', 
                       'last_modified', 'timestamp', 'event_timestamp']:
        return {
            "mode": "SYSTEM",
            "sources": [{"kind": "ENV", "ref": "runtime.timestamp"}],
            "process": {"engine": "NONE", "spec": {}},
            "null_policy": "ERROR",
            "error_policy": "ERROR",
            "evidence": {"evidence_keys": ["run_id"], "artifacts": ["EVIDENCE_RUN_META_JSON"]}
        }
    
    if header_name in ['file_id', 'edge_id', 'entity_id', 'run_id', 'task_id', 
                       'event_id', 'record_id', 'registry_version']:
        return {
            "mode": "SYSTEM",
            "sources": [{"kind": "ENV", "ref": f"runtime.{header_name}"}],
            "process": {"engine": "NONE", "spec": {}},
            "null_policy": "ERROR",
            "error_policy": "ERROR",
            "evidence": {"evidence_keys": ["run_id"], "artifacts": ["EVIDENCE_RUN_META_JSON"]}
        }
    
    # Filesystem extraction
    if header_name in ['absolute_path', 'canonical_path', 'relative_path', 
                       'file_name', 'extension', 'size_bytes', 'mime_type',
                       'file_hash', 'sha256']:
        return {
            "mode": "EXTRACTED",
            "sources": [{"kind": "FILESYSTEM", "ref": f"scan_event.{header_name}"}],
            "process": {
                "engine": "TASK_OUTPUT",
                "spec": {
                    "task_id": "TASK_FS_SCAN_010",
                    "output_key": header_name
                }
            },
            "null_policy": "ALLOW_NULL" if header_def.get('presence', {}).get('policy') == 'OPTIONAL' else "ERROR",
            "error_policy": "WARN",
            "evidence": {"evidence_keys": ["fs_scan.event_id"], "artifacts": ["EVIDENCE_FS_SCAN_JSONL"]}
        }
    
    # GEU framework lookups
    if header_name.startswith('geu_') or header_name in ['governance_domain', 'required_suite_key']:
        return {
            "mode": "LOOKUP",
            "sources": [
                {"kind": "COLUMN", "ref": "file_id"},
                {"kind": "REGISTRY", "ref": "governance/geu_registry.json"}
            ],
            "process": {
                "engine": "LOOKUP_SPEC",
                "spec": {
                    "registry_ref": "governance/geu_registry.json",
                    "key": {"op": "col", "name": "file_id"},
                    "lookup_path_template": f"/files/{{key}}/{header_name}"
                }
            },
            "null_policy": "ALLOW_NULL",
            "error_policy": "WARN",
            "evidence": {"evidence_keys": ["geu_registry.checksum"], "artifacts": ["EVIDENCE_REGISTRY_SNAPSHOT"]}
        }
    
    # Registry lookups (general)
    if '_id' in header_name and header_name not in ['file_id', 'edge_id', 'entity_id']:
        return {
            "mode": "LOOKUP",
            "sources": [
                {"kind": "COLUMN", "ref": "primary_key"},
                {"kind": "REGISTRY", "ref": "registry/main.json"}
            ],
            "process": {
                "engine": "LOOKUP_SPEC",
                "spec": {
                    "registry_ref": "registry/main.json",
                    "key": {"op": "col", "name": "primary_key"},
                    "lookup_path_template": f"/entities/{{key}}/{header_name}"
                }
            },
            "null_policy": "ALLOW_NULL",
            "error_policy": "WARN",
            "evidence": {"evidence_keys": ["registry.checksum"], "artifacts": ["EVIDENCE_REGISTRY_SNAPSHOT"]}
        }
    
    # Boolean flags (often derived from presence of other data)
    if header_def.get('value_schema', {}).get('type') == 'boolean' or \
       (isinstance(header_def.get('value_schema', {}).get('type'), list) and 'boolean' in header_def.get('value_schema', {}).get('type')):
        return {
            "mode": "DERIVED",
            "sources": [{"kind": "COLUMN", "ref": "to_be_specified"}],
            "process": {
                "engine": "FORMULA_AST",
                "spec": {
                    "op": "exists",
                    "args": [{"op": "col", "name": "to_be_specified"}]
                }
            },
            "null_policy": "COERCE_DEFAULT",
            "error_policy": "WARN",
            "evidence": {"evidence_keys": [], "artifacts": []}
        }
    
    # Array types (often aggregated or collected)
    if header_def.get('value_schema', {}).get('type') == 'array':
        return {
            "mode": "AGGREGATED",
            "sources": [{"kind": "REGISTRY", "ref": "to_be_specified"}],
            "process": {
                "engine": "TRANSFORM_CHAIN",
                "spec": {
                    "steps": [
                        {"op": "filter", "condition": "to_be_specified"},
                        {"op": "collect", "field": "to_be_specified"}
                    ]
                }
            },
            "null_policy": "COERCE_DEFAULT",
            "error_policy": "WARN",
            "evidence": {"evidence_keys": [], "artifacts": []}
        }
    
    # Enums (usually looked up or validated input)
    if 'enum' in header_def.get('value_schema', {}):
        return {
            "mode": "INPUT",
            "sources": [{"kind": "COLUMN", "ref": header_name}],
            "process": {"engine": "NONE", "spec": {}},
            "null_policy": "ALLOW_NULL" if header_def.get('presence', {}).get('policy') == 'OPTIONAL' else "ERROR",
            "error_policy": "ERROR",
            "evidence": {"evidence_keys": [], "artifacts": []}
        }
    
    # Default: user input (to be refined)
    return {
        "mode": "INPUT",
        "sources": [{"kind": "COLUMN", "ref": header_name}],
        "process": {"engine": "NONE", "spec": {}},
        "null_policy": "ALLOW_NULL" if header_def.get('presence', {}).get('policy') == 'OPTIONAL' else "ERROR",
        "error_policy": "WARN",
        "evidence": {"evidence_keys": [], "artifacts": []}
    }


def add_derivation_to_dictionary(input_path: Path, output_path: Path) -> dict:
    """
    Add derivation section to all headers in the dictionary.
    
    Returns statistics about the operation.
    """
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    stats = {
        'total_headers': 0,
        'by_mode': {},
        'by_engine': {},
        'updated': []
    }
    
    # Add derivation to each header
    for header_name, header_def in data['headers'].items():
        stats['total_headers'] += 1
        
        # Derive the derivation spec
        derivation = classify_header_derivation(header_name, header_def)
        
        # Add it to the header
        header_def['derivation'] = derivation
        
        # Track statistics
        mode = derivation['mode']
        engine = derivation['process']['engine']
        
        stats['by_mode'][mode] = stats['by_mode'].get(mode, 0) + 1
        stats['by_engine'][engine] = stats['by_engine'].get(engine, 0) + 1
        stats['updated'].append(header_name)
    
    # Update metadata
    data['dictionary_version'] = '4.0.0'  # Major version bump for new section
    data['generated_utc'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return stats


def main():
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    
    input_file = repo_root / '2026012816000001_COLUMN_DICTIONARY.json'
    output_file = repo_root / '2026012816000001_COLUMN_DICTIONARY.json.new'
    
    if not input_file.exists():
        print(f"ERROR: Input file not found: {input_file}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Reading from: {input_file}")
    print(f"Writing to: {output_file}")
    print()
    
    stats = add_derivation_to_dictionary(input_file, output_file)
    
    print("=" * 60)
    print("DERIVATION SECTION ADDED SUCCESSFULLY")
    print("=" * 60)
    print(f"Total headers updated: {stats['total_headers']}")
    print()
    
    print("Distribution by derivation mode:")
    for mode, count in sorted(stats['by_mode'].items(), key=lambda x: -x[1]):
        pct = (count / stats['total_headers']) * 100
        print(f"  {mode:20s} {count:3d} ({pct:5.1f}%)")
    print()
    
    print("Distribution by process engine:")
    for engine, count in sorted(stats['by_engine'].items(), key=lambda x: -x[1]):
        pct = (count / stats['total_headers']) * 100
        print(f"  {engine:20s} {count:3d} ({pct:5.1f}%)")
    print()
    
    print("Next steps:")
    print("  1. Review the output file for correctness")
    print("  2. Refine 'INPUT' and 'to_be_specified' entries")
    print("  3. Replace original: mv <new_file> <original_file>")
    print("  4. Create derivation validator that enforces:")
    print("     - mode=DERIVED requires sources in formula")
    print("     - mode=LOOKUP requires registry_ref")
    print("     - mode=TASK_OUTPUT requires task_id + evidence")
    print("     - null_policy=ERROR matches presence.policy=REQUIRED")
    

if __name__ == '__main__':
    main()
