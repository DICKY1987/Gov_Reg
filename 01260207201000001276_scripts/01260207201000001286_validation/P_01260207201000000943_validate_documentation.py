#!/usr/bin/env python3
"""Validate documentation completeness."""

import sys
from pathlib import Path


CRITICAL_DOCS = [
    'README.md',
    'docs/api_reference.md',
    'schemas'
]


def validate_documentation():
    """Validate documentation is complete."""
    missing = []
    
    for doc_path in CRITICAL_DOCS:
        path = Path(doc_path)
        if not path.exists():
            missing.append(doc_path)
    
    if missing:
        print("✗ Documentation validation FAILED")
        print(f"Missing {len(missing)} critical document(s):")
        for doc in missing:
            print(f"  - {doc}")
        return 1
    else:
        print("✓ Documentation validation PASSED")
        print(f"All {len(CRITICAL_DOCS)} critical documents present")
        return 0


if __name__ == '__main__':
    sys.exit(validate_documentation())
