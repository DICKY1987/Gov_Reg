#!/usr/bin/env python3
"""
Registry Path Cleaner - Remove FILE WATCHER pollution

Purpose:
  - Clean polluted relative_path, file_path, module_name
  - Remove FILE WATCHER prefix from paths
  - Re-run dedup after cleanup
  - Fail if pollution remains after cleanup

Usage:
  python P_01999000042260305020_registry_path_cleaner.py --registry PATH [--apply]
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
import re

_FILE_WATCHER_PREFIX = "01260207201000001245_FILE WATCHER"


class RegistryPathCleaner:
    def __init__(self, registry_path: Path):
        self.registry_path = registry_path
        self.polluted_count = 0
        self.cleaned_count = 0
        self.errors = []
    
    def detect_pollution(self, registry: Dict[str, Any]) -> List[int]:
        ""Detect files with polluted paths.""
        polluted_indices = []
        
        for idx, file_rec in enumerate(registry.get("files", [])):
            rel_path = file_rec.get("relative_path", "")
            file_path = file_rec.get("file_path", "")
            module_name = file_rec.get("module_name", "")
            
            if (_FILE_WATCHER_PREFIX in rel_path or 
                _FILE_WATCHER_PREFIX in file_path or 
                _FILE_WATCHER_PREFIX in module_name):
                polluted_indices.append(idx)
        
        return polluted_indices
    
    def clean_path(self, path: str) -> str:
        ""Remove FILE WATCHER prefix from path.""
        if _FILE_WATCHER_PREFIX in path:
            # Remove the prefix and normalize
            cleaned = path.replace(_FILE_WATCHER_PREFIX + "\\", "")
            cleaned = cleaned.replace(_FILE_WATCHER_PREFIX + "/", "")
            cleaned = cleaned.replace(_FILE_WATCHER_PREFIX, "")
            return cleaned.lstrip("\\/")
        return path
    
    def clean_registry(self, registry: Dict[str, Any]) -> Dict[str, Any]:
        ""Clean all polluted paths in registry.""
        files = registry.get("files", [])
        
        for idx, file_rec in enumerate(files):
            was_polluted = False
            
            if "relative_path" in file_rec:
                cleaned = self.clean_path(file_rec["relative_path"])
                if cleaned != file_rec["relative_path"]:
                    file_rec["relative_path"] = cleaned
                    was_polluted = True
            
            if "file_path" in file_rec:
                cleaned = self.clean_path(file_rec["file_path"])
                if cleaned != file_rec["file_path"]:
                    file_rec["file_path"] = cleaned
                    was_polluted = True
            
            if "module_name" in file_rec:
                cleaned = self.clean_path(file_rec["module_name"])
                if cleaned != file_rec["module_name"]:
                    file_rec["module_name"] = cleaned
                    was_polluted = True
            
            if was_polluted:
                self.cleaned_count += 1
        
        return registry
    
    def run(self, apply: bool = False) -> bool:
        ""Run path cleanup.""
        with open(self.registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
        
        # Detect pollution
        polluted_indices = self.detect_pollution(registry)
        self.polluted_count = len(polluted_indices)
        
        print(f"Found {self.polluted_count} polluted files")
        
        if self.polluted_count == 0:
            print("✅ No pollution detected")
            return True
        
        if not apply:
            print("Run with --apply to clean paths")
            return True
        
        # Clean paths
        registry = self.clean_registry(registry)
        
        # Verify cleanup
        remaining = self.detect_pollution(registry)
        if remaining:
            self.errors.append(f"Pollution remains after cleanup: {len(remaining)} files")
            return False
        
        # Save cleaned registry
        backup_path = self.registry_path.parent / f"{self.registry_path.name}.backup"
        import shutil
        shutil.copy(self.registry_path, backup_path)
        
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2)
        
        print(f"✅ Cleaned {self.cleaned_count} files")
        print(f"Backup: {backup_path}")
        
        return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean polluted registry paths")
    parser.add_argument('--registry', type=Path, required=True)
    parser.add_argument('--apply', action='store_true', help='Apply changes')
    
    args = parser.parse_args()
    
    cleaner = RegistryPathCleaner(args.registry)
    success = cleaner.run(args.apply)
    
    if cleaner.errors:
        for err in cleaner.errors:
            print(f"❌ {err}", file=sys.stderr)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
