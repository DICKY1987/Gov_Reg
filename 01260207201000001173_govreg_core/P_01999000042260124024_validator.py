"""Registry validator for checking schema compliance and completeness
FILE_ID: P_01999000042260124024
"""
import json
import sys
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Set
try:
    import jsonschema
except ImportError:
    jsonschema = None

# Import config module with P_ prefix
def _import_config():
    config_path = Path(__file__).parent / "P_01999000042260124021_config.py"
    spec = importlib.util.spec_from_file_location("config", config_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

_config = _import_config()
load_repo_roots = _config.load_repo_roots
load_registry = _config.load_registry
load_schema = _config.load_schema
resolve_path = _config.resolve_path


class RegistryValidator:
    """Validates governance registry against schema and rules"""
    
    def __init__(self, registry_path: str, schema_path: str, repo_roots_path: str):
        self.registry_path = registry_path
        self.schema_path = schema_path
        self.repo_roots_path = repo_roots_path
        
        # Load data
        self.repo_roots = load_repo_roots(repo_roots_path)
        self.registry = load_registry(registry_path)
        self.schema = load_schema(schema_path)
        
        # Results tracking
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.checklist: List[Dict[str, str]] = []
    
    def validate(self) -> Dict[str, Any]:
        """Run all validation checks"""
        self._validate_schema()
        self._validate_unique_ids()
        self._validate_path_integrity()
        self._validate_canonicality()
        self._validate_referential_integrity()
        self._validate_test_coverage()
        
        # Build checklist
        self._build_checklist()
        
        return {
            'valid': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'checklist': self.checklist
        }
    
    def _validate_schema(self):
        """Validate registry against JSON schema"""
        if jsonschema is None:
            self.warnings.append("jsonschema not installed - skipping schema validation")
            return
        
        try:
            jsonschema.validate(instance=self.registry, schema=self.schema)
            self._add_check("Schema Validity", "PASS", "Registry conforms to schema")
        except jsonschema.ValidationError as e:
            self.errors.append(f"Schema validation failed: {e.message}")
            self._add_check("Schema Validity", "FAIL", f"Schema error: {e.message}")
        except Exception as e:
            self.errors.append(f"Schema validation error: {str(e)}")
            self._add_check("Schema Validity", "FAIL", str(e))
    
    def _validate_unique_ids(self):
        """Check that all file IDs are unique"""
        files = self.registry.get('files', [])
        file_ids = [f.get('file_id') for f in files]
        
        # Check for duplicates
        seen = set()
        duplicates = set()
        for fid in file_ids:
            if fid in seen:
                duplicates.add(fid)
            seen.add(fid)
        
        if duplicates:
            for dup_id in duplicates:
                self.errors.append(f"Duplicate file_id found: {dup_id}")
            self._add_check("Unique IDs & References", "FAIL", 
                          f"{len(duplicates)} duplicate ID(s) found")
        else:
            self._add_check("Unique IDs & References", "PASS", 
                          "All file IDs are unique")
    
    def _validate_path_integrity(self):
        """Validate that all paths point to existing files"""
        files = self.registry.get('files', [])
        missing_count = 0
        
        for entry in files:
            # Skip directories
            if entry.get('is_directory', False):
                continue
            
            file_id = entry.get('file_id')
            relative_path = entry.get('relative_path')
            repo_root_id = entry.get('repo_root_id')
            
            # Resolve path
            abs_path = resolve_path(relative_path, repo_root_id, self.repo_roots)
            
            if abs_path is None:
                self.errors.append(f"Unknown repo_root_id '{repo_root_id}' for {file_id}")
                missing_count += 1
            elif not abs_path.exists():
                self.warnings.append(
                    f"File not found on disk: {file_id} ({relative_path})"
                )
                missing_count += 1
        
        if missing_count == 0:
            self._add_check("Path Integrity", "PASS", 
                          "All registry paths point to existing files")
        else:
            self._add_check("Path Integrity", "FAIL", 
                          f"{missing_count} file(s) missing on disk")
    
    def _validate_canonicality(self):
        """Check canonicality constraints"""
        files = self.registry.get('files', [])
        
        # Group by required_suite_key
        suite_canonicals: Dict[str, List[str]] = {}
        
        for entry in files:
            suite_key = entry.get('required_suite_key', '')
            canonicality = entry.get('canonicality', 'CANONICAL')
            
            if suite_key and canonicality == 'CANONICAL':
                if suite_key not in suite_canonicals:
                    suite_canonicals[suite_key] = []
                suite_canonicals[suite_key].append(entry['file_id'])
        
        # Check for conflicts (multiple canonicals per suite)
        conflicts = []
        for suite_key, file_ids in suite_canonicals.items():
            if len(file_ids) > 1:
                conflicts.append(f"Suite '{suite_key}' has {len(file_ids)} canonical files")
                self.errors.append(
                    f"Duplicate canonicals for suite '{suite_key}': {', '.join(file_ids)}"
                )
        
        if conflicts:
            self._add_check("Canonicality Constraints", "FAIL", 
                          f"{len(conflicts)} conflict(s) found")
        else:
            self._add_check("Canonicality Constraints", "PASS", 
                          "No canonicality conflicts")
    
    def _validate_referential_integrity(self):
        """Check that cross-references are valid"""
        files = self.registry.get('files', [])
        file_ids = {f.get('file_id') for f in files}
        
        broken_refs = []
        
        # Check enforced_by and enforces arrays
        for entry in files:
            file_id = entry.get('file_id')
            
            for ref_id in entry.get('enforced_by', []):
                if ref_id not in file_ids:
                    broken_refs.append(f"{file_id} references unknown ID in enforced_by: {ref_id}")
            
            # Note: enforces can reference rule IDs, not just file IDs, so we skip checking those
        
        # Check edges
        edges = self.registry.get('edges', [])
        for edge in edges:
            source = edge.get('source_file_id')
            target = edge.get('target_file_id')
            
            if source and source not in file_ids:
                broken_refs.append(f"Edge references unknown source_file_id: {source}")
            if target and target not in file_ids:
                broken_refs.append(f"Edge references unknown target_file_id: {target}")
        
        if broken_refs:
            for ref in broken_refs:
                self.errors.append(f"Broken reference: {ref}")
            self._add_check("Referential Integrity", "FAIL", 
                          f"{len(broken_refs)} broken reference(s)")
        else:
            self._add_check("Referential Integrity", "PASS", 
                          "All references are valid")
    
    def _validate_test_coverage(self):
        """Check test coverage for critical files"""
        files = self.registry.get('files', [])
        
        # Count files that should have tests
        should_have_tests = []
        has_tests = []
        
        for entry in files:
            artifact_kind = entry.get('artifact_kind')
            layer = entry.get('layer')
            
            # Critical files that should have tests
            if artifact_kind in ['PYTHON_MODULE', 'SCRIPT'] and \
               layer in ['VALIDATION', 'EXECUTION', 'CORE', 'GATES']:
                should_have_tests.append(entry['file_id'])
                if entry.get('has_tests', False):
                    has_tests.append(entry['file_id'])
        
        if should_have_tests:
            coverage_pct = (len(has_tests) / len(should_have_tests)) * 100
            if coverage_pct < 50:
                self._add_check("Test Coverage", "WARN", 
                              f"{len(has_tests)}/{len(should_have_tests)} critical files have tests ({coverage_pct:.0f}%)")
            else:
                self._add_check("Test Coverage", "PASS", 
                              f"{len(has_tests)}/{len(should_have_tests)} critical files have tests ({coverage_pct:.0f}%)")
        else:
            self._add_check("Test Coverage", "PASS", 
                          "No testable files found")
    
    def _add_check(self, name: str, status: str, details: str = ""):
        """Add a checklist item"""
        self.checklist.append({
            'name': name,
            'status': status,
            'details': details
        })
    
    def _build_checklist(self):
        """Ensure all checklist items are present"""
        existing_names = {c['name'] for c in self.checklist}
        
        # Add missing checks with SKIP status
        required_checks = [
            "Schema Validity",
            "Unique IDs & References",
            "Path Integrity",
            "Canonicality Constraints",
            "Referential Integrity",
            "Test Coverage"
        ]
        
        for check_name in required_checks:
            if check_name not in existing_names:
                self._add_check(check_name, "SKIP", "Check not performed")
