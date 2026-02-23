#!/usr/bin/env python3
"""
Enhanced Bundle Detector - Groups related governance files into bundles.

Uses multiple strategies:
1. Name-based clustering (files with similar names)
2. Layer-based clustering (SSOT, GOVERNANCE, VALIDATION)
3. Explicit schema references
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent / "PATH_FILES"))

try:
    from path_registry import resolve_path
    REGISTRY_PATH = resolve_path("REGISTRY_UNIFIED")
except ImportError:
    # Fallback: look in parent directory (since we're now in scripts/)
    REGISTRY_PATH = Path(__file__).parent.parent / "01999000042260124503_governance_registry_unified.json"

class EnhancedBundleDetector:
    def __init__(self, registry_path: Path):
        with open(registry_path, 'r', encoding='utf-8') as f:
            self.registry = json.load(f)
        self.files = {f['file_id']: f for f in self.registry.get('files', [])}
        self.bundles = {}
        self.bundle_counter = 1000000000000000
        
    def normalize_name(self, path: str) -> str:
        """Extract normalized stem from path for matching."""
        name = Path(path).stem
        # Remove file_id prefix (digits followed by __)
        name = re.sub(r'^\d+__', '', name)
        # Remove DOC- prefix patterns
        name = re.sub(r'^DOC-[A-Z]+-', '', name)
        # Normalize to lowercase, replace separators
        name = name.lower().replace('-', '_').replace('.', '_')
        return name
    
    def extract_base_name(self, path: str) -> str:
        """Extract base name for grouping (e.g., 'govreg' from 'P_01999000042260124015_govreg.py')"""
        name = Path(path).stem
        # Remove prefixes (P_, file_id, DOC-)
        name = re.sub(r'^[A-Z]_\d+_', '', name)
        name = re.sub(r'^\d+__', '', name)
        name = re.sub(r'^DOC-[A-Z]+-', '', name)
        # Take first meaningful part
        parts = name.split('_')
        if parts:
            return parts[0].lower()
        return name.lower()
    
    def create_bundle(self, bundle_key: str, anchor_id: str, file_ids: List[str]):
        """Create a bundle with given key and files."""
        bundle_id = str(self.bundle_counter)
        self.bundle_counter += 1
        
        self.bundles[bundle_id] = {
            'bundle_id': bundle_id,
            'bundle_key': bundle_key.upper(),
            'anchor_file_id': anchor_id,
            'file_ids': file_ids
        }
        return bundle_id
    
    def detect_bundles(self):
        """Main bundle detection logic."""
        print("=== Enhanced Bundle Detection ===\n")
        
        assigned_files = set()
        
        # Strategy 1: Schema-based bundles
        print("Step 1: Schema-based bundles")
        schema_bundles = self.detect_schema_bundles()
        for bundle_id, bundle_data in schema_bundles.items():
            self.bundles[bundle_id] = bundle_data
            assigned_files.update(bundle_data['file_ids'])
        print(f"  Created {len(schema_bundles)} schema bundles\n")
        
        # Strategy 2: Name-based clustering (govreg_core modules)
        print("Step 2: Name-based clustering")
        name_bundles = self.detect_name_clusters(assigned_files)
        for bundle_id, bundle_data in name_bundles.items():
            self.bundles[bundle_id] = bundle_data
            assigned_files.update(bundle_data['file_ids'])
        print(f"  Created {len(name_bundles)} name-based bundles\n")
        
        # Strategy 3: Layer-based bundles (SSOT, GOVERNANCE, VALIDATION)
        print("Step 3: Layer-based clustering")
        layer_bundles = self.detect_layer_bundles(assigned_files)
        for bundle_id, bundle_data in layer_bundles.items():
            self.bundles[bundle_id] = bundle_data
            assigned_files.update(bundle_data['file_ids'])
        print(f"  Created {len(layer_bundles)} layer-based bundles\n")
        
        # Strategy 4: Documentation bundles
        print("Step 4: Documentation clustering")
        doc_bundles = self.detect_doc_bundles(assigned_files)
        for bundle_id, bundle_data in doc_bundles.items():
            self.bundles[bundle_id] = bundle_data
            assigned_files.update(bundle_data['file_ids'])
        print(f"  Created {len(doc_bundles)} doc bundles\n")
        
        print(f"Total bundles: {len(self.bundles)}")
        print(f"Files assigned: {len(assigned_files)}/{len(self.files)}\n")
    
    def detect_schema_bundles(self) -> Dict:
        """Group schema files with their related artifacts."""
        bundles = {}
        
        for file_id, file_data in self.files.items():
            if file_data.get('artifact_kind') == 'SCHEMA':
                rel_path = file_data.get('relative_path', '')
                bundle_key = self.normalize_name(rel_path)
                
                # Find related files (same name pattern)
                related_ids = [file_id]
                
                bundle_id = self.create_bundle(bundle_key, file_id, related_ids)
                bundles[bundle_id] = self.bundles[bundle_id]
        
        return bundles
    
    def detect_name_clusters(self, assigned_files: Set[str]) -> Dict:
        """Group files by base name (e.g., govreg, scanner, validator)."""
        bundles = {}
        
        # Group by base name
        by_base_name = defaultdict(list)
        for file_id, file_data in self.files.items():
            if file_id in assigned_files:
                continue
            
            rel_path = file_data.get('relative_path', '')
            base_name = self.extract_base_name(rel_path)
            
            # Only group Python modules and related files
            if file_data.get('artifact_kind') in ['PYTHON_MODULE', 'TEST', 'JSON', 'YAML']:
                by_base_name[base_name].append(file_id)
        
        # Create bundles for groups with 2+ files
        for base_name, file_ids in by_base_name.items():
            if len(file_ids) >= 1:  # Even single files get bundles
                # Pick first as anchor
                anchor_id = file_ids[0]
                bundle_key = f"{base_name}_module"
                
                bundle_id = self.create_bundle(bundle_key, anchor_id, file_ids)
                bundles[bundle_id] = self.bundles[bundle_id]
        
        return bundles
    
    def detect_layer_bundles(self, assigned_files: Set[str]) -> Dict:
        """Group files by layer (SSOT, GOVERNANCE, VALIDATION, etc.)."""
        bundles = {}
        
        # Group by layer
        by_layer = defaultdict(list)
        for file_id, file_data in self.files.items():
            if file_id in assigned_files:
                continue
            
            layer = file_data.get('layer')
            if layer in ['SSOT', 'GOVERNANCE', 'VALIDATION', 'EXECUTION']:
                by_layer[layer].append(file_id)
        
        # Create bundles per layer
        for layer, file_ids in by_layer.items():
            if file_ids:
                anchor_id = file_ids[0]
                bundle_key = f"{layer.lower()}_bundle"
                
                bundle_id = self.create_bundle(bundle_key, anchor_id, file_ids)
                bundles[bundle_id] = self.bundles[bundle_id]
        
        return bundles
    
    def detect_doc_bundles(self, assigned_files: Set[str]) -> Dict:
        """Group documentation files."""
        bundles = {}
        
        doc_files = []
        for file_id, file_data in self.files.items():
            if file_id in assigned_files:
                continue
            
            if file_data.get('artifact_kind') == 'MARKDOWN' or file_data.get('layer') == 'DOCUMENTATION':
                doc_files.append(file_id)
        
        if doc_files:
            anchor_id = doc_files[0]
            bundle_key = "documentation_bundle"
            
            bundle_id = self.create_bundle(bundle_key, anchor_id, doc_files)
            bundles[bundle_id] = self.bundles[bundle_id]
        
        return bundles
    
    def assign_bundle_fields(self):
        """Assign bundle fields to all files."""
        updates = 0
        
        for bundle_id, bundle_data in self.bundles.items():
            anchor_id = bundle_data['anchor_file_id']
            bundle_key = bundle_data['bundle_key']
            
            for file_id in bundle_data['file_ids']:
                file_entry = self.files[file_id]
                
                # Assign bundle fields
                file_entry['bundle_id'] = bundle_id
                file_entry['bundle_key'] = bundle_key
                file_entry['anchor_file_id'] = anchor_id
                
                # Infer bundle_role
                file_entry['bundle_role'] = self.infer_bundle_role(file_entry)
                
                updates += 1
        
        print(f"Updated {updates} file entries with bundle assignments")
    
    def infer_bundle_role(self, file_entry: Dict) -> str:
        """Infer bundle_role from file metadata."""
        artifact_kind = file_entry.get('artifact_kind', '')
        layer = file_entry.get('layer', '')
        rel_path = file_entry.get('relative_path', '').lower()
        
        if artifact_kind == 'SCHEMA':
            return 'SCHEMA'
        elif artifact_kind == 'TEST':
            return 'TEST'
        elif 'validator' in rel_path or 'validate' in rel_path:
            return 'VALIDATOR'
        elif 'scanner' in rel_path or 'scan' in rel_path:
            return 'TOOL'
        elif 'runner' in rel_path or 'gate' in rel_path or layer == 'EXECUTION':
            return 'RUNNER'
        elif 'reporter' in rel_path or 'report' in rel_path or layer == 'REPORTING':
            return 'REPORT'
        elif layer == 'DOCUMENTATION':
            return 'DOC'
        elif layer == 'SSOT':
            return 'SCHEMA'
        elif layer == 'GOVERNANCE':
            return 'EXECUTOR'
        elif artifact_kind == 'PYTHON_MODULE':
            return 'TOOL'
        
        return None
    
    def save_registry(self):
        """Save updated registry."""
        self.registry['files'] = list(self.files.values())
        
        with open(REGISTRY_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.registry, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Registry saved to {REGISTRY_PATH}")
    
    def run(self):
        """Run the enhanced bundle detection."""
        self.detect_bundles()
        self.assign_bundle_fields()
        self.save_registry()
        print("\n✓ Enhanced bundle detection complete")

def main():
    detector = EnhancedBundleDetector(REGISTRY_PATH)
    detector.run()

if __name__ == "__main__":
    main()
