#!/usr/bin/env python3
"""End-to-End Validation (Week 3 - Component 3/6)"""
import json
import sys
from pathlib import Path
from P_01999000042260305005_column_loader import ColumnLoader
from P_01999000042260305006_column_validator import ColumnValidator

class EndToEndValidator:
    def __init__(self):
        self.loader = ColumnLoader()
        self.validator = ColumnValidator()
        self.errors = []
    
    def validate_registry_structure(self, registry: dict) -> bool:
        """Validate registry has required top-level structure."""
        required_keys = ["files", "edges"]
        missing = [k for k in required_keys if k not in registry]
        
        if missing:
            self.errors.append(f"Missing top-level keys: {missing}")
            return False
        
        return True
    
    def validate_all_files(self, files: list) -> bool:
        """Validate all file records."""
        all_valid = True
        
        for idx, file_rec in enumerate(files):
            is_valid, errors = self.validator.validate_record(file_rec)
            if not is_valid:
                all_valid = False
                self.errors.extend([f"File {idx}: {e}" for e in errors])
        
        return all_valid
    
    def run_validation(self, registry_path: Path) -> bool:
        """Run complete validation."""
        with open(registry_path, encoding='utf-8') as f:
            registry = json.load(f)
        
        if not self.validate_registry_structure(registry):
            return False
        
        files = registry.get("files", [])
        print(f"Validating {len(files)} files...")
        
        return self.validate_all_files(files)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--registry', required=True)
    args = parser.parse_args()
    
    validator = EndToEndValidator()
    
    if validator.run_validation(Path(args.registry)):
        print("✅ Validation passed")
        sys.exit(0)
    else:
        print(f"❌ Validation failed: {len(validator.errors)} errors")
        for err in validator.errors[:10]:
            print(f"  • {err}")
        sys.exit(1)

if __name__ == "__main__":
    main()
