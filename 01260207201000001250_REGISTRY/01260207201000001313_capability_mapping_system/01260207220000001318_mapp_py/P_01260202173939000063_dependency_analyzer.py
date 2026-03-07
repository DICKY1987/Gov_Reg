#!/usr/bin/env python3
"""
Dependency Analyzer - Phase A Core Script
Produces: py_imports_list, py_imports_hash, py_stdlib_imports_count, py_external_imports_count

Analyzes Python imports and classifies them as stdlib vs external.
Requires Python 3.10+ for sys.stdlib_module_names.
"""
import ast
import hashlib
import json
import sys
from pathlib import Path
from typing import List, Dict, Set, Any


# Fallback for Python < 3.10
if sys.version_info >= (3, 10):
    STDLIB_MODULES = sys.stdlib_module_names
else:
    # Minimal fallback set for Python 3.9
    STDLIB_MODULES = {
        "abc",
        "argparse",
        "ast",
        "asyncio",
        "base64",
        "collections",
        "contextlib",
        "copy",
        "csv",
        "datetime",
        "decimal",
        "enum",
        "functools",
        "hashlib",
        "io",
        "itertools",
        "json",
        "logging",
        "math",
        "os",
        "pathlib",
        "pickle",
        "re",
        "shutil",
        "socket",
        "sqlite3",
        "string",
        "subprocess",
        "sys",
        "tempfile",
        "threading",
        "time",
        "typing",
        "unittest",
        "urllib",
        "uuid",
        "warnings",
        "weakref",
    }


class ImportVisitor(ast.NodeVisitor):
    """Extract imports from Python AST."""

    def __init__(self):
        self.imports = []

    def visit_Import(self, node: ast.Import):
        """Handle 'import module' statements."""
        for alias in node.names:
            self.imports.append(
                {
                    "type": "import",
                    "module": alias.name,
                    "name": alias.asname or alias.name,
                    "lineno": node.lineno,
                    "col_offset": node.col_offset,
                }
            )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Handle 'from module import name' statements."""
        module = node.module or ""
        level = node.level  # Relative import level (0 = absolute)

        for alias in node.names:
            self.imports.append(
                {
                    "type": "from",
                    "module": module,
                    "name": alias.name,
                    "asname": alias.asname,
                    "level": level,
                    "lineno": node.lineno,
                    "col_offset": node.col_offset,
                }
            )
        self.generic_visit(node)


def get_top_level_module(module_name: str) -> str:
    """Extract top-level module name from dotted path."""
    if not module_name:
        return ""
    return module_name.split(".")[0]


def is_stdlib_module(module_name: str) -> bool:
    """Check if module is in Python standard library."""
    if not module_name:
        return False

    top_level = get_top_level_module(module_name)
    return top_level in STDLIB_MODULES


def classify_imports(imports: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Classify imports as stdlib, external, or relative.

    Returns:
    - stdlib: List of stdlib imports
    - external: List of external/third-party imports
    - relative: List of relative imports
    """
    stdlib = []
    external = []
    relative = []

    for imp in imports:
        module = imp["module"]

        # Relative imports
        if imp.get("level", 0) > 0:
            relative.append(imp)
        # Stdlib imports
        elif is_stdlib_module(module):
            stdlib.append(imp)
        # External imports
        else:
            external.append(imp)

    return {"stdlib": stdlib, "external": external, "relative": relative}


def analyze_dependencies(file_path: Path) -> dict:
    """
    Analyze dependencies in a Python file.

    Returns dict with:
    - py_imports_list: List[Dict] (all imports)
    - py_imports_hash: str
    - py_stdlib_imports_count: int
    - py_external_imports_count: int
    - classification: Dict (stdlib/external/relative lists)
    - success: bool
    - error: Optional[str]
    """
    try:
        source_text = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source_text, filename=str(file_path))

        visitor = ImportVisitor()
        visitor.visit(tree)

        # Sort imports by line number for deterministic ordering
        imports = sorted(visitor.imports, key=lambda i: (i["lineno"], i["col_offset"]))

        # Classify imports
        classification = classify_imports(imports)

        # Compute canonical hash of imports
        canonical_json = json.dumps(imports, sort_keys=True, separators=(",", ":"))
        imports_hash = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

        return {
            "py_imports_list": imports,
            "py_imports_hash": imports_hash,
            "py_stdlib_imports_count": len(classification["stdlib"]),
            "py_external_imports_count": len(classification["external"]),
            "py_relative_imports_count": len(classification["relative"]),
            "classification": classification,
            "success": True,
            "error": None,
        }

    except SyntaxError as e:
        return {
            "py_imports_list": [],
            "py_imports_hash": None,
            "py_stdlib_imports_count": 0,
            "py_external_imports_count": 0,
            "py_relative_imports_count": 0,
            "classification": {"stdlib": [], "external": [], "relative": []},
            "success": False,
            "error": f"Syntax error: {e}",
        }

    except Exception as e:
        return {
            "py_imports_list": [],
            "py_imports_hash": None,
            "py_stdlib_imports_count": 0,
            "py_external_imports_count": 0,
            "py_relative_imports_count": 0,
            "classification": {"stdlib": [], "external": [], "relative": []},
            "success": False,
            "error": f"Dependency analysis failed: {e}",
        }


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: dependency_analyzer.py <file_path>", file=sys.stderr)
        sys.exit(1)

    file_path = Path(sys.argv[1])

    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    result = analyze_dependencies(file_path)

    # Handle --json flag
    if '--json' in sys.argv:
        idx = sys.argv.index('--json')
        out_path = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
        if out_path:
            with open(out_path, 'w') as f:
                json.dump(result, f, indent=2, sort_keys=True)
        else:
            print(json.dumps(result, indent=2, sort_keys=True))
        sys.exit(0)

    if result["success"]:
        print(f"Total imports: {len(result['py_imports_list'])}")
        print(f"Stdlib: {result['py_stdlib_imports_count']}")
        print(f"External: {result['py_external_imports_count']}")
        print(f"Relative: {result['py_relative_imports_count']}")
        print(f"Imports Hash: {result['py_imports_hash']}")
        print(f"\nClassification: {json.dumps(result['classification'], indent=2)}")
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
