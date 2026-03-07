#!/usr/bin/env python3
"""
DOC_ID: DOC-CORE-2-VALIDATION-FIXING-VALIDATE-DOC-ID-1162
Reference Validator
Validates that all doc_id references point to registered IDs
"""

import argparse
import json
import re
import sys
from pathlib import Path
from datetime import datetime
import yaml

def main(output: str = None):
    """Validate doc_id references"""
    base = Path(__file__).parent.parent
    repo_root = base.parent.parent.parent
    registry_path = base / "5_REGISTRY_DATA" / "DOC_ID_REGISTRY.yaml"

    # Load registry
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = yaml.safe_load(f)

    registered_ids = {d.get('doc_id') for d in registry.get('documents', []) if d.get('doc_id')}

    # Scan for references
    doc_link_pattern = re.compile(r'DOC_LINK:\s*(DOC-[A-Z0-9-]+)')
    found_refs = set()
    invalid_refs = []

    # Scan key directories
    scan_dirs = [
        repo_root / "RUNTIME",
        repo_root / "scripts",
        repo_root / "automation",
    ]

    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue
        for file_path in scan_dir.rglob("*.py"):
            try:
                content = file_path.read_text(encoding='utf-8')
                for match in doc_link_pattern.finditer(content):
                    ref_id = match.group(1)
                    found_refs.add(ref_id)
                    if ref_id not in registered_ids:
                        invalid_refs.append({
                            'doc_id': ref_id,
                            'file': str(file_path.relative_to(repo_root))
                        })
            except Exception:
                pass

    passed = len(invalid_refs) == 0

    results = {
        "task_id": "AUTO-008",
        "timestamp": datetime.now().isoformat(),
        "status": "PASSED" if passed else "FAILED",
        "total_references": len(found_refs),
        "invalid_count": len(invalid_refs)
    }

    # Output results
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

    # Console output
    print(f"\n=== DOC_ID Reference Validation ===")
    print(f"Total references found: {len(found_refs)}")
    print(f"Invalid references: {len(invalid_refs)}")

    if passed:
        print("\n✅ PASSED: All references are valid")
        return 0
    else:
        print("\n❌ FAILED: Invalid references detected")
        for ref in invalid_refs[:10]:
            print(f"   {ref['doc_id']} in {ref['file']}")
        if len(invalid_refs) > 10:
            print(f"   ... and {len(invalid_refs) - 10} more")
        return 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reference Validator")
    parser.add_argument("--output", help="Output JSON file path (optional)")
    args = parser.parse_args()
    sys.exit(main(args.output))
    parser.add_argument("--output", required=True, help="Output JSON file path")
    args = parser.parse_args()
    sys.exit(main(args.output))