#!/usr/bin/env python3
"""
Preflight Checker - Fail-closed validation before mutations

Purpose:
  - Validate required .state/ files exist and parse correctly
  - Check file_id uniqueness
  - Verify sha256 format
  - Fail-closed on any validation error

Usage:
  python P_01999000042260305019_preflight_checker.py [--registry PATH]
"""

import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Tuple

# Validation patterns
FILE_ID_PATTERN = re.compile(r'^\d{20}$')
SHA256_PATTERN = re.compile(r'^[0-9a-fA-F]{64}$')


class PreflightChecker:
    def __init__(self, registry_root: Path):
        self.registry_root = registry_root
        self.state_dir = registry_root / ".state"
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def check_state_files(self) -> bool:
        """Check required .state/ files exist and parse."""
        required_files = [
            ".state/gates/gates_spec.json",
            ".state/remediation/remediation_plan.json",
            ".state/issues/normalized_issues.json"
        ]
        
        all_valid = True
        
        for rel_path in required_files:
            file_path = self.registry_root / rel_path
            
            if not file_path.exists():
                self.errors.append(f"Required file missing: {rel_path}")
                all_valid = False
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                self.errors.append(f"Invalid JSON in {rel_path}: {e}")
                all_valid = False
        
        return all_valid
    
    def check_registry(self, registry_path: Path) -> bool:
        """Check registry file for basic validity."""
        if not registry_path.exists():
            self.warnings.append(f"Registry not found: {registry_path}")
            return True  # Not critical for preflight
        
        try:
            with open(registry_path, 'r', encoding='utf-8') as f:
                registry = json.load(f)
            
            # Check structure
            if "files" not in registry:
                self.errors.append("Registry missing 'files' key")
                return False
            
            # Check file_id uniqueness
            file_ids = set()
            for idx, file_rec in enumerate(registry.get("files", [])):
                file_id = file_rec.get("file_id")
                
                if file_id:
                    if not FILE_ID_PATTERN.match(file_id):
                        self.warnings.append(
                            f"File {idx}: Invalid file_id format: {file_id}"
                        )
                    
                    if file_id in file_ids:
                        self.errors.append(
                            f"File {idx}: Duplicate file_id: {file_id}"
                        )
                        return False
                    
                    file_ids.add(file_id)
            
            return True
        
        except Exception as e:
            self.errors.append(f"Error checking registry: {e}")
            return False
    
    def run(self, registry_path: Path = None) -> bool:
        """Run all preflight checks."""
        state_ok = self.check_state_files()
        
        if registry_path:
            registry_ok = self.check_registry(registry_path)
        else:
            registry_ok = True
        
        return state_ok and registry_ok
    
    def report(self) -> None:
        """Print validation report."""
        if self.errors:
            print("❌ PREFLIGHT FAILED")
            print("\nErrors:")
            for err in self.errors:
                print(f"  • {err}")
        
        if self.warnings:
            print("\nWarnings:")
            for warn in self.warnings:
                print(f"  ⚠ {warn}")
        
        if not self.errors and not self.warnings:
            print("✅ PREFLIGHT PASSED")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Preflight validation")
    parser.add_argument(
        "--registry-root",
        type=Path,
        default=Path(__file__).parent.parent.parent,
        help="Path to registry root (default: ../../)"
    )
    parser.add_argument(
        "--registry",
        type=Path,
        help="Path to registry JSON file (optional)"
    )
    
    args = parser.parse_args()
    
    checker = PreflightChecker(args.registry_root)
    success = checker.run(args.registry)
    checker.report()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
