#!/usr/bin/env python3
"""
Entity Canonicalization - doc_id Resolver (Week 2 Track B - Script 1/2)

Purpose:
  - Resolve doc_id collisions and inconsistencies
  - Build canonical doc_id → file_id mappings
  - Detect and flag ambiguous doc_ids
  - Generate DOC_ID_RESOLUTION.json

Usage:
  python P_01999000042260305012_doc_id_resolver.py --registry PATH --output PATH
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict

_FILE_WATCHER_PREFIX = "01260207201000001245_FILE WATCHER"

class DocIdResolver:
    def __init__(self, registry_path: Path):
        self.registry_path = registry_path
        self.doc_id_to_file_ids: Dict[str, List[str]] = defaultdict(list)
        self.collisions: List[Dict[str, Any]] = []
        self.resolutions: Dict[str, str] = {}
    
    def load_registry(self) -> Dict[str, Any]:
        """Load registry."""
        with open(self.registry_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def analyze_doc_ids(self, registry: Dict[str, Any]) -> None:
        """Analyze doc_id usage across files."""
        files = registry.get("files", [])
        files = [f for f in files
                 if not f.get("relative_path", "").startswith(_FILE_WATCHER_PREFIX)]
        
        for file_record in files:
            doc_id = file_record.get("doc_id")
            file_id = file_record.get("file_id")
            
            if doc_id and file_id:
                self.doc_id_to_file_ids[doc_id].append(file_id)
    
    def detect_collisions(self) -> None:
        """Detect doc_id collisions (1 doc_id → multiple file_ids)."""
        for doc_id, file_ids in self.doc_id_to_file_ids.items():
            if len(file_ids) > 1:
                self.collisions.append({
                    "doc_id": doc_id,
                    "file_ids": file_ids,
                    "collision_count": len(file_ids)
                })
    
    def resolve_collisions(self, registry: Dict[str, Any]) -> None:
        """
        Resolve collisions using heuristics:
        1. Prefer CANONICAL over LEGACY
        2. Prefer newer timestamps
        3. Prefer shorter paths
        """
        files_by_id = {f["file_id"]: f for f in registry.get("files", []) if "file_id" in f}
        
        for collision in self.collisions:
            doc_id = collision["doc_id"]
            file_ids = collision["file_ids"]
            
            # Score each file
            scored = []
            for fid in file_ids:
                file_rec = files_by_id.get(fid, {})
                score = 0
                
                # Canonicality score
                canonicality = file_rec.get("canonicality", "")
                if canonicality == "CANONICAL":
                    score += 100
                elif canonicality == "ALTERNATE":
                    score += 50
                elif canonicality == "LEGACY":
                    score += 0
                
                # Path length (shorter is better)
                path = file_rec.get("relative_path", "")
                score -= len(path) * 0.1
                
                scored.append((fid, score))
            
            # Pick highest score
            winner = max(scored, key=lambda x: x[1])[0]
            self.resolutions[doc_id] = winner
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate resolution report."""
        return {
            "registry_source": str(self.registry_path),
            "total_doc_ids": len(self.doc_id_to_file_ids),
            "collisions_detected": len(self.collisions),
            "collisions": self.collisions,
            "canonical_resolutions": self.resolutions,
            "doc_id_to_file_id": {
                doc_id: file_ids[0] if len(file_ids) == 1 else self.resolutions.get(doc_id)
                for doc_id, file_ids in self.doc_id_to_file_ids.items()
            }
        }
    
    def run(self, output_path: Path) -> int:
        """Run doc_id resolution."""
        try:
            print("Loading registry...")
            registry = self.load_registry()
            
            print("Analyzing doc_ids...")
            self.analyze_doc_ids(registry)
            
            print("Detecting collisions...")
            self.detect_collisions()
            
            if self.collisions:
                print(f"⚠️  Found {len(self.collisions)} doc_id collisions")
                print("Resolving collisions...")
                self.resolve_collisions(registry)
            
            print("Generating report...")
            report = self.generate_report()
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ Report: {output_path}")
            print(f"   Total doc_ids: {report['total_doc_ids']}")
            print(f"   Collisions: {report['collisions_detected']}")
            
            return 0 if not self.collisions else 1
            
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return 2


    def generate_resolution_patches(self) -> List[Dict[str, Any]]:
        ""Generate RFC-6902 patches for resolved collisions.""
        patches = []
        
        for doc_id, canonical_file_id in self.resolutions.items():
            # Patch to update doc_id references
            patches.append({
                "op": "replace",
                "path": f"/doc_id_resolution/{doc_id}",
                "value": canonical_file_id,
                "reason": "Resolved doc_id collision"
            })
        
        return patches
    
    def apply_resolutions(self, registry: Dict[str, Any], backup: bool = True) -> bool:
        ""Apply resolution patches to registry.""
        if backup:
            backup_path = self.registry_path.parent / f"{self.registry_path.name}.backup"
            import shutil
            shutil.copy(self.registry_path, backup_path)
            print(f"Backup created: {backup_path}")
        
        # Apply resolutions
        files = registry.get("files", [])
        for file_rec in files:
            doc_id = file_rec.get("doc_id")
            if doc_id in self.resolutions:
                # Update to canonical file_id reference
                file_rec["resolved_doc_id"] = self.resolutions[doc_id]
        
        return True

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='doc_id Resolver')
    parser.add_argument('--registry', 
                       default='../../01999000042260124503_REGISTRY_file.json')
    parser.add_argument('--output',
                       default='../../.state/entity_resolution/DOC_ID_RESOLUTION.json')
    args = parser.parse_args()
    
    script_dir = Path(__file__).parent
    registry_path = (script_dir / args.registry).resolve()
    output_path = (script_dir / args.output).resolve()
    
    resolver = DocIdResolver(registry_path)
    exit_code = resolver.run(output_path)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
