#!/usr/bin/env python3
"""
Entity Canonicalization - Module Name Deduplicator (Week 2 Track B - Script 2/2)

Purpose:
  - Detect duplicate module names across repo roots
  - Build canonical module_name → file_id mappings
  - Flag cross-repo ambiguities
  - Generate MODULE_NAME_RESOLUTION.json

Usage:
  python P_01999000042260305013_module_dedup.py --registry PATH --output PATH
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict

_FILE_WATCHER_PREFIX = "01260207201000001245_FILE WATCHER"

class ModuleDeduplicator:
    def __init__(self, registry_path: Path):
        self.registry_path = registry_path
        self.module_to_files: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.duplicates: List[Dict[str, Any]] = []
        self.resolutions: Dict[str, str] = {}
    
    def load_registry(self) -> Dict[str, Any]:
        """Load registry."""
        with open(self.registry_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def extract_module_name(self, relative_path: str) -> str:
        """Extract Python module name from path."""
        path = Path(relative_path)
        
        if path.suffix == '.py':
            # Convert path to module notation
            parts = path.with_suffix('').parts
            # Skip common prefixes
            filtered = [p for p in parts if not p.startswith('.') and not p.startswith('01')]
            module = '.'.join(filtered) if filtered else path.stem
            return module
        
        return ""
    
    def analyze_modules(self, registry: Dict[str, Any]) -> None:
        """Analyze module names across files."""
        files = registry.get("files", [])
        files = [f for f in files
                 if not f.get("relative_path", "").startswith(_FILE_WATCHER_PREFIX)]
        
        for file_record in files:
            rel_path = file_record.get("relative_path", "")
            
            if rel_path.endswith('.py'):
                module_name = self.extract_module_name(rel_path)
                
                if module_name:
                    self.module_to_files[module_name].append({
                        "file_id": file_record.get("file_id"),
                        "relative_path": rel_path,
                        "repo_root_id": file_record.get("repo_root_id"),
                        "canonicality": file_record.get("canonicality")
                    })
    
    def detect_duplicates(self) -> None:
        """Detect duplicate module names."""
        for module_name, files in self.module_to_files.items():
            if len(files) > 1:
                self.duplicates.append({
                    "module_name": module_name,
                    "occurrences": len(files),
                    "files": files
                })
    
    def resolve_duplicates(self) -> None:
        """Resolve duplicates by preferring CANONICAL in same repo_root."""
        for dup in self.duplicates:
            module_name = dup["module_name"]
            files = dup["files"]
            
            # Group by repo_root_id
            by_repo = defaultdict(list)
            for f in files:
                repo_root = f.get("repo_root_id", "UNKNOWN")
                by_repo[repo_root].append(f)
            
            # If all in same repo, pick CANONICAL
            if len(by_repo) == 1:
                repo_files = list(by_repo.values())[0]
                canonical = [f for f in repo_files if f.get("canonicality") == "CANONICAL"]
                
                if canonical:
                    self.resolutions[module_name] = canonical[0]["file_id"]
                else:
                    # Pick first
                    self.resolutions[module_name] = repo_files[0]["file_id"]
            else:
                # Cross-repo ambiguity - cannot resolve automatically
                self.resolutions[module_name] = None
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate deduplication report."""
        return {
            "registry_source": str(self.registry_path),
            "total_modules": len(self.module_to_files),
            "duplicates_detected": len(self.duplicates),
            "duplicates": self.duplicates,
            "canonical_resolutions": {
                k: v for k, v in self.resolutions.items() if v is not None
            },
            "unresolvable_ambiguities": [
                k for k, v in self.resolutions.items() if v is None
            ]
        }
    
    def run(self, output_path: Path) -> int:
        """Run module deduplication."""
        try:
            print("Loading registry...")
            registry = self.load_registry()
            
            print("Analyzing modules...")
            self.analyze_modules(registry)
            
            print("Detecting duplicates...")
            self.detect_duplicates()
            
            if self.duplicates:
                print(f"⚠️  Found {len(self.duplicates)} duplicate module names")
                print("Resolving duplicates...")
                self.resolve_duplicates()
            
            print("Generating report...")
            report = self.generate_report()
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ Report: {output_path}")
            print(f"   Total modules: {report['total_modules']}")
            print(f"   Duplicates: {report['duplicates_detected']}")
            print(f"   Resolved: {len(report['canonical_resolutions'])}")
            print(f"   Unresolvable: {len(report['unresolvable_ambiguities'])}")
            
            return 0 if not report['unresolvable_ambiguities'] else 1
            
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return 2

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Module Name Deduplicator')
    parser.add_argument('--registry', 
                       default='../../01999000042260124503_REGISTRY_file.json')
    parser.add_argument('--output',
                       default='../../.state/entity_resolution/MODULE_NAME_RESOLUTION.json')
    args = parser.parse_args()
    
    script_dir = Path(__file__).parent
    registry_path = (script_dir / args.registry).resolve()
    output_path = (script_dir / args.output).resolve()
    
    deduplicator = ModuleDeduplicator(registry_path)
    exit_code = deduplicator.run(output_path)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
