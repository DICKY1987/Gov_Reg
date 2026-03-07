# DOC_LINK: DOC-CORE-CHANGE-DETECTOR-700
"""
Change Detector

Detects which files have changed since last build for incremental updates.

Uses file hashing to detect:
- Added files (new doc_ids)
- Modified files (content hash changed)
- Deleted files (doc_id no longer in inventory)

Version 2.0: Uses separate file manifest for all files (not just those with edges)
"""
# DOC_ID: DOC-CORE-CHANGE-DETECTOR-700

from pathlib import Path
from typing import List, Dict, Set, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json

from core.file_manifest import FileManifest


@dataclass
class ChangeManifest:
    """
    Manifest of changes detected since last build.

    Attributes:
        added: List of doc_ids for new files
        modified: List of doc_ids for changed files
        deleted: List of doc_ids for removed files
        timestamp: When changes were detected
    """
    added: List[str]
    modified: List[str]
    deleted: List[str]
    timestamp: datetime

    def total_changes(self) -> int:
        """Total number of changes."""
        return len(self.added) + len(self.modified) + len(self.deleted)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "added": self.added,
            "modified": self.modified,
            "deleted": self.deleted,
            "total_changes": self.total_changes(),
            "timestamp": self.timestamp.isoformat()
        }


class ChangeDetector:
    """
    Detect file changes for incremental builds.

    Version 2.0: Uses separate file manifest for accurate change detection.

    Compares current file state against cached state to identify:
    - New files to analyze
    - Modified files to re-analyze
    - Deleted files to remove from index
    """

    def __init__(self, registry, cache_dir: Path):
        """
        Initialize change detector.

        Args:
            registry: SimpleDocIDRegistry instance
            cache_dir: Directory containing cache files
        """
        self.registry = registry
        self.cache_dir = cache_dir
        self.manifest_path = cache_dir / "file_manifest.json"
        self.file_manifest = FileManifest(self.manifest_path)
        self.repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent  # core/ -> SUB_RELATIONSHIP_INDEX/ -> relationship_index/ -> RUNTIME/ -> ALL_AI/

    def detect_changes(self) -> ChangeManifest:
        """
        Detect changes since last cached build.

        Uses file manifest for accurate detection across all files.

        Returns:
            ChangeManifest with added/modified/deleted files
        """
        # Get current state
        current_docs = self.registry.get_all_docs()
        current_doc_ids = {doc["doc_id"] for doc in current_docs}
        current_docs_by_id = {doc["doc_id"]: doc for doc in current_docs}

        # Get cached state from file manifest
        cached_manifest = self.file_manifest.load_manifest()
        cached_doc_ids = set(cached_manifest.keys())

        if not cached_manifest:
            # First build - all files are new
            print("      No cached manifest found (first build)")
            return ChangeManifest(
                added=sorted(current_doc_ids),
                modified=[],
                deleted=[],
                timestamp=datetime.now(timezone.utc)
            )

        # Detect additions
        added = sorted(current_doc_ids - cached_doc_ids)

        # Detect deletions
        deleted = sorted(cached_doc_ids - current_doc_ids)

        # Detect modifications (compare file hashes)
        modified = []
        for doc_id in current_doc_ids & cached_doc_ids:
            doc = current_docs_by_id[doc_id]
            current_hash = self._compute_file_hash(doc["path"])
            cached_hash = cached_manifest.get(doc_id, "")

            if current_hash != cached_hash and current_hash != "":
                modified.append(doc_id)

        return ChangeManifest(
            added=added,
            modified=modified,
            deleted=deleted,
            timestamp=datetime.now(timezone.utc)
        )


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
