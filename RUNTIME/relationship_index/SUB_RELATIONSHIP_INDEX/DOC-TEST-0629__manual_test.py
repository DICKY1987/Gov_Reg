#!/usr/bin/env python3
# DOC_ID: DOC-TEST-0629
"""Manually step through processing SUB_DOC_ID/README.md."""

import sys
from pathlib import Path

.parent))

from core.index_builder import RelationshipIndexBuilder

# Build builder
builder = RelationshipIndexBuilder(run_id="manual_test")
nodes = builder._build_nodes()

# Find the SUB_DOC_ID/README.md node
target_path = "SUB_DOC_ID/README.md"
target_node = None
for node in nodes:
    if node['path'] == target_path:
        target_node = node
        break

if not target_node:
    print(f"❌ Node not found for {target_path}")
    print(f"\nSearching for similar paths...")
    similar = [n for n in nodes if 'SUB_DOC_ID' in n['path'] and 'README' in n['path']]
    for n in similar[:5]:
        print(f"  • {n['path']}")
    sys.exit(1)

print(f"✅ Found node: {target_node}")
print(f"\n   Path: {target_node['path']}")
print(f"   Doc ID: {target_node['doc_id']}")
print(f"   File type: {target_node['file_type']}")

# Now manually test if the analyzer can analyze it
from analyzers import MarkdownLinkAnalyzer
from core.confidence_engine import ConfidenceEngine

analyzer = MarkdownLinkAnalyzer(builder.registry, ConfidenceEngine())

repo_root = Path(__file__).parent.parent
file_path = repo_root / target_node['path']

print(f"\n   File exists: {file_path.exists()}")
print(f"   Can analyze: {analyzer.can_analyze(file_path, target_node['file_type'])}")

# Manually analyze
if file_path.exists() and analyzer.can_analyze(file_path, target_node['file_type']):
    edges = analyzer.analyze(file_path, target_node['doc_id'])
    print(f"\n   ✅ Analyzer found {len(edges)} edges!")
    for e in edges[:3]:
        print(f"      → {e.target_doc_id}")
else:
    print("\n   ❌ Cannot analyze file")
