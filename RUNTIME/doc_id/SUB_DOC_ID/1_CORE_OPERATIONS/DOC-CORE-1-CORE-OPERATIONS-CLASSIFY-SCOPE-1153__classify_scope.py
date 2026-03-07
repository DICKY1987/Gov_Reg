#!/usr/bin/env python3
"""
AUTO-002: Doc-ID Scope Classifier
Determines if file requires doc_id based on path/type
"""
DOC_ID: DOC-CORE-1-CORE-OPERATIONS-CLASSIFY-SCOPE-1153

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# Files/directories that REQUIRE doc_id
REQUIRES_DOC_ID = [
    "*.md",
    "*.json",
    "*.yaml",
    "*.yml"
]

# Excluded patterns (no doc_id needed)
EXCLUDE_PATTERNS = [
    ".git/*",
    "node_modules/*",
    "venv/*",
    "*.pyc",
    "__pycache__/*",
    ".pytest_cache/*",
    "logs/*",
    "run/*",
    "out/*"
]

def classify_scope(filepath: str, output: str):
    """Classify if file requires doc_id."""
    results = {
        "task_id": "AUTO-002",
        "timestamp": datetime.utcnow().isoformat(),
        "filepath": filepath,
        "requires_doc_id": False,
        "reason": "",
        "file_type": ""
    }

    try:
        path = Path(filepath)

        # Check exclusions first
        for pattern in EXCLUDE_PATTERNS:
            if path.match(pattern):
                results["requires_doc_id"] = False
                results["reason"] = f"Excluded by pattern: {pattern}"
                results["file_type"] = "excluded"
                break
        else:
            # Check inclusions
            for pattern in REQUIRES_DOC_ID:
                if path.match(pattern):
                    results["requires_doc_id"] = True
                    results["reason"] = f"Matches pattern: {pattern}"
                    results["file_type"] = path.suffix
                    break
            else:
                results["requires_doc_id"] = False
                results["reason"] = "Does not match any doc_id pattern"
                results["file_type"] = path.suffix or "no_extension"

    except Exception as e:
        results["error"] = str(e)

    # Write output
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Classify doc_id scope")
    parser.add_argument("--filepath", required=True, help="File path to classify")
    parser.add_argument("--output", required=True, help="Output JSON file path")

    args = parser.parse_args()
    sys.exit(classify_scope(args.filepath, args.output))
