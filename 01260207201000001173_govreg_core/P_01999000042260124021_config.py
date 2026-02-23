"""Configuration and registry loading utilities
FILE_ID: P_01999000042260124021
"""
import json
from pathlib import Path
from typing import Dict, List, Any, Optional


def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load and parse a JSON file"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_file(file_path: str, data: Dict[str, Any], indent: int = 2) -> None:
    """Save data to a JSON file"""
    path = Path(file_path)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def load_repo_roots(repo_roots_path: str) -> Dict[str, Dict[str, str]]:
    """Load repository root configurations"""
    data = load_json_file(repo_roots_path)
    
    # Convert list to dict keyed by repo_root_id
    roots = {}
    for root in data.get('repo_roots', []):
        roots[root['repo_root_id']] = {
            'absolute_path': root['absolute_path'],
            'description': root.get('description', '')
        }
    
    return roots


def load_registry(registry_path: str) -> Dict[str, Any]:
    """Load governance registry"""
    return load_json_file(registry_path)


def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load JSON schema"""
    return load_json_file(schema_path)


def resolve_path(relative_path: str, repo_root_id: str, repo_roots: Dict[str, Dict[str, str]]) -> Optional[Path]:
    """Resolve a relative path to an absolute path using repo roots"""
    if repo_root_id not in repo_roots:
        return None
    
    root_path = Path(repo_roots[repo_root_id]['absolute_path'])
    return root_path / relative_path


def normalize_path(path: Path) -> str:
    """Normalize path for cross-platform compatibility"""
    return str(path).replace('\\', '/')
