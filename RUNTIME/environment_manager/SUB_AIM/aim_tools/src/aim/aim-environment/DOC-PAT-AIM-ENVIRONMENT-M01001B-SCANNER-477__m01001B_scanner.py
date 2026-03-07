"""
Environment scanner for detecting issues and inefficiencies.

Scans for:
- Duplicate files (by hash)
- Misplaced cache directories
- Multiple tool installations
- Inefficient storage patterns
"""
# DOC_ID: DOC-PAT-AIM-ENVIRONMENT-M01001B-SCANNER-477

import hashlib
import os
import shutil
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from modules.aim_environment import ScannerError


@dataclass
class DuplicateGroup:
    """Group of duplicate files with same hash."""

    file_hash: str
    files: list[str]
    size_bytes: int

    @property
    def size_mb(self) -> float:
        """Size in megabytes."""
        return self.size_bytes / (1024 * 1024)

    @property
    def wasted_bytes(self) -> int:
        """Bytes wasted by duplicates (total - one copy)."""
        return self.size_bytes * (len(self.files) - 1)

    @property
    def wasted_mb(self) -> float:
        """MB wasted by duplicates."""
        return self.wasted_bytes / (1024 * 1024)


@dataclass
class MisplacedCache:
    """Cache directory outside central location."""

    path: str
    pattern: str
    size_bytes: int
    file_count: int

    @property
    def size_mb(self) -> float:
        """Size in megabytes."""
        return self.size_bytes / (1024 * 1024)


@dataclass
class ScanReport:
    """Complete environment scan report."""

    duplicates: list[DuplicateGroup] = field(default_factory=list)
    misplaced_caches: list[MisplacedCache] = field(default_factory=list)
    total_scanned_files: int = 0
    total_scanned_bytes: int = 0

    @property
    def total_wasted_mb(self) -> float:
        """Total MB wasted by duplicates."""
        return sum(d.wasted_mb for d in self.duplicates)

    @property
    def total_cache_mb(self) -> float:
        """Total MB in misplaced caches."""
        return sum(c.size_mb for c in self.misplaced_caches)


