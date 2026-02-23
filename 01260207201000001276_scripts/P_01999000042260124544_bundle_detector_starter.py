#!/usr/bin/env python3
"""
Bundle Detection Starter Script

This script provides a framework for Phase 1 bundle detection:
- Identify anchor files (schemas, SSOT)
- Extract hard wiring edges (imports, $refs, CLI calls)
- Build connected components
- Assign bundle_id and bundle_key values

TODO: Implement the detection logic based on your specific needs.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent / "PATH_FILES"))

try:
    from path_registry import resolve_path
    REGISTRY_PATH = resolve_path("REGISTRY_UNIFIED")
except ImportError:
    # Fallback: look in parent directory (since we're now in scripts/)
    REGISTRY_PATH = Path(__file__).parent.parent / "01999000042260124503_governance_registry_unified.json"

class BundleDetector:
    def __init__(self, registry_path: Path):
        with open(registry_path, 'r', encoding='utf-8') as f:
            self.registry = json.load(f)
        self.files = {f['file_id']: f for f in self.registry.get('files', [])}
        self.edges = []
        self.bundles = {}
        
    def identify_anchors(self) -> List[str]:
        """
        Identify anchor files (schemas, SSOT, rule definitions).
        Priority order:
        1. Schema files (*.schema.json)
        2. SSOT policy/rule definitions
        3. Gate/runner entrypoints
        """
        anchors = []
        
        for file_id, file_data in self.files.items():
            rel_path = file_data.get('relative_path', '')
            artifact_kind = file_data.get('artifact_kind', '')
            layer = file_data.get('layer', '')
            
            # Schema files are primary anchors
            if '.schema.json' in rel_path or artifact_kind == 'SCHEMA':
                anchors.append(file_id)
                continue
            
            # SSOT/rule definitions
            if layer == 'SSOT' or 'rule' in rel_path.lower():
                anchors.append(file_id)
                continue
            
            # Gate/runner entrypoints
            if 'gate' in rel_path.lower() or 'runner' in rel_path.lower():
                if artifact_kind == 'PYTHON_MODULE':
                    anchors.append(file_id)
        
        print(f"Identified {len(anchors)} anchor files")
        return anchors
    
    def extract_edges(self):
        """
        Extract hard wiring edges from files.
        
        Edge types:
        - USES_SCHEMA: JSON Schema $ref
        - DEPENDS_ON: Python import
        - EXECUTES: CLI/runner calls
        - VALIDATES: Validator referencing schema
        - TESTS: Test importing module
        """
        # TODO: Implement edge extraction
        # For now, this is a placeholder
        
        # Example edge structure:
        # {
        #   "source_file_id": "0199900004226012451",
        #   "edge_type": "DEPENDS_ON",
        #   "target_file_id": "0199900004226012452",
        #   "evidence": {
        #     "evidence_type": "PY_IMPORT",
        #     "evidence_locator": "line 10: from module import X",
        #     "status": "PROVEN"
        #   }
        # }
        
        print(f"Edge extraction: TODO - implement for your codebase")
        pass
    
    def build_bundles(self, anchors: List[str]):
        """
        Build connected components around anchors.
        Each component = one bundle.
        """
        # TODO: Implement connected component algorithm
        # For now, create one bundle per anchor
        
        bundle_counter = 1000000000000000  # 16-digit base
        
        for anchor_id in anchors:
            bundle_id = str(bundle_counter)
            bundle_counter += 1
            
            # Generate bundle_key from anchor filename
            anchor_file = self.files[anchor_id]
            rel_path = anchor_file.get('relative_path', '')
            bundle_key = self._generate_bundle_key(rel_path)
            
            self.bundles[bundle_id] = {
                'bundle_id': bundle_id,
                'bundle_key': bundle_key,
                'anchor_file_id': anchor_id,
                'file_ids': [anchor_id]  # TODO: expand to connected component
            }
            
            print(f"  Bundle {bundle_id}: {bundle_key} (anchor: {anchor_id})")
        
        print(f"Created {len(self.bundles)} bundles")
    
    def _generate_bundle_key(self, path: str) -> str:
        """Generate human-readable bundle key from path."""
        # Extract meaningful name from path
        name = Path(path).stem
        
        # Remove file_id prefix if present
        if '_' in name:
            parts = name.split('_')
            if parts[0].isdigit():
                name = '_'.join(parts[1:])
        
        # Convert to uppercase snake_case
        bundle_key = name.upper().replace('-', '_').replace('.', '_')
        
        return bundle_key
    
    def assign_bundle_fields(self):
        """Assign bundle_id, bundle_key, bundle_role to files."""
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
                
                # Infer bundle_role from artifact_kind
                file_entry['bundle_role'] = self._infer_bundle_role(file_entry)
                
                updates += 1
        
        print(f"Updated {updates} file entries with bundle assignments")
    
    def _infer_bundle_role(self, file_entry: Dict) -> str:
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
        elif 'runner' in rel_path or 'gate' in rel_path:
            return 'RUNNER'
        elif 'report' in rel_path:
            return 'REPORT'
        elif layer == 'DOCUMENTATION':
            return 'DOC'
        
        return None  # Unknown role
    
    def save_registry(self):
        """Save updated registry back to file."""
        # Update files array
        self.registry['files'] = list(self.files.values())
        
        # Add edges array
        self.registry['edges'] = self.edges
        
        # Write back
        with open(REGISTRY_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.registry, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Registry saved to {REGISTRY_PATH}")
    
    def run(self):
        """Run the full bundle detection pipeline."""
        print("=== Bundle Detection Pipeline ===\n")
        
        print("Step 1: Identify anchors")
        anchors = self.identify_anchors()
        
        print("\nStep 2: Extract edges")
        self.extract_edges()
        
        print("\nStep 3: Build bundles")
        self.build_bundles(anchors)
        
        print("\nStep 4: Assign bundle fields")
        self.assign_bundle_fields()
        
        print("\nStep 5: Save registry")
        self.save_registry()
        
        print("\n✓ Bundle detection complete")

def main():
    detector = BundleDetector(REGISTRY_PATH)
    detector.run()

if __name__ == "__main__":
    main()
