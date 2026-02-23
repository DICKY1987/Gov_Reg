"""
Canonical Hash Protocol - Deterministic Content Hashing

Provides deterministic SHA256 hashing for:
- PFMS mutation sets (content_hash for comparison)
- File content (content_hash for drift detection)

Rules:
- Dict keys sorted alphabetically
- JSON serialization with sorted keys
- UTF-8 encoding
- Lowercase hex output (64 chars)
"""

import hashlib
import json
from typing import Dict, Any
from pathlib import Path


def hash_canonical_data(data: Dict[str, Any]) -> str:
    """
    Compute deterministic SHA256 hash of structured data.

    Args:
        data: Dictionary to hash (will be canonicalized)

    Returns:
        64-character lowercase hex string (SHA256)

    Example:
        >>> hash_canonical_data({"key": "value"})
        'a1b2c3...'

    Rules:
    - Dict keys sorted alphabetically
    - JSON serialization with sorted keys
    - UTF-8 encoding
    - Lowercase hex output
    """
    # Canonicalize: Sort keys, minimize whitespace
    canonical_json = json.dumps(data, sort_keys=True, separators=(",", ":"))

    # Hash UTF-8 encoded bytes
    hash_bytes = hashlib.sha256(canonical_json.encode("utf-8")).digest()

    # Return lowercase hex
    return hash_bytes.hex()


def hash_file_content(path: Path) -> str:
    """
    Compute SHA256 hash of file content.

    Args:
        path: Path to file to hash

    Returns:
        64-character lowercase hex string (SHA256)

    Raises:
        FileNotFoundError: If file does not exist
        IOError: If file cannot be read

    Example:
        >>> hash_file_content(Path('src/a.py'))
        'e8c7f9a3...'
    """
    if not isinstance(path, Path):
        path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Cannot hash non-existent file: {path}")

    # Stream file in chunks (handles large files)
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def verify_determinism(data: Dict[str, Any], expected_hash: str) -> bool:
    """
    Verify that data hashes to expected value (for testing).

    Args:
        data: Dictionary to hash
        expected_hash: Expected hash value

    Returns:
        True if hash matches, False otherwise
    """
    actual_hash = hash_canonical_data(data)
    return actual_hash == expected_hash
