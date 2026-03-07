#!/usr/bin/env python3
"""
Enum Canon + Drift Gate (Phase 0 Step 0.1)

Purpose:
  - Build canonical enum definitions with legacy aliases
  - Validate drift in repo_root_id and canonicality across registry data
  - Generate RFC-6902 normalization patches for auto-fixable violations
  
Usage:
  python P_01999000042260305000_enum_drift_gate.py [--fix]
  
  Without --fix: Validates and reports violations
  With --fix: Applies normalization patches after backup

Exit codes:
  0: No enum drift detected - GATE PASSED
  1: Enum drift detected (violations reported)
  2: Fatal error (cannot proceed)
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple

# Canonical enum definitions with legacy aliases
REGISTRY_ENUMS_CANON = {
    "repo_root_id": {
        "canonical": ["GOV_REG_WORKSPACE", "ALL_AI", "AI_PROD_PIPELINE"],
        "aliases": {
            "AI_PIPELINE": "AI_PROD_PIPELINE",  # Legacy alias
            "PROD_PIPELINE": "AI_PROD_PIPELINE",
            "AI": "ALL_AI",
            "01": "GOV_REG_WORKSPACE"  # Data corruption fix - likely truncated value
        },
        "description": "Repository root identifier for multi-root governance"
    },
    "canonicality": {
        "canonical": ["CANONICAL", "LEGACY", "ALTERNATE", "EXPERIMENTAL"],
        "aliases": {
            "PRIMARY": "CANONICAL",
            "DEPRECATED": "LEGACY",
            "ALT": "ALTERNATE",
            "EXPERIMENTAL_DRAFT": "EXPERIMENTAL",
            "SUPERSEDED": "LEGACY"  # Superseded files are legacy
        },
        "description": "File canonicality status in multi-version scenarios"
    }
}

class EnumDriftGate:
    def __init__(self, registry_path: str):
        self.registry_path = Path(registry_path)
        self.violations: List[Dict[str, Any]] = []
        self.patches: List[Dict[str, Any]] = []
        
    def load_registry(self) -> Dict[str, Any]:
        """Load registry JSON with UTF-8 encoding."""
        with open(self.registry_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def normalize_enum_value(self, field_name: str, value: Any) -> Tuple[Any, bool]:
        """
        Normalize enum value using canonical definitions and aliases.
        
        Returns:
            (normalized_value, was_normalized)
        """
        if value is None:
            return None, False
            
        enum_def = REGISTRY_ENUMS_CANON.get(field_name)
        if not enum_def:
            return value, False
        
        # Check if already canonical
        if value in enum_def["canonical"]:
            return value, False
        
        # Check aliases
        normalized = enum_def["aliases"].get(value)
        if normalized:
            return normalized, True
        
        # Unknown value - cannot auto-fix
        return value, False
    
    def validate_files(self, registry: Dict[str, Any]) -> None:
        """Validate enum fields in files array."""
        files = registry.get("files", [])
        
        for idx, file_record in enumerate(files):
            file_id = file_record.get("file_id", f"<index {idx}>")
            rel_path = file_record.get("relative_path", "<unknown>")
            
            # Validate repo_root_id
            if "repo_root_id" in file_record:
                current_value = file_record["repo_root_id"]
                normalized_value, was_normalized = self.normalize_enum_value(
                    "repo_root_id", current_value
                )
                
                if was_normalized:
                    self.violations.append({
                        "record_type": "file",
                        "record_id": file_id,
                        "relative_path": rel_path,
                        "field": "repo_root_id",
                        "current_value": current_value,
                        "canonical_value": normalized_value,
                        "auto_fixable": True
                    })
                    
                    # Generate RFC-6902 patch
                    self.patches.append({
                        "op": "replace",
                        "path": f"/files/{idx}/repo_root_id",
                        "value": normalized_value
                    })
                elif current_value not in REGISTRY_ENUMS_CANON["repo_root_id"]["canonical"]:
                    self.violations.append({
                        "record_type": "file",
                        "record_id": file_id,
                        "relative_path": rel_path,
                        "field": "repo_root_id",
                        "current_value": current_value,
                        "canonical_value": None,
                        "auto_fixable": False,
                        "error": f"Unknown value '{current_value}' - no alias mapping"
                    })
            
            # Validate canonicality
            if "canonicality" in file_record:
                current_value = file_record["canonicality"]
                normalized_value, was_normalized = self.normalize_enum_value(
                    "canonicality", current_value
                )
                
                if was_normalized:
                    self.violations.append({
                        "record_type": "file",
                        "record_id": file_id,
                        "relative_path": rel_path,
                        "field": "canonicality",
                        "current_value": current_value,
                        "canonical_value": normalized_value,
                        "auto_fixable": True
                    })
                    
                    self.patches.append({
                        "op": "replace",
                        "path": f"/files/{idx}/canonicality",
                        "value": normalized_value
                    })
                elif current_value not in REGISTRY_ENUMS_CANON["canonicality"]["canonical"]:
                    self.violations.append({
                        "record_type": "file",
                        "record_id": file_id,
                        "relative_path": rel_path,
                        "field": "canonicality",
                        "current_value": current_value,
                        "canonical_value": None,
                        "auto_fixable": False,
                        "error": f"Unknown value '{current_value}' - no alias mapping"
                    })
    
    def validate_edges(self, registry: Dict[str, Any]) -> None:
        """Validate enum fields in edges array (repo_root_id only)."""
        edges = registry.get("edges", [])
        
        for idx, edge_record in enumerate(edges):
            edge_id = edge_record.get("edge_id", f"<index {idx}>")
            
            if "repo_root_id" in edge_record:
                current_value = edge_record["repo_root_id"]
                normalized_value, was_normalized = self.normalize_enum_value(
                    "repo_root_id", current_value
                )
                
                if was_normalized:
                    self.violations.append({
                        "record_type": "edge",
                        "record_id": edge_id,
                        "field": "repo_root_id",
                        "current_value": current_value,
                        "canonical_value": normalized_value,
                        "auto_fixable": True
                    })
                    
                    self.patches.append({
                        "op": "replace",
                        "path": f"/edges/{idx}/repo_root_id",
                        "value": normalized_value
                    })
                elif current_value not in REGISTRY_ENUMS_CANON["repo_root_id"]["canonical"]:
                    self.violations.append({
                        "record_type": "edge",
                        "record_id": edge_id,
                        "field": "repo_root_id",
                        "current_value": current_value,
                        "canonical_value": None,
                        "auto_fixable": False,
                        "error": f"Unknown value '{current_value}' - no alias mapping"
                    })
    
    def report_violations(self) -> None:
        """Print violation report to stdout."""
        if not self.violations:
            print("✅ No enum drift detected - GATE PASSED")
            return
        
        auto_fixable = [v for v in self.violations if v.get("auto_fixable", False)]
        not_fixable = [v for v in self.violations if not v.get("auto_fixable", False)]
        
        print(f"❌ Enum drift detected: {len(self.violations)} violations")
        print(f"   Auto-fixable: {len(auto_fixable)}")
        print(f"   Cannot auto-fix: {len(not_fixable)}")
        print()
        
        if auto_fixable:
            print("Auto-fixable violations (will normalize on --fix):")
            for v in auto_fixable[:10]:  # Limit to first 10
                print(f"  • {v['record_type']} {v['record_id']}: "
                      f"{v['field']} '{v['current_value']}' → '{v['canonical_value']}'")
                if 'relative_path' in v:
                    print(f"    Path: {v['relative_path']}")
            if len(auto_fixable) > 10:
                print(f"  ... and {len(auto_fixable) - 10} more")
            print()
        
        if not_fixable:
            print("⚠️  CANNOT AUTO-FIX (manual decision required):")
            for v in not_fixable:
                print(f"  • {v['record_type']} {v['record_id']}: "
                      f"{v['field']} = '{v['current_value']}'")
                if 'relative_path' in v:
                    print(f"    Path: {v['relative_path']}")
                print(f"    Error: {v.get('error', 'Unknown value')}")
            print()
    
    def apply_patches(self) -> None:
        """Apply normalization patches to registry."""
        if not self.patches:
            print("No patches to apply.")
            return
        
        # Backup first
        backup_dir = self.registry_path.parent.parent / "01260207201000001133_backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"REGISTRY_file_pre_enum_norm_{timestamp}.json"
        
        print(f"Creating backup: {backup_path}")
        with open(self.registry_path, 'r', encoding='utf-8') as src:
            registry = json.load(src)
        
        with open(backup_path, 'w', encoding='utf-8') as dst:
            json.dump(registry, dst, indent=2, ensure_ascii=False)
        
        # Apply patches
        print(f"Applying {len(self.patches)} normalization patches...")
        
        for patch in self.patches:
            path_parts = patch["path"].strip("/").split("/")
            target = registry
            
            for part in path_parts[:-1]:
                if part.isdigit():
                    target = target[int(part)]
                else:
                    target = target[part]
            
            last_key = path_parts[-1]
            if last_key.isdigit():
                target[int(last_key)] = patch["value"]
            else:
                target[last_key] = patch["value"]
        
        # Write normalized registry
        print(f"Writing normalized registry: {self.registry_path}")
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)
        
        print("✅ Normalization complete")
    
    def write_canon_file(self) -> None:
        """Write REGISTRY_ENUMS_CANON.json to .state directory."""
        state_dir = self.registry_path.parent.parent / ".state"
        state_dir.mkdir(parents=True, exist_ok=True)
        
        canon_path = state_dir / "REGISTRY_ENUMS_CANON.json"
        
        output = {
            "generated_at": datetime.now().isoformat(),
            "enums": REGISTRY_ENUMS_CANON,
            "source": "P_01999000042260305000_enum_drift_gate.py"
        }
        
        with open(canon_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"Written canonical enum definitions to: {canon_path}")
    
    def run(self, apply_fix: bool = False) -> int:
        """
        Run validation gate.
        
        Returns:
            0: No drift
            1: Drift detected (fixable or not)
            2: Fatal error
        """
        try:
            print(f"Loading registry: {self.registry_path}")
            registry = self.load_registry()
            
            print("Validating files array...")
            self.validate_files(registry)
            
            print("Validating edges array...")
            self.validate_edges(registry)
            
            print()
            self.report_violations()
            
            # Write canonical enum file
            self.write_canon_file()
            
            if not self.violations:
                return 0
            
            # Check for non-fixable violations
            not_fixable = [v for v in self.violations if not v.get("auto_fixable", False)]
            if not_fixable and not apply_fix:
                print("\n❌ STOP: Manual decision required for non-fixable violations")
                print("   Review the violations above and update enum aliases or data manually.")
                return 2
            
            if apply_fix:
                if not_fixable:
                    print("\n❌ Cannot apply --fix: non-fixable violations present")
                    return 2
                
                print()
                self.apply_patches()
                return 0
            else:
                print("\nRun with --fix to apply normalization patches")
                return 1
        
        except FileNotFoundError:
            print(f"❌ ERROR: Registry file not found: {self.registry_path}", file=sys.stderr)
            return 2
        except json.JSONDecodeError as e:
            print(f"❌ ERROR: Invalid JSON in registry: {e}", file=sys.stderr)
            return 2
        except Exception as e:
            print(f"❌ FATAL ERROR: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return 2


def main():
    # Determine registry path
    script_dir = Path(__file__).parent
    registry_root = script_dir.parent.parent
    registry_path = registry_root / "01999000042260124503_REGISTRY_file.json"
    
    apply_fix = "--fix" in sys.argv
    
    gate = EnumDriftGate(str(registry_path))
    exit_code = gate.run(apply_fix=apply_fix)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
