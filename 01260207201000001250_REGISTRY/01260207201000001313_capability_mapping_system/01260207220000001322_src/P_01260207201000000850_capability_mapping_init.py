"""
Capability Mapping System Package

This package provides a three-step system for mapping repository files to their capabilities:
1. Discover capabilities from CLI commands, gate validators, schemas, and documentation
2. Build complete file inventory with objective metadata
3. Create purpose registry mapping files → capabilities

The system follows strict determinism requirements and uses precedence-based
conflict resolution when sources disagree about capabilities.

Exports:
    - CapabilityDiscoverer: Step 1 - Discover capabilities
    - FileInventoryBuilder: Step 2 - Build file inventory
    - PurposeRegistryBuilder: Step 3 - Map files to capabilities
    - ArgparseExtractor: Utility - Extract CLI commands from Python files
    - CallGraphBuilder: Utility - Build import/call graphs
"""

__version__ = "1.0.0"
__author__ = "Gov_Reg System"

# Import main classes (will be available once modules are created)
try:
    from .P_01260207201000000982_01999000042260130005_capability_discoverer import CapabilityDiscoverer
except ImportError:
    CapabilityDiscoverer = None

try:
    from .P_01260207201000000983_01999000042260130006_file_inventory_builder import FileInventoryBuilder
except ImportError:
    FileInventoryBuilder = None

try:
    from .P_01260207201000000984_01999000042260130008_purpose_registry_builder import PurposeRegistryBuilder
except ImportError:
    PurposeRegistryBuilder = None

try:
    from .P_01260207201000000980_01999000042260130003_argparse_extractor import ArgparseExtractor, extract_argparse_commands
except ImportError:
    ArgparseExtractor = None
    extract_argparse_commands = None

try:
    from .P_01260207201000000981_01999000042260130004_call_graph_builder import CallGraphBuilder
except ImportError:
    CallGraphBuilder = None

__all__ = [
    "CapabilityDiscoverer",
    "FileInventoryBuilder",
    "PurposeRegistryBuilder",
    "ArgparseExtractor",
    "extract_argparse_commands",
    "CallGraphBuilder",
]
