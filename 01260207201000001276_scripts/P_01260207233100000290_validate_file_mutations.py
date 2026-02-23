#!/usr/bin/env python3
"""
File Mutation Validator

Validates that file mutations have deterministic execution methods with hash guards
and evidence requirements. Enforces schema validation and strict rules for mutation
execution.

Exit codes:
  0 = All validations pass
  1 = Schema validation failure
  2 = Validation logic failure
  3 = Hash guard failure
"""

import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple


class FileMutationValidator:
    """Validates file mutations against schema and rules."""
    
    HASH_PATTERN = re.compile(r"^[a-f0-9]{64}$")
    REQUIRED_EXECUTION_METHODS = {"FULL_REWRITE", "UNIFIED_DIFF_APPLY", "AST_TRANSFORM"}
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.checks_passed: List[str] = []
    
    def validate(self, mutations_file: str) -> int:
        """Main validation entry point."""
        try:
            mutations = self._load_json(mutations_file)
        except Exception as e:
            self._error(f"Failed to load mutations file: {e}")
            return 1
        
        # Run all validations
        if not self._validate_schema(mutations):
            return 1
        
        if not self._validate_execution_methods(mutations):
            return 2
        
        if not self._validate_hash_guards(mutations):
            return 3
        
        if not self._validate_evidence_outputs(mutations):
            return 2
        
        return self._report_results()
    
    def _load_json(self, path: str) -> Dict[str, Any]:
        """Load and parse JSON file."""
        with open(path) as f:
            return json.load(f)
    
    def _validate_schema(self, mutations: Dict) -> bool:
        """Validate basic JSON schema structure."""
        # Check top-level required fields
        if "mutations" not in mutations:
            self._error("Missing 'mutations' field at root level")
            return False
        
        mut_obj = mutations["mutations"]
        if not isinstance(mut_obj, dict):
            self._error("'mutations' must be an object")
            return False
        
        self.checks_passed.append("Schema validation")
        return True
    
    def _validate_execution_methods(self, mutations: Dict) -> bool:
        """Validate execution methods are present and valid."""
        mut_obj = mutations.get("mutations", {})
        modified_files = mut_obj.get("modified_files", [])
        created_files = mut_obj.get("created_files", [])
        
        all_files = modified_files + created_files
        
        for i, file_entry in enumerate(all_files):
            rel_path = file_entry.get("relative_path", f"[file {i}]")
            
            # Check execution_method presence
            if "execution_method" not in file_entry:
                self._error(f"File '{rel_path}': missing 'execution_method'")
                return False
            
            method = file_entry["execution_method"]
            if method not in self.REQUIRED_EXECUTION_METHODS:
                self._error(
                    f"File '{rel_path}': invalid execution_method '{method}'. "
                    f"Must be one of: {', '.join(sorted(self.REQUIRED_EXECUTION_METHODS))}"
                )
                return False
            
            # Validate method-specific constraints
            if method == "UNIFIED_DIFF_APPLY":
                if not self._validate_unified_diff_constraints(file_entry, rel_path):
                    return False
            
            elif method == "FULL_REWRITE":
                if not self._validate_full_rewrite_constraints(file_entry, rel_path):
                    return False
        
        self.checks_passed.append("Execution method validation")
        return True
    
    def _validate_unified_diff_constraints(self, file_entry: Dict, rel_path: str) -> bool:
        """Validate UNIFIED_DIFF_APPLY method constraints."""
        payload = file_entry.get("method_payload", {})
        
        # Check allow_fuzz must be false
        if payload.get("allow_fuzz") is not False:
            self._error(
                f"File '{rel_path}': UNIFIED_DIFF_APPLY requires "
                "'allow_fuzz' = false (strict mode)"
            )
            return False
        
        # Check rejects_allowed must be false
        if payload.get("rejects_allowed") is not False:
            self._error(
                f"File '{rel_path}': UNIFIED_DIFF_APPLY requires "
                "'rejects_allowed' = false (strict mode)"
            )
            return False
        
        # Check patch_path exists
        if "patch_path" not in payload:
            self._error(
                f"File '{rel_path}': UNIFIED_DIFF_APPLY requires 'patch_path'"
            )
            return False
        
        return True
    
    def _validate_full_rewrite_constraints(self, file_entry: Dict, rel_path: str) -> bool:
        """Validate FULL_REWRITE method constraints."""
        payload = file_entry.get("method_payload", {})
        source = payload.get("content_source")
        
        if source == "inline":
            if "content_text" not in payload:
                self._error(
                    f"File '{rel_path}': FULL_REWRITE with content_source='inline' "
                    "requires 'content_text'"
                )
                return False
        elif source == "artifact":
            if "artifact_id" not in payload:
                self._error(
                    f"File '{rel_path}': FULL_REWRITE with content_source='artifact' "
                    "requires 'artifact_id'"
                )
                return False
        else:
            self._error(
                f"File '{rel_path}': FULL_REWRITE requires "
                "'content_source' = 'inline' or 'artifact'"
            )
            return False
        
        return True
    
    def _validate_hash_guards(self, mutations: Dict) -> bool:
        """Validate hash guard XOR constraints."""
        mut_obj = mutations.get("mutations", {})
        modified_files = mut_obj.get("modified_files", [])
        created_files = mut_obj.get("created_files", [])
        
        all_files = modified_files + created_files
        
        for file_entry in all_files:
            rel_path = file_entry.get("relative_path", "[unknown]")
            
            # Check before hash (modified files only)
            if file_entry in modified_files:
                before_literal = "expected_before_sha256" in file_entry
                before_ref = "expected_before_sha256_ref" in file_entry
                
                if before_literal and before_ref:
                    self._error(
                        f"File '{rel_path}': Cannot specify both "
                        "'expected_before_sha256' and 'expected_before_sha256_ref'"
                    )
                    return False
                
                if before_literal:
                    hash_val = file_entry.get("expected_before_sha256")
                    if not self._is_valid_hash(hash_val):
                        self._error(
                            f"File '{rel_path}': invalid 'expected_before_sha256' format"
                        )
                        return False
            
            # Check after hash
            after_literal = "expected_after_sha256" in file_entry
            after_ref = "expected_after_sha256_ref" in file_entry
            
            if after_literal and after_ref:
                self._error(
                    f"File '{rel_path}': Cannot specify both "
                    "'expected_after_sha256' and 'expected_after_sha256_ref'"
                )
                return False
            
            if after_literal:
                hash_val = file_entry.get("expected_after_sha256")
                if not self._is_valid_hash(hash_val):
                    self._error(
                        f"File '{rel_path}': invalid 'expected_after_sha256' format"
                    )
                    return False
        
        self.checks_passed.append("Hash guard validation")
        return True
    
    def _validate_evidence_outputs(self, mutations: Dict) -> bool:
        """Validate evidence output paths are correctly formatted."""
        mut_obj = mutations.get("mutations", {})
        modified_files = mut_obj.get("modified_files", [])
        created_files = mut_obj.get("created_files", [])
        
        all_files = modified_files + created_files
        evidence_pattern = re.compile(r"^\.state/evidence/file_mutations/.*")
        
        for file_entry in all_files:
            rel_path = file_entry.get("relative_path", "[unknown]")
            evidence = file_entry.get("evidence_outputs", {})
            
            if not evidence:
                self._warning(f"File '{rel_path}': no evidence_outputs specified")
                continue
            
            required_keys = [
                "before_hash_path", "after_hash_path", 
                "diff_patch_path", "apply_log_path"
            ]
            
            for key in required_keys:
                if key not in evidence:
                    self._warning(
                        f"File '{rel_path}': missing evidence_outputs.{key}"
                    )
                    continue
                
                path = evidence[key]
                if not evidence_pattern.match(path):
                    self._error(
                        f"File '{rel_path}': evidence path must be under "
                        "'.state/evidence/file_mutations/' (got: {path})"
                    )
                    return False
        
        self.checks_passed.append("Evidence outputs validation")
        return True
    
    def _is_valid_hash(self, value: Any) -> bool:
        """Check if value is a valid SHA256 hash."""
        if not isinstance(value, str):
            return False
        return bool(self.HASH_PATTERN.match(value))
    
    def _error(self, msg: str) -> None:
        """Record an error."""
        self.errors.append(msg)
    
    def _warning(self, msg: str) -> None:
        """Record a warning."""
        self.warnings.append(msg)
    
    def _report_results(self) -> int:
        """Print validation results and return exit code."""
        # Print passed checks
        for check in self.checks_passed:
            print(f"PASS: {check}")
        
        # Print warnings
        if self.warnings:
            print()
            for warning in self.warnings:
                print(f"WARN: {warning}")
        
        # Print errors
        if self.errors:
            print()
            for error in self.errors:
                print(f"FAIL: {error}")
            return 2
        
        print()
        print("All validations passed!")
        return 0


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python validate_file_mutations.py <mutations_file>")
        print("\nExit codes:")
        print("  0 = All validations pass")
        print("  1 = Schema validation failure")
        print("  2 = Validation logic failure")
        print("  3 = Hash guard failure")
        sys.exit(1)
    
    mutations_file = sys.argv[1]
    
    if not Path(mutations_file).exists():
        print(f"FAIL: File not found: {mutations_file}")
        sys.exit(1)
    
    validator = FileMutationValidator()
    exit_code = validator.validate(mutations_file)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
