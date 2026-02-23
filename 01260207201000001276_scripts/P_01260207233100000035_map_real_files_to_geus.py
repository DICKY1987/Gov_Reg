#!/usr/bin/env python3
r"""
Map Real Files to GEU Registry with File IDs

Scans C:\Users\richg\ALL_AI\GOVERNANCE for files matching the GEU file-role mapping,
allocates 20-digit file IDs, and updates the consolidated GEU registry.
"""

import json
import hashlib
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional


def generate_file_id(file_path: Path) -> str:
    """
    Generate a 20-digit file ID based on file path hash.
    Format: 01 (file prefix) + 18 digits derived from path hash
    """
    # Get normalized path string
    path_str = str(file_path.resolve()).lower()
    
    # Create hash
    path_hash = hashlib.sha256(path_str.encode()).hexdigest()
    
    # Take first 18 hex chars, convert to int, then to 18-digit string
    hash_int = int(path_hash[:18], 16)
    hash_digits = str(hash_int)[-18:].zfill(18)
    
    return f"01{hash_digits}"


def find_file_in_governance(partial_path: str, governance_root: Path) -> Optional[Path]:
    """
    Find a file in GOVERNANCE directory matching partial path patterns.
    Handles various path formats from the GEU documentation.
    """
    # Extract key parts from partial path
    if '\\' in partial_path:
        # Windows path - extract filename and parent dirs
        parts = Path(partial_path).parts
        if len(parts) >= 2:
            # Look for files matching the pattern
            pattern = parts[-1]  # filename
            parent = parts[-2] if len(parts) > 1 else None
        else:
            pattern = parts[0]
            parent = None
    else:
        # Unix-style path like ai-prod-pipeline/schemas/work_unit_schema.json
        parts = partial_path.split('/')
        pattern = parts[-1]
        parent = parts[-2] if len(parts) > 1 else None
    
    # Search for files matching the pattern
    candidates = []
    for file_path in governance_root.rglob('*'):
        if not file_path.is_file():
            continue
        
        # Check if filename matches
        if file_path.name == pattern:
            candidates.append(file_path)
        # Also check for DOC-* prefixed versions
        elif pattern in file_path.name:
            candidates.append(file_path)
    
    # If we have candidates, prefer ones with matching parent directory
    if candidates:
        if parent:
            for candidate in candidates:
                if parent.lower() in str(candidate.parent).lower():
                    return candidate
        return candidates[0]
    
    return None


