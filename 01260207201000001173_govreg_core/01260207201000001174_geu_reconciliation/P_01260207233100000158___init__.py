"""
GEU Reconciliation CLI Module

Fixes GEU (Governance Enforcement Unit) grouping reliability by:
1. Normalizing file_id format (19-digit → 20-digit)
2. Merging duplicate file_id entries deterministically
3. Normalizing geu_ids type (string → array)
4. Mapping GEU labels to canonical IDs (GEU-2 → 99...)
5. Enforcing column dictionary rules

Phase 1 Implementation (Week 1):
- registry_loader: String-safe JSON loading
- id_normalizer: File ID canonicalization and duplicate merging
- patch_writer: RFC-6902 patch generation and evidence logging
"""

__version__ = "0.1.0"
__author__ = "Gov_Reg Core Team"

from .registry_loader import load_registry, save_registry
from .id_normalizer import (
    normalize_file_id,
    detect_duplicates,
    merge_duplicates,
    IDNormalizationResult,
)
from .patch_writer import PatchWriter

__all__ = [
    "load_registry",
    "save_registry",
    "normalize_file_id",
    "detect_duplicates",
    "merge_duplicates",
    "IDNormalizationResult",
    "PatchWriter",
]
