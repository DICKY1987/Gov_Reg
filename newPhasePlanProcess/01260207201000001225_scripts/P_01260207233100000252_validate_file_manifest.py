#!/usr/bin/env python3
"""
File Manifest Validation

Validates file_manifest section completeness including file tracking,
permissions, and conflict risk analysis.

Exit Codes:
    0: Manifest valid
    1: Validation errors
    2: File not found
    3: Invalid JSON
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FileManifestValidator:
    """Validates file manifest structure and completeness"""
    
    VALID_FILE_TYPES = ['source', 'test', 'config', 'docs', 'schema', 'script', 'evidence']
    VALID_PERMISSIONS = ['create', 'read', 'write', 'delete']
    VALID_CONFLICT_RISKS = ['none', 'low', 'medium', 'high']
    
    def __init__(self, plan_path: str):
        self.plan_path = Path(plan_path)
        self.plan_data: Dict[str, Any] = {}
        self.errors: List[Dict[str, str]] = []
        self.warnings: List[Dict[str, str]] = []
        
    def validate(self) -> Tuple[bool, Dict[str, Any]]:
        """Run all manifest validation checks"""
        logger.info(f"Validating file manifest: {self.plan_path}")
        
        if not self._load_plan():
            return False, self._generate_evidence()
        
        self._validate_manifest_structure()
        self._validate_file_entries()
        self._validate_permissions()
        self._validate_conflict_risks()
        self._check_duplicate_files()
        
        is_valid = len(self.errors) == 0
        logger.info(f"{'✅ PASSED' if is_valid else '❌ FAILED'}: {len(self.errors)} errors")
        return is_valid, self._generate_evidence()
    
    def _load_plan(self) -> bool:
        """Load plan JSON"""
        if not self.plan_path.exists():
            self.errors.append({'error_code': 'FILE_NOT_FOUND', 'error_message': f'Plan not found: {self.plan_path}', 'severity': 'critical'})
            return False
        
        try:
            with open(self.plan_path, 'r', encoding='utf-8') as f:
                self.plan_data = json.load(f)
            return True
        except json.JSONDecodeError as e:
            self.errors.append({'error_code': 'INVALID_JSON', 'error_message': str(e), 'severity': 'critical'})
            return False
    
    def _validate_manifest_structure(self):
        """Validate file_manifest exists and has proper structure"""
        if 'plan' not in self.plan_data or 'file_manifest' not in self.plan_data['plan']:
            self.warnings.append({'warning_code': 'MISSING_FILE_MANIFEST', 'warning_message': 'file_manifest section missing'})
            return
        
        manifest = self.plan_data['plan']['file_manifest']
        if not isinstance(manifest, dict):
            self.errors.append({'error_code': 'INVALID_MANIFEST_TYPE', 'error_message': 'file_manifest must be object', 'severity': 'error'})
    
    def _validate_file_entries(self):
        """Validate individual file entries"""
        manifest = self.plan_data.get('plan', {}).get('file_manifest', {})
        
        for file_path, file_data in manifest.items():
            if not isinstance(file_data, dict):
                self.errors.append({'error_code': 'INVALID_FILE_ENTRY', 'error_message': f'File entry {file_path} must be object', 'severity': 'error'})
                continue
            
            # Validate file_type
            file_type = file_data.get('file_type')
            if file_type and file_type not in self.VALID_FILE_TYPES:
                self.errors.append({'error_code': 'INVALID_FILE_TYPE', 'error_message': f'File {file_path} has invalid type: {file_type}', 'severity': 'error'})
            
            # Check for required fields
            if 'phase_id' not in file_data:
                self.warnings.append({'warning_code': 'MISSING_PHASE_ID', 'warning_message': f'File {file_path} missing phase_id'})
    
    def _validate_permissions(self):
        """Validate permission specifications"""
        manifest = self.plan_data.get('plan', {}).get('file_manifest', {})
        
        for file_path, file_data in manifest.items():
            if not isinstance(file_data, dict):
                continue
            
            permissions = file_data.get('permissions', [])
            if not isinstance(permissions, list):
                self.errors.append({'error_code': 'INVALID_PERMISSIONS_TYPE', 'error_message': f'File {file_path} permissions must be array', 'severity': 'error'})
                continue
            
            for perm in permissions:
                if perm not in self.VALID_PERMISSIONS:
                    self.errors.append({'error_code': 'INVALID_PERMISSION', 'error_message': f'File {file_path} has invalid permission: {perm}', 'severity': 'error'})
    
    def _validate_conflict_risks(self):
        """Validate conflict_risk levels"""
        manifest = self.plan_data.get('plan', {}).get('file_manifest', {})
        
        for file_path, file_data in manifest.items():
            if not isinstance(file_data, dict):
                continue
            
            risk = file_data.get('conflict_risk')
            if risk and risk not in self.VALID_CONFLICT_RISKS:
                self.errors.append({'error_code': 'INVALID_CONFLICT_RISK', 'error_message': f'File {file_path} has invalid conflict_risk: {risk}', 'severity': 'error'})
    
    def _check_duplicate_files(self):
        """Check for duplicate file paths"""
        manifest = self.plan_data.get('plan', {}).get('file_manifest', {})
        seen = set()
        
        for file_path in manifest.keys():
            normalized = Path(file_path).as_posix().lower()
            if normalized in seen:
                self.errors.append({'error_code': 'DUPLICATE_FILE', 'error_message': f'Duplicate file path: {file_path}', 'severity': 'error'})
            seen.add(normalized)
    
    def _generate_evidence(self) -> Dict[str, Any]:
        """Generate evidence artifact"""
        manifest = self.plan_data.get('plan', {}).get('file_manifest', {})
        
        return {
            'gate_id': 'FILE_MANIFEST_VALIDATION',
            'validated_at': datetime.utcnow().isoformat() + 'Z',
            'validator_version': '1.0.0',
            'plan_file': str(self.plan_path),
            'validation_result': {
                'status': 'valid' if len(self.errors) == 0 else 'invalid',
                'errors_count': len(self.errors),
                'warnings_count': len(self.warnings),
                'errors': self.errors,
                'warnings': self.warnings
            },
            'statistics': {
                'total_files': len(manifest),
                'files_by_type': self._count_by_type(manifest)
            }
        }
    
    def _count_by_type(self, manifest: Dict) -> Dict[str, int]:
        """Count files by type"""
        counts = {}
        for file_data in manifest.values():
            if isinstance(file_data, dict):
                file_type = file_data.get('file_type', 'unknown')
                counts[file_type] = counts.get(file_type, 0) + 1
        return counts


def main():
    parser = argparse.ArgumentParser(description='Validate file manifest')
    parser.add_argument('--plan-file', required=True, help='Path to plan JSON file')
    parser.add_argument('--evidence-dir', default='.state/evidence/FILE_MANIFEST')
    
    args = parser.parse_args()
    
    validator = FileManifestValidator(args.plan_file)
    is_valid, evidence = validator.validate()
    
    evidence_dir = Path(args.evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    
    with open(evidence_dir / 'file_manifest_validation.json', 'w') as f:
        json.dump(evidence, f, indent=2)
    
    print(f"\n{'✅ PASSED' if is_valid else '❌ FAILED'}: File Manifest Validation")
    print(f"Errors: {len(validator.errors)}, Warnings: {len(validator.warnings)}\n")
    
    sys.exit(0 if is_valid else 1)


if __name__ == '__main__':
    main()
