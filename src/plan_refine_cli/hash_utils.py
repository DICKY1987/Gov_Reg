"""
Hash Utilities
Cryptographic hashing functions for artifact tracking and validation.
"""
import hashlib
import json
from pathlib import Path
from typing import Union, Dict, Any


def compute_file_hash(file_path: Union[str, Path]) -> str:
    """Compute SHA256 hash of a file
    
    Args:
        file_path: Path to file
        
    Returns:
        64-character hex SHA256 hash
    """
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def compute_json_hash(data: Union[Dict, list, Any]) -> str:
    """Compute SHA256 hash of JSON-serializable data
    
    Args:
        data: JSON-serializable object
        
    Returns:
        64-character hex SHA256 hash
        
    Note:
        Uses canonical JSON serialization (sorted keys, no whitespace)
        for deterministic hashing across platforms
    """
    canonical = json.dumps(data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def compute_string_hash(text: str) -> str:
    """Compute SHA256 hash of a string
    
    Args:
        text: Input string
        
    Returns:
        64-character hex SHA256 hash
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def verify_hash(file_path: Union[str, Path], expected_hash: str) -> bool:
    """Verify file hash matches expected value
    
    Args:
        file_path: Path to file
        expected_hash: Expected SHA256 hash
        
    Returns:
        True if hash matches, False otherwise
    """
    actual_hash = compute_file_hash(file_path)
    return actual_hash == expected_hash


def compute_artifact_index(artifact_paths: list) -> Dict[str, str]:
    """Compute hash index for multiple artifacts
    
    Args:
        artifact_paths: List of file paths
        
    Returns:
        Dictionary mapping paths to SHA256 hashes
    """
    index = {}
    for path in artifact_paths:
        if Path(path).exists():
            index[str(path)] = compute_file_hash(path)
    return index