# GEU file mapping from the documentation
GEU_FILE_MAPPING = {
    "GEU_01_WORK_UNIT_CONTRACT": {
        "geu_id": "99010000000000000001",
        "geu_type": "SCHEMA_BASED",
        "files": [
            ("ai-prod-pipeline/schemas/work_unit_schema.json", "SCHEMA", True, "Canonical contract"),
            ("ai-prod-pipeline/schemas/work_unit.schema.json", "SCHEMA", False, "Compatibility alias"),
            ("ai-prod-pipeline/src/validation/validate_work_unit.py", "VALIDATOR", True, "Semantic enforcement"),
            ("ai-prod-pipeline/src/core/execute_work_unit.py", "RUNNER", True, "Execution engine"),
            ("ai-prod-pipeline/src/errors/work_unit_failures.py", "FAILURE_MODE", True, "Error taxonomy"),
        ],
        "outputs": [
            ("ai-prod-pipeline/evidence/work_unit_run_manifest.json", "EVIDENCE_OUTPUT", "Execution proof"),
        ],
        "tests": [
            ("ai-prod-pipeline/tests/test_work_unit_validation.py", "Validator correctness"),
        ]
    },
    
    "GEU_02_RUNNER_EVIDENCE_GATE": {
        "geu_id": "99030000000000000002",
        "geu_type": "RUNNER_BASED",
        "files": [
            (r"C:\Users\richg\ALL_AI\GOVERNANCE\gates\gate_runner.py", "RUNNER", True, "Gate orchestration"),
            (r"C:\Users\richg\ALL_AI\GOVERNANCE\gates\enforcement_bridge.py", "SHARED_LIB", True, "Manifest translation"),
            (r"C:\Users\richg\ALL_AI\GOVERNANCE\events\event_emitter.py", "SHARED_LIB", False, "Event emission"),
            (r"C:\Users\richg\ALL_AI\GOVERNANCE\events\event_router.py", "SHARED_LIB", False, "Event routing"),
            (r"C:\Users\richg\ALL_AI\GOVERNANCE\events\event_sinks.py", "SHARED_LIB", False, "Event persistence"),
            (r"C:\Users\richg\ALL_AI\scripts\DOC-SCRIPT-RUN-ALL-GATES-001__run_all_gates.py", "RUNNER", True, "Batch execution"),
        ],
        "outputs": [
            ("ai-prod-pipeline/reports/latest_run_report.json", "REPORT", "Run results"),
        ],
        "tests": [
            ("ai-prod-pipeline/tests/test_gate_runner.py", "Gate determinism proof"),
        ]
    },
    
    "GEU_03_DETERMINISTIC_TRACE_REPLAY": {
        "geu_id": "99050000000000000003",
        "geu_type": "EVIDENCE_ONLY",
        "files": [
            ("ai-prod-pipeline/src/trace/trace_storage.py", "EVIDENCE_OUTPUT", True, "Durable storage"),
            ("ai-prod-pipeline/src/trace/trace_context.py", "SHARED_LIB", False, "Context propagation"),
            ("ai-prod-pipeline/src/trace/determinism_checker.py", "VALIDATOR", True, "Replay validation"),
        ],
        "outputs": [
            ("ai-prod-pipeline/artifacts/trace.db", "EVIDENCE_OUTPUT", "Trace database"),
        ],
        "tests": [
            ("ai-prod-pipeline/tests/test_trace_replay.py", "Replay proof"),
        ]
    },
    
    "GEU_05_VALIDATOR_SUITE": {
        "geu_id": "99030000000000000005",
        "geu_type": "RUNNER_BASED",
        "files": [
            (r"C:\Users\richg\ALL_AI\GOVERNANCE\ssot\SSOT_System\SSOT_SYS_tools\DOC-CORE-SSOT-SYS-TOOLS-VALIDATE-MANIFEST-1109__validate_manifest.py", "VALIDATOR", True, "Manifest validation"),
            (r"C:\Users\richg\ALL_AI\GOVERNANCE\ssot\SSOT_System\SSOT_SYS_tools\DOC-CORE-SSOT-SYS-TOOLS-VALIDATE-SSOT-1112__validate_ssot.py", "VALIDATOR", True, "SSOT consistency"),
            (r"C:\Users\richg\ALL_AI\GOVERNANCE\ssot\SSOT_System\SSOT_SYS_tools\DOC-CORE-SSOT-SYS-TOOLS-VALIDATE-AUTOMATION-SPEC-518__validate_automation_spec.py", "VALIDATOR", True, "Automation enforcement"),
        ],
        "outputs": [],
        "tests": [
            ("ai-prod-pipeline/tests/test_validators.py", "Validator proof"),
        ]
    },
    
    "GEU_08_REPORTING_SYSTEM": {
        "geu_id": "99030000000000000008",
        "geu_type": "RUNNER_BASED",
        "files": [
            (r"C:\Users\richg\ALL_AI\GOVERNANCE\ssot\SSOT_System\SSOT_SYS_tools\DOC-CORE-SSOT-SYS-TOOLS-RENDER-PIPELINE-1301__render_pipeline.py", "RUNNER", True, "Report orchestration"),
            (r"C:\Users\richg\ALL_AI\GOVERNANCE\ssot\SSOT_System\SSOT_SYS_tools\DOC-CORE-SSOT-SYS-TOOLS-RENDER-FILE-TREE-1304__render_file_tree.py", "REPORT", False, "Structure visualization"),
            (r"C:\Users\richg\ALL_AI\GOVERNANCE\ssot\SSOT_System\SSOT_SYS_tools\DOC-CORE-SSOT-SYS-TOOLS-MERGE-SCAN-OVERLAY-1303__merge_scan_overlay.py", "REPORT", False, "Registry overlays"),
        ],
        "outputs": [
            ("ai-prod-pipeline/reports/latest_run_report.md", "REPORT", "Human-readable output"),
        ],
        "tests": []
    },
    
    "GEU_10_INTEGRATION_AUTOMATION": {
        "geu_id": "99030000000000000010",
        "geu_type": "RUNNER_BASED",
        "files": [
            (r"C:\Users\richg\ALL_AI\GOVERNANCE\ssot\SSOT_System\SSOT_SYS_ci\DOC-CORE-SSOT-SYS-CI-CI-GATE-1095__ci_gate.py", "RUNNER", True, "CI enforcement"),
        ],
        "outputs": [],
        "tests": []
    },
}


