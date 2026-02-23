"""
Context Generator
Generates context bundles from repository state.
"""
import json
import subprocess
from pathlib import Path
from typing import Dict, List
from datetime import datetime
from uuid import uuid4

from .hash_utils import compute_json_hash


class ContextGenerator:
    """Generates repository context bundles for plan grounding"""
    
    def __init__(self, repo_root: Path, schema_dir: Path):
        self.repo_root = Path(repo_root)
        self.schema_dir = Path(schema_dir)
    
    def generate_context_bundle(self) -> Dict:
        """Generate context bundle from current repository state
        
        Returns:
            Context bundle dictionary
        """
        timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        short_uuid = str(uuid4()).replace('-', '')[:8]
        
        bundle = {
            "bundle_id": f"CONTEXT_{timestamp}_{short_uuid}",
            "repo_root": str(self.repo_root),
            "repo_summary": self._get_repo_summary(),
            "recent_changes": self._get_recent_changes(),
            "known_templates": self._discover_templates(),
            "known_gates": self._discover_gates(),
            "registries": self._discover_registries(),
            "file_tree_snapshot": self._get_file_tree_snapshot()
        }
        
        return bundle
    
    def _get_repo_summary(self) -> Dict:
        """Extract repository summary"""
        return {
            "name": self.repo_root.name,
            "purpose": "Governance and Regulatory Compliance System",
            "primary_language": "Python",
            "frameworks": ["Click", "LangGraph", "jsonschema"]
        }
    
    def _get_recent_changes(self, limit: int = 10) -> List[Dict]:
        """Get recent git commits
        
        Args:
            limit: Maximum number of commits to retrieve
            
        Returns:
            List of commit dictionaries
        """
        try:
            result = subprocess.run(
                ['git', '--no-pager', 'log', f'-{limit}', 
                 '--pretty=format:%H|%s|%aI|%an'],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return []
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                parts = line.split('|')
                if len(parts) >= 4:
                    commits.append({
                        "commit_sha": parts[0],
                        "message": parts[1],
                        "timestamp": parts[2],
                        "author": parts[3]
                    })
            
            return commits
        except Exception:
            return []
    
    def _discover_templates(self) -> List[Dict]:
        """Discover available templates in repository"""
        templates = []
        
        # Look for template files
        template_patterns = [
            "newPhasePlanProcess/*TEMPLATE*.json",
            "templates/*.json"
        ]
        
        for pattern in template_patterns:
            for template_path in self.repo_root.glob(pattern):
                templates.append({
                    "template_id": template_path.stem,
                    "path": str(template_path.relative_to(self.repo_root)),
                    "version": self._extract_version_from_path(template_path),
                    "description": f"Template from {template_path.parent.name}"
                })
        
        return templates
    
    def _discover_gates(self) -> List[Dict]:
        """Discover existing validation gates"""
        gates = []
        
        # Look for gate definitions
        gate_dirs = list(self.repo_root.glob("*gates*"))
        
        for gate_dir in gate_dirs:
            if gate_dir.is_dir():
                for gate_file in gate_dir.glob("*.json"):
                    try:
                        with open(gate_file, 'r') as f:
                            gate_data = json.load(f)
                            if "gate_id" in gate_data:
                                gates.append({
                                    "gate_id": gate_data["gate_id"],
                                    "gate_type": gate_data.get("gate_type", "UNKNOWN"),
                                    "required_evidence": gate_data.get("required_evidence", []),
                                    "pass_criteria": gate_data.get("pass_criteria", "")
                                })
                    except Exception:
                        continue
        
        return gates
    
    def _discover_registries(self) -> List[Dict]:
        """Discover registry files"""
        registries = []
        
        registry_patterns = [
            "*REGISTRY*/*.json",
            "registries/*.json"
        ]
        
        for pattern in registry_patterns:
            for reg_path in self.repo_root.glob(pattern):
                if reg_path.is_file() and reg_path.stat().st_size > 0:
                    try:
                        with open(reg_path, 'r') as f:
                            data = json.load(f)
                            entry_count = len(data) if isinstance(data, list) else 0
                            
                            registries.append({
                                "registry_id": reg_path.stem,
                                "path": str(reg_path.relative_to(self.repo_root)),
                                "entry_count": entry_count
                            })
                    except Exception:
                        continue
        
        return registries
    
    def _get_file_tree_snapshot(self) -> Dict:
        """Create snapshot of repository file structure"""
        total_files = 0
        total_dirs = 0
        key_directories = []
        
        for item in self.repo_root.rglob('*'):
            if item.is_file():
                total_files += 1
            elif item.is_dir():
                total_dirs += 1
                # Track important directories
                if any(marker in item.name.lower() for marker in 
                       ['src', 'tests', 'schemas', 'config', 'scripts']):
                    rel_path = str(item.relative_to(self.repo_root))
                    if rel_path not in key_directories:
                        key_directories.append(rel_path)
        
        return {
            "total_files": total_files,
            "total_directories": total_dirs,
            "key_directories": sorted(key_directories[:20])  # Top 20
        }
    
    def _extract_version_from_path(self, path: Path) -> str:
        """Extract version from path or filename"""
        name = path.stem
        if 'V3' in name:
            return "3.0.0"
        elif 'V2' in name:
            return "2.0.0"
        elif 'V1' in name:
            return "1.0.0"
        return "unknown"
    
    def save_context_bundle(self, bundle: Dict, output_path: Path):
        """Save context bundle to file
        
        Args:
            bundle: Context bundle dictionary
            output_path: Path to save bundle
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(bundle, f, indent=2)
    
    def get_bundle_hash(self, bundle: Dict) -> str:
        """Compute hash of context bundle
        
        Args:
            bundle: Context bundle dictionary
            
        Returns:
            SHA256 hash
        """
        return compute_json_hash(bundle)
