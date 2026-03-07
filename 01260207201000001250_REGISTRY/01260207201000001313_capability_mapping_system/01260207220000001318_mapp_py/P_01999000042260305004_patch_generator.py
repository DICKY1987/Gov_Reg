#!/usr/bin/env python3
"""
Comprehensive Registry Patch Generator (Week 1 Steps 1.6-1.7)

Purpose:
  - Generate RFC-6902 JSON Patches for registry updates
  - Handle Phase A column additions
  - Update file records with new analysis data
  - Apply patches with backup and validation

Usage:
  python P_01999000042260305004_patch_generator.py --mode {generate|apply|validate}
  
Modes:
  generate  - Generate patches from analysis results
  apply     - Apply patches to registry
  validate  - Validate patches without applying
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import hashlib


class PatchGenerator:
    def __init__(self, registry_path: Path):
        self.registry_path = registry_path
        self.patches: List[Dict[str, Any]] = []
        
    def load_registry(self) -> Dict[str, Any]:
        """Load registry JSON."""
        with open(self.registry_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def generate_add_column_patch(self, file_index: int, column_name: str, value: Any) -> Dict[str, Any]:
        """Generate patch to add a column to a file record."""
        return {
            "op": "add",
            "path": f"/files/{file_index}/{column_name}",
            "value": value
        }
    
    def generate_replace_column_patch(self, file_index: int, column_name: str, value: Any) -> Dict[str, Any]:
        """Generate patch to replace a column value."""
        return {
            "op": "replace",
            "path": f"/files/{file_index}/{column_name}",
            "value": value
        }
    
    def find_file_by_id(self, registry: Dict[str, Any], file_id: str) -> int:
        """Find file index by file_id."""
        files = registry.get("files", [])
        for idx, file_record in enumerate(files):
            if file_record.get("file_id") == file_id:
                return idx
        return -1
    
    def generate_patches_from_analysis(self, registry: Dict[str, Any], 
                                      analysis_results: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate patches from analysis results.
        
        analysis_results: {file_id: {column: value, ...}, ...}
        """
        patches = []
        
        for file_id, columns in analysis_results.items():
            file_idx = self.find_file_by_id(registry, file_id)
            
            if file_idx == -1:
                print(f"⚠️  Warning: File ID {file_id} not found in registry")
                continue
            
            file_record = registry["files"][file_idx]
            
            for column_name, value in columns.items():
                # Check if column exists
                if column_name in file_record:
                    # Replace if value changed
                    if file_record[column_name] != value:
                        patch = self.generate_replace_column_patch(file_idx, column_name, value)
                        patches.append(patch)
                else:
                    # Add new column
                    patch = self.generate_add_column_patch(file_idx, column_name, value)
                    patches.append(patch)
        
        return patches
    
    def validate_patches(self, registry: Dict[str, Any], patches: List[Dict[str, Any]]) -> bool:
        """Validate patches against registry structure."""
        errors = []
        
        for idx, patch in enumerate(patches):
            op = patch.get("op")
            path = patch.get("path")
            
            if op not in ["add", "replace", "remove"]:
                errors.append(f"Patch {idx}: Invalid operation '{op}'")
                continue
            
            if not path:
                errors.append(f"Patch {idx}: Missing path")
                continue
            
            # Validate path format
            parts = path.strip("/").split("/")
            if len(parts) < 2:
                errors.append(f"Patch {idx}: Invalid path '{path}'")
                continue
            
            if parts[0] != "files":
                errors.append(f"Patch {idx}: Path must start with /files, got '{path}'")
                continue
            
            # Validate file index
            try:
                file_idx = int(parts[1])
                if file_idx < 0 or file_idx >= len(registry.get("files", [])):
                    errors.append(f"Patch {idx}: Invalid file index {file_idx}")
            except ValueError:
                errors.append(f"Patch {idx}: File index must be integer, got '{parts[1]}'")
        
        if errors:
            print(f"❌ Validation failed with {len(errors)} errors:")
            for err in errors[:10]:
                print(f"  • {err}")
            return False
        
        return True
    
    def apply_patches(self, registry: Dict[str, Any], patches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply patches to registry."""
        import copy
        patched = copy.deepcopy(registry)
        
        for patch in patches:
            op = patch["op"]
            path = patch["path"]
            value = patch.get("value")
            
            # Parse path
            parts = path.strip("/").split("/")
            
            # Navigate to parent
            target = patched
            for part in parts[:-1]:
                if part.isdigit():
                    target = target[int(part)]
                else:
                    target = target[part]
            
            # Apply operation
            last_key = parts[-1]
            
            if op == "add":
                if last_key.isdigit():
                    target.insert(int(last_key), value)
                else:
                    target[last_key] = value
            
            elif op == "replace":
                if last_key.isdigit():
                    target[int(last_key)] = value
                else:
                    target[last_key] = value
            
            elif op == "remove":
                if last_key.isdigit():
                    target.pop(int(last_key))
                else:
                    del target[last_key]
        
        return patched
    
    def backup_registry(self) -> Path:
        """Create backup of registry."""
        backup_dir = self.registry_path.parent.parent / "01260207201000001133_backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"REGISTRY_file_pre_patch_{timestamp}.json"
        
        # Copy registry
        with open(self.registry_path, 'r', encoding='utf-8') as src:
            registry = json.load(src)
        
        with open(backup_path, 'w', encoding='utf-8') as dst:
            json.dump(registry, dst, indent=2, ensure_ascii=False)
        
        print(f"✅ Backup created: {backup_path}")
        return backup_path


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Registry Patch Generator')
    parser.add_argument('--mode', required=True,
                       choices=['generate', 'apply', 'validate'],
                       help='Operation mode')
    parser.add_argument('--registry',
                       default='../../01999000042260124503_REGISTRY_file.json',
                       help='Registry path')
    parser.add_argument('--analysis-dir',
                       help='Directory with analysis results (for generate mode)')
    parser.add_argument('--patches-file',
                       default='../../.state/patches/registry_patches.json',
                       help='Patches file')
    parser.add_argument('--output',
                       help='Output path for patched registry')
    
    args = parser.parse_args()
    
    # Resolve paths
    script_dir = Path(__file__).parent
    registry_path = (script_dir / args.registry).resolve()
    patches_path = (script_dir / args.patches_file).resolve()
    
    generator = PatchGenerator(registry_path)
    
    if args.mode == 'generate':
        if not args.analysis_dir:
            print("❌ Error: --analysis-dir required for generate mode", file=sys.stderr)
            sys.exit(1)
        
        print("Loading registry...")
        registry = generator.load_registry()
        
        print(f"Loading analysis results from {args.analysis_dir}...")
        analysis_dir = Path(args.analysis_dir)
        
        # Collect analysis results
        analysis_results = {}
        for result_file in analysis_dir.glob("*.json"):
            with open(result_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "file_id" in data and "data" in data:
                    analysis_results[data["file_id"]] = data["data"]
        
        print(f"Generating patches for {len(analysis_results)} files...")
        patches = generator.generate_patches_from_analysis(registry, analysis_results)
        
        print(f"Generated {len(patches)} patches")
        
        # Save patches
        patches_path.parent.mkdir(parents=True, exist_ok=True)
        output = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "generator": "P_01999000042260305004_patch_generator.py",
            "registry_source": str(registry_path),
            "patches_count": len(patches),
            "patches": patches
        }
        
        with open(patches_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Patches saved to: {patches_path}")
    
    elif args.mode == 'validate':
        print("Loading registry...")
        registry = generator.load_registry()
        
        print(f"Loading patches from {patches_path}...")
        with open(patches_path, 'r', encoding='utf-8') as f:
            patches_data = json.load(f)
        
        patches = patches_data.get("patches", [])
        print(f"Validating {len(patches)} patches...")
        
        if generator.validate_patches(registry, patches):
            print("✅ All patches valid")
            sys.exit(0)
        else:
            print("❌ Validation failed")
            sys.exit(1)
    
    elif args.mode == 'apply':
        print("Loading registry...")
        registry = generator.load_registry()
        
        print(f"Loading patches from {patches_path}...")
        with open(patches_path, 'r', encoding='utf-8') as f:
            patches_data = json.load(f)
        
        patches = patches_data.get("patches", [])
        print(f"Applying {len(patches)} patches...")
        
        # Validate first
        if not generator.validate_patches(registry, patches):
            print("❌ Validation failed - aborting", file=sys.stderr)
            sys.exit(1)
        
        # Backup
        generator.backup_registry()
        
        # Apply
        patched_registry = generator.apply_patches(registry, patches)
        
        # Write output
        output_path = Path(args.output) if args.output else registry_path
        print(f"Writing patched registry to: {output_path}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(patched_registry, f, indent=2, ensure_ascii=False)
        
        print("✅ Patches applied successfully")


if __name__ == "__main__":
    main()
