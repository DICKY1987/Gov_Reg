#!/usr/bin/env python3
"""
Registry Snapshot Tool

Creates immutable snapshots of registry files for before/after comparison.
Snapshots include metadata (timestamp, file hash, record counts) for audit trail.

Usage:
    python snapshot.py --in <registry.json> --out <snapshot.json>
"""

import json
import hashlib
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any


def create_snapshot(registry_path: Path, output_path: Path) -> Dict[str, Any]:
    """
    Create a snapshot of a registry file.
    
    Args:
        registry_path: Path to registry JSON file
        output_path: Path to write snapshot
        
    Returns:
        Snapshot metadata dict
    """
    if not registry_path.exists():
        raise FileNotFoundError(f"Registry file not found: {registry_path}")
    
    # Read registry
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry_data = json.load(f)
    
    # Calculate file hash
    with open(registry_path, 'rb') as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    
    # Gather metadata
    snapshot = {
        "snapshot_metadata": {
            "source_file": str(registry_path),
            "snapshot_time": datetime.now(timezone.utc).isoformat(),
            "file_size_bytes": registry_path.stat().st_size,
            "file_sha256": file_hash,
            "record_count": len(registry_data.get("entities", [])) if isinstance(registry_data.get("entities"), list) else 0,
            "snapshot_version": "1.0.0"
        },
        "registry_data": registry_data
    }
    
    # Write snapshot
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)
    
    return snapshot["snapshot_metadata"]


def main():
    parser = argparse.ArgumentParser(description="Create registry snapshot")
    parser.add_argument('--in', dest='input', required=True, help='Input registry JSON file')
    parser.add_argument('--out', dest='output', required=True, help='Output snapshot JSON file')
    parser.add_argument('--quiet', action='store_true', help='Suppress output')
    
    args = parser.parse_args()
    
    registry_path = Path(args.input)
    output_path = Path(args.output)
    
    try:
        metadata = create_snapshot(registry_path, output_path)
        
        if not args.quiet:
            print(f"✓ Snapshot created: {output_path}")
            print(f"  Source: {metadata['source_file']}")
            print(f"  Records: {metadata['record_count']}")
            print(f"  SHA256: {metadata['file_sha256'][:16]}...")
            print(f"  Size: {metadata['file_size_bytes']} bytes")
        
        return 0
    
    except Exception as e:
        print(f"✗ Error creating snapshot: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
