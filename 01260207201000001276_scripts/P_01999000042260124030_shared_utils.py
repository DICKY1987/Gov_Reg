"""Shared utilities for ID management system.

FILE_ID: 01999000042260124030
DOC_ID: P_01999000042260124030
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

# Platform-specific file locking
if sys.platform == 'win32':
    import msvcrt
else:
    import fcntl


def utc_timestamp() -> str:
    """Get current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def acquire_file_lock(file_handle, timeout: int = 10):
    """Acquire cross-process file lock (Windows + Unix compatible).
    
    Args:
        file_handle: Open file handle
        timeout: Seconds to wait for lock
        
    Raises:
        TimeoutError: If lock not acquired within timeout
    """
    start_time = time.time()
    
    while True:
        try:
            if sys.platform == 'win32':
                # Windows: lock first byte
                msvcrt.locking(file_handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                # Unix: exclusive lock
                fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return  # Lock acquired
        except (IOError, OSError):
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Could not acquire file lock within {timeout}s")
            time.sleep(0.1)  # Wait 100ms before retry


def release_file_lock(file_handle):
    """Release cross-process file lock."""
    try:
        if sys.platform == 'win32':
            msvcrt.locking(file_handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)
    except (IOError, OSError):
        pass  # Best effort release


def atomic_json_write(file_path: Path, data: Dict, lock_timeout: int = 10) -> None:
    """Write JSON file atomically with cross-process file locking.
    
    Args:
        file_path: Target file path
        data: Dictionary to serialize
        lock_timeout: Seconds to wait for lock
        
    Strategy:
    1. Acquire lock on lock file
    2. Write to temp file
    3. Atomically rename temp to target
    4. Release lock
    """
    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create lock file
    lock_path = file_path.with_suffix(file_path.suffix + ".lock")
    
    # Acquire cross-process lock via lock file
    with open(lock_path, "w") as lock_file:
        acquire_file_lock(lock_file, timeout=lock_timeout)
        
        try:
            # Write to temp file first
            temp_path = file_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write("\n")
                f.flush()
                os.fsync(f.fileno())  # Force write to disk
            
            # Atomic rename (replaces existing file)
            temp_path.replace(file_path)
        
        finally:
            release_file_lock(lock_file)


def atomic_json_read(file_path: Path, lock_timeout: int = 10) -> Dict:
    """Read JSON file with cross-process file locking.
    
    Args:
        file_path: Target file path
        lock_timeout: Seconds to wait for lock
        
    Returns:
        Parsed JSON dictionary
        
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Open for reading with shared lock
    with open(file_path, "r+", encoding="utf-8") as f:
        acquire_file_lock(f, timeout=lock_timeout)
        try:
            f.seek(0)
            data = json.load(f)
        finally:
            release_file_lock(f)
    
    return data
