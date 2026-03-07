# DOC_LINK: DOC-ERROR-ENGINE-FILE-HASH-CACHE-117
"""Incremental validation cache implementation.

Stores a JSON mapping of absolute file paths to their last validated hash and metadata.
"""

# DOC_ID: DOC-ERROR-ENGINE-FILE-HASH-CACHE-117
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Optional

from phase6_error_recovery.modules.error_engine.src.shared.utils.hashing import (
    sha256_file,
)
from phase6_error_recovery.modules.error_engine.src.shared.utils.time import utc_now_iso


class FileHashCache:
    """Stores hashes of previously validated files for incremental runs."""

    def __init__(self, cache_path: Path) -> None:
        self.cache_path = cache_path
        self.cache: Dict[str, Dict[str, object]] = {}

    def load(self) -> None:
        """Load the cache data from disk."""
        try:
            if self.cache_path.exists():
                text = self.cache_path.read_text(encoding="utf-8")
                self.cache = json.loads(text) if text.strip() else {}
            else:
                self.cache = {}
        except Exception:
            # Corrupt cache: start fresh but do not raise
            self.cache = {}

    def save(self) -> None:
        """Persist the cache data to disk."""
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.cache_path.with_suffix(self.cache_path.suffix + ".tmp")
        data = json.dumps(self.cache, ensure_ascii=False, separators=(",", ":"))
        tmp.write_text(data, encoding="utf-8")
        os.replace(tmp, self.cache_path)

    def has_changed(self, file_path: Path) -> bool:
        """Return ``True`` when the file content differs from the cached entry."""
        key = str(file_path.resolve())
        try:
            current_hash = sha256_file(file_path)
        except FileNotFoundError:
            # Treat missing file as changed (caller can handle)
            return True
        entry = self.cache.get(key)
        if not entry or entry.get("hash") != current_hash:
            # Update in-memory to the new hash and timestamp; caller can persist
            self.cache[key] = {
                "hash": current_hash,
                "last_validated": utc_now_iso(),
            }
            return True
        return False

    def mark_validated(
        self, file_path: Path, had_errors: Optional[bool] = None
    ) -> None:
        """Update the cache record for a file after successful validation."""
        key = str(file_path.resolve())
        try:
            current_hash = sha256_file(file_path)
        except FileNotFoundError:
            current_hash = ""
        entry = self.cache.get(key, {})
        entry.update(
            {
                "hash": current_hash,
                "last_validated": utc_now_iso(),
            }
        )
        if had_errors is not None:
            entry["had_errors"] = bool(had_errors)
        self.cache[key] = entry
