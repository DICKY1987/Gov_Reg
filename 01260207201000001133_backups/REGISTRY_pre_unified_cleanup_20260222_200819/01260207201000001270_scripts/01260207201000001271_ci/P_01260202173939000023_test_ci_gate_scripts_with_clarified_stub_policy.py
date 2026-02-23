#!/usr/bin/env python3
"""TASK-014 & TASK-018: CI Gate Scripts with clarified stub policy"""
import sys, json
from pathlib import Path

# TASK-018: Allowed patterns (not considered stubs)
ALLOWED_PATTERNS = [
    "return self._canonical.",
    "if error_policy ==",
    "# Passthrough",
]


def is_allowed_stub(line: str, context: list) -> bool:
    if any(p in line for p in ALLOWED_PATTERNS):
        return True
    for ctx_line in context:
        if any(p in ctx_line for p in ALLOWED_PATTERNS):
            return True
    return False


def check_no_stubs():
    src_dir = Path("src")
    if not src_dir.exists():
        print("✓ No src/ directory")
        return 0

    violations = []
    for py_file in src_dir.rglob("*.py"):
        lines = py_file.read_text().splitlines()
        for i, line in enumerate(lines):
            if "raise NotImplementedError" in line:
                start, end = max(0, i - 5), min(len(lines), i + 6)
                context = lines[start:end]
                if not is_allowed_stub(line, context):
                    violations.append(f"{py_file}:{i+1}")

    if violations:
        print(f"✗ Found {len(violations)} stub violations")
        for v in violations[:5]:
            print(f"  {v}")
        return 1
    print("✓ No disallowed stubs")
    return 0


def validate_evidence():
    evidence_dir = Path(".state/evidence")
    if not evidence_dir.exists():
        return 0
    violations = []
    for f in evidence_dir.rglob("*.json"):
        try:
            json.loads(f.read_text())
        except:
            violations.append(str(f))
    if violations:
        print(f"✗ Invalid JSON: {len(violations)} files")
        return 1
    print("✓ Evidence valid")
    return 0


if __name__ == "__main__":
    sys.exit(
        check_no_stubs()
        if len(sys.argv) < 2 or sys.argv[1] == "stubs"
        else validate_evidence()
    )
