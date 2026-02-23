"""ID Allocation Module - Proactive ID Assignment.

FILE_ID: 01999000042260124027
DOC_ID: P_01999000042260124027

This module provides proactive ID allocation to prevent race conditions
when multiple developers create files simultaneously.

FIXED ISSUES:
- Cross-process file locking (Windows msvcrt + Unix fcntl)
- Path relative to module location (not CWD)
- 3-digit suffix formatting (matches existing file IDs)
- History rotation (max 100 entries)
"""
from __future__ import annotations

import sys
import threading
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent / "PATH_FILES"))

try:
    from path_registry import resolve_path, import_module
    shared_utils = import_module("SHARED_UTILS")
    utc_timestamp = shared_utils.utc_timestamp
    atomic_json_read = shared_utils.atomic_json_read
    atomic_json_write = shared_utils.atomic_json_write
except ImportError:
    # Fallback to direct import
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from P_01999000042260124030_shared_utils import utc_timestamp, atomic_json_read, atomic_json_write
    resolve_path = None

# Thread-safe lock for in-process concurrency
_lock = threading.Lock()

# Path resolved via registry (location-independent)
def _get_counter_path():
    if resolve_path:
        return resolve_path("ID_COUNTER")
    else:
        return Path(__file__).parent / "01999000042260124026_ID_COUNTER.json"

ID_COUNTER_PATH = _get_counter_path()

# History rotation settings
MAX_HISTORY_ENTRIES = 100


def read_counter() -> Dict:
    """Read the ID counter file with file locking."""
    return atomic_json_read(ID_COUNTER_PATH)


def write_counter(counter: Dict) -> None:
    """Write the ID counter file atomically with file locking."""
    # Rotate history if needed
    if len(counter.get("allocation_history", [])) > MAX_HISTORY_ENTRIES:
        counter["allocation_history"] = counter["allocation_history"][-MAX_HISTORY_ENTRIES:]
    
    atomic_json_write(ID_COUNTER_PATH, counter)


def allocate_single_id(purpose: str = "File creation") -> str:
    """Allocate a single ID atomically.
    
    Args:
        purpose: Description of what this ID will be used for
        
    Returns:
        Full file ID string (e.g., "0199900004226012497")
        
    Raises:
        FileNotFoundError: If ID counter file doesn't exist
    """
    with _lock:
        counter = read_counter()
        
        # Get next ID
        next_suffix = counter["last_allocated"] + 1
        prefix = counter["prefix"]
        
        # Format as 5-digit suffix (supports up to 99999)
        full_id = f"{prefix}{next_suffix:03d}"
        
        # Update counter
        counter["last_allocated"] = next_suffix
        counter["allocation_history"].append({
            "id": full_id,
            "allocated_at": utc_timestamp(),
            "purpose": purpose
        })
        
        write_counter(counter)
        
        return full_id


def allocate_batch_ids(count: int, purpose: str = "Batch file creation") -> List[str]:
    """Allocate multiple IDs atomically.
    
    Args:
        count: Number of IDs to allocate
        purpose: Description of what these IDs will be used for
        
    Returns:
        List of file ID strings
        
    Raises:
        ValueError: If count < 1
        FileNotFoundError: If ID counter file doesn't exist
    """
    if count < 1:
        raise ValueError(f"Count must be >= 1, got {count}")
    
    with _lock:
        counter = read_counter()
        
        prefix = counter["prefix"]
        start_suffix = counter["last_allocated"] + 1
        end_suffix = start_suffix + count
        
        # Generate IDs (5-digit suffix)
        ids = [f"{prefix}{suffix:03d}" for suffix in range(start_suffix, end_suffix)]
        
        # Update counter
        counter["last_allocated"] = end_suffix - 1
        counter["allocation_history"].append({
            "id_range": f"{ids[0]} - {ids[-1]}",
            "count": count,
            "allocated_at": utc_timestamp(),
            "purpose": purpose
        })
        
        write_counter(counter)
        
        return ids


def peek_next_id() -> str:
    """Peek at the next available ID without allocating it.
    
    Returns:
        The next ID that would be allocated
    """
    counter = read_counter()
    next_suffix = counter["last_allocated"] + 1
    return f"{counter['prefix']}{next_suffix:03d}"


def get_allocation_stats() -> Dict:
    """Get statistics about ID allocation.
    
    Returns:
        Dict with next_id, total_allocated, and recent history
    """
    counter = read_counter()
    
    return {
        "next_available_id": f"{counter['prefix']}{counter['last_allocated'] + 1:03d}",
        "total_allocated": counter["last_allocated"],
        "prefix": counter["prefix"],
        "recent_allocations": counter["allocation_history"][-10:]  # Last 10
    }


def _utc_timestamp() -> str:
    """Get current UTC timestamp in ISO format."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def reserve_id_range(start_suffix: int, end_suffix: int, purpose: str) -> None:
    """Reserve a range of IDs for planned future use.
    
    This is useful for pre-planning file structures.
    
    Args:
        start_suffix: Starting suffix number
        end_suffix: Ending suffix number (inclusive)
        purpose: Description of the reservation
        
    Raises:
        ValueError: If range overlaps with already allocated IDs
    """
    with _lock:
        counter = read_counter()
        
        if start_suffix <= counter["last_allocated"]:
            raise ValueError(
                f"Range {start_suffix}-{end_suffix} overlaps with "
                f"already allocated IDs (up to {counter['last_allocated']})"
            )
        
        prefix = counter["prefix"]
        
        # Update counter to mark range as reserved
        counter["last_allocated"] = end_suffix
        counter["allocation_history"].append({
            "id_range": f"{prefix}{start_suffix:03d} - {prefix}{end_suffix:03d}",
            "count": end_suffix - start_suffix + 1,
            "allocated_at": _utc_timestamp(),
            "purpose": f"RESERVED: {purpose}",
            "reserved": True
        })
        
        write_counter(counter)


if __name__ == "__main__":
    # CLI interface for testing
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python P_01999000042260124027_id_allocator.py allocate <purpose>")
        print("  python P_01999000042260124027_id_allocator.py batch <count> <purpose>")
        print("  python P_01999000042260124027_id_allocator.py peek")
        print("  python P_01999000042260124027_id_allocator.py stats")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "allocate":
        purpose = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Manual allocation"
        file_id = allocate_single_id(purpose)
        print(f"Allocated ID: {file_id}")
    
    elif cmd == "batch":
        if len(sys.argv) < 3:
            print("Error: batch command requires count")
            sys.exit(1)
        count = int(sys.argv[2])
        purpose = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else "Batch allocation"
        ids = allocate_batch_ids(count, purpose)
        print(f"Allocated {count} IDs:")
        for file_id in ids:
            print(f"  {file_id}")
    
    elif cmd == "peek":
        next_id = peek_next_id()
        print(f"Next available ID: {next_id}")
    
    elif cmd == "stats":
        stats = get_allocation_stats()
        print(f"Next available: {stats['next_available_id']}")
        print(f"Total allocated: {stats['total_allocated']}")
        print(f"\nRecent allocations:")
        for alloc in stats["recent_allocations"]:
            if "id" in alloc:
                print(f"  {alloc['id']} - {alloc['purpose']}")
            else:
                print(f"  {alloc.get('id_range', 'N/A')} ({alloc.get('count', 0)} IDs) - {alloc['purpose']}")
    
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
