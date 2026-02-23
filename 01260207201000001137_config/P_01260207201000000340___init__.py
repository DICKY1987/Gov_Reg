"""
config/ - Contract loader modules for Registry Automation

Provides canonical loaders for:
- Column Dictionary (147 headers, types, enums, normalization)
- Write Policy (immutable, tool_only, null_policy)
- Derivations (computed field formulas)
- Registry paths
"""

__version__ = "1.0.0"

# Compatibility imports for tests expecting canonical loader module names.
from . import P_01260207233100000001_column_dictionary_loader as column_dictionary_loader
from . import P_01260207233100000002_derivations_loader as derivations_loader
from . import P_01260207233100000004_write_policy_loader as write_policy_loader

__all__ = [
    "column_dictionary_loader",
    "derivations_loader",
    "write_policy_loader",
]
