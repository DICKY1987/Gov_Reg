"""Registry scanner for discovering governance artifacts
FILE_ID: P_01999000042260124023
"""
import hashlib
import os
import sys
import importlib.util
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Set

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
save_json_file = _config.save_json_file
resolve_path = _config.resolve_path


class RegistryScanner:
    """Scans repository for governance artifacts and updates registry"""
    
    def __init__(self, registry_path: str, schema_path: str, repo_roots_path: str):
        self.registry_path = registry_path
        self.schema_path = schema_path
        self.repo_roots_path = repo_roots_path
        
        # Load configurations
        self.repo_roots = load_repo_roots(repo_roots_path)
        self.schema = load_schema(schema_path)
        
        # Try to load existing registry or create new
        try:
            self.registry = load_registry(registry_path)
        except FileNotFoundError:
            self.registry = {"files": [], "edges": [], "schema_version": "v3"}
        
        # Track changes
        self.new_files: List[Dict] = []
        self.updated_files: List[Dict] = []
        self.orphaned_ids: Set[str] = set()
        
        # Build lookup for existing entries
        self.existing_files = {f['file_id']: f for f in self.registry.get('files', [])}
        self.path_to_id = {
            (f.get('repo_root_id'), f.get('relative_path')): f['file_id'] 
            for f in self.registry.get('files', [])
            if f.get('repo_root_id') and f.get('relative_path')
        }
    
    def scan(self) -> Dict[str, int]:
        """Scan all repo roots for governance artifacts"""
        found_ids = set()
        
        for repo_root_id, root_info in self.repo_roots.items():
            root_path = Path(root_info['absolute_path'])
            
            if not root_path.exists():
                print(f"⚠ Warning: Repo root does not exist: {root_path}")
                continue
            
            print(f"  Scanning: {repo_root_id} ({root_path})")
            
            # Scan for governance-related files
            governance_dirs = ['GOVERNANCE', 'governance', 'Gov_Reg', 'ssot', 'gates', 
                             'validators', 'schemas', 'registry', 'scripts']
            
            for gov_dir in governance_dirs:
                gov_path = root_path / gov_dir
                if gov_path.exists():
                    self._scan_directory(gov_path, root_path, repo_root_id, found_ids)
        
        # Identify orphaned entries
        for file_id in self.existing_files:
            if file_id not in found_ids:
                self.orphaned_ids.add(file_id)
        
        return {
            'files_found': len(found_ids),
            'new_entries': len(self.new_files),
            'updated_entries': len(self.updated_files),
            'orphaned_entries': len(self.orphaned_ids)
        }
    
    def _scan_directory(self, directory: Path, root_path: Path, repo_root_id: str, found_ids: Set[str]):
        """Recursively scan a directory for governance files"""
        for item in directory.rglob('*'):
            if not item.is_file():
                continue
            
            # Skip temporary/hidden files
            if item.name.startswith('.') or item.name.startswith('tmp'):
                continue
            
            # Check if file looks like a governance artifact
            if self._is_governance_artifact(item):
                relative_path = str(item.relative_to(root_path)).replace('\\', '/')
                
                # Check if already in registry
                key = (repo_root_id, relative_path)
                if key in self.path_to_id:
                    file_id = self.path_to_id[key]
                    found_ids.add(file_id)
                    self._check_for_updates(file_id, item)
                else:
                    # New file - assign ID and add
                    file_id = self._assign_file_id()
                    found_ids.add(file_id)
                    self._add_new_file(file_id, item, relative_path, repo_root_id)
    
    def _is_governance_artifact(self, file_path: Path) -> bool:
        """Determine if a file is a governance artifact"""
        # Check file extension
        gov_extensions = {'.py', '.json', '.yaml', '.yml', '.md', '.sh', '.ps1'}
        if file_path.suffix not in gov_extensions:
            return False
        
        # Check for governance-related naming patterns
        name_lower = file_path.name.lower()
        governance_keywords = [
            'governance', 'registry', 'schema', 'validate', 'gate', 'ssot',
            'manifest', 'enforce', 'remedy', 'validator', 'runner', 'checker',
            'policy', 'rule', 'control', 'audit', 'evidence'
        ]
        
        return any(keyword in name_lower for keyword in governance_keywords)
    
    def _assign_file_id(self) -> str:
        """Assign a new 20-digit numeric file ID using the ID allocator"""
        # Use the proactive ID allocator for consistent ID assignment
        try:
            from P_01999000042260124027_id_allocator import allocate_single_id
            return allocate_single_id("Scanner auto-assignment")
        except ImportError:
            # Fallback: Find the highest existing numeric ID and increment
            max_id = 0
            for file_id in self.existing_files:
                try:
                    id_num = int(file_id)
                    if id_num > max_id:
                        max_id = id_num
                except ValueError:
                    continue
        
            new_id = max_id + 1
            # Return 20-digit format: use current timestamp-based prefix + sequence
            return f"01999000042260124{new_id:03d}"
    
    def _add_new_file(self, file_id: str, file_path: Path, relative_path: str, repo_root_id: str):
        """Add a new file entry to registry"""
        # Infer metadata from file
        artifact_kind = self._infer_artifact_kind(file_path)
        governance_domain = self._infer_domain(file_path)
        layer = self._infer_layer(file_path, artifact_kind)
        
        entry = {
            "file_id": file_id,
            "relative_path": relative_path,
            "repo_root_id": repo_root_id,
            "governance_domain": governance_domain,
            "artifact_kind": artifact_kind,
            "layer": layer,
            "required_suite_key": "",
            "bundle_id": None,
            "bundle_key": None,
            "bundle_role": None,
            "bundle_version": None,
            "anchor_file_id": None,
            "canonicality": "CANONICAL",
            "enforced_by": [],
            "enforced_by_file_ids": [],
            "enforces": [],
            "enforces_rule_ids": [],
            "depends_on_file_ids": [],
            "test_file_ids": [],
            "has_tests": False,
            "evidence_outputs": [],
            "report_outputs": [],
            "coverage_status": None,
            "superseded_by": None,
            "one_line_purpose": "",
            "description": "",
            "deliverables": [],
            "path_aliases": [],
            "is_directory": False,
            "first_seen_utc": datetime.utcnow().isoformat() + "Z",
            "created_by": "govreg_scanner_v0.1"
        }
        
        # Add SHA256 if possible
        try:
            entry["sha256"] = self._compute_sha256(file_path)
        except Exception:
            pass
        
        self.new_files.append(entry)
        self.existing_files[file_id] = entry
        self.path_to_id[(repo_root_id, relative_path)] = file_id
    
    def _check_for_updates(self, file_id: str, file_path: Path):
        """Check if an existing entry needs updates"""
        entry = self.existing_files[file_id]
        
        # Check SHA256 if present
        if 'sha256' in entry:
            try:
                current_hash = self._compute_sha256(file_path)
                if current_hash != entry['sha256']:
                    entry['sha256'] = current_hash
                    self.updated_files.append(entry)
            except Exception:
                pass
    
    def _compute_sha256(self, file_path: Path) -> str:
        """Compute SHA256 hash of file"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def _infer_artifact_kind(self, file_path: Path) -> str:
        """Infer artifact kind from file characteristics"""
        suffix = file_path.suffix.lower()
        name = file_path.name.lower()
        
        if 'schema' in name and suffix == '.json':
            return 'SCHEMA'
        elif suffix == '.py':
            if 'test_' in name:
                return 'TEST'
            elif any(x in name for x in ['runner', 'executor', 'cli']):
                return 'SCRIPT'
            else:
                return 'PYTHON_MODULE'
        elif suffix in ['.json', '.yaml', '.yml']:
            if 'registry' in name:
                return 'REGISTRY'
            elif 'config' in name:
                return 'CONFIG'
            else:
                return 'JSON_DATA' if suffix == '.json' else 'YAML_DATA'
        elif suffix == '.md':
            return 'MARKDOWN_DOC'
        elif suffix in ['.sh', '.ps1']:
            return 'SCRIPT'
        else:
            return 'OTHER'
    
    def _infer_domain(self, file_path: Path) -> str:
        """Infer governance domain from file path"""
        path_str = str(file_path).lower()
        
        if 'schema' in path_str:
            return 'SCHEMAS'
        elif 'registry' in path_str or 'Gov_Reg' in str(file_path):
            return 'REGISTRY'
        elif 'ssot' in path_str:
            return 'EXTERNAL'  # SSOT is in external system
        elif 'gate' in path_str:
            return 'EXTERNAL'
        elif 'test' in path_str:
            return 'TESTS'
        elif 'evidence' in path_str:
            return 'EVIDENCE'
        elif 'report' in path_str:
            return 'REPORTS'
        else:
            return 'ROOT'
    
    def _infer_layer(self, file_path: Path, artifact_kind: str) -> str:
        """Infer architectural layer"""
        name = file_path.name.lower()
        
        if artifact_kind in ['SCHEMA', 'REGISTRY']:
            return 'DEFINITION'
        elif artifact_kind == 'TEST':
            return 'TESTING'
        elif 'validate' in name or 'validator' in name:
            return 'VALIDATION'
        elif 'config' in name:
            return 'CONFIGURATION'
        elif artifact_kind == 'MARKDOWN_DOC':
            return 'DOCUMENTATION'
        elif 'gate' in name or 'enforce' in name:
            return 'GATES'
        elif 'ssot' in name:
            return 'SSOT'
        else:
            return 'GOVERNANCE'
    
    def save_registry(self):
        """Save updated registry to file"""
        # Combine existing, new, and updated files
        all_files = []
        
        # Add all non-orphaned files
        for file_id, entry in self.existing_files.items():
            if file_id not in self.orphaned_ids:
                all_files.append(entry)
        
        self.registry['files'] = all_files
        
        save_json_file(self.registry_path, self.registry)
