# DOC_LINK: DOC-CORE-CORE-INIT-536
"""
Core Module

Core primitives for relationship index generation.

Exports:
- edge_id_generator: Generate stable relationship edge IDs
- confidence_engine: Rule-based confidence scoring
- index_builder: Main orchestrator for building the relationship index
"""
# DOC_ID: DOC-CORE-CORE-INIT-536

from .edge_id_generator import generate_edge_id, validate_edge_id_format, parse_edge_id
from .confidence_engine import ConfidenceEngine
from .index_builder import RelationshipIndexBuilder, SimpleDocIDRegistry

__all__ = [
    "generate_edge_id",
    "validate_edge_id_format",
    "parse_edge_id",
    "ConfidenceEngine",
    "RelationshipIndexBuilder",
    "SimpleDocIDRegistry",
]