class EnvironmentScanner:
    """Scan environment for issues and inefficiencies."""

    DEFAULT_CACHE_PATTERNS = [
        ".aider",
        ".jules",
        ".claude",
        "node_modules/.cache",
        ".pytest_cache",
        "__pycache__",
        ".mypy_cache",
        ".ruff_cache",
        ".eslintcache",
        ".tsbuildinfo",
        ".next/cache",
        ".nuxt",
        "dist",
        "build",
        ".venv/Lib/site-packages",
        ".git/objects",
    ]

    def __init__(self, cache_patterns: Optional[list[str]] = None):
        """
        Initialize scanner.

        Args:
            cache_patterns: Custom cache patterns to detect (uses defaults if None)
        """
        self.cache_patterns = cache_patterns or self.DEFAULT_CACHE_PATTERNS

    def _hash_file(self, path: Path, chunk_size: int = 8192) -> str:
        """
        Calculate SHA256 hash of file.

        Args:
            path: File path
            chunk_size: Bytes to read per chunk

        Returns:
            Hex digest of file hash
        """
        hasher = hashlib.sha256()

        try:
            with open(path, "rb") as f:
                while chunk := f.read(chunk_size):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except (OSError, PermissionError):
            return ""

    def _dir_size(self, path: Path) -> tuple[int, int]:
        """
        Calculate total size and file count of directory.

        Args:
            path: Directory path

        Returns:
            Tuple of (total_bytes, file_count)
        """
        total_bytes = 0
        file_count = 0

        try:
            for item in path.rglob("*"):
                if item.is_file():
                    try:
                        total_bytes += item.stat().st_size
                        file_count += 1
                    except (OSError, PermissionError):
                        pass
        except (OSError, PermissionError):
            pass

        return total_bytes, file_count

    def find_duplicates(
        self,
        roots: list[Path],
        min_size_kb: int = 100,
        extensions: Optional[list[str]] = None
    ) -> list[DuplicateGroup]:
        """
        Find duplicate files by content hash.

        Args:
            roots: Root directories to scan
            min_size_kb: Minimum file size in KB to check
            extensions: File extensions to check (None = all)

        Returns:
            List of duplicate file groups
        """
        hash_map = defaultdict(list)
        min_size_bytes = min_size_kb * 1024

        for root in roots:
            if not root.exists():
                continue

            try:
                for file_path in root.rglob("*"):
                    if not file_path.is_file():
                        continue

                    # Skip if too small
                    try:
                        size = file_path.stat().st_size
                        if size < min_size_bytes:
                            continue
                    except (OSError, PermissionError):
                        continue

                    # Skip if extension filter doesn't match
                    if extensions and file_path.suffix.lower() not in extensions:
                        continue

                    # Calculate hash
                    file_hash = self._hash_file(file_path)
                    if file_hash:
                        hash_map[file_hash].append((str(file_path), size))

            except (OSError, PermissionError):
                continue

        # Build duplicate groups
        duplicates = []
        for file_hash, files in hash_map.items():
            if len(files) > 1:
                # All files with same hash have same size
                size = files[0][1]
                file_paths = [f[0] for f in files]
                duplicates.append(DuplicateGroup(
                    file_hash=file_hash,
                    files=file_paths,
                    size_bytes=size
                ))

        # Sort by wasted space (descending)
        duplicates.sort(key=lambda d: d.wasted_bytes, reverse=True)

        return duplicates

    def find_misplaced_caches(
        self,
        roots: list[Path],
        central_cache: Optional[Path] = None
    ) -> list[MisplacedCache]:
        """
        Find cache directories outside central location.

        Args:
            roots: Root directories to scan
            central_cache: Central cache location (caches here are not flagged)

        Returns:
            List of misplaced cache directories
        """
        misplaced = []

        for root in roots:
            if not root.exists():
                continue

            try:
                for pattern in self.cache_patterns:
                    # Handle glob patterns
                    if "/" in pattern:
                        # Complex pattern like "node_modules/.cache"
                        for cache_path in root.rglob(pattern):
                            if not cache_path.is_dir():
                                continue

                            # Skip if in central cache
                            if central_cache and cache_path.is_relative_to(central_cache):
                                continue

                            size_bytes, file_count = self._dir_size(cache_path)

                            if size_bytes > 0:
                                misplaced.append(MisplacedCache(
                                    path=str(cache_path),
                                    pattern=pattern,
                                    size_bytes=size_bytes,
                                    file_count=file_count
                                ))
                    else:
                        # Simple pattern like "__pycache__"
                        for cache_path in root.rglob(pattern):
                            if not cache_path.is_dir():
                                continue

                            if central_cache and cache_path.is_relative_to(central_cache):
                                continue

                            size_bytes, file_count = self._dir_size(cache_path)

                            if size_bytes > 0:
                                misplaced.append(MisplacedCache(
                                    path=str(cache_path),
                                    pattern=pattern,
                                    size_bytes=size_bytes,
                                    file_count=file_count
                                ))

            except (OSError, PermissionError):
                continue

        # Sort by size (descending)
        misplaced.sort(key=lambda c: c.size_bytes, reverse=True)

        return misplaced

    def scan(
        self,
        roots: list[Path],
        min_duplicate_size_kb: int = 100,
        central_cache: Optional[Path] = None
    ) -> ScanReport:
        """
        Perform complete environment scan.

        Args:
            roots: Root directories to scan
            min_duplicate_size_kb: Minimum file size for duplicate detection
            central_cache: Central cache location

        Returns:
            Complete scan report
        """
        report = ScanReport()

        # Find duplicates
        report.duplicates = self.find_duplicates(roots, min_duplicate_size_kb)

        # Find misplaced caches
        report.misplaced_caches = self.find_misplaced_caches(roots, central_cache)

        # Calculate totals
        for root in roots:
            if root.exists():
                try:
                    for file_path in root.rglob("*"):
                        if file_path.is_file():
                            try:
                                report.total_scanned_bytes += file_path.stat().st_size
                                report.total_scanned_files += 1
                            except (OSError, PermissionError):
                                pass
                except (OSError, PermissionError):
                    pass

        return report

    def cleanup_cache(self, cache_path: Path) -> bool:
        """
        Remove a cache directory.

        Args:
            cache_path: Path to cache directory

        Returns:
            True if cleanup successful
        """
        try:
            if cache_path.exists() and cache_path.is_dir():
                shutil.rmtree(cache_path)
                return True
        except (OSError, PermissionError) as e:
            raise ScannerError(f"Failed to cleanup {cache_path}: {e}")

        return False

    def remove_duplicates(
        self,
        duplicate_group: DuplicateGroup,
        keep_index: int = 0
    ) -> list[str]:
        """
        Remove duplicate files, keeping one copy.

        Args:
            duplicate_group: Group of duplicate files
            keep_index: Index of file to keep (default: first)

        Returns:
            List of removed file paths
        """
        removed = []

        for i, file_path in enumerate(duplicate_group.files):
            if i == keep_index:
                continue

            try:
                path = Path(file_path)
                if path.exists():
                    path.unlink()
                    removed.append(file_path)
            except (OSError, PermissionError) as e:
                raise ScannerError(f"Failed to remove {file_path}: {e}")

        return removed
