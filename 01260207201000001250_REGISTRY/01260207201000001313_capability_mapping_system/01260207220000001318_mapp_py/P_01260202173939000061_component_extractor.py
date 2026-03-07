#!/usr/bin/env python3
"""
Component Extractor - Phase A Core Script
Produces: py_defs_classes_count, py_defs_functions_count, py_component_count,
          py_components_list, py_defs_public_api_hash

Extracts Python components (classes, functions, methods) from AST.
"""
import ast
import hashlib
import json
import sys
from pathlib import Path
from typing import List, Dict, Any


class ComponentVisitor(ast.NodeVisitor):
    """Extract components from Python AST."""

    def __init__(self, source_text: str):
        self.source_text = source_text
        self.source_lines = source_text.splitlines()
        self.classes = []
        self.functions = []
        self.methods = []
        self.current_class = None

    def visit_ClassDef(self, node: ast.ClassDef):
        """Extract class definition."""
        class_info = {
            "kind": "class",
            "name": node.name,
            "qualname": self._get_qualname(node.name),
            "lineno": node.lineno,
            "col_offset": node.col_offset,
            "end_lineno": node.end_lineno,
            "end_col_offset": node.end_col_offset,
            "decorators": [self._get_decorator_name(d) for d in node.decorator_list],
            "bases": [self._get_base_name(b) for b in node.bases],
            "docstring": ast.get_docstring(node),
            "methods": [],
        }

        self.classes.append(class_info)

        # Visit methods inside this class
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Extract function/method definition."""
        if self.current_class:
            # This is a method
            method_info = {
                "kind": "method",
                "name": node.name,
                "qualname": f"{self.current_class}.{node.name}",
                "class_name": self.current_class,
                "lineno": node.lineno,
                "col_offset": node.col_offset,
                "end_lineno": node.end_lineno,
                "end_col_offset": node.end_col_offset,
                "decorators": [
                    self._get_decorator_name(d) for d in node.decorator_list
                ],
                "args": self._get_args(node.args),
                "returns": self._get_annotation(node.returns),
                "docstring": ast.get_docstring(node),
                "is_async": isinstance(node, ast.AsyncFunctionDef),
            }
            self.methods.append(method_info)
        else:
            # This is a module-level function
            func_info = {
                "kind": "function",
                "name": node.name,
                "qualname": node.name,
                "lineno": node.lineno,
                "col_offset": node.col_offset,
                "end_lineno": node.end_lineno,
                "end_col_offset": node.end_col_offset,
                "decorators": [
                    self._get_decorator_name(d) for d in node.decorator_list
                ],
                "args": self._get_args(node.args),
                "returns": self._get_annotation(node.returns),
                "docstring": ast.get_docstring(node),
                "is_async": isinstance(node, ast.AsyncFunctionDef),
            }
            self.functions.append(func_info)

        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Handle async functions same as regular functions."""
        self.visit_FunctionDef(node)

    def _get_qualname(self, name: str) -> str:
        """Get qualified name for component."""
        if self.current_class:
            return f"{self.current_class}.{name}"
        return name

    def _get_decorator_name(self, node: ast.expr) -> str:
        """Extract decorator name."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return ast.unparse(node)
        elif isinstance(node, ast.Call):
            return self._get_decorator_name(node.func)
        return ast.unparse(node)

    def _get_base_name(self, node: ast.expr) -> str:
        """Extract base class name."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return ast.unparse(node)
        return ast.unparse(node)

    def _get_args(self, args: ast.arguments) -> List[Dict[str, Any]]:
        """Extract function arguments."""
        result = []

        # Regular args
        for arg in args.args:
            result.append(
                {
                    "name": arg.arg,
                    "annotation": self._get_annotation(arg.annotation),
                    "kind": "positional",
                }
            )

        # *args
        if args.vararg:
            result.append(
                {
                    "name": args.vararg.arg,
                    "annotation": self._get_annotation(args.vararg.annotation),
                    "kind": "vararg",
                }
            )

        # **kwargs
        if args.kwarg:
            result.append(
                {
                    "name": args.kwarg.arg,
                    "annotation": self._get_annotation(args.kwarg.annotation),
                    "kind": "kwarg",
                }
            )

        return result

    def _get_annotation(self, node: ast.expr) -> str:
        """Extract type annotation."""
        if node is None:
            return None
        return ast.unparse(node)


def extract_components(file_path: Path) -> dict:
    """
    Extract all components from a Python file.

    Returns dict with:
    - py_defs_classes_count: int
    - py_defs_functions_count: int
    - py_component_count: int (total: classes + functions + methods)
    - py_components_list: List[Dict]
    - py_defs_public_api_hash: str
    - success: bool
    - error: Optional[str]
    """
    try:
        source_text = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source_text, filename=str(file_path))

        visitor = ComponentVisitor(source_text)
        visitor.visit(tree)

        # Combine all components
        all_components = visitor.classes + visitor.functions + visitor.methods

        # Sort by line number for deterministic ordering
        all_components.sort(key=lambda c: (c["lineno"], c["col_offset"]))

        # Compute canonical hash
        canonical_json = json.dumps(
            all_components, sort_keys=True, separators=(",", ":")
        )
        components_hash = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
        
        component_count = len(visitor.classes) + len(visitor.functions) + len(visitor.methods)

        return {
            "py_defs_classes_count": len(visitor.classes),
            "py_defs_functions_count": len(visitor.functions),
            "py_component_count": component_count,
            "py_components_list": all_components,
            "py_defs_public_api_hash": components_hash,
            "success": True,
            "error": None,
        }

    except SyntaxError as e:
        return {
            "py_defs_classes_count": 0,
            "py_defs_functions_count": 0,
            "py_component_count": 0,
            "py_components_list": [],
            "py_defs_public_api_hash": None,
            "success": False,
            "error": f"Syntax error: {e}",
        }

    except Exception as e:
        return {
            "py_defs_classes_count": 0,
            "py_defs_functions_count": 0,
            "py_component_count": 0,
            "py_components_list": [],
            "py_defs_public_api_hash": None,
            "success": False,
            "error": f"Component extraction failed: {e}",
        }


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: component_extractor.py <file_path>", file=sys.stderr)
        sys.exit(1)

    file_path = Path(sys.argv[1])

    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    result = extract_components(file_path)

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
        print(f"Classes: {result['py_defs_classes_count']}")
        print(f"Functions: {result['py_defs_functions_count']}")
        print(f"Component Count: {result['py_component_count']}")
        print(f"Components Hash: {result['py_defs_public_api_hash']}")
        print(f"\nComponents: {json.dumps(result['py_components_list'], indent=2)}")
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
