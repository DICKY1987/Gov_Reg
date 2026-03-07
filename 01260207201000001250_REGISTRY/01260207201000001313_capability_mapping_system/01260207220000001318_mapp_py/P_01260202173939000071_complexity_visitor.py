#!/usr/bin/env python3
"""
Complexity Analyzer - Phase C Script (Optional)
Produces: py_cyclomatic_complexity

Computes cyclomatic complexity using radon or manual calculation.
"""
import ast
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional


class ComplexityVisitor(ast.NodeVisitor):
    """Calculate cyclomatic complexity manually."""

    def __init__(self):
        self.complexity = 1  # Base complexity
        self.functions = {}
        self.current_function = None

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Track function-level complexity."""
        old_function = self.current_function
        self.current_function = node.name
        self.functions[node.name] = {"complexity": 1, "lineno": node.lineno}

        self.generic_visit(node)

        self.current_function = old_function

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Handle async functions."""
        self.visit_FunctionDef(node)

    def visit_If(self, node: ast.If):
        """If statement adds complexity."""
        self._add_complexity()
        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        """For loop adds complexity."""
        self._add_complexity()
        self.generic_visit(node)

    def visit_While(self, node: ast.While):
        """While loop adds complexity."""
        self._add_complexity()
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        """Exception handler adds complexity."""
        self._add_complexity()
        self.generic_visit(node)

    def visit_With(self, node: ast.With):
        """With statement adds complexity."""
        self._add_complexity()
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp):
        """Boolean operation adds complexity per operand."""
        # and/or operators add complexity
        self._add_complexity(len(node.values) - 1)
        self.generic_visit(node)

    def _add_complexity(self, amount: int = 1):
        """Add to complexity counter."""
        if self.current_function:
            self.functions[self.current_function]["complexity"] += amount
        self.complexity += amount


def calculate_complexity_manual(file_path: Path) -> Dict[str, Any]:
    """Calculate cyclomatic complexity manually using AST."""
    try:
        source_text = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source_text, filename=str(file_path))

        visitor = ComplexityVisitor()
        visitor.visit(tree)

        # Calculate average and max
        if visitor.functions:
            complexities = [f["complexity"] for f in visitor.functions.values()]
            avg_complexity = sum(complexities) / len(complexities)
            max_complexity = max(complexities)
        else:
            avg_complexity = visitor.complexity
            max_complexity = visitor.complexity

        return {
            "total_complexity": visitor.complexity,
            "average_complexity": round(avg_complexity, 2),
            "max_complexity": max_complexity,
            "function_complexities": visitor.functions,
        }

    except Exception as e:
        return {
            "error": str(e),
            "total_complexity": 0,
            "average_complexity": 0,
            "max_complexity": 0,
            "function_complexities": {},
        }


def calculate_complexity_radon(file_path: Path) -> Optional[Dict[str, Any]]:
    """Try to use radon if available."""
    try:
        result = subprocess.run(
            ["radon", "cc", str(file_path), "-j"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0 and result.stdout:
            data = json.loads(result.stdout)
            # Parse radon output
            file_data = data.get(str(file_path), [])

            if file_data:
                complexities = [item["complexity"] for item in file_data]
                return {
                    "total_complexity": sum(complexities),
                    "average_complexity": round(
                        sum(complexities) / len(complexities), 2
                    ),
                    "max_complexity": max(complexities),
                    "tool": "radon",
                }

        return None

    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return None


def analyze_complexity(file_path: Path) -> dict:
    """
    Analyze cyclomatic complexity.

    Returns dict with:
    - py_cyclomatic_complexity: float (average)
    - py_max_complexity: int
    - py_total_complexity: int
    - function_complexities: Dict
    - success: bool
    - error: Optional[str]
    """
    try:
        # Try radon first
        radon_result = calculate_complexity_radon(file_path)

        if radon_result:
            return {
                "py_complexity_cyclomatic": radon_result["average_complexity"],
                "py_max_complexity": radon_result["max_complexity"],
                "py_total_complexity": radon_result["total_complexity"],
                "method": "radon",
                "success": True,
                "error": None,
            }

        # Fall back to manual calculation
        manual_result = calculate_complexity_manual(file_path)

        if "error" in manual_result:
            raise Exception(manual_result["error"])

        return {
            "py_complexity_cyclomatic": manual_result["average_complexity"],
            "py_max_complexity": manual_result["max_complexity"],
            "py_total_complexity": manual_result["total_complexity"],
            "function_complexities": manual_result["function_complexities"],
            "method": "manual",
            "success": True,
            "error": None,
        }

    except Exception as e:
        return {
            "py_complexity_cyclomatic": 0.0,
            "py_max_complexity": 0,
            "py_total_complexity": 0,
            "function_complexities": {},
            "success": False,
            "error": f"Complexity analysis failed: {e}",
        }


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: complexity_analyzer.py <file_path>", file=sys.stderr)
        sys.exit(1)

    file_path = Path(sys.argv[1])

    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    result = analyze_complexity(file_path)

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
        print(f"Average complexity: {result['py_complexity_cyclomatic']}")
        print(f"Max complexity: {result['py_max_complexity']}")
        print(f"Total complexity: {result['py_total_complexity']}")
        print(f"Method: {result.get('method', 'unknown')}")
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
