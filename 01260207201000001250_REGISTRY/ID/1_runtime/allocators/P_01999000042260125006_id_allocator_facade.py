"""
ID Allocator Facade

This is the ONLY module that may be imported for ID allocation.
All allocation requests MUST go through this facade.

Backend allocator implementations are marked INTERNAL and blocked from direct import.

Contract: docs/ID_IDENTITY_CONTRACT.md
"""

from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import json
import os
import sys

MODULE_DIR = Path(__file__).resolve().parent
RUNTIME_ROOT = MODULE_DIR.parent
PROJECT_ROOT = MODULE_DIR.parents[2]
VALIDATORS_DIR = RUNTIME_ROOT / "validators"

if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
if str(VALIDATORS_DIR) not in sys.path:
    sys.path.insert(0, str(VALIDATORS_DIR))

repo_root = PROJECT_ROOT

# Import from same directory
sys.path.insert(0, str(MODULE_DIR))
from P_01999000042260124031_unified_id_allocator import UnifiedIDAllocator


def _expand_path(value: str, base: Path) -> Path:
    expanded = os.path.expandvars(os.path.expanduser(value))
    path = Path(expanded)
    if not path.is_absolute():
        path = (base / path).resolve()
    return path


def _is_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _load_allocator_config(repo_root: Path) -> Tuple[Optional[Path], Optional[int]]:
    config_path = repo_root / ".idpkg" / "config.json"
    if not config_path.exists():
        return None, None

    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    allocator_cfg = data.get("allocator", {})
    store_path = allocator_cfg.get("allocator_store_path")
    lock_timeout_ms = allocator_cfg.get("lock_timeout_ms")
    if not store_path:
        return None, lock_timeout_ms

    return _expand_path(store_path, repo_root), lock_timeout_ms


class IDAllocatorFacade:
    """
    Facade for ID allocation operations.
    
    This is the canonical entrypoint for all ID allocation.
    Direct imports of backend allocators are blocked by the pre-commit gate.
    """
    
    def __init__(self, counter_store_path: Optional[Path] = None):
        """
        Initialize facade.
        
        Args:
            counter_store_path: Optional path to counter store
                               (defaults to standard location)
        """
        if counter_store_path is None:
            counter_store_path, lock_timeout_ms = _load_allocator_config(repo_root)
            if counter_store_path is None:
                appdata = os.environ.get("APPDATA")
                if not appdata:
                    appdata = str(Path.home() / "AppData" / "Roaming")
                counter_store_path = Path(appdata) / "GovReg" / "IdAllocator" / "COUNTER_STORE.json"
                lock_timeout_ms = 5000
        else:
            lock_timeout_ms = 5000

        if lock_timeout_ms is None:
            lock_timeout_ms = 5000

        if _is_within(counter_store_path, repo_root):
            raise ValueError("Allocator store path must be outside the project root")

        lock_timeout = max(int(lock_timeout_ms or 0) / 1000.0, 0)
        self._allocator = UnifiedIDAllocator(counter_store_path, lock_timeout=lock_timeout)
    
    def allocate_file_id(self, 
                         context: Optional[str] = None,
                         metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Allocate a new 20-digit file_id.
        
        Args:
            context: Optional context string for logging
            metadata: Optional metadata dict for traceability
            
        Returns:
            20-digit numeric file_id
        """
        return self._allocator.allocate_single_id(
            purpose=context or "file_allocation",
            allocated_by=metadata.get("allocated_by", "facade") if metadata else "facade"
        )
    
    def allocate_enhanced_id(self,
                            context: Optional[str] = None,
                            metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Allocate a new 20-digit enhanced_id (same as file_id for now).
        
        Args:
            context: Optional context string for logging
            metadata: Optional metadata dict for traceability
            
        Returns:
            20-digit enhanced_id
        """
        return self._allocator.allocate_single_id(
            purpose=context or "enhanced_allocation",
            allocated_by=metadata.get("allocated_by", "facade") if metadata else "facade"
        )
    
    def validate_id(self, identifier: str) -> Dict[str, Any]:
        """
        Validate an ID and return its properties.
        
        Args:
            identifier: ID string to validate
            
        Returns:
            Dictionary with validation results:
            {
                "valid": bool,
                "id_type": "file_id" | "doc_id" | "enhanced_id" | None,
                "numeric_id": str (20-digit file_id)
            }
        """
        from P_01999000042260125002_canonical_id_patterns import (
            detect_id_type, normalize_to_file_id
        )
        
        id_type = detect_id_type(identifier)
        numeric_id = normalize_to_file_id(identifier)
        
        return {
            "valid": id_type is not None,
            "id_type": id_type,
            "numeric_id": numeric_id
        }


# ============================================================================
# Convenience Functions (module-level API)
# ============================================================================

_default_facade: Optional[IDAllocatorFacade] = None


def _get_default_facade() -> IDAllocatorFacade:
    """Get or create the default facade instance."""
    global _default_facade
    if _default_facade is None:
        _default_facade = IDAllocatorFacade()
    return _default_facade


def allocate_id(context: Optional[str] = None,
                metadata: Optional[Dict[str, Any]] = None) -> str:
    """
    Allocate a new 20-digit file_id (convenience function).
    
    This is the most common allocation operation.
    
    Args:
        context: Optional context string for logging
        metadata: Optional metadata dict for traceability
        
    Returns:
        20-digit numeric file_id
        
    Example:
        >>> from govreg_core.P_01999000042260125006_id_allocator_facade import allocate_id
        >>> new_id = allocate_id(context="my_operation")
        >>> print(new_id)
        01999000042260125007
    """
    return _get_default_facade().allocate_file_id(context, metadata)


def allocate_file_id(context: Optional[str] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> str:
    """Allocate a new 20-digit file_id (alias for allocate_id)."""
    return allocate_id(context, metadata)


def allocate_enhanced_id(context: Optional[str] = None,
                         metadata: Optional[Dict[str, Any]] = None) -> str:
    """Allocate a new 22-digit enhanced_id."""
    return _get_default_facade().allocate_enhanced_id(context, metadata)


def allocate_dir_id(relative_path: str,
                   context: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> tuple[str, Dict]:
    """
    Allocate a new directory ID with metadata tracking.
    
    This function allocates a 20-digit directory ID from the unified allocator
    and returns both the ID and its allocation metadata.
    
    Args:
        relative_path: Directory path relative to project root
        context: Optional context string for logging
        metadata: Optional additional metadata for traceability
        
    Returns:
        tuple: (dir_id, allocation_metadata)
            dir_id: 20-digit numeric directory ID
            allocation_metadata: Dict with allocation details
            
    Example:
        >>> from govreg_core.P_01999000042260125006_id_allocator_facade import allocate_dir_id
        >>> dir_id, meta = allocate_dir_id("src/module_a")
        >>> print(dir_id)
        01999000042260125008
        >>> print(meta['entity_kind'])
        directory
    """
    facade = _get_default_facade()
    
    # Prepare metadata
    alloc_metadata = metadata or {}
    alloc_metadata["relative_path"] = relative_path
    
    # Use allocate_with_metadata from allocator
    dir_id, full_metadata = facade._allocator.allocate_with_metadata(
        entity_kind="directory",
        purpose=context or f"directory:{relative_path}",
        metadata=alloc_metadata,
        allocated_by="dir_id_allocator"
    )
    
    return dir_id, full_metadata



def validate_id(identifier: str) -> Dict[str, Any]:
    """Validate an ID and return its properties."""
    return _get_default_facade().validate_id(identifier)
