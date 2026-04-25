"""Reservation ledger manager for tracking file ID reservations.

FILE_ID: 01999000042260124032
DOC_ID: P_01999000042260124032
PHASE: 1.3 - Foundation
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import sys
import os

RUNTIME_ROOT = Path(__file__).resolve().parent.parent
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from P_01999000042260124030_shared_utils import atomic_json_write, atomic_json_read, utc_timestamp


@dataclass
class ReservationEntry:
    """Single reservation entry."""
    file_id: str
    relative_path: str
    reservation_timestamp: str
    state: str  # RESERVED, COMMITTED, CANCELLED
    committed_at: Optional[str] = None
    committed_by_mutation_set_id: Optional[str] = None


class ReservationLedger:
    """Manages per-plan reservation ledgers with state transitions."""
    
    def __init__(self, plan_id: str, registry_root: Path | str):
        """Initialize ledger for a specific plan.
        
        Args:
            plan_id: Unique plan identifier
            registry_root: Root directory containing REGISTRY/reservations/
        """
        self.plan_id = plan_id
        self.registry_root = Path(registry_root)
        self.reservations_dir = self.registry_root / "REGISTRY" / "reservations"
        self.ledger_path = self.reservations_dir / f"RES-{plan_id}.json"
        
        # Ensure directory exists
        self.reservations_dir.mkdir(parents=True, exist_ok=True)
    
    def create_reservation(
        self,
        file_ids: List[str],
        relative_paths: List[str],
        allocated_by: str = "system",
        allocation_metadata: Optional[Dict] = None
    ) -> Dict:
        """Create a new reservation ledger.
        
        Args:
            file_ids: List of allocated file IDs
            relative_paths: Corresponding relative paths (same length)
            allocated_by: Who allocated the IDs
            allocation_metadata: Additional context (e.g., plan name, user)
            
        Returns:
            Dict: Status report
            
        Raises:
            ValueError: If lengths don't match or ledger already exists
        """
        if len(file_ids) != len(relative_paths):
            raise ValueError(
                f"Length mismatch: {len(file_ids)} IDs vs {len(relative_paths)} paths"
            )
        
        if self.ledger_path.exists():
            raise ValueError(f"Reservation already exists: {self.ledger_path}")
        
        # Sort by path for determinism
        paired = sorted(zip(relative_paths, file_ids), key=lambda x: x[0])
        relative_paths_sorted, file_ids_sorted = zip(*paired) if paired else ([], [])
        
        # Create entries
        entries = {}
        for file_id, rel_path in zip(file_ids_sorted, relative_paths_sorted):
            entries[file_id] = {
                "file_id": file_id,
                "relative_path": rel_path,
                "reservation_timestamp": utc_timestamp(),
                "state": "RESERVED",
                "committed_at": None,
                "committed_by_mutation_set_id": None
            }
        
        # Create ledger
        ledger_data = {
            "plan_id": self.plan_id,
            "created_at": utc_timestamp(),
            "allocated_by": allocated_by,
            "allocation_metadata": allocation_metadata or {},
            "total_reservations": len(entries),
            "entries": entries
        }
        
        # Write atomically
        atomic_json_write(self.ledger_path, ledger_data)
        
        return {
            "status": "SUCCESS",
            "plan_id": self.plan_id,
            "ledger_path": str(self.ledger_path),
            "total_reservations": len(entries),
            "created_at": ledger_data["created_at"]
        }
    
    def get_reservation(self, file_id: str) -> Optional[ReservationEntry]:
        """Get a single reservation entry.
        
        Args:
            file_id: File ID to look up
            
        Returns:
            Optional[ReservationEntry]: Entry if found, None otherwise
        """
        if not self.ledger_path.exists():
            return None
        
        try:
            ledger = atomic_json_read(self.ledger_path)
            entry_data = ledger.get("entries", {}).get(file_id)
            
            if not entry_data:
                return None
            
            return ReservationEntry(
                file_id=entry_data["file_id"],
                relative_path=entry_data["relative_path"],
                reservation_timestamp=entry_data["reservation_timestamp"],
                state=entry_data["state"],
                committed_at=entry_data.get("committed_at"),
                committed_by_mutation_set_id=entry_data.get("committed_by_mutation_set_id")
            )
        except Exception:
            return None
    
    def commit_reservation(
        self,
        file_id: str,
        mutation_set_id: str
    ) -> ReservationEntry:
        """Commit a reservation (transition RESERVED → COMMITTED).
        
        Args:
            file_id: File ID to commit
            mutation_set_id: Mutation set ID performing the commitment
            
        Returns:
            ReservationEntry: Updated entry
            
        Raises:
            ValueError: If entry not found or already committed
        """
        if not self.ledger_path.exists():
            raise ValueError(f"Reservation ledger not found: {self.ledger_path}")
        
        ledger = atomic_json_read(self.ledger_path)
        
        if file_id not in ledger.get("entries", {}):
            raise ValueError(f"File ID not in reservation: {file_id}")
        
        entry = ledger["entries"][file_id]
        
        if entry["state"] != "RESERVED":
            raise ValueError(
                f"Cannot commit {file_id}: already {entry['state']}"
            )
        
        # Update state
        entry["state"] = "COMMITTED"
        entry["committed_at"] = utc_timestamp()
        entry["committed_by_mutation_set_id"] = mutation_set_id
        
        ledger["updated_at"] = utc_timestamp()
        
        # Write atomically
        atomic_json_write(self.ledger_path, ledger)
        
        return ReservationEntry(
            file_id=entry["file_id"],
            relative_path=entry["relative_path"],
            reservation_timestamp=entry["reservation_timestamp"],
            state=entry["state"],
            committed_at=entry["committed_at"],
            committed_by_mutation_set_id=entry["committed_by_mutation_set_id"]
        )
    
    def cancel_reservation(
        self,
        file_id: str,
        reason: str,
        cancelled_by: str = "system"
    ) -> ReservationEntry:
        """Cancel a reservation (transition RESERVED → CANCELLED).
        
        Args:
            file_id: File ID to cancel
            reason: Reason for cancellation (audit)
            cancelled_by: Who cancelled
            
        Returns:
            ReservationEntry: Updated entry
            
        Raises:
            ValueError: If entry not found or already committed
        """
        if not self.ledger_path.exists():
            raise ValueError(f"Reservation ledger not found: {self.ledger_path}")
        
        ledger = atomic_json_read(self.ledger_path)
        
        if file_id not in ledger.get("entries", {}):
            raise ValueError(f"File ID not in reservation: {file_id}")
        
        entry = ledger["entries"][file_id]
        
        if entry["state"] == "COMMITTED":
            raise ValueError(f"Cannot cancel {file_id}: already COMMITTED")
        
        # Update state
        entry["state"] = "CANCELLED"
        entry["cancelled_at"] = utc_timestamp()
        entry["cancelled_reason"] = reason
        entry["cancelled_by"] = cancelled_by
        
        ledger["updated_at"] = utc_timestamp()
        
        # Write atomically
        atomic_json_write(self.ledger_path, ledger)
        
        return ReservationEntry(
            file_id=entry["file_id"],
            relative_path=entry["relative_path"],
            reservation_timestamp=entry["reservation_timestamp"],
            state=entry["state"],
            committed_at=entry.get("committed_at"),
            committed_by_mutation_set_id=entry.get("committed_by_mutation_set_id")
        )
    
    def expire_uncommitted(self, max_age_seconds: int = 86400) -> int:
        """Expire uncommitted reservations older than max_age.
        
        Args:
            max_age_seconds: Age threshold (default 1 day)
            
        Returns:
            int: Number of entries marked EXPIRED
        """
        if not self.ledger_path.exists():
            return 0
        
        from datetime import datetime, timedelta, timezone
        
        ledger = atomic_json_read(self.ledger_path)
        now = datetime.now(timezone.utc)
        expired_count = 0
        
        for file_id, entry in ledger.get("entries", {}).items():
            if entry["state"] == "RESERVED":
                created = datetime.fromisoformat(entry["reservation_timestamp"])
                age = (now - created).total_seconds()
                
                if age > max_age_seconds:
                    entry["state"] = "EXPIRED"
                    entry["expired_at"] = utc_timestamp()
                    expired_count += 1
        
        if expired_count > 0:
            ledger["updated_at"] = utc_timestamp()
            atomic_json_write(self.ledger_path, ledger)
        
        return expired_count
    
    def validate_all_committed(self) -> Tuple[bool, List[str]]:
        """Validate that all reservations are committed.
        
        Returns:
            Tuple[bool, List[str]]: (all_committed, list_of_uncommitted_ids)
        """
        if not self.ledger_path.exists():
            return False, ["Ledger not found"]
        
        try:
            ledger = atomic_json_read(self.ledger_path)
            uncommitted = [
                file_id
                for file_id, entry in ledger.get("entries", {}).items()
                if entry.get("state") != "COMMITTED"
            ]
            
            return len(uncommitted) == 0, uncommitted
        except Exception as e:
            return False, [f"Error reading ledger: {e}"]
    
    def generate_audit_report(self) -> Dict:
        """Generate audit report for the reservation.
        
        Returns:
            Dict: Comprehensive audit report
        """
        if not self.ledger_path.exists():
            return {"status": "NOT_FOUND", "plan_id": self.plan_id}
        
        try:
            ledger = atomic_json_read(self.ledger_path)
            
            entries = ledger.get("entries", {})
            states = {}
            for entry in entries.values():
                state = entry.get("state")
                states[state] = states.get(state, 0) + 1
            
            return {
                "plan_id": self.plan_id,
                "created_at": ledger.get("created_at"),
                "updated_at": ledger.get("updated_at"),
                "allocated_by": ledger.get("allocated_by"),
                "total_reservations": ledger.get("total_reservations", 0),
                "state_counts": states,
                "all_committed": len(entries) > 0 and states.get("COMMITTED", 0) == len(entries),
                "uncommitted_count": states.get("RESERVED", 0) + states.get("CANCELLED", 0),
                "ledger_path": str(self.ledger_path)
            }
        except Exception as e:
            return {"status": "ERROR", "error": str(e), "plan_id": self.plan_id}
