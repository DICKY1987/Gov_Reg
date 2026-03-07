#!/usr/bin/env python3
# DOC_ID: DOC-SCRIPT-1012
"""
Restructure DOC_ID_REGISTRY.yaml to have documents under 'documents' key
Phase 1 Task T1.3
"""

import sys
import yaml
from pathlib import Path

def restructure_registry():
    registry_path = Path(__file__).parent / "5_REGISTRY_DATA" / "DOC_ID_REGISTRY.yaml"
    backup_path = registry_path.with_suffix('.yaml.backup')

    print(f"📖 Reading registry: {registry_path}")

    # Load current registry
    with open(registry_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    print(f"  Current structure keys: {list(data.keys())}")

    # Check if already has 'documents' key
    if 'documents' in data:
        print("  ✅ Registry already has 'documents' key")
        doc_count = len(data['documents'])
        print(f"  Document count: {doc_count}")
        return 0

    # Find the documents list (it's the unnamed root-level list)
    # The YAML has metadata at top, then a list of doc entries
    documents = []
    metadata = {}
    categories = {}

    # Split metadata and documents
    for key, value in data.items():
        if key == 'doc_id' and isinstance(value, str):
            # This is the first doc entry marker
            continue
        elif isinstance(value, list):
            # This might be the documents list
            documents = value
        elif key in ['metadata', 'categories']:
            locals()[key] = value
        else:
            metadata[key] = value

    # If documents still empty, the structure is different
    # Let's re-read and parse more carefully
    with open(registry_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Find where document entries start (after categories section)
    doc_start_line = 0
    in_categories = False
    for i, line in enumerate(lines):
        if line.strip().startswith('categories:'):
            in_categories = True
        elif in_categories and line.startswith('- doc_id:'):
            doc_start_line = i
            break
        elif in_categories and not line.startswith(' ') and not line.strip().startswith('-'):
            # Exited categories section without finding docs
            if line.startswith('- doc_id:'):
                doc_start_line = i
                break

    if doc_start_line == 0:
        print("  ❌ Could not find document entries start")
        return 1

    print(f"  Found documents starting at line {doc_start_line}")

    # Create backup
    print(f"  Creating backup: {backup_path}")
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    # Write new structure
    print(f"  Writing restructured registry...")
    with open(registry_path, 'w', encoding='utf-8') as f:
        # Write everything before documents
        for line in lines[:doc_start_line]:
            f.write(line)

        # Write documents key
        f.write('documents:\n')

        # Write all document entries (with proper indentation)
        for line in lines[doc_start_line:]:
            if line.startswith('- '):
                f.write('  ' + line)  # Indent list items
            elif line.strip() and not line.startswith(' '):
                # Top-level key after documents - this shouldn't happen
                f.write(line)
            else:
                # Already indented content
                f.write('  ' + line)

    print(f"  ✅ Registry restructured successfully")

    # Validate
    with open(registry_path, 'r', encoding='utf-8') as f:
        new_data = yaml.safe_load(f)

    if 'documents' in new_data:
        doc_count = len(new_data['documents'])
        print(f"  ✅ Validation passed: {doc_count} documents")
        return 0
    else:
        print(f"  ❌ Validation failed: 'documents' key not found")
        return 1

if __name__ == "__main__":
    sys.exit(restructure_registry())
