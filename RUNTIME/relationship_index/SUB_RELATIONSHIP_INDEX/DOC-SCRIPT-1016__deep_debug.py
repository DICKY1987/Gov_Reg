#!/usr/bin/env python3
# DOC_ID: DOC-SCRIPT-1016
"""Deep debug - manually test markdown analyzer on several files."""

import sys
from pathlib import Path

.parent))

from core.index_builder import SimpleDocIDRegistry
from analyzers import MarkdownLinkAnalyzer
from core.confidence_engine import ConfidenceEngine

# Initialize
registry = SimpleDocIDRegistry()
confidence = ConfidenceEngine()
analyzer = MarkdownLinkAnalyzer(registry, confidence)

# Test on specific markdown files
test_files = [
    "SUB_RELATIONSHIP_INDEX/README.md",
    "SUB_RELATIONSHIP_INDEX/PHASE_1_STATUS.md",
    "SUB_DOC_ID/README.md",
    "README.md",
    "DOCSYS/README.md"
]

print("=== Testing Markdown Analyzer on Sample Files ===\n")

repo_root = Path(__file__).parent.parent
total_edges = 0

for rel_path in test_files:
    file_path = repo_root / rel_path

    if not file_path.exists():
        print(f"❌ {rel_path}: File not found")
        continue

    # Get doc_id
    doc_id = registry.lookup_by_path(rel_path)
    if not doc_id:
        print(f"⚠️  {rel_path}: No doc_id in registry")
        continue

    print(f"📄 {rel_path}")
    print(f"   Doc ID: {doc_id}")

    # Analyze
    try:
        edges = analyzer.analyze(file_path, doc_id)
        print(f"   Edges found: {len(edges)}")
        total_edges += len(edges)

        for edge in edges[:3]:  # Show first 3
            print(f"     → {edge.target_doc_id}")
            print(f"       {edge.evidence['snippet'][:60]}...")

        if len(edges) > 3:
            print(f"     ... and {len(edges) - 3} more")

    except Exception as e:
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()

    print()

print(f"Total edges found: {total_edges}")