def map_files_to_geus(governance_root: Path) -> Dict:
    """
    Map real files in GOVERNANCE directory to GEU structure with file IDs.
    """
    file_id_map = {}  # path -> file_id
    geu_data = {}
    
    print(f"\n{'='*80}")
    print("MAPPING REAL FILES TO GEU REGISTRY")
    print(f"{'='*80}\n")
    print(f"Scanning: {governance_root}\n")
    
    for geu_key, geu_info in GEU_FILE_MAPPING.items():
        print(f"\n📦 {geu_key}")
        print(f"   GEU ID: {geu_info['geu_id']}")
        print(f"   Type: {geu_info['geu_type']}")
        
        members = []
        outputs = []
        tests = []
        found_count = 0
        missing_count = 0
        
        # Process member files
        for file_spec in geu_info['files']:
            partial_path, role_slot, required, notes = file_spec
            
            # Try to find the file
            found_path = find_file_in_governance(partial_path, governance_root)
            
            if found_path:
                file_id = file_id_map.get(str(found_path))
                if not file_id:
                    file_id = generate_file_id(found_path)
                    file_id_map[str(found_path)] = file_id
                
                members.append({
                    "file_id": file_id,
                    "file_path": str(found_path),
                    "role_slot": role_slot,
                    "required": required,
                    "shared_access": "OWNER",  # First GEU to claim it is owner
                    "notes": notes
                })
                print(f"   ✅ {role_slot:15} {found_path.name}")
                found_count += 1
            else:
                print(f"   ❌ {role_slot:15} NOT FOUND: {partial_path}")
                missing_count += 1
        
        # Process outputs
        for output_spec in geu_info['outputs']:
            partial_path, output_kind, notes = output_spec
            found_path = find_file_in_governance(partial_path, governance_root)
            
            if found_path:
                file_id = file_id_map.get(str(found_path))
                if not file_id:
                    file_id = generate_file_id(found_path)
                    file_id_map[str(found_path)] = file_id
                
                outputs.append({
                    "file_id": file_id,
                    "file_path": str(found_path),
                    "output_kind": output_kind,
                    "shared_access": "OWNER",
                    "notes": notes
                })
                print(f"   ✅ OUTPUT:         {found_path.name}")
                found_count += 1
        
        # Process tests
        for test_spec in geu_info['tests']:
            partial_path, notes = test_spec
            found_path = find_file_in_governance(partial_path, governance_root)
            
            if found_path:
                file_id = file_id_map.get(str(found_path))
                if not file_id:
                    file_id = generate_file_id(found_path)
                    file_id_map[str(found_path)] = file_id
                
                tests.append({
                    "file_id": file_id,
                    "file_path": str(found_path),
                    "shared_access": "OWNER",
                    "notes": notes
                })
                print(f"   ✅ TEST:           {found_path.name}")
                found_count += 1
        
        print(f"   📊 Found: {found_count}, Missing: {missing_count}")
        
        geu_data[geu_key] = {
            "geu_id": geu_info["geu_id"],
            "geu_type": geu_info["geu_type"],
            "members": members,
            "outputs": outputs,
            "tests": tests
        }
    
    return geu_data, file_id_map


def main():
    governance_root = Path(r"C:\Users\richg\ALL_AI\GOVERNANCE")
    
    if not governance_root.exists():
        print(f"❌ ERROR: GOVERNANCE directory not found: {governance_root}")
        return 1
    
    # Map files to GEUs
    geu_data, file_id_map = map_files_to_geus(governance_root)
    
    # Save file ID map
    map_output = Path("C:/Users/richg/Gov_Reg/governance_file_id_map.json")
    with open(map_output, 'w') as f:
        json.dump(file_id_map, f, indent=2)
    print(f"\n✅ Saved file ID map to {map_output}")
    print(f"   Total files mapped: {len(file_id_map)}")
    
    # Save GEU data with real files
    geu_output = Path("C:/Users/richg/Gov_Reg/governance_geu_mapping.json")
    with open(geu_output, 'w') as f:
        json.dump(geu_data, f, indent=2)
    print(f"✅ Saved GEU mapping to {geu_output}")
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total GEUs processed: {len(geu_data)}")
    print(f"Total files mapped: {len(file_id_map)}")
    print(f"\nNext step: Run update_registry_with_real_files.py to merge into registry")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
