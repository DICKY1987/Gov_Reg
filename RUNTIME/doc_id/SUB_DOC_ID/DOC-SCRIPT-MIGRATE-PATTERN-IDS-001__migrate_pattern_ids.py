#!/usr/bin/env python3
# DOC_LINK: DOC-SCRIPT-MIGRATE-PATTERN-IDS-001
# DOC_ID: DOC-SCRIPT-MIGRATE-PATTERN-IDS-001
"""
doc_id: DOC-SCRIPT-MIGRATE-PATTERN-IDS-001
Migration script for pattern_id format update
Migrates from PATTERN-{CAT}-{SEQ} to PATTERN-{CAT}-{NAME}-{SEQ}
"""

import os
import sys
import yaml
import shutil
import argparse
from pathlib import Path
from datetime import datetime
import re

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent
MIGRATION_MAP = SCRIPT_DIR / "pattern_id_migration_map.yaml"
REGISTRY_FILE = SCRIPT_DIR / "pattern_id" / "5_REGISTRY_DATA" / "PAT_ID_REGISTRY.yaml"
BACKUP_DIR = SCRIPT_DIR / ".backups" / "migration"

def load_migration_map():
    """Load the migration mapping file"""
    with open(MIGRATION_MAP, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def backup_files():
    """Create backups of all files to be modified"""
    print("\n=== Creating Backups ===")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / timestamp
    backup_path.mkdir(parents=True, exist_ok=True)
    
    # Backup registry
    shutil.copy2(REGISTRY_FILE, backup_path / "PAT_ID_REGISTRY.yaml")
    print(f"✓ Backed up registry to {backup_path}")
    
    return backup_path

def find_references(old_id):
    """Find all files containing references to the old ID"""
    references = []
    search_dirs = [
        REPO_ROOT / "RUNTIME",
        REPO_ROOT / "WORKFLOWS",
        REPO_ROOT / "REFERENCE",
        REPO_ROOT / "scripts",
    ]
    
    pattern = re.escape(old_id)
    
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
            
        for file_path in search_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix in ['.py', '.yaml', '.yml', '.md', '.txt', '.json', '.ps1', '.bat']:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if re.search(pattern, content):
                            references.append(file_path)
                except Exception as e:
                    pass
    
    return references

def scan_all_references(mappings):
    """Scan for all references to pattern IDs"""
    print("\n=== Scanning for References ===")
    all_references = {}
    
    for mapping in mappings:
        old_id = mapping['old_id']
        print(f"Scanning for {old_id}...")
        refs = find_references(old_id)
        if refs:
            all_references[old_id] = refs
            print(f"  Found {len(refs)} references")
    
    return all_references

def update_registry(mappings, dry_run=True):
    """Update the registry file with new IDs"""
    print("\n=== Updating Registry ===")
    
    with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
        registry = yaml.safe_load(f)
    
    # Update each pattern entry
    for pattern in registry.get('patterns', []):
        old_id = pattern.get('pattern_id')
        
        # Find mapping
        mapping = next((m for m in mappings if m['old_id'] == old_id), None)
        if mapping:
            print(f"  {old_id} → {mapping['new_id']}")
            if not dry_run:
                pattern['pattern_id'] = mapping['new_id']
    
    # Update metadata
    if not dry_run:
        registry['meta']['updated_utc'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        
        with open(REGISTRY_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(registry, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        print("✓ Registry updated")
    else:
        print("(dry-run: no changes made)")

def update_references(references, mappings, dry_run=True):
    """Update all references in files"""
    print("\n=== Updating References ===")
    
    for old_id, files in references.items():
        mapping = next((m for m in mappings if m['old_id'] == old_id), None)
        if not mapping:
            continue
            
        new_id = mapping['new_id']
        print(f"\n{old_id} → {new_id}")
        
        for file_path in files:
            print(f"  {file_path.relative_to(REPO_ROOT)}")
            
            if not dry_run:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Replace old ID with new ID
                    updated_content = content.replace(old_id, new_id)
                    
                    if content != updated_content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(updated_content)
                        print(f"    ✓ Updated")
                except Exception as e:
                    print(f"    ✗ Error: {e}")

def rollback(backup_path):
    """Rollback to backup"""
    print(f"\n=== Rolling Back from {backup_path} ===")
    
    backup_registry = backup_path / "PAT_ID_REGISTRY.yaml"
    if backup_registry.exists():
        shutil.copy2(backup_registry, REGISTRY_FILE)
        print("✓ Registry restored")
    
    print("✓ Rollback complete")

def main():
    parser = argparse.ArgumentParser(description='Migrate pattern_id format')
    parser.add_argument('--execute', action='store_true', help='Execute migration (default is dry-run)')
    parser.add_argument('--rollback', type=str, help='Rollback to backup (provide backup timestamp)')
    args = parser.parse_args()
    
    if args.rollback:
        backup_path = BACKUP_DIR / args.rollback
        if not backup_path.exists():
            print(f"Error: Backup not found at {backup_path}")
            sys.exit(1)
        rollback(backup_path)
        return
    
    dry_run = not args.execute
    mode = "DRY-RUN" if dry_run else "EXECUTION"
    
    print(f"\n{'='*60}")
    print(f"PATTERN_ID MIGRATION - {mode}")
    print(f"{'='*60}")
    
    # Load migration map
    migration_data = load_migration_map()
    mappings = migration_data['mappings']
    
    print(f"\nMigrating {len(mappings)} pattern IDs")
    print(f"Format: {migration_data['format_change']['old']} → {migration_data['format_change']['new']}")
    
    # Create backup (even for dry-run for safety)
    backup_path = backup_files()
    
    # Scan for references
    references = scan_all_references(mappings)
    
    print(f"\n=== Summary ===")
    print(f"Total IDs to migrate: {len(mappings)}")
    print(f"Total files with references: {sum(len(refs) for refs in references.values())}")
    
    if dry_run:
        print("\n⚠️  DRY-RUN MODE - No changes will be made")
        print("Run with --execute to perform migration")
    else:
        print("\n⚠️  EXECUTION MODE - Changes will be made!")
        response = input("\nProceed with migration? (yes/no): ")
        if response.lower() != 'yes':
            print("Migration cancelled")
            return
    
    # Perform migration
    update_registry(mappings, dry_run)
    update_references(references, mappings, dry_run)
    
    print("\n" + "="*60)
    if dry_run:
        print("DRY-RUN COMPLETE")
        print(f"Backup saved at: {backup_path}")
        print("\nTo execute: python migrate_pattern_ids.py --execute")
    else:
        print("MIGRATION COMPLETE")
        print(f"Backup saved at: {backup_path}")
        print(f"To rollback: python migrate_pattern_ids.py --rollback {backup_path.name}")
    print("="*60)

if __name__ == '__main__':
    main()
