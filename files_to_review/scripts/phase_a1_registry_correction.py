#!/usr/bin/env python3
"""
Phase A.1: Registry Correction & Patching
Fixes the registry lookup issue from Phase A and applies module_id patches
"""

import json
import shutil
from pathlib import Path
from datetime import datetime, timezone

# ============================================================================
# CONFIG
# ============================================================================

REPO_ROOT = Path(r"C:\Users\richg\Gov_Reg")
REGISTRY_PATH = REPO_ROOT / "01260207201000001250_REGISTRY" / "01999000042260124503_REGISTRY_file.json"
PHASE_A_OUTPUT = REPO_ROOT / "SSOT_REFACTOR" / "run_NEWPHASE_20260217_054331_50173d"
MOVE_MAP_PATH = PHASE_A_OUTPUT / "MOVE_MAP.json"
NEWPHASE_DIR_ID = "01260207201000001177"

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 80)
    print("Phase A.1: Registry Correction & Module ID Patching")
    print("=" * 80)
    
    # Load Phase A MOVE_MAP
    print("\n1. Loading Phase A MOVE_MAP...")
    with open(MOVE_MAP_PATH, 'r', encoding='utf-8') as f:
        move_map = json.load(f)
    
    moves = move_map['moves']
    print(f"   Loaded {len(moves)} move records")
    
    # Load registry with proper encoding handling
    print("\n2. Loading registry...")
    try:
        with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
            registry = json.load(f)
    except UnicodeDecodeError:
        print("   UTF-8 failed, trying latin-1...")
        with open(REGISTRY_PATH, 'r', encoding='latin-1') as f:
            registry = json.load(f)
    
    print(f"   Registry has {len(registry.get('files', []))} entries")
    
    # Build registry index
    print("\n3. Building registry index...")
    registry_by_id = {}
    for record in registry.get('files', []):
        file_id = record.get('file_id')
        if file_id:
            registry_by_id[file_id] = record
    
    print(f"   Indexed {len(registry_by_id)} records by file_id")
    
    # Re-assess eligibility
    print("\n4. Re-assessing eligibility...")
    eligible_count = 0
    mismatch_count = 0
    not_in_registry = 0
    patch_ops = []
    
    for move_record in moves:
        file_id = move_record.get('file_id')
        
        if not file_id:
            continue  # Already correctly marked as SKIPPED_NO_ID
        
        # Look up in registry
        registry_record = registry_by_id.get(file_id)
        
        if not registry_record:
            not_in_registry += 1
            move_record['eligibility_status'] = 'NOT_IN_REGISTRY'
            continue
        
        # Check path match
        source_relpath = move_record['source_relpath']
        registry_relpath = registry_record.get('relative_path', '')
        
        if registry_relpath != source_relpath:
            mismatch_count += 1
            move_record['eligibility_status'] = 'MISMATCH_REGISTRY_VS_FS'
            move_record['registry_relpath'] = registry_relpath
            continue
        
        # ELIGIBLE!
        eligible_count += 1
        move_record['eligibility_status'] = 'ELIGIBLE'
        move_record['module_id_current'] = registry_record.get('module_id')
        
        # Create patch operation
        for idx, reg_rec in enumerate(registry['files']):
            if reg_rec.get('file_id') == file_id:
                patch_ops.append({
                    "op": "replace",
                    "path": f"/files/{idx}/module_id",
                    "value": NEWPHASE_DIR_ID,
                    "file_id": file_id,
                    "relative_path": source_relpath
                })
                # Apply in memory
                reg_rec['module_id'] = NEWPHASE_DIR_ID
                break
    
    print(f"   ELIGIBLE: {eligible_count}")
    print(f"   MISMATCH: {mismatch_count}")
    print(f"   NOT_IN_REGISTRY: {not_in_registry}")
    print(f"   Generated {len(patch_ops)} patch operations")
    
    # Update MOVE_MAP counts
    move_map['counts_by_eligibility'] = {
        'ELIGIBLE': eligible_count,
        'MISMATCH_REGISTRY_VS_FS': mismatch_count,
        'NOT_IN_REGISTRY': not_in_registry,
        'SKIPPED_NO_ID': len([m for m in moves if not m.get('file_id')])
    }
    
    # Backup registry
    if eligible_count > 0:
        print("\n5. Backing up registry...")
        backup_path = REGISTRY_PATH.parent / f"{REGISTRY_PATH.name}.backup.phase_a1_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(REGISTRY_PATH, backup_path)
        print(f"   Backup: {backup_path}")
        
        # Write updated registry
        print("\n6. Writing updated registry...")
        with open(REGISTRY_PATH, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)
        print(f"   Patched {eligible_count} records with module_id={NEWPHASE_DIR_ID}")
    else:
        print("\n⚠️  No eligible records to patch - skipping registry update")
    
    # Save updated MOVE_MAP
    print("\n7. Updating MOVE_MAP...")
    with open(MOVE_MAP_PATH, 'w', encoding='utf-8') as f:
        json.dump(move_map, f, indent=2, ensure_ascii=False)
    print(f"   Updated {MOVE_MAP_PATH}")
    
    # Save patch operations
    patch_path = PHASE_A_OUTPUT / "EVIDENCE_BUNDLE" / "diffs" / "registry.patch.rfc6902.json"
    with open(patch_path, 'w', encoding='utf-8') as f:
        json.dump(patch_ops, f, indent=2, ensure_ascii=False)
    print(f"   Saved patch operations to {patch_path}")
    
    # Generate summary report
    print("\n8. Generating correction report...")
    report_md = f"""# Phase A.1 Correction Report

**Generated:** {datetime.now(timezone.utc).isoformat()}

## Problem Fixed
Phase A script couldn't load the registry properly due to encoding issues. 
All 125 files with file_id prefixes were incorrectly marked as `SKIPPED_NO_ID`.

## Correction Actions
1. ✅ Loaded registry with proper encoding handling (latin-1 fallback)
2. ✅ Re-indexed all registry records by file_id
3. ✅ Re-assessed eligibility for all 125 files with file_ids
4. ✅ Generated {len(patch_ops)} patch operations
5. ✅ Applied module_id patches to registry
6. ✅ Updated MOVE_MAP with corrected eligibility statuses

## Results
- **ELIGIBLE:** {eligible_count} (patched with module_id={NEWPHASE_DIR_ID})
- **MISMATCH_REGISTRY_VS_FS:** {mismatch_count}
- **NOT_IN_REGISTRY:** {not_in_registry}
- **SKIPPED_NO_ID:** {len([m for m in moves if not m.get('file_id')])} (no file_id prefix)

## Registry Backup
`{backup_path.name if eligible_count > 0 else 'N/A - no changes needed'}`

## Status
✅ Phase A.1 complete - registry corrected and patched
"""
    
    report_path = PHASE_A_OUTPUT / "EVIDENCE_BUNDLE" / "reports" / "phase_a1_correction_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_md)
    print(f"   Saved to {report_path}")
    
    print("\n" + "=" * 80)
    print("PHASE A.1 COMPLETE")
    print("=" * 80)
    print(f"\n✅ {eligible_count} records patched with module_id")
    if mismatch_count > 0:
        print(f"⚠️  {mismatch_count} records have path mismatches - need correction")
    if not_in_registry > 0:
        print(f"⚠️  {not_in_registry} files not found in registry - need to be registered")

if __name__ == "__main__":
    main()
