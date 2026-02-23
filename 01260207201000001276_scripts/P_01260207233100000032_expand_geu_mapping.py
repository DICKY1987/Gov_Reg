#!/usr/bin/env python3
r"""
Expand GEU File Mapping - Phase 2

Scans additional ALL_AI directories (ssot, schemas, registry, etc.) to complete
the GEU file mappings for all 10 GEUs.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional


def generate_file_id(file_path: Path) -> str:
    """Generate deterministic 20-digit file ID."""
    path_str = str(file_path.resolve()).lower()
    path_hash = hashlib.sha256(path_str.encode()).hexdigest()
    hash_int = int(path_hash[:18], 16)
    hash_digits = str(hash_int)[-18:].zfill(18)
    return f"01{hash_digits}"


def find_file_by_name(filename: str, search_roots: List[Path]) -> Optional[Path]:
    """Find file by name in multiple search roots."""
    for root in search_roots:
        if not root.exists():
            continue
        for file_path in root.rglob(filename):
            if file_path.is_file():
                return file_path
    return None


# Expanded GEU file mapping with fallback search patterns
EXPANDED_GEU_MAPPING = {
    "GEU_01_WORK_UNIT_CONTRACT": {
        "geu_id": "99010000000000000001",
        "geu_type": "SCHEMA_BASED",
        "search_patterns": [
            ("work_unit_schema.json", "SCHEMA", True, "Canonical contract"),
            ("work_unit.schema.json", "SCHEMA", False, "Compatibility alias"),
            ("*work_unit*.schema.json", "SCHEMA", False, "Work unit schema variant"),
        ]
    },
    
    "GEU_04_REGISTRY_SSOT_DRIFT": {
        "geu_id": "99010000000000000004",
        "geu_type": "SCHEMA_BASED",
        "search_patterns": [
            ("*registry*.json", "SCHEMA", True, "Registry SSOT"),
            ("registry_schema.json", "SCHEMA", True, "Registry schema"),
            ("*drift*.py", "VALIDATOR", True, "Drift detection"),
        ]
    },
    
    "GEU_06_DAG_SCHEDULER": {
        "geu_id": "99030000000000000006",
        "geu_type": "RUNNER_BASED",
        "search_patterns": [
            ("scheduler.py", "RUNNER", True, "DAG execution engine"),
            ("*dag*.py", "SHARED_LIB", False, "DAG utilities"),
        ]
    },
    
    "GEU_07_ERROR_CLASSIFIER_REMEDY": {
        "geu_id": "99020000000000000007",
        "geu_type": "RULE_BASED",
        "search_patterns": [
            ("errors.py", "RULE", True, "Error classification"),
            ("*error*.py", "RULE", False, "Error handling"),
            ("ERROR_TAXONOMY.json", "RULE", False, "Error taxonomy"),
        ]
    },
    
    "GEU_09_SSOT_CLI_SYSTEM": {
        "geu_id": "99030000000000000009",
        "geu_type": "RUNNER_BASED",
        "known_files": [
            (r"C:\Users\richg\ALL_AI\ssot\__main__.py", "RUNNER", True, "7-phase SSOT pipeline"),
            (r"C:\Users\richg\ALL_AI\ssot\cli\orchestrator.py", "RUNNER", True, "Phase orchestration"),
            (r"C:\Users\richg\ALL_AI\ssot\phases\phase_3_validate.py", "VALIDATOR", True, "Validation phase"),
        ]
    }
}


def scan_for_additional_files(all_ai_root: Path) -> Dict:
    """Scan ALL_AI directory for additional GEU files."""
    print(f"\n{'='*80}")
    print("PHASE 2: EXPANDED FILE MAPPING")
    print(f"{'='*80}\n")
    
    search_roots = [
        all_ai_root / "ssot",
        all_ai_root / "GOVERNANCE",
        all_ai_root / "RUNTIME",
        all_ai_root / "data" / "schemas",
        all_ai_root / "registry_files",
        all_ai_root / "scripts",
    ]
    
    file_id_map = {}
    geu_data = {}
    
    # First, load existing mappings
    existing_map_path = Path("C:/Users/richg/Gov_Reg/governance_file_id_map.json")
    if existing_map_path.exists():
        with open(existing_map_path) as f:
            file_id_map = json.load(f)
        print(f"📥 Loaded {len(file_id_map)} existing file IDs\n")
    
    for geu_key, geu_info in EXPANDED_GEU_MAPPING.items():
        print(f"📦 {geu_key}")
        print(f"   GEU ID: {geu_info['geu_id']}")
        
        members = []
        found_count = 0
        
        # Handle known files
        if 'known_files' in geu_info:
            for file_spec in geu_info['known_files']:
                file_path_str, role_slot, required, notes = file_spec
                file_path = Path(file_path_str)
                
                if file_path.exists():
                    if str(file_path) not in file_id_map:
                        file_id = generate_file_id(file_path)
                        file_id_map[str(file_path)] = file_id
                    else:
                        file_id = file_id_map[str(file_path)]
                    
                    members.append({
                        "file_id": file_id,
                        "file_path": str(file_path),
                        "role_slot": role_slot,
                        "required": required,
                        "shared_access": "OWNER",
                        "notes": notes
                    })
                    print(f"   ✅ {role_slot:15} {file_path.name}")
                    found_count += 1
                else:
                    print(f"   ❌ {role_slot:15} NOT FOUND: {file_path.name}")
        
        # Handle search patterns
        if 'search_patterns' in geu_info:
            for pattern_spec in geu_info['search_patterns']:
                pattern, role_slot, required, notes = pattern_spec
                
                # Try each search root
                found = False
                for root in search_roots:
                    if not root.exists():
                        continue
                    
                    # Use glob to find matching files
                    matches = list(root.rglob(pattern))
                    if matches:
                        file_path = matches[0]  # Take first match
                        
                        if str(file_path) not in file_id_map:
                            file_id = generate_file_id(file_path)
                            file_id_map[str(file_path)] = file_id
                        else:
                            file_id = file_id_map[str(file_path)]
                        
                        members.append({
                            "file_id": file_id,
                            "file_path": str(file_path),
                            "role_slot": role_slot,
                            "required": required,
                            "shared_access": "OWNER",
                            "notes": notes
                        })
                        print(f"   ✅ {role_slot:15} {file_path.name}")
                        found_count += 1
                        found = True
                        break
                
                if not found:
                    print(f"   ⏭️  {role_slot:15} Pattern not matched: {pattern}")
        
        print(f"   📊 Found: {found_count} files\n")
        
        if members:
            geu_data[geu_key] = {
                "geu_id": geu_info["geu_id"],
                "geu_type": geu_info["geu_type"],
                "members": members,
                "outputs": [],
                "tests": []
            }
    
    return geu_data, file_id_map


def merge_with_existing(new_data: Dict, existing_path: Path) -> Dict:
    """Merge new GEU data with existing mapping."""
    if existing_path.exists():
        with open(existing_path) as f:
            existing = json.load(f)
    else:
        existing = {}
    
    # Merge, preferring new data
    merged = {**existing, **new_data}
    return merged


def main():
    all_ai_root = Path(r"C:\Users\richg\ALL_AI")
    
    if not all_ai_root.exists():
        print(f"❌ ERROR: ALL_AI directory not found: {all_ai_root}")
        return 1
    
    # Scan for additional files
    new_geu_data, file_id_map = scan_for_additional_files(all_ai_root)
    
    # Merge with existing mapping
    existing_mapping_path = Path("C:/Users/richg/Gov_Reg/governance_geu_mapping.json")
    merged_geu_data = merge_with_existing(new_geu_data, existing_mapping_path)
    
    # Save updated file ID map
    map_output = Path("C:/Users/richg/Gov_Reg/governance_file_id_map.json")
    with open(map_output, 'w') as f:
        json.dump(file_id_map, f, indent=2)
    print(f"✅ Updated file ID map: {map_output}")
    print(f"   Total files: {len(file_id_map)}")
    
    # Save merged GEU mapping
    with open(existing_mapping_path, 'w') as f:
        json.dump(merged_geu_data, f, indent=2)
    print(f"✅ Updated GEU mapping: {existing_mapping_path}")
    print(f"   Total GEUs: {len(merged_geu_data)}")
    
    print(f"\n{'='*80}")
    print("PHASE 2 COMPLETE")
    print(f"{'='*80}")
    print(f"New files found: {len(file_id_map) - 13}")
    print(f"New GEUs mapped: {len(new_geu_data)}")
    print(f"\nNext step: python scripts/update_registry_with_real_files.py")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
