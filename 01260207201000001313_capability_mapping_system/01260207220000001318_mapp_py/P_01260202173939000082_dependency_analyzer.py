#!/usr/bin/env python3
"""
Dependency Analyzer for mapp_py Analysis Pipeline
Produces: py_imports_list, py_imports_hash, py_stdlib_dependencies,
         py_external_dependencies

Analyzes import statements and categorizes dependencies.
Requires Python 3.10+ for sys.stdlib_module_names.
"""

import ast
import hashlib
import json
import sys
from typing import List, Set, Dict, Any, Optional


# Python 3.10+ check
if sys.version_info < (3, 10):
    raise RuntimeError(
        "dependency_analyzer requires Python 3.10+ for sys.stdlib_module_names. "
        f"Current version: {sys.version_info.major}.{sys.version_info.minor}"
    )


class ImportAnalyzer(ast.NodeVisitor):
    """Analyze imports from Python AST."""

    def __init__(self):
        self.imports: List[Dict[str, Any]] = []
        self.all_modules: Set[str] = set()

    def visit_Import(self, node: ast.Import):
        """Handle 'import x' statements."""
        for alias in node.names:
            module = alias.name
            asname = alias.asname

            self.imports.append(
                {
                    "type": "import",
                    "module": module,
                    "name": None,
                    "asname": asname,
                    "level": 0,
                }
            )

            # Track top-level module
            top_module = module.split(".")[0]
            self.all_modules.add(top_module)

        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Handle 'from x import y' statements."""
        module = node.module or ""
        level = node.level

        for alias in node.names:
            name = alias.name
            asname = alias.asname

            self.imports.append(
                {
                    "type": "from",
                    "module": module,
                    "name": name,
                    "asname": asname,
                    "level": level,
                }
            )

        # Track top-level module (only for absolute imports)
        if level == 0 and module:
            top_module = module.split(".")[0]
            self.all_modules.add(top_module)

        self.generic_visit(node)


def categorize_dependencies(modules: Set[str]) -> Dict[str, List[str]]:
    """
    Categorize modules into stdlib vs external.

    Args:
        modules: Set of top-level module names

    Returns:
        Dictionary with 'stdlib' and 'external' lists
    """
    stdlib = set(sys.stdlib_module_names)

    stdlib_deps = sorted([m for m in modules if m in stdlib])
    external_deps = sorted([m for m in modules if m not in stdlib])

    return {"stdlib": stdlib_deps, "external": external_deps}


def analyze_dependencies(tree: ast.AST) -> Dict[str, Any]:
    """
    Analyze imports and dependencies from AST.

    Args:
        tree: AST tree

    Returns:
        Dictionary with dependency analysis results
    """
    analyzer = ImportAnalyzer()
    analyzer.visit(tree)

    # Categorize dependencies
    categorized = categorize_dependencies(analyzer.all_modules)

    # Canonical imports list (sorted for determinism)
    imports_sorted = sorted(
        analyzer.imports, key=lambda x: (x["module"] or "", x["name"] or "", x["type"])
    )

    # Compute imports hash
    imports_json = json.dumps(imports_sorted, sort_keys=True, separators=(",", ":"))
    imports_hash = hashlib.sha256(imports_json.encode("utf-8")).hexdigest()

    return {
        "py_imports_list": imports_sorted,
        "py_imports_hash": imports_hash,
        "py_stdlib_dependencies": categorized["stdlib"],
        "py_external_dependencies": categorized["external"],
    }


def analyze_file(file_path: str, ast_tree: Optional[ast.AST] = None) -> dict:
    """
    Analyze file dependencies.

    Args:
        file_path: Path to Python file
        ast_tree: Optional pre-parsed AST tree

    Returns:
        Dictionary with dependency analysis results
    """
    if ast_tree is None:
        # Parse AST if not provided
        from pathlib import Path

        try:
            source = Path(file_path).read_text(encoding="utf-8")
            ast_tree = ast.parse(source)
        except Exception as e:
            return {
                "py_imports_list": None,
                "py_imports_hash": None,
                "py_stdlib_dependencies": None,
                "py_external_dependencies": None,
                "error": f"{type(e).__name__}: {str(e)}",
            }

    return analyze_dependencies(ast_tree)


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Analyze Python file dependencies")
    parser.add_argument("file_path", help="Path to Python file")
    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed import information"
    )

    args = parser.parse_args()

    result = analyze_file(args.file_path)

    if "error" in result:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        sys.exit(1)

    print(f"Stdlib dependencies: {result['py_stdlib_dependencies']}")
    print(f"External dependencies: {result['py_external_dependencies']}")
    print(f"Imports hash: {result['py_imports_hash']}")

    if args.verbose:
        print("\nAll imports:")
        for imp in result["py_imports_list"]:
            if imp["type"] == "import":
                print(
                    f"  import {imp['module']}"
                    + (f" as {imp['asname']}" if imp["asname"] else "")
                )
            else:
                level_prefix = "." * imp["level"]
                print(
                    f"  from {level_prefix}{imp['module']} import {imp['name']}"
                    + (f" as {imp['asname']}" if imp["asname"] else "")
                )

    sys.exit(0)


if __name__ == "__main__":
    main()
