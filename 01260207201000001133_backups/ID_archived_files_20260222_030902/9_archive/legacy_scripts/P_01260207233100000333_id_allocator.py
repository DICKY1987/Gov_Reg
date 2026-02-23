"""
Canonical ID Allocator for Registry records.

Handles:
- allocate_id() returns 20-digit string starting with '01999'
- Monotonic, sequential, no duplicates
- is_allocated() checks existing files[] for collision
- save_registry() uses atomic write pattern
"""

import json
import os
from pathlib import Path
from typing import Optional, Set, Dict, Any
from datetime import datetime


class IDAllocator:
    """
    Canonical 20-digit file_id allocator in src/registry_writer/.
    Delegates to existing scripts/P_01999000042260124027_id_allocator.py logic.
    """
    
    def __init__(self, registry_path: Optional[Path] = None):
        """
        Initialize ID allocator.
        
        Args:
            registry_path: Path to registry file (default from config)
        """
        if registry_path is None:
            from config.registry_paths import REGISTRY_PATH
            registry_path = REGISTRY_PATH
        
        self.registry_path = Path(registry_path)
        self.registry_data: Optional[Dict[str, Any]] = None
        self.allocated_ids: Set[str] = set()
        self.next_sequence: Optional[int] = None
    
    def load_registry(self) -> Dict[str, Any]:
        """
        Load registry and extract allocated IDs.
        
        Returns:
            Registry data dict
        """
        with open(self.registry_path) as f:
            self.registry_data = json.load(f)
        
        # Extract all allocated file_ids
        self.allocated_ids = set()
        for file_rec in self.registry_data.get("files", []):
            file_id = file_rec.get("file_id")
            if file_id:
                self.allocated_ids.add(str(file_id))
        
        # Determine next sequence number
        self.next_sequence = self._compute_next_sequence()
        
        return self.registry_data
    
    def _compute_next_sequence(self) -> int:
        """Compute next sequence number from existing IDs."""
        if not self.allocated_ids:
            # Start from a 3-digit suffix to keep 20-digit IDs
            return 1
        
        # Find highest sequence number
        max_seq = 0
        for file_id in self.allocated_ids:
            if file_id.startswith("01999"):
                try:
                    # Extract last 4 digits as sequence
                    seq = int(file_id[-4:])
                    if seq > max_seq:
                        max_seq = seq
                except ValueError:
                    continue
        
        return max_seq + 1
    
    def get_next_sequence(self) -> int:
        """
        Get next sequence number.
        
        Returns:
            Next sequence number
        """
        if self.next_sequence is None:
            self.load_registry()
        return self.next_sequence
    
    def allocate_id(self) -> str:
        """
        Allocate new 20-digit file_id.
        
        Returns:
            New file_id string (20 digits starting with '01999')
        """
        if self.next_sequence is None:
            self.load_registry()
        
        # Format: 01999000042260124XXX (20 digits)
        # Prefix: 01999000042260124 (17 digits)
        # Sequence: XXX (3-4 digits)
        prefix = "01999000042260124"
        seq = self.next_sequence
        
        # Pad sequence to ensure 20 total digits
        seq_str = str(seq).zfill(20 - len(prefix))
        file_id = prefix + seq_str
        
        # Ensure no collision
        while self.is_allocated(file_id):
            seq += 1
            seq_str = str(seq).zfill(20 - len(prefix))
            file_id = prefix + seq_str
        
        # Register ID
        self.register_id(file_id)
        self.next_sequence = seq + 1
        
        return file_id
    
    def is_allocated(self, file_id: str) -> bool:
        """
        Check if file_id is already allocated.
        
        Args:
            file_id: ID to check
            
        Returns:
            True if allocated, False otherwise
        """
        if self.allocated_ids is None:
            self.load_registry()
        
        return file_id in self.allocated_ids
    
    def register_id(self, file_id: str):
        """
        Register a file_id as allocated.
        
        Args:
            file_id: ID to register
        """
        if self.allocated_ids is None:
            self.load_registry()
        
        self.allocated_ids.add(file_id)
    
    def save_registry(self, registry_data: Dict[str, Any]):
        """
        Save registry using atomic write pattern.
        
        Args:
            registry_data: Registry data to save
        """
        # Atomic write: temp file + fsync + rename
        temp_path = self.registry_path.with_suffix(".tmp")
        
        with open(temp_path, 'w') as f:
            json.dump(registry_data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        
        # Atomic rename
        temp_path.replace(self.registry_path)
        
        # Reload allocated IDs
        self.load_registry()
