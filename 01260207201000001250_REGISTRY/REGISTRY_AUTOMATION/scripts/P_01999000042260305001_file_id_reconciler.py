#!/usr/bin/env python3
"""
File ID Reconciliation Layer (Week 1 Step 1.3)

Purpose:
  - Build sha256 → file_id and file_id → sha256 mappings
  - Validate file_id format (20-digit numeric)
  - Validate sha256 format (64-char hex)
  - Generate SHA256_TO_FILE_ID.json for downstream use

CRITICAL: Component IDs must use file_id (20-digit), never doc_id or content_sha256.

Usage:
  python P_01999000042260305001_file_id_reconciler.py [--registry PATH] [--output PATH]
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Tuple
import re

# Validation patterns
FILE_ID_PATTERN = re.compile(r'^\d{20}$')
SHA256_PATTERN = re.compile(r'^[0-9a-fA-F]{64}$')


class FileIDReconciler:
    def __init__(self, registry_path: str):
        self.registry_path = Path(registry_path)
        self.sha256_to_file_id: Dict[str, str] = {}
        self.file_id_to_sha256: Dict[str, str] = {}
        self.validation_errors = []
        
    def load_registry(self) -> Dict[str, Any]:
        """Load registry JSON."""
        with open(self.registry_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def validate_file_id(self, file_id: Any) -> Tuple[bool, str]:
        """Validate file_id is 20-digit numeric string."""
        if not isinstance(file_id, str):
            return False, f"file_id must be string, got {type(file_id).__name__}"
        
        if not FILE_ID_PATTERN.match(file_id):
            return False, f"file_id must be 20-digit numeric, got: {file_id}"
        
        return True, ""
    
    def validate_sha256(self, sha256: Any) -> Tuple[bool, str]:
        """Validate sha256 is 64-char hex string."""
        if sha256 is None:
            return False, "sha256 is None"
        
        if not isinstance(sha256, str):
            return False, f"sha256 must be string, got {type(sha256).__name__}"
        
        if not SHA256_PATTERN.match(sha256):
            return False, f"sha256 must be 64-char hex, got: {sha256}"
        
        return True, ""
    
    def build_mappings(self, registry: Dict[str, Any]) -> None:
        """Build bidirectional mappings from registry."""
        files = registry.get("files", [])
        
        for idx, file_record in enumerate(files):
            file_id = file_record.get("file_id")
            sha256 = file_record.get("sha256")
            relative_path = file_record.get("relative_path", f"<index {idx}>")
            
            # Validate file_id
            valid_fid, fid_error = self.validate_file_id(file_id)
            if not valid_fid:
                self.validation_errors.append({
                    "record_index": idx,
                    "relative_path": relative_path,
                    "field": "file_id",
                    "value": file_id,
                    "error": fid_error
                })
                continue
            
            # Validate sha256
            valid_sha, sha_error = self.validate_sha256(sha256)
            if not valid_sha:
                self.validation_errors.append({
                    "record_index": idx,
                    "relative_path": relative_path,
                    "field": "sha256",
                    "value": sha256,
                    "error": sha_error
                })
                continue
            
            # Build mappings
            self.sha256_to_file_id[sha256] = file_id
            self.file_id_to_sha256[file_id] = sha256
    
    def write_output(self, output_path: Path) -> None:
        """Write SHA256_TO_FILE_ID.json."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        output_data = {
            "sha256_to_file_id": self.sha256_to_file_id,
            "file_id_to_sha256": self.file_id_to_sha256,
            "total_mappings": len(self.sha256_to_file_id),
            "validation_errors": self.validation_errors,
            "source": "P_01999000042260305001_file_id_reconciler.py",
            "registry_source": str(self.registry_path)
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    def report(self) -> None:
        """Print reconciliation report."""
        print(f"Registry: {self.registry_path}")
        print(f"Total mappings: {len(self.sha256_to_file_id)}")
        
        if self.validation_errors:
            print(f"\n⚠️  Validation errors: {len(self.validation_errors)}")
            for err in self.validation_errors[:10]:
                print(f"  • {err['relative_path']}: {err['field']} - {err['error']}")
            if len(self.validation_errors) > 10:
                print(f"  ... and {len(self.validation_errors) - 10} more")
        else:
            print("✅ No validation errors")
    
    def run(self, output_path: Path) -> int:
        """Run reconciliation."""
        try:
            print("Loading registry...")
            registry = self.load_registry()
            
            print("Building mappings...")
            self.build_mappings(registry)
            
            print("Writing output...")
            self.write_output(output_path)
            
            print()
            self.report()
            
            if self.validation_errors:
                return 1
            return 0
        
        except Exception as e:
            print(f"❌ ERROR: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return 2


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='File ID Reconciliation Layer')
    parser.add_argument('--registry', 
                       default='../../01999000042260124503_REGISTRY_file.json',
                       help='Path to registry JSON')
    parser.add_argument('--output',
                       default='../../.state/purpose_mapping/SHA256_TO_FILE_ID.json',
                       help='Output path for mappings')
    
    args = parser.parse_args()
    
    # Resolve paths relative to script location
    script_dir = Path(__file__).parent
    registry_path = (script_dir / args.registry).resolve()
    output_path = (script_dir / args.output).resolve()
    
    reconciler = FileIDReconciler(str(registry_path))
    exit_code = reconciler.run(output_path)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
