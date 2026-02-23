#!/usr/bin/env python3
"""
Registry Snapshot Diff Tool

Compares two registry snapshots and generates detailed diff summary.
Produces deterministic comparison excluding timestamps.

Usage:
    python diff_snapshots.py --before <before.json> --after <after.json> --out <diff.json>
"""

import json
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Set


def deep_diff(before: Any, after: Any, path: str = "") -> List[Dict[str, Any]]:
    """
    Recursively compare two data structures and return differences.
    
    Args:
        before: Original data
        after: Modified data
        path: JSONPath to current location
        
    Returns:
        List of difference dictionaries
    """
    diffs = []
    
    if type(before) != type(after):
        diffs.append({
            "path": path,
            "change_type": "type_changed",
            "before_type": type(before).__name__,
            "after_type": type(after).__name__
        })
        return diffs
    
    if isinstance(before, dict):
        # Keys added
        for key in after.keys() - before.keys():
            diffs.append({
                "path": f"{path}/{key}",
                "change_type": "added",
                "value": after[key]
            })
        
        # Keys removed
        for key in before.keys() - after.keys():
            diffs.append({
                "path": f"{path}/{key}",
                "change_type": "removed",
                "value": before[key]
            })
        
        # Keys changed
        for key in before.keys() & after.keys():
            diffs.extend(deep_diff(before[key], after[key], f"{path}/{key}"))
    
    elif isinstance(before, list):
        if len(before) != len(after):
            diffs.append({
                "path": path,
                "change_type": "length_changed",
                "before_length": len(before),
                "after_length": len(after)
            })
        
        # Compare elements
        for i, (b_item, a_item) in enumerate(zip(before, after)):
            diffs.extend(deep_diff(b_item, a_item, f"{path}[{i}]"))
    
    else:
        # Primitive comparison
        if before != after:
            diffs.append({
                "path": path,
                "change_type": "value_changed",
                "before": before,
                "after": after
            })
    
    return diffs


def diff_snapshots(before_path: Path, after_path: Path, output_path: Path) -> Dict[str, Any]:
    """
    Compare two registry snapshots and generate diff summary.
    
    Args:
        before_path: Path to before snapshot
        after_path: Path to after snapshot
        output_path: Path to write diff summary
        
    Returns:
        Diff summary dictionary
    """
    if not before_path.exists():
        raise FileNotFoundError(f"Before snapshot not found: {before_path}")
    
    if not after_path.exists():
        raise FileNotFoundError(f"After snapshot not found: {after_path}")
    
    # Read snapshots
    with open(before_path, 'r', encoding='utf-8') as f:
        before_snapshot = json.load(f)
    
    with open(after_path, 'r', encoding='utf-8') as f:
        after_snapshot = json.load(f)
    
    # Extract registry data (ignore snapshot metadata)
    before_data = before_snapshot.get("registry_data", before_snapshot)
    after_data = after_snapshot.get("registry_data", after_snapshot)
    
    # Calculate differences
    differences = deep_diff(before_data, after_data)
    
    # Categorize changes
    added_count = sum(1 for d in differences if d['change_type'] == 'added')
    removed_count = sum(1 for d in differences if d['change_type'] == 'removed')
    changed_count = sum(1 for d in differences if d['change_type'] == 'value_changed')
    
    # Build summary
    summary = {
        "diff_metadata": {
            "before_snapshot": str(before_path),
            "after_snapshot": str(after_path),
            "diff_time": datetime.now(timezone.utc).isoformat(),
            "before_hash": before_snapshot.get("snapshot_metadata", {}).get("file_sha256", "unknown"),
            "after_hash": after_snapshot.get("snapshot_metadata", {}).get("file_sha256", "unknown"),
            "diff_version": "1.0.0"
        },
        "summary": {
            "total_changes": len(differences),
            "added": added_count,
            "removed": removed_count,
            "changed": changed_count,
            "has_changes": len(differences) > 0
        },
        "differences": differences[:1000]  # Limit to first 1000 for readability
    }
    
    # Write diff
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    return summary


def main():
    parser = argparse.ArgumentParser(description="Diff two registry snapshots")
    parser.add_argument('--before', required=True, help='Before snapshot JSON')
    parser.add_argument('--after', required=True, help='After snapshot JSON')
    parser.add_argument('--out', required=True, help='Output diff summary JSON')
    parser.add_argument('--quiet', action='store_true', help='Suppress output')
    
    args = parser.parse_args()
    
    before_path = Path(args.before)
    after_path = Path(args.after)
    output_path = Path(args.out)
    
    try:
        summary = diff_snapshots(before_path, after_path, output_path)
        
        if not args.quiet:
            print(f"✓ Diff summary created: {output_path}")
            print(f"  Total changes: {summary['summary']['total_changes']}")
            print(f"  Added: {summary['summary']['added']}")
            print(f"  Removed: {summary['summary']['removed']}")
            print(f"  Changed: {summary['summary']['changed']}")
        
        return 0
    
    except Exception as e:
        print(f"✗ Error creating diff: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
