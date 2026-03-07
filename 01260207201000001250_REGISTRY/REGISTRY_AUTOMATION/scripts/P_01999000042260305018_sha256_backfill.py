#!/usr/bin/env python3
"""
SHA256 Backfill Utility

Purpose:
  - Compute sha256 for all registry files missing it
  - Update registry with computed hashes
  - Create backup before modification
  - Log progress for long-running operations

Usage:
  python P_01999000042260305018_sha256_backfill.py --registry PATH [--dry-run]
"""

import json
import hashlib
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 hash of file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

class SHA256Backfiller:
    def __init__(self, registry_path: Path, gov_reg_root: Path):
        self.registry_path = registry_path
        self.gov_reg_root = gov_reg_root
        self.stats = {
            'total': 0,
            'already_hashed': 0,
            'newly_hashed': 0,
            'errors': 0
        }
        self.errors = []
    
    def backfill(self, dry_run: bool = False) -> Dict[str, Any]:
        """Backfill missing sha256 hashes."""
        print(f"Loading registry: {self.registry_path}")
        with open(self.registry_path, encoding='utf-8') as f:
            registry = json.load(f)
        
        files = registry.get('files', [])
        self.stats['total'] = len(files)
        
        print(f"Processing {len(files)} files...")
        print()
        
        for idx, file_rec in enumerate(files):
            if (idx + 1) % 10 == 0:
                print(f"Progress: {idx + 1}/{len(files)} "
                      f"(hashed: {self.stats['newly_hashed']}, "
                      f"errors: {self.stats['errors']})", end='\r')
            
            # Skip if already has sha256
            if file_rec.get('sha256'):
                self.stats['already_hashed'] += 1
                continue
            
            # Compute hash
            rel_path = file_rec.get('relative_path')
            if not rel_path:
                self.errors.append(f"Record {idx} missing relative_path")
                self.stats['errors'] += 1
                continue
            
            file_path = self.gov_reg_root / rel_path
            
            try:
                sha256 = compute_sha256(file_path)
                if not dry_run:
                    file_rec['sha256'] = sha256
                self.stats['newly_hashed'] += 1
            except Exception as e:
                self.errors.append(f"{rel_path}: {e}")
                self.stats['errors'] += 1
        
        print()  # Clear progress line
        print()
        
        if not dry_run and self.stats['newly_hashed'] > 0:
            # Backup original
            backup_path = self.registry_path.parent / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.registry_path.name}"
            print(f"Creating backup: {backup_path}")
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(registry, f, indent=2, ensure_ascii=False)
            
            # Write updated registry
            print(f"Updating registry: {self.registry_path}")
            with open(self.registry_path, 'w', encoding='utf-8') as f:
                json.dump(registry, f, indent=2, ensure_ascii=False)
        
        return self.stats

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='SHA256 Backfill Utility')
    parser.add_argument('--registry', 
                       default='../../01999000042260124503_REGISTRY_file.json',
                       help='Path to registry JSON')
    parser.add_argument('--gov-reg-root',
                       default=r'C:\Users\richg\Gov_Reg',
                       help='Root directory for resolving relative paths')
    parser.add_argument('--dry-run', action='store_true',
                       help='Simulate without modifying registry')
    
    args = parser.parse_args()
    
    # Resolve paths
    script_dir = Path(__file__).parent
    registry_path = (script_dir / args.registry).resolve()
    gov_reg_root = Path(args.gov_reg_root)
    
    if not registry_path.exists():
        print(f"ERROR: Registry not found: {registry_path}", file=sys.stderr)
        return 2
    
    print("=== SHA256 Backfill Utility ===")
    print()
    
    backfiller = SHA256Backfiller(registry_path, gov_reg_root)
    stats = backfiller.backfill(dry_run=args.dry_run)
    
    print("=== Backfill Report ===")
    print(f"Total files: {stats['total']}")
    print(f"Already hashed: {stats['already_hashed']}")
    print(f"Newly hashed: {stats['newly_hashed']}")
    print(f"Errors: {stats['errors']}")
    
    if backfiller.errors:
        print()
        print(f"Errors encountered ({len(backfiller.errors)}):")
        for err in backfiller.errors[:10]:
            print(f"  • {err}")
        if len(backfiller.errors) > 10:
            print(f"  ... and {len(backfiller.errors) - 10} more")
    
    if args.dry_run:
        print()
        print("[DRY RUN - no changes made]")
    elif stats['newly_hashed'] > 0:
        print()
        print(f"✓ Successfully backfilled {stats['newly_hashed']} sha256 hashes")
    
    return 0 if stats['errors'] == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
