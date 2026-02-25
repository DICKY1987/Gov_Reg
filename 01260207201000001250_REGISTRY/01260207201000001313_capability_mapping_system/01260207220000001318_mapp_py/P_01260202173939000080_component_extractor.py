#!/usr/bin/env python3
"""
Component Extractor for mapp_py Analysis Pipeline
Produces: py_components_json, py_top_level_names, py_exports_list,
         py_classes_count, py_functions_count

Extracts Python components (classes, functions, methods) with signatures.
"""

import ast
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Set


class ComponentExtractor(ast.NodeVisitor):
    """Extract components from Python AST."""

    def __init__(self):
        self.components: List[Dict[str, Any]] = []
        self.top_level_names: Set[str] = set()
        self.exports: Set[str] = set()
        self.classes_count = 0
        self.functions_count = 0
        self.current_class: Optional[str] = None
        self.scope_stack: List[str] = []

    def visit_ClassDef(self, node: ast.ClassDef):
        """Extract class definition."""
        qualname = ".".join(self.scope_stack + [node.name])

        # Extract base classes
        bases = [self._get_name(base) for base in node.bases]

        # Extract decorators
        decorators = [self._get_name(dec) for dec in node.decorator_list]

        component = {
            "kind": "class",
            "name": node.name,
            "qualname": qualname,
            "bases": bases,
            "decorators": decorators,
            "methods": [],
            "line_start": node.lineno,
            "line_end": node.end_lineno,
        }

        self.components.append(component)
        self.classes_count += 1

        # Track top-level names
        if not self.scope_stack:
            self.top_level_names.add(node.name)

        # Visit methods
        old_class = self.current_class
        self.current_class = qualname
        self.scope_stack.append(node.name)

        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                self.visit_FunctionDef(item, is_method=True)

        self.scope_stack.pop()
        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef, is_method: bool = False):
        """Extract function/method definition."""
        qualname = ".".join(self.scope_stack + [node.name])

        # Extract signature
        args = self._extract_args(node.args)
        returns = self._get_annotation(node.returns)

        # Extract decorators
        decorators = [self._get_name(dec) for dec in node.decorator_list]

        component = {
            "kind": "method" if is_method else "function",
            "name": node.name,
            "qualname": qualname,
            "signature": {"args": args, "returns": returns},
            "decorators": decorators,
            "line_start": node.lineno,
            "line_end": node.end_lineno,
        }

        if is_method:
            # Add to current class methods
            for comp in reversed(self.components):
                if comp["kind"] == "class" and comp["qualname"] == self.current_class:
                    comp["methods"].append(component)
                    break
        else:
            self.components.append(component)
            self.functions_count += 1

            # Track top-level names
            if not self.scope_stack:
                self.top_level_names.add(node.name)

    def visit_Assign(self, node: ast.Assign):
        """Track __all__ exports."""
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "__all__":
                if isinstance(node.value, (ast.List, ast.Tuple)):
                    for elt in node.value.elts:
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                            self.exports.add(elt.value)
        self.generic_visit(node)

    def _extract_args(self, args: ast.arguments) -> List[Dict[str, Any]]:
        """Extract function arguments with annotations."""
        result = []

        # Regular args
        for arg in args.args:
            result.append(
                {
                    "name": arg.arg,
                    "annotation": self._get_annotation(arg.annotation),
                    "kind": "regular",
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

    def _get_annotation(self, node: Optional[ast.expr]) -> Optional[str]:
        """Convert annotation node to string."""
        if node is None:
            return None
        return ast.unparse(node)

    def _get_name(self, node: ast.expr) -> str:
        """Extract name from expression node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return ast.unparse(node)
        elif isinstance(node, ast.Call):
            return self._get_name(node.func)
        else:
            return ast.unparse(node)


def extract_components(tree: ast.AST) -> Dict[str, Any]:
    """
    Extract all components from AST.

    Args:
        tree: AST tree

    Returns:
        Dictionary with component extraction results
    """
    extractor = ComponentExtractor()
    extractor.visit(tree)

    return {
        "py_components_json": json.dumps(
            extractor.components, sort_keys=True, separators=(",", ":")
        ),
        "py_top_level_names": sorted(extractor.top_level_names),
        "py_exports_list": sorted(extractor.exports) if extractor.exports else None,
        "py_classes_count": extractor.classes_count,
        "py_functions_count": extractor.functions_count,
    }


def analyze_file(file_path: str, ast_tree: Optional[ast.AST] = None) -> dict:
    """
    Analyze file and extract components.

    Args:
        file_path: Path to Python file
        ast_tree: Optional pre-parsed AST tree

    Returns:
        Dictionary with component extraction results
    """
    if ast_tree is None:
        # Parse AST if not provided
        from . import DOC_SCRIPT_2002__ast_parser as ast_parser

        result = ast_parser.analyze_file(file_path)

        if not result.get("py_ast_parse_ok"):
            return {
                "py_components_json": None,
                "py_top_level_names": None,
                "py_exports_list": None,
                "py_classes_count": 0,
                "py_functions_count": 0,
                "error": result.get("error", "AST parse failed"),
            }

        ast_tree = result["ast_tree"]

    return extract_components(ast_tree)


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract Python components (classes, functions) from file"
    )
    parser.add_argument("file_path", help="Path to Python file")
    parser.add_argument(
        "--pretty", action="store_true", help="Pretty-print JSON output"
    )

    args = parser.parse_args()

    result = analyze_file(args.file_path)

    if "error" in result:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        sys.exit(1)

    print(f"Classes: {result['py_classes_count']}")
    print(f"Functions: {result['py_functions_count']}")
    print(f"Top-level names: {result['py_top_level_names']}")
    print(f"Exports (__all__): {result['py_exports_list']}")

    if args.pretty:
        components = json.loads(result["py_components_json"])
        print("\nComponents:")
        print(json.dumps(components, indent=2))

    sys.exit(0)


if __name__ == "__main__":
    main()
