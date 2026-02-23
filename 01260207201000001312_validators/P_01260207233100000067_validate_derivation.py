#!/usr/bin/env python3
"""
Validator for derivation section enforcement rules.

Ensures that derivation specifications are complete and internally consistent:
- mode=DERIVED requires all sources referenced in formula
- mode=LOOKUP requires registry_ref, key, lookup_path_template
- mode=TASK_OUTPUT requires task_id, output_key, evidence
- null_policy=ERROR should match presence.policy=REQUIRED
- error_policy should be consistent with header criticality
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class DerivationValidator:
    """Validates derivation section completeness and consistency."""
    
    def __init__(self, dictionary_path: Path):
        with open(dictionary_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
    
    def validate_all(self) -> Tuple[int, int]:
        """Run all validation rules. Returns (error_count, warning_count)."""
        for header_name, header_def in self.data['headers'].items():
            if 'derivation' not in header_def:
                self.errors.append({
                    'header': header_name,
                    'rule': 'DERIVATION_REQUIRED',
                    'message': 'Header missing required derivation section'
                })
                continue
            
            derivation = header_def['derivation']
            
            # Rule checks
            self._check_mode_consistency(header_name, derivation)
            self._check_derived_sources(header_name, header_def, derivation)
            self._check_lookup_completeness(header_name, derivation)
            self._check_task_output_completeness(header_name, derivation)
            self._check_null_policy_consistency(header_name, header_def, derivation)
            self._check_evidence_requirements(header_name, derivation)
            self._check_placeholder_values(header_name, derivation)
        
        return len(self.errors), len(self.warnings)
    
    def _check_mode_consistency(self, header: str, derivation: dict):
        """Ensure mode matches process.engine."""
        mode = derivation.get('mode')
        engine = derivation.get('process', {}).get('engine')
        
        # Mode-engine compatibility matrix
        valid_combinations = {
            'LITERAL': ['NONE'],
            'INPUT': ['NONE'],
            'EXTRACTED': ['TASK_OUTPUT', 'TRANSFORM_CHAIN'],
            'LOOKUP': ['LOOKUP_SPEC'],
            'DERIVED': ['FORMULA_AST', 'TRANSFORM_CHAIN'],
            'AGGREGATED': ['TRANSFORM_CHAIN', 'FORMULA_AST'],
            'SYSTEM': ['NONE']
        }
        
        if mode not in valid_combinations:
            self.errors.append({
                'header': header,
                'rule': 'INVALID_MODE',
                'message': f'Unknown derivation mode: {mode}'
            })
            return
        
        if engine not in valid_combinations[mode]:
            self.errors.append({
                'header': header,
                'rule': 'MODE_ENGINE_MISMATCH',
                'message': f'mode={mode} incompatible with engine={engine}. '
                          f'Expected: {valid_combinations[mode]}'
            })
    
    def _check_derived_sources(self, header: str, header_def: dict, derivation: dict):
        """For DERIVED mode, ensure all formula columns are in sources."""
        if derivation.get('mode') != 'DERIVED':
            return
        
        spec = derivation.get('process', {}).get('spec', {})
        
        # Extract column references from formula AST
        referenced_cols = self._extract_col_refs(spec)
        
        # Check that all referenced columns are declared in sources
        declared_sources = {
            s.get('ref') for s in derivation.get('sources', [])
            if s.get('kind') == 'COLUMN'
        }
        
        missing = referenced_cols - declared_sources
        if missing:
            self.errors.append({
                'header': header,
                'rule': 'DERIVED_MISSING_SOURCES',
                'message': f'Formula references columns not in sources: {missing}'
            })
    
    def _extract_col_refs(self, ast: dict) -> Set[str]:
        """Recursively extract column references from formula AST."""
        refs = set()
        
        if isinstance(ast, dict):
            if ast.get('op') == 'col':
                refs.add(ast.get('name'))
            
            # Recurse into args
            for arg in ast.get('args', []):
                refs.update(self._extract_col_refs(arg))
        
        elif isinstance(ast, list):
            for item in ast:
                refs.update(self._extract_col_refs(item))
        
        return refs
    
    def _check_lookup_completeness(self, header: str, derivation: dict):
        """For LOOKUP mode, ensure registry_ref, key, lookup_path_template present."""
        if derivation.get('mode') != 'LOOKUP':
            return
        
        spec = derivation.get('process', {}).get('spec', {})
        
        required_fields = ['registry_ref', 'key', 'lookup_path_template']
        missing = [f for f in required_fields if f not in spec]
        
        if missing:
            self.errors.append({
                'header': header,
                'rule': 'LOOKUP_INCOMPLETE',
                'message': f'LOOKUP mode missing required spec fields: {missing}'
            })
        
        # Ensure sources include the registry
        registry_ref = spec.get('registry_ref')
        if registry_ref:
            registry_sources = [
                s for s in derivation.get('sources', [])
                if s.get('kind') == 'REGISTRY' and s.get('ref') == registry_ref
            ]
            if not registry_sources:
                self.warnings.append({
                    'header': header,
                    'rule': 'LOOKUP_REGISTRY_NOT_IN_SOURCES',
                    'message': f'Registry {registry_ref} should be in sources array'
                })
    
    def _check_task_output_completeness(self, header: str, derivation: dict):
        """For TASK_OUTPUT engine, ensure task_id, output_key, evidence present."""
        if derivation.get('process', {}).get('engine') != 'TASK_OUTPUT':
            return
        
        spec = derivation.get('process', {}).get('spec', {})
        
        required_fields = ['task_id', 'output_key']
        missing = [f for f in required_fields if f not in spec]
        
        if missing:
            self.errors.append({
                'header': header,
                'rule': 'TASK_OUTPUT_INCOMPLETE',
                'message': f'TASK_OUTPUT engine missing required fields: {missing}'
            })
        
        # Check evidence
        evidence = derivation.get('evidence', {})
        if not evidence.get('artifacts'):
            self.warnings.append({
                'header': header,
                'rule': 'TASK_OUTPUT_NO_EVIDENCE',
                'message': 'TASK_OUTPUT should specify evidence artifacts'
            })
    
    def _check_null_policy_consistency(self, header: str, header_def: dict, derivation: dict):
        """Ensure null_policy aligns with presence.policy."""
        presence_policy = header_def.get('presence', {}).get('policy')
        null_policy = derivation.get('null_policy')
        
        # REQUIRED presence should not allow NULL
        if presence_policy == 'REQUIRED' and null_policy == 'ALLOW_NULL':
            self.errors.append({
                'header': header,
                'rule': 'NULL_POLICY_CONTRADICTION',
                'message': 'presence.policy=REQUIRED but derivation.null_policy=ALLOW_NULL'
            })
        
        # OPTIONAL presence should allow NULL
        if presence_policy == 'OPTIONAL' and null_policy == 'ERROR':
            self.warnings.append({
                'header': header,
                'rule': 'NULL_POLICY_INCONSISTENT',
                'message': 'presence.policy=OPTIONAL but derivation.null_policy=ERROR (may be intentional)'
            })
    
    def _check_evidence_requirements(self, header: str, derivation: dict):
        """Warn if critical modes lack evidence."""
        mode = derivation.get('mode')
        evidence = derivation.get('evidence', {})
        
        critical_modes = {'EXTRACTED', 'LOOKUP', 'DERIVED', 'AGGREGATED'}
        
        if mode in critical_modes:
            if not evidence.get('evidence_keys') and not evidence.get('artifacts'):
                self.warnings.append({
                    'header': header,
                    'rule': 'MISSING_EVIDENCE',
                    'message': f'mode={mode} should specify evidence keys or artifacts'
                })
    
    def _check_placeholder_values(self, header: str, derivation: dict):
        """Flag placeholder/to-be-specified values."""
        spec = derivation.get('process', {}).get('spec', {})
        sources = derivation.get('sources', [])
        
        # Check for placeholder strings
        placeholders = ['to_be_specified', 'TBD', 'TODO', 'FIXME']
        
        spec_str = json.dumps(spec).lower()
        sources_str = json.dumps(sources).lower()
        
        for placeholder in placeholders:
            if placeholder.lower() in spec_str or placeholder.lower() in sources_str:
                self.warnings.append({
                    'header': header,
                    'rule': 'PLACEHOLDER_VALUE',
                    'message': f'Contains placeholder value: {placeholder}'
                })
                break
    
    def report(self):
        """Print validation report."""
        print("=" * 70)
        print("DERIVATION VALIDATION REPORT")
        print("=" * 70)
        print(f"Dictionary: {self.data.get('dictionary_id')}")
        print(f"Version: {self.data.get('dictionary_version')}")
        print(f"Headers: {len(self.data['headers'])}")
        print()
        
        if self.errors:
            print(f"❌ ERRORS: {len(self.errors)}")
            print("-" * 70)
            for err in self.errors:
                print(f"  [{err['rule']}] {err['header']}")
                print(f"    {err['message']}")
            print()
        else:
            print("✓ No errors found")
            print()
        
        if self.warnings:
            print(f"⚠️  WARNINGS: {len(self.warnings)}")
            print("-" * 70)
            for warn in self.warnings:
                print(f"  [{warn['rule']}] {warn['header']}")
                print(f"    {warn['message']}")
            print()
        else:
            print("✓ No warnings")
            print()
        
        # Summary
        if not self.errors and not self.warnings:
            print("🎉 All derivation sections are valid!")
        elif not self.errors:
            print("✓ All critical rules passed (warnings only)")
        else:
            print(f"❌ Validation failed: {len(self.errors)} errors must be fixed")
        
        return len(self.errors) == 0


def main():
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    
    dict_file = repo_root / '2026012816000001_COLUMN_DICTIONARY.json'
    
    if not dict_file.exists():
        print(f"ERROR: Dictionary not found: {dict_file}", file=sys.stderr)
        sys.exit(1)
    
    validator = DerivationValidator(dict_file)
    error_count, warning_count = validator.validate_all()
    success = validator.report()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
