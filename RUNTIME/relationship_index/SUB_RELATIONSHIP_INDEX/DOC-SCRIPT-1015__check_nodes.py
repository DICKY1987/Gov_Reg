#!/usr/bin/env python3
# DOC_ID: DOC-SCRIPT-1015
"""Check what nodes are being built."""

import sys
from pathlib import Path

.parent))

from core.index_builder import RelationshipIndexBuilder

# Build just the nodes
builder = RelationshipIndexBuilder(run_id="test_nodes")
nodes = builder._build_nodes()

print(f"Total nodes: {len(nodes)}")

# Count by file type
from collections import Counter
file_types = Counter(n['file_type'] for n in nodes)

print("\nFile types in nodes:")
for ft, count in sorted(file_types.items(), key=lambda x: -x[1])[:15]:
    print(f"  {ft}: {count}")

# Check for specific markdown files
md_nodes = [n for n in nodes if n['file_type'] == 'md']
print(f"\nMarkdown nodes: {len(md_nodes)}")

if md_nodes:
    print("\nSample markdown nodes:")
    for n in md_nodes[:5]:
        print(f"  • {n['path']}")
        print(f"    doc_id: {n['doc_id']}")
