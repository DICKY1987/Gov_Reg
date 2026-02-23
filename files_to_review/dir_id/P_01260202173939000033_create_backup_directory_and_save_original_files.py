#!/usr/bin/env python3
"""
Fix file_id format issues system-wide

This script:
1. Corrects file_id values in the unified registry
2. Updates all anchor_file_id and reference fields
3. Searches and replaces IDs in all documentation files
4. Generates an audit report

Work ID: WORK-MAPP-PY-001 (Registry Repair)
Created: 2026-02-02
"""

import json
import re
import os
from pathlib import Path
from datetime import datetime
import shutil

# Configuration
REGISTRY_ROOT = Path(r"C:\Users\richg\Gov_Reg\REGISTRY")
REGISTRY_FILE = REGISTRY_ROOT / "01999000042260124503_governance_registry_unified.json"
BACKUP_DIR = REGISTRY_ROOT / "backups" / f"file_id_correction_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# ID Patterns
OLD_PREFIX = "001999000042260124"
NEW_PREFIX = "01999000042260124"
OLD_PATTERN = re.compile(r'\b00(1999000042260124)(\d{2})\b')


def create_backup():
    """Create backup directory and save original files."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ Backup directory: {BACKUP_DIR}")
    return BACKUP_DIR


def build_id_mapping(registry_data):
    """Build mapping of old IDs to new IDs."""
    mapping = {}

    for file_record in registry_data.get("files", []):
        old_id = file_record.get("file_id")
        if old_id and old_id.startswith(OLD_PREFIX):
            # Extract suffix (last 2 digits) and pad to 3 digits
            suffix = old_id[-2:].zfill(3)
            new_id = f"{NEW_PREFIX}{suffix}"
            mapping[old_id] = new_id

    print(f"\n📋 ID Mapping ({len(mapping)} IDs):")
    for old, new in sorted(mapping.items())[:5]:
        print(f"  {old} → {new}")
    if len(mapping) > 5:
        print(f"  ... and {len(mapping) - 5} more")

    return mapping


def fix_registry_file(registry_path, mapping, backup_dir):
    """Fix all file_id references in the registry JSON."""
    print(f"\n🔧 Fixing registry: {registry_path.name}")

    # Backup original
    backup_path = backup_dir / registry_path.name
    shutil.copy2(registry_path, backup_path)
    print(f"  ✓ Backed up to: {backup_path.name}")

    # Load registry
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = json.load(f)

    fixes = 0

    # Fix file_id in file records
    for file_record in registry.get("files", []):
        old_id = file_record.get("file_id")
        if old_id in mapping:
            file_record["file_id"] = mapping[old_id]
            fixes += 1

        # Fix anchor_file_id references
        old_anchor = file_record.get("anchor_file_id")
        if old_anchor in mapping:
            file_record["anchor_file_id"] = mapping[old_anchor]
            fixes += 1

        # Fix depends_on_file_ids arrays
        if "depends_on_file_ids" in file_record and file_record["depends_on_file_ids"]:
            file_record["depends_on_file_ids"] = [
                mapping.get(fid, fid) for fid in file_record["depends_on_file_ids"]
            ]

        # Fix enforced_by_file_ids arrays
        if "enforced_by_file_ids" in file_record and file_record["enforced_by_file_ids"]:
            file_record["enforced_by_file_ids"] = [
                mapping.get(fid, fid) for fid in file_record["enforced_by_file_ids"]
            ]

        # Fix test_file_ids arrays
        if "test_file_ids" in file_record and file_record["test_file_ids"]:
            file_record["test_file_ids"] = [
                mapping.get(fid, fid) for fid in file_record["test_file_ids"]
            ]

    # Write corrected registry
    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    print(f"  ✓ Fixed {fixes} ID references")
    return fixes


def fix_text_file(file_path, mapping, backup_dir):
    """Fix file_id references in text/markdown/yaml files."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        fixes = 0

        # Replace each old ID with new ID
        for old_id, new_id in mapping.items():
            if old_id in content:
                content = content.replace(old_id, new_id)
                fixes += 1

        if fixes > 0:
            # Backup original
            rel_path = file_path.relative_to(REGISTRY_ROOT)
            backup_path = backup_dir / rel_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, backup_path)

            # Write fixed content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"  ✓ {file_path.name}: {fixes} IDs fixed")
            return fixes

    except Exception as e:
        print(f"  ⚠ {file_path.name}: {e}")

    return 0


