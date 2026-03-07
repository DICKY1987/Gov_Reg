# DOC_LINK: DOC-CORE-FILE-MANIFEST-703
"""
File Manifest

Lightweight file manifest for tracking ALL files, not just those with edges.

Purpose:
- Store file hashes for all 3,394 files
- Enable true incremental detection
- Separate from edge cache (smaller, faster to load)
"""
# DOC_ID: DOC-CORE-FILE-MANIFEST-703

from pathlib import Path
from typing import Dict, Set
from datetime import datetime, timezone
import json
import hashlib


class FileManifest:
    """
    Tracks file hashes for all files in repository.

    Separate from edge cache for performance:
    - Smaller file (just hashes, not edges)
    - Faster to load/compare
    - Enables true incremental detection
    """

    def __init__(self, manifest_path: Path):
        """
        Initialize file manifest.

        Args:
            manifest_path: Path to manifest file (cache/file_manifest.json)
        """
        self.manifest_path = manifest_path
        self.repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent  # core/ -> SUB_RELATIONSHIP_INDEX/ -> relationship_index/ -> RUNTIME/ -> ALL_AI/

    def build_manifest(self, registry) -> Dict[str, str]:
        """
        Build file manifest from registry.

        Args:
            registry: SimpleDocIDRegistry instance

        Returns:
            Dict mapping doc_id -> file_hash
        """
        manifest = {}
        docs = registry.get_all_docs()

        print(f"      Building file manifest for {len(docs)} files...")

        for i, doc in enumerate(docs):
            if (i + 1) % 500 == 0:
                print(f"      Hashing {i + 1}/{len(docs)}...")

            doc_id = doc["doc_id"]
            file_hash = self._compute_file_hash(doc["path"])
            manifest[doc_id] = file_hash

        return manifest

    def load_manifest(self) -> Dict[str, str]:
        """
        Load file manifest from disk.

        Returns:
            Dict mapping doc_id -> file_hash, or empty dict if not found
        """
        if not self.manifest_path.exists():
            return {}

        try:
            with open(self.manifest_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get("files", {})
        except (json.JSONDecodeError, IOError):
            return {}

    def save_manifest(self, manifest: Dict[str, str]):
        """
        Save file manifest to disk.

        Args:
            manifest: Dict mapping doc_id -> file_hash
        """
        data = {
            "version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "file_count": len(manifest),
            "files": manifest
        }

        with open(self.manifest_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, sort_keys=True)

    def _compute_file_hash(self, rel_path: str) -> str:
        """
        Compute SHA-256 hash of file content.

        Args:
            rel_path: Path relative to repo root

        Returns:
            SHA-256 hex digest, or empty string if file doesn't exist
        """
        file_path = self.repo_root / rel_path

        if not file_path.exists():
            return ""

        try:
            content = file_path.read_bytes()
            return hashlib.sha256(content).hexdigest()
        except (IOError, OSError):
            return ""
