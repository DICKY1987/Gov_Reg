#!/usr/bin/env python3
"""
Deliverable Analyzer - Phase B Script
Produces: py_deliverable_kind, py_interface_signature, py_interface_hash

Determines what the file delivers (library/service/script/test/config) and extracts public interface.
"""
import ast
import hashlib
import json
import sys
from pathlib import Path
from typing import List, Dict, Set, Any, Optional


class InterfaceVisitor(ast.NodeVisitor):
    """Extract public interface from Python AST."""

    def __init__(self):
        self.public_classes = []
        self.public_functions = []
        self.has_main = False
        self.has_cli = False
        self.has_fastapi = False
        self.has_flask = False
        self.has_test_functions = False

    def visit_ClassDef(self, node: ast.ClassDef):
        """Extract public classes."""
        if not node.name.startswith("_"):
            self.public_classes.append(
                {
                    "name": node.name,
                    "bases": [self._get_name(b) for b in node.bases],
                    "methods": self._extract_public_methods(node),
                }
            )
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Extract public functions and detect patterns."""
        # Check for test functions
        if node.name.startswith("test_"):
            self.has_test_functions = True

        # Check for main function
        if node.name == "main":
            self.has_main = True

        # Extract public functions
        if not node.name.startswith("_"):
            self.public_functions.append(
                {
                    "name": node.name,
                    "args": [arg.arg for arg in node.args.args],
                    "returns": self._get_name(node.returns) if node.returns else None,
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                }
            )

        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Handle async functions."""
        self.visit_FunctionDef(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Detect framework imports."""
        if node.module:
            if "fastapi" in node.module:
                self.has_fastapi = True
            elif "flask" in node.module:
                self.has_flask = True
            elif "argparse" in node.module or "click" in node.module:
                self.has_cli = True
        self.generic_visit(node)

    def _extract_public_methods(self, class_node: ast.ClassDef) -> List[str]:
        """Extract public method names from class."""
        methods = []
        for item in class_node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not item.name.startswith("_") or item.name in (
                    "__init__",
                    "__call__",
                ):
                    methods.append(item.name)
        return methods

    def _get_name(self, node: Optional[ast.expr]) -> str:
        """Get name from AST node."""
        if node is None:
            return ""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return ast.unparse(node)
        return ast.unparse(node)


def determine_deliverable_kind(
    file_path: Path, visitor: InterfaceVisitor, source: str
) -> str:
    """
    Determine what kind of deliverable this file is.

    Priority order:
    1. TEST - has test_ functions or is in tests/ directory
    2. CONFIG - is .py config file (settings.py, config.py)
    3. SERVICE - has FastAPI/Flask app or async server patterns
    4. SCRIPT - has main() or if __name__ == '__main__'
    5. LIBRARY - exports public classes/functions
    6. UTILITY - internal helper module
    """
    file_name = file_path.name
    parent_dir = file_path.parent.name

    # TEST
    if visitor.has_test_functions or "test_" in file_name or parent_dir == "tests":
        return "TEST"

    # CONFIG
    if file_name in ("settings.py", "config.py", "configuration.py"):
        return "CONFIG"

    # SERVICE
    if visitor.has_fastapi or visitor.has_flask:
        return "SERVICE"

    # SCRIPT
    if visitor.has_main or "if __name__ ==" in source:
        return "SCRIPT"

    # LIBRARY (has public API)
    if visitor.public_classes or visitor.public_functions:
        return "LIBRARY"

    # UTILITY (internal module)
    return "UTILITY"


def extract_interface_signature(visitor: InterfaceVisitor) -> Dict[str, Any]:
    """
    Extract public interface signature.

    Returns:
    - classes: List of public class names and their methods
    - functions: List of public function signatures
    """
    return {"classes": visitor.public_classes, "functions": visitor.public_functions}


def analyze_deliverable(file_path: Path) -> dict:
    """
    Analyze what a Python file delivers.

    Returns dict with:
    - py_deliverable_kind: str
    - py_interface_signature: Dict
    - py_interface_hash: str
    - success: bool
    - error: Optional[str]
    """
    try:
        source_text = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source_text, filename=str(file_path))

        visitor = InterfaceVisitor()
        visitor.visit(tree)

        # Determine deliverable kind
        deliverable_kind = determine_deliverable_kind(file_path, visitor, source_text)

        # Extract interface signature
        interface_sig = extract_interface_signature(visitor)

        # Compute interface hash
        canonical_json = json.dumps(
            interface_sig, sort_keys=True, separators=(",", ":")
        )
        interface_hash = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

        return {
            "py_deliverable_kind": deliverable_kind,
            "py_interface_signature": interface_sig,
            "py_interface_hash": interface_hash,
            "success": True,
            "error": None,
        }

    except SyntaxError as e:
        return {
            "py_deliverable_kind": "ERROR",
            "py_interface_signature": {},
            "py_interface_hash": None,
            "success": False,
            "error": f"Syntax error: {e}",
        }

    except Exception as e:
        return {
            "py_deliverable_kind": "ERROR",
            "py_interface_signature": {},
            "py_interface_hash": None,
            "success": False,
            "error": f"Deliverable analysis failed: {e}",
        }


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: deliverable_analyzer.py <file_path>", file=sys.stderr)
        sys.exit(1)

    file_path = Path(sys.argv[1])

    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    result = analyze_deliverable(file_path)

    if result["success"]:
        print(f"Deliverable kind: {result['py_deliverable_kind']}")
        print(f"Interface hash: {result['py_interface_hash']}")
        print(
            f"\nInterface signature: {json.dumps(result['py_interface_signature'], indent=2)}"
        )
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
