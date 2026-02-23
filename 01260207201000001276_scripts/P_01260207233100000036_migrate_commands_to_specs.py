#!/usr/bin/env python3
"""
Command Spec Migration Tool

Migrates string commands to structured command_spec format.
Usage: python scripts/migrate_commands_to_specs.py --sections-dir sections/
"""

import json
import re
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple


def parse_command_string(cmd: str) -> Dict[str, Any]:
    """
    Parse a command string into {exe, args} format.
    Handles common patterns like:
    - "python script.py --flag value"
    - "pytest tests/ -v"
    - "git --no-pager status"
    """
    # Split command preserving quoted strings
    parts = re.findall(r'(?:[^\s"]|"(?:\\.|[^"])*")+', cmd)
    
    if not parts:
        return {"exe": "echo", "args": ["ERROR: empty command"]}
    
    exe = parts[0]
    args = parts[1:] if len(parts) > 1 else []
    
    # Clean up quoted args
    args = [arg.strip('"') for arg in args]
    
    return {
        "exe": exe,
        "args": args,
        "timeout_seconds": 600,  # Default timeout
        "expected_exit_codes": [0]
    }


def migrate_section_commands(section_path: Path, dry_run: bool = False) -> Tuple[int, List[str]]:
    """
    Migrate all command strings in a section to structured format.
    Returns: (migrations_count, errors)
    """
    with open(section_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    migrations = 0
    errors = []
    
    def migrate_recursive(obj: Any, path: str = "") -> Any:
        """Recursively find and migrate command fields"""
        nonlocal migrations, errors
        
        if isinstance(obj, dict):
            # Check if this dict has a 'command' field that's a string
            if 'command' in obj and isinstance(obj['command'], str):
                old_command = obj['command']
                try:
                    new_command = parse_command_string(old_command)
                    obj['command'] = new_command
                    migrations += 1
                    print(f"  ✓ Migrated: {path}.command")
                    print(f"    Old: {old_command[:60]}...")
                    print(f"    New: {new_command['exe']} {' '.join(new_command['args'][:3])}...")
                except Exception as e:
                    errors.append(f"{path}.command: {str(e)}")
            
            # Recurse into dict values
            for key, value in obj.items():
                obj[key] = migrate_recursive(value, f"{path}.{key}" if path else key)
        
        elif isinstance(obj, list):
            # Recurse into list items
            for i, item in enumerate(obj):
                obj[i] = migrate_recursive(item, f"{path}[{i}]")
        
        return obj
    
    # Migrate
    data = migrate_recursive(data)
    
    # Write back if not dry run
    if not dry_run and migrations > 0:
        # Backup original
        backup_path = section_path.with_suffix('.json.backup')
        section_path.rename(backup_path)
        
        # Write migrated version
        with open(section_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"  → Backed up to: {backup_path.name}")
        print(f"  → Wrote migrated: {section_path.name}")
    
    return migrations, errors


def main():
    parser = argparse.ArgumentParser(description="Migrate string commands to structured command_spec format")
    parser.add_argument('--sections-dir', type=str, default='sections/', help="Path to sections directory")
    parser.add_argument('--dry-run', action='store_true', help="Preview changes without writing")
    parser.add_argument('--force', action='store_true', help="Overwrite existing backups")
    
    args = parser.parse_args()
    
    sections_dir = Path(args.sections_dir)
    
    if not sections_dir.exists():
        print(f"Error: Directory not found: {sections_dir}", file=sys.stderr)
        sys.exit(2)
    
    # Find sections with violations (from PH-02 evidence)
    evidence_path = Path('.state/evidence/PH-02/command_spec_validation.json')
    if evidence_path.exists():
        with open(evidence_path, 'r') as f:
            evidence = json.load(f)
        
        # Get unique files with violations
        files_with_violations = set(v['file'] for v in evidence.get('violations', []))
        section_files = [sections_dir / f for f in files_with_violations]
    else:
        # Fallback: check all sections
        section_files = list(sections_dir.glob('sec_*.json'))
    
    total_migrations = 0
    total_errors = []
    
    print(f"\n{'=' * 60}")
    print(f"Command Spec Migration Tool")
    print(f"{'=' * 60}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE MIGRATION'}")
    print(f"Sections to check: {len(section_files)}")
    print(f"{'=' * 60}\n")
    
    for section_file in sorted(section_files):
        if not section_file.exists():
            continue
        
        print(f"\n📄 {section_file.name}")
        print(f"{'-' * 60}")
        
        migrations, errors = migrate_section_commands(section_file, dry_run=args.dry_run)
        
        total_migrations += migrations
        total_errors.extend(errors)
        
        if migrations == 0:
            print("  No commands to migrate")
        
        if errors:
            print(f"  ⚠️  Errors: {len(errors)}")
            for error in errors:
                print(f"    - {error}")
    
    print(f"\n{'=' * 60}")
    print(f"Summary")
    print(f"{'=' * 60}")
    print(f"Total migrations: {total_migrations}")
    print(f"Total errors: {len(total_errors)}")
    
    if args.dry_run:
        print(f"\n⚠️  DRY RUN - No files were modified")
        print(f"Run without --dry-run to apply changes")
    else:
        print(f"\n✅ Migration complete!")
        print(f"Backups saved as *.json.backup")
    
    sys.exit(0 if len(total_errors) == 0 else 1)


if __name__ == "__main__":
    main()
