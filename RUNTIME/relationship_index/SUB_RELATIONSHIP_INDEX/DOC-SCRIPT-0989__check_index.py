#!/usr/bin/env python3
# DOC_ID: DOC-SCRIPT-0989
"""Check if markdown edges made it to the index."""

import json
from pathlib import Path

index_path = Path("data/RELATIONSHIP_INDEX.json")
idx = json.load(open(index_path))

edges = idx['edges']
print(f"Total edges in index: {len(edges)}")
print(f"\nEdge types: {set(e['type'] for e in edges)}")
print(f"\nAnalyzers:")
for analyzer_id in set(e['analyzer_id'] for e in edges):
    count = len([e for e in edges if e['analyzer_id'] == analyzer_id])
    print(f"  • {analyzer_id}: {count}")

# Check specifically for markdown
md_edges = [e for e in edges if e.get('analyzer_id') == 'markdown_link_analyzer']
print(f"\nMarkdown edges in final index: {len(md_edges)}")

if md_edges:
    print("\nSample markdown edges:")
    for e in md_edges[:5]:
        print(f"  {e['source']} → {e['target']}")
