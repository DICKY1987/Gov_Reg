"""
FILE_ID: 01999000042260125013
Migrated from: C:\Users\richg\eafix-modular\repo_autoops\automation_descriptor\normalizer.py

Facade: delegates to src/registry_writer/normalizer.py
"""

"""
Normalizer

doc_id: DOC-AUTO-DESC-0011
purpose: Automatic normalization on write
phase: Phase 5 - Registry Writer
contract: frozen_contracts.path_contract (relative_path, POSIX format)
"""

import sys
from typing import Dict, Any, Optional
from pathlib import Path

# Add parent directories to path for imports
_repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_repo_root))

from src.registry_writer.normalizer import Normalizer as CanonicalNormalizer


class Normalizer:
    """
    Facade: delegates to src/registry_writer/normalizer.py
    
    Automatic normalization on registry write.
    
    Contract (Frozen):
    - Paths: Forward-slash (POSIX), repo-relative
    - Enum values: LOWERCASE per Column Dictionary (record_kind, entity_kind, extension)
    - Timestamps: ISO 8601 with 'Z' suffix
    """
    
    def __init__(self):
        """Initialize facade with canonical normalizer."""
        self._canonical = CanonicalNormalizer()
    
    def normalize_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a registry record.
        
        Args:
            record: Registry record dict
            
        Returns:
            Normalized record (new dict, original unchanged)
        """
        return self._canonical.normalize_record(record)
        
    def normalize_path(self, path: Optional[str]) -> Optional[str]:
        """
        Normalize path to POSIX forward-slash format.
        
        Args:
            path: Path (may be Windows-style with backslashes)
            
        Returns:
            POSIX-style path with forward slashes
            
        Example:
            "repo_autoops\\tools\\example.py" → "repo_autoops/tools/example.py"
        """
        return self._canonical.normalize_path(path)
        
    def normalize_timestamp(self, timestamp: Optional[str]) -> Optional[str]:
        """
        Ensure timestamp is ISO 8601 with 'Z' suffix.
        
        Args:
            timestamp: Timestamp string
            
        Returns:
            ISO 8601 timestamp with 'Z' suffix
            
        Example:
            "2026-01-23T14:00:00" → "2026-01-23T14:00:00Z"
        """
        return self._canonical.normalize_timestamp(timestamp)
        
    def normalize_rel_type(self, rel_type: str) -> str:
        """
        Normalize rel_type enum (legacy method).
        
        Args:
            rel_type: Relationship type
            
        Returns:
            Normalized rel_type
        """
        return rel_type.lower() if rel_type else rel_type
