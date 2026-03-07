#!/usr/bin/env python3
# DOC_LINK: DOC-CORE-ADAPTERS-FS-ADAPTER-1176
"""
Filesystem Adapter with write containment and audit logging.

DOC_ID: DOC-CORE-ADAPTERS-FS-ADAPTER-1176
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from datetime import datetime


class FilesystemAdapter:
    """
    Filesystem operations with semantic path resolution and write containment.
    """

    def __init__(self, path_registry, allowed_write_keys: Optional[List[str]] = None):
        self.registry = path_registry
        self.allowed_write_keys = allowed_write_keys or ['data:', 'logs:', 'reports:']
        self.audit_log: List[Dict] = []

    def _check_write_allowed(self, semantic_key: str):
        """Check if write is allowed to this semantic key."""
        for prefix in self.allowed_write_keys:
            if semantic_key.startswith(prefix):
                return True
        raise PermissionError(
            f"Write to '{semantic_key}' not allowed. "
            f"Approved prefixes: {self.allowed_write_keys}"
        )

    def read_file(self, semantic_key: str) -> str:
        """Read file content by semantic key."""
        path = self.registry.resolve(semantic_key)

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.audit_log.append({
            'timestamp': datetime.utcnow().isoformat(),
            'operation': 'read_file',
            'key': semantic_key,
            'path': str(path)
        })

        return content

    def write_file(self, semantic_key: str, content: str):
        """Write file content by semantic key (with containment check)."""
        self._check_write_allowed(semantic_key)

        path = self.registry.resolve(semantic_key)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

        self.audit_log.append({
            'timestamp': datetime.utcnow().isoformat(),
            'operation': 'write_file',
            'key': semantic_key,
            'path': str(path),
            'size_bytes': len(content)
        })

    def read_json(self, semantic_key: str) -> Dict:
        """Read JSON file by semantic key."""
        content = self.read_file(semantic_key)
        return json.loads(content)

    def write_json(self, semantic_key: str, data: Dict):
        """Write JSON file by semantic key."""
        content = json.dumps(data, indent=2)
        self.write_file(semantic_key, content)

    def list_directory(self, semantic_key: str) -> List[str]:
        """List directory contents by semantic key."""
        path = self.registry.resolve(semantic_key)

        if not path.is_dir():
            raise NotADirectoryError(f"{path} is not a directory")

        files = [f.name for f in path.iterdir()]

        self.audit_log.append({
            'timestamp': datetime.utcnow().isoformat(),
            'operation': 'list_directory',
            'key': semantic_key,
            'path': str(path),
            'file_count': len(files)
        })

        return sorted(files)

    def export_audit_log(self) -> List[Dict]:
        """Export audit log."""
        return self.audit_log.copy()