def scan_and_fix_all_files(mapping, backup_dir):
    """Scan all text files in REGISTRY and fix ID references."""
    print(f"\n🔍 Scanning all documentation files...")

    extensions = {'.json', '.md', '.txt', '.yaml', '.yml', '.py'}
    total_fixes = 0
    files_modified = 0

    for file_path in REGISTRY_ROOT.rglob('*'):
        if file_path.is_file() and file_path.suffix in extensions:
            # Skip backup directories
            if 'backup' in str(file_path).lower():
                continue

            fixes = fix_text_file(file_path, mapping, backup_dir)
            if fixes > 0:
                total_fixes += fixes
                files_modified += 1

    print(f"\n  ✓ Modified {files_modified} files")
    print(f"  ✓ Total ID corrections: {total_fixes}")
    return files_modified, total_fixes


def generate_audit_report(mapping, backup_dir, stats):
    """Generate audit report of all changes."""
    report_path = backup_dir / "AUDIT_REPORT.md"

    report = f"""# File ID Correction Audit Report

**Date**: {datetime.now().isoformat()}
**Work ID**: WORK-MAPP-PY-001 (Registry Repair)

## Summary

- **IDs Corrected**: {len(mapping)}
- **Files Modified**: {stats['files_modified']}
- **Total Replacements**: {stats['total_fixes']}

## ID Mappings

| Old ID | New ID |
|--------|--------|
"""

    for old_id, new_id in sorted(mapping.items()):
        report += f"| `{old_id}` | `{new_id}` |\n"

    report += f"""
## Files Modified

See backup directory for original versions:
`{backup_dir}`

## Validation

Run validation gate:
```bash
python scripts/validate_file_id_format.py
```

Expected result: All file_id values match pattern `^01999000042260124\\d{{3}}$`

## Rollback

If needed, restore from backup:
```bash
cp {backup_dir}/* {REGISTRY_ROOT}/
```
"""

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n📄 Audit report: {report_path}")
    return report_path


def main():
    """Main execution."""
    print("=" * 70)
    print("FILE_ID PREFIX CORRECTION SCRIPT")
    print("=" * 70)

    # Create backup
    backup_dir = create_backup()

    # Load registry and build mapping
    with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
        registry = json.load(f)

    mapping = build_id_mapping(registry)

    if not mapping:
        print("\n✓ No corrections needed. All file_ids are correct.")
        return

    # Save mapping
    mapping_path = backup_dir / "id_mapping.json"
    with open(mapping_path, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, indent=2)
    print(f"  ✓ Mapping saved: {mapping_path.name}")

    # Fix registry
    registry_fixes = fix_registry_file(REGISTRY_FILE, mapping, backup_dir)

    # Fix all other files
    files_modified, total_fixes = scan_and_fix_all_files(mapping, backup_dir)

    # Generate audit report
    stats = {
        'files_modified': files_modified + 1,  # +1 for registry
        'total_fixes': total_fixes + registry_fixes
    }
    generate_audit_report(mapping, backup_dir, stats)

    print("\n" + "=" * 70)
    print("✅ FILE_ID CORRECTION COMPLETE")
    print("=" * 70)
    print(f"\n📁 Backup location: {backup_dir}")
    print(f"📋 IDs corrected: {len(mapping)}")
    print(f"📄 Files modified: {stats['files_modified']}")
    print(f"\n⚠️  NEXT STEPS:")
    print("   1. Run validation: python scripts/validate_file_id_format.py")
    print("   2. Review audit report in backup directory")
    print("   3. Commit changes with message: 'fix: Correct file_id prefix per SSOT (WORK-MAPP-PY-001)'")


if __name__ == "__main__":
    main()
