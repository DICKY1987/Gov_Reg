"""
Gov_Reg Core Module - Registry-Planning Integration

Core components:
- canonical_hash: Deterministic content hashing
- feature_flags: Migration phase control
- registry_writer: Non-destructive updates
- conflict_validator: Mutation conflict detection
"""

__version__ = "1.2.0"

from .canonical_hash import hash_canonical_data, hash_file_content
from .feature_flags import FeatureFlags, MigrationPhase, get_feature_flags

__all__ = [
    "hash_canonical_data",
    "hash_file_content",
    "FeatureFlags",
    "MigrationPhase",
    "get_feature_flags",
]
