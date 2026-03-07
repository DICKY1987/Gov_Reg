#!/usr/bin/env python3
# DOC_LINK: DOC-ERROR-PATH-STANDARDIZER-PLUGIN-130
"""Path standardizer plugin using CCPM path tools"""

import subprocess
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
import re

def validate_paths(file_paths: List[str], project_root: str, autofix: bool = False) -> Dict[str, Any]:
    """Validate and optionally fix path standards"""
# DOC_ID: DOC-ERROR-PATH-STANDARDIZER-PLUGIN-130

    check_script = Path(project_root) / "scripts" / "check-path-standards.sh"
    fix_script = Path(project_root) / "scripts" / "fix-path-standards.sh"

    if not check_script.exists():
        return {"tool": "path_standardizer", "errors": []}

    errors = []

    for file_path in file_paths:
        # Check path standards
        result = subprocess.run(
            ["bash", str(check_script), file_path],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            # Path violations found
            violations = parse_violations(result.stdout, default_file=file_path)

            if autofix and fix_script.exists():
                # Apply fixes
                fix_result = subprocess.run(
                    ["bash", str(fix_script), file_path],
                    capture_output=True,
                    text=True
                )

                if fix_result.returncode == 0:
                    continue  # Fixed successfully

            # Add violations to errors
            # Attach normalized file path if missing
            norm = normalize_path(file_path)
            for v in violations:
                v.setdefault("file", norm)
            errors.extend(violations)

    return {
        "tool": "path_standardizer",
        "errors": errors
    }

def normalize_path(p: str) -> str:
    """Normalize Windows/Unix paths to a repo-relative forward-slash form."""
    # Strip optional drive letter (e.g., C or C:) and leading slashes
    p2 = re.sub(r"^[A-Za-z]:?[/\\]+", "", p)
    # Normalize separators
    p2 = p2.replace("\\", "/")
    p2 = re.sub(r"/+", "/", p2)
    p2 = p2.lstrip("./")
    return p2


def parse_violations(output: str, default_file: str | None = None) -> List[Dict[str, Any]]:
    """Parse path violation messages and attempt to extract file/line.

    Falls back to returning the whole line as message.
    """
    errors: List[Dict[str, Any]] = []
    file_hint = normalize_path(default_file) if default_file else ""
    for raw in output.split('\n'):
        line = raw.strip()
        if not line:
            continue
        # Try patterns like: "<file>:<line>: <message>" (handle Windows drive like C:)
        m = re.match(r"(?P<file>(?:[A-Za-z]:)?[^:]+):(?P<line>\d+):\s*(?P<msg>.*)", line)
        if m:
            errors.append({
                "category": "path_standard",
                "severity": "warning",
                "message": m.group("msg").strip(),
                "file": normalize_path(m.group("file")),
                "line": int(m.group("line")),
            })
            continue
        m2 = re.match(r"(?P<file>[^\s]+)\s+-\s+(?P<msg>.*)", line)
        if m2:
            errors.append({
                "category": "path_standard",
                "severity": "warning",
                "message": m2.group("msg").strip(),
                "file": normalize_path(m2.group("file")),
                "line": 0,
            })
            continue
        # Default
        errors.append({
            "category": "path_standard",
            "severity": "warning",
            "message": line,
            "file": file_hint,
            "line": 0,
        })
    return errors

if __name__ == "__main__":
    file_paths = sys.argv[1:-1] if len(sys.argv) > 2 else []
    autofix = sys.argv[-1] == "--fix" if len(sys.argv) > 1 else False

    result = validate_paths(file_paths, str(Path.cwd()), autofix)
    print(json.dumps(result, indent=2))
