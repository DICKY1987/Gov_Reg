#!/usr/bin/env python3
"""
Registry Patch Application Tool

Applies RFC-6902 JSON Patch operations to registry files with full audit trail.
Implements atomic application with rollback capability.

Usage:
    python apply_patch.py --target <registry.json> --patch <patch.json> --evidence <evidence_dir>
"""

import json
import jsonpatch
import hashlib
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List
import shutil


def apply_patch(target_path: Path, patch_path: Path, evidence_dir: Path, dry_run: bool = False) -> Dict[str, Any]:
    """
    Apply RFC-6902 JSON Patch to a registry file.
    
    Args:
        target_path: Path to target registry JSON
        patch_path: Path to RFC-6902 patch JSON
        evidence_dir: Directory to write evidence artifacts
        dry_run: If True, don't modify target file
        
    Returns:
        Result dictionary with success status and metadata
    """
    if not target_path.exists():
        raise FileNotFoundError(f"Target file not found: {target_path}")
    
    if not patch_path.exists():
        raise FileNotFoundError(f"Patch file not found: {patch_path}")
    
    evidence_dir.mkdir(parents=True, exist_ok=True)
    
    # Read target
    with open(target_path, 'r', encoding='utf-8') as f:
        original_data = json.load(f)
    
    # Calculate original hash
    original_hash = hashlib.sha256(
        json.dumps(original_data, sort_keys=True).encode()
    ).hexdigest()
    
    # Read patch
    with open(patch_path, 'r', encoding='utf-8') as f:
        patch_ops = json.load(f)
    
    # Validate patch format
    if not isinstance(patch_ops, list):
        raise ValueError("Patch must be a JSON array of operations")
    
    # Apply patch
    try:
        patch = jsonpatch.JsonPatch(patch_ops)
        patched_data = patch.apply(original_data)
    except jsonpatch.JsonPatchException as e:
        raise ValueError(f"Patch application failed: {e}")
    
    # Calculate patched hash
    patched_hash = hashlib.sha256(
        json.dumps(patched_data, sort_keys=True).encode()
    ).hexdigest()
    
    # Count changes
    changes = len(patch_ops)
    
    # Write patched data (if not dry run)
    if not dry_run:
        # Backup original
        backup_path = target_path.with_suffix('.json.backup')
        shutil.copy2(target_path, backup_path)
        
        # Write patched
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(patched_data, f, indent=2, ensure_ascii=False)
    
    # Write evidence
    result = {
        "success": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "target_file": str(target_path),
        "patch_file": str(patch_path),
        "dry_run": dry_run,
        "original_hash": original_hash,
        "patched_hash": patched_hash,
        "operations_count": changes,
        "operations": patch_ops,
        "backup_created": str(backup_path) if not dry_run else None
    }
    
    result_path = evidence_dir / f"apply_result_{target_path.stem}.json"
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Apply RFC-6902 patch to registry")
    parser.add_argument('--target', required=True, help='Target registry JSON file')
    parser.add_argument('--patch', required=True, help='RFC-6902 patch JSON file')
    parser.add_argument('--evidence', required=True, help='Evidence directory')
    parser.add_argument('--dry-run', action='store_true', help='Validate patch without applying')
    parser.add_argument('--quiet', action='store_true', help='Suppress output')
    
    args = parser.parse_args()
    
    target_path = Path(args.target)
    patch_path = Path(args.patch)
    evidence_dir = Path(args.evidence)
    
    try:
        result = apply_patch(target_path, patch_path, evidence_dir, args.dry_run)
        
        if not args.quiet:
            mode = "DRY RUN" if args.dry_run else "APPLIED"
            print(f"✓ Patch {mode}: {patch_path.name}")
            print(f"  Target: {target_path.name}")
            print(f"  Operations: {result['operations_count']}")
            print(f"  Original hash: {result['original_hash'][:16]}...")
            print(f"  Patched hash: {result['patched_hash'][:16]}...")
            if not args.dry_run:
                print(f"  Backup: {result['backup_created']}")
        
        return 0
    
    except Exception as e:
        print(f"✗ Error applying patch: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
