"""Unified ID allocator consolidating multiple allocation strategies.

FILE_ID: 01999000042260124031
DOC_ID: P_01999000042260124031
PHASE: 1.2 - Foundation
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass
import sys
import os

# Add scripts directory to path for shared_utils
scripts_path = str(Path(__file__).parent.parent / "01260207201000001276_scripts")
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

from P_01999000042260124030_shared_utils import atomic_json_write, atomic_json_read, utc_timestamp


@dataclass
class AllocationRecord:
    """Record of an ID allocation event."""
    file_id: str
    scope: str
    namespace: str
    type_code: str
    purpose: str
    allocated_at: str
    allocated_by: str


class UnifiedIDAllocator:
    """Consolidated ID allocator using COUNTER_STORE as SSOT.
    
    Generates 20-digit IDs in format: 012602072010000XXXXX
    where XXXXX is the 5-digit counter value from COUNTER_STORE (00000-99999).
    
    Format breakdown:
    - Scope: "012602" (6 digits)
    - Namespace: "072" (3 digits) 
    - Type: "01" (2 digits)
    - Counter: 9 digits (000000000-999999999) formatted as :09d
    - Total: 20 digits (6+3+2+9)
    
    Schema constraint: Produces exactly 20-digit numeric IDs per contracts
    """
    
    BASE_ID_PREFIX = "01260207201"  # 11 digits: scope(6) + namespace(3) + type(2)
    SCOPE = "012602"
    NAMESPACE = "072"
    TYPE_CODE = "01"
    COUNTER_KEY = f"{SCOPE}:{NAMESPACE}:{TYPE_CODE}"
    COUNTER_MAX = 999999999  # 9-digit max for 20-digit total
    COUNTER_FORMAT = ":09d"  # Format to 9 digits
    
    def __init__(self, counter_store_path: Path | str, lock_timeout: float = 10.0):
        """Initialize allocator.
        
        Args:
            counter_store_path: Path to COUNTER_STORE.json
            lock_timeout: Seconds to wait for file lock
        """
        self.counter_store_path = Path(counter_store_path)
        self.lock_timeout = lock_timeout
        self.allocation_history: List[AllocationRecord] = []
        self._ensure_store()

    def _ensure_store(self) -> None:
        """Create counter store if missing."""
        if self.counter_store_path.exists():
            return

        store = {
            "schema_version": "COUNTER-STORE-1.0",
            "scope": self.SCOPE,
            "updated_utc": utc_timestamp(),
            "counter_key": ["TYPE", "NS", "SCOPE"],
            "key_format": "{SCOPE}:{NS}:{TYPE}",
            "counters": {
                self.COUNTER_KEY: 0
            },
        }

        atomic_json_write(self.counter_store_path, store, lock_timeout=self.lock_timeout)

    def _load_store(self) -> Dict:
        """Load counter store with initialization fallback."""
        if not self.counter_store_path.exists():
            self._ensure_store()

        store = atomic_json_read(self.counter_store_path, lock_timeout=self.lock_timeout)
        if "counters" not in store:
            store["counters"] = {}
        if self.COUNTER_KEY not in store["counters"]:
            store["counters"][self.COUNTER_KEY] = 0
        return store
    
    def allocate_single_id(self, purpose: str, allocated_by: str = "system") -> str:
        """Allocate a single ID.
        
        Args:
            purpose: Purpose of allocation (for audit)
            allocated_by: Who requested allocation
            
        Returns:
            str: Allocated ID (22 digits: prefix + counter)
            
        Raises:
            ValueError: If counter store is invalid or counter overflow
        """
        try:
            store = self._load_store()
            
            # Increment counter atomically
            counter = store["counters"].get(self.COUNTER_KEY, 0)
            counter += 1
            
            if counter > self.COUNTER_MAX:
                raise ValueError(
                    f"Counter overflow: {counter} exceeds maximum {self.COUNTER_MAX}. "
                    f"All available IDs exhausted."
                )
            
            store["counters"][self.COUNTER_KEY] = counter
            store["updated_utc"] = utc_timestamp()
            
            atomic_json_write(self.counter_store_path, store, lock_timeout=self.lock_timeout)
            
            # Generate ID: base (11 digits) + counter (9 digits) = 20 digits
            file_id = f"{self.BASE_ID_PREFIX}{counter:09d}"
            
            # Record allocation
            record = AllocationRecord(
                file_id=file_id,
                scope=self.SCOPE,
                namespace=self.NAMESPACE,
                type_code=self.TYPE_CODE,
                purpose=purpose,
                allocated_at=utc_timestamp(),
                allocated_by=allocated_by
            )
            self.allocation_history.append(record)
            
            return file_id
            
        except Exception as e:
            raise ValueError(f"Failed to allocate ID: {e}")
    
    def reserve_id_range(
        self,
        count: int,
        purpose: str,
        reservation_id: str,
        allocated_by: str = "system"
    ) -> List[str]:
        """Reserve a range of IDs for batch allocation.
        
        Args:
            count: Number of IDs to reserve
            purpose: Purpose of reservation (for audit)
            reservation_id: Unique reservation identifier (e.g., RES-{plan_id})
            allocated_by: Who requested reservation
            
        Returns:
            List[str]: List of allocated IDs (22 digits each)
            
        Raises:
            ValueError: If counter store is invalid or allocation fails
        """
        try:
            store = self._load_store()
            
            # Increment counter atomically
            start_counter = store["counters"].get(self.COUNTER_KEY, 0)
            end_counter = start_counter + count
            
            if end_counter > self.COUNTER_MAX:
                raise ValueError(
                    f"Counter overflow: requesting {count} IDs would exceed maximum. "
                    f"Current: {start_counter}, End: {end_counter}, Max: {self.COUNTER_MAX}"
                )
            
            store["counters"][self.COUNTER_KEY] = end_counter
            store["updated_utc"] = utc_timestamp()
            
            atomic_json_write(self.counter_store_path, store, lock_timeout=self.lock_timeout)
            
            # Generate IDs
            allocated_ids = []
            for i in range(count):
                counter_val = start_counter + i + 1
                file_id = f"{self.BASE_ID_PREFIX}{counter_val:09d}"
                allocated_ids.append(file_id)
                
                # Record allocation
                record = AllocationRecord(
                    file_id=file_id,
                    scope=self.SCOPE,
                    namespace=self.NAMESPACE,
                    type_code=self.TYPE_CODE,
                    purpose=f"{purpose} [{reservation_id}]",
                    allocated_at=utc_timestamp(),
                    allocated_by=allocated_by
                )
                self.allocation_history.append(record)
            
            return allocated_ids
            
        except Exception as e:
            raise ValueError(f"Failed to reserve ID range: {e}")
    
    def get_counter_value(self) -> int:
        """Get current counter value without incrementing.
        
        Returns:
            int: Current counter value
        """
        try:
            store = self._load_store()
            return store["counters"].get(self.COUNTER_KEY, 0)
        except Exception as e:
            raise ValueError(f"Failed to read counter: {e}")
    
    def get_allocation_history(self) -> List[Dict]:
        """Get allocation history for this session.
        
        Returns:
            List[Dict]: Allocation records
        """
        return [
            {
                "file_id": r.file_id,
                "scope": r.scope,
                "namespace": r.namespace,
                "type_code": r.type_code,
                "purpose": r.purpose,
                "allocated_at": r.allocated_at,
                "allocated_by": r.allocated_by
            }
            for r in self.allocation_history
        ]
    
    def allocate_with_metadata(
        self,
        entity_kind: str,
        purpose: str,
        metadata: Dict | None = None,
        allocated_by: str = "system"
    ) -> tuple[str, Dict]:
        """Allocate ID with entity metadata tracking.
        
        Extended allocator that tracks entity_kind (file vs directory) for
        unified governance. Returns both ID and full allocation metadata.
        
        Args:
            entity_kind: Type of entity ('file' or 'directory')
            purpose: Purpose of allocation
            metadata: Optional additional metadata
            allocated_by: Who requested allocation
            
        Returns:
            tuple: (allocated_id, metadata_dict)
            
        Raises:
            ValueError: If counter store is invalid or counter overflow
        """
        # Allocate ID using base method
        allocated_id = self.allocate_single_id(purpose, allocated_by)
        
        # Build metadata
        allocation_metadata = {
            "allocated_id": allocated_id,
            "entity_kind": entity_kind,
            "purpose": purpose,
            "allocated_by": allocated_by,
            "allocated_at": utc_timestamp(),
            "allocator_version": "1.0.0",
            "scope": self.SCOPE,
            "namespace": self.NAMESPACE,
            "type_code": self.TYPE_CODE,
        }
        
        # Merge custom metadata
        if metadata:
            allocation_metadata["custom_metadata"] = metadata
        
        return allocated_id, allocation_metadata
