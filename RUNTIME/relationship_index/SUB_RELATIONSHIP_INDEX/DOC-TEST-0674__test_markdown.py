#!/usr/bin/env python3
# DOC_ID: DOC-TEST-0674
"""Quick test script to debug markdown analyzer."""

import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from core.index_builder import SimpleDocIDRegistry, RelationshipIndexBuilder
    from analyzers import MarkdownLinkAnalyzer
except ImportError as e:
    import pytest
    pytest.skip(f"Missing dependencies: {e}", allow_module_level=True)

# Initialize
registry = SimpleDocIDRegistry()
from core.confidence_engine import ConfidenceEngine
confidence = ConfidenceEngine()

analyzer = MarkdownLinkAnalyzer(registry, confidence)

# Test file
readme_path = Path(__file__).parent / "README.md"
if readme_path.exists():
    print(f"Testing: {readme_path}")
    print(f"Can analyze: {analyzer.can_analyze(readme_path, 'md')}")

    # Try to find doc_id for README
    doc_id = registry.lookup_by_path("SUB_RELATIONSHIP_INDEX/README.md")
    print(f"README doc_id: {doc_id}")

    if doc_id:
        # Analyze
        edges = analyzer.analyze(readme_path, doc_id)
        print(f"\nFound {len(edges)} edges:")
        for edge in edges[:10]:
            print(f"  {edge.source_doc_id} -> {edge.target_doc_id} ({edge.edge_type})")
            print(f"    Evidence: {edge.evidence['snippet']}")
else:
    print("README.md not found")
