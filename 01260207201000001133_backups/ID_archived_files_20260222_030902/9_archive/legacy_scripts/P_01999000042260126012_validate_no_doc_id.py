#!/usr/bin/env python3
"""
Validator: Ensure no doc_id in registry records

This script validates that the doc_id elimination was successful by checking:
1. No registry JSON files contain "doc_id" as a record field
2. Schema files don't define doc_id
3. Policy/derivation files don't reference doc_id

Usage:
    python ID/P_01999000042260126012_validate_no_doc_id.py
    
Exit codes:
    0: Success - no doc_id found
    1: Validation failed - doc_id still exists
"""

import json
import sys
from pathlib import Path
from typing import List, Tuple

def check_json_file(filepath: Path) -> List[str]:
    """Check if a JSON file contains 'doc_id' as a key in any record."""
    violations = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check if doc_id exists in the data structure
        if isinstance(data, dict):
            if 'doc_id' in data and filepath.name != '2026012816000001_COLUMN_DICTIONARY.json':
                # Allow provenance references but not as a registry column
                if 'headers' not in data:  # Not the column dictionary
                    violations.append(f"{filepath}: Found 'doc_id' key in top-level object")
            
            # Check nested structures
            if 'files' in data and isinstance(data['files'], list):
                for idx, record in enumerate(data['files']):
                    if isinstance(record, dict) and 'doc_id' in record:
                        violations.append(f"{filepath}: Record {idx} contains 'doc_id' field")
            
            # Check properties in schema
            if 'properties' in data:
                props = data['properties']
                if isinstance(props, dict) and 'doc_id' in props:
                    violations.append(f"{filepath}: Schema defines 'doc_id' property")
            
            # Check definitions
            if 'definitions' in data:
                for def_name, def_obj in data['definitions'].items():
                    if isinstance(def_obj, dict):
                        if 'properties' in def_obj and isinstance(def_obj['properties'], dict):
                            if 'doc_id' in def_obj['properties']:
                                violations.append(f"{filepath}: Definition '{def_name}' contains 'doc_id' property")
                        if 'required' in def_obj and isinstance(def_obj['required'], list):
                            if 'doc_id' in def_obj['required']:
                                violations.append(f"{filepath}: Definition '{def_name}' requires 'doc_id'")
    
    except json.JSONDecodeError as e:
        violations.append(f"{filepath}: JSON decode error - {e}")
    except Exception as e:
        violations.append(f"{filepath}: Error reading file - {e}")
    
    return violations

def check_yaml_file(filepath: Path) -> List[str]:
    """Check if a YAML file contains doc_id references in columns or derived_columns."""
    violations = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Simple text search for doc_id in policy/derivation contexts
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            # Check for doc_id as a column definition (not in comments or strings)
            if line.strip().startswith('doc_id:'):
                violations.append(f"{filepath}:{line_num}: Found 'doc_id:' definition")
            
            # Check for doc_id in depends_on arrays
            if '"doc_id"' in line or "'doc_id'" in line:
                if 'depends_on' in line or 'exceptions' in line:
                    violations.append(f"{filepath}:{line_num}: Found 'doc_id' in dependency/exception list")
    
    except Exception as e:
        violations.append(f"{filepath}: Error reading file - {e}")
    
    return violations

def main():
    repo_root = Path(__file__).parent.parent
    
    violations = []
    
    # Check registry schema
    schema_file = repo_root / "REGISTRY" / "01999000042260124012_governance_registry_schema.v3.json"
    if schema_file.exists():
        violations.extend(check_json_file(schema_file))
    
    # Check WRITE_POLICY
    write_policy = repo_root / "UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml"
    if write_policy.exists():
        violations.extend(check_yaml_file(write_policy))
    
    # Check DERIVATIONS
    derivations = repo_root / "UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml"
    if derivations.exists():
        violations.extend(check_yaml_file(derivations))
    
    # Check column dictionary
    col_dict = repo_root / "2026012816000001_COLUMN_DICTIONARY.json"
    if col_dict.exists():
        try:
            with open(col_dict, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check if doc_id exists in headers
            if 'headers' in data and 'doc_id' in data['headers']:
                violations.append(f"{col_dict}: 'doc_id' still exists in headers")
            
            # Check if doc_id exists in header_order
            if 'header_order' in data and 'doc_id' in data['header_order']:
                violations.append(f"{col_dict}: 'doc_id' still exists in header_order")
            
            # Verify count is 147
            if data.get('header_count_expected') != 147:
                violations.append(f"{col_dict}: header_count_expected is {data.get('header_count_expected')}, expected 147")
        
        except Exception as e:
            violations.append(f"{col_dict}: Error validating - {e}")
    
    # Report results
    if violations:
        print("❌ VALIDATION FAILED: doc_id still exists in the following locations:\n")
        for violation in violations:
            print(f"  • {violation}")
        print(f"\nTotal violations: {len(violations)}")
        return 1
    else:
        print("✅ VALIDATION PASSED: No doc_id found in registry contracts or schemas")
        print("   • WRITE_POLICY: clean")
        print("   • DERIVATIONS: clean")
        print("   • Registry schema: clean")
        print("   • Column dictionary: clean (147 headers)")
        return 0

if __name__ == "__main__":
    sys.exit(main())
