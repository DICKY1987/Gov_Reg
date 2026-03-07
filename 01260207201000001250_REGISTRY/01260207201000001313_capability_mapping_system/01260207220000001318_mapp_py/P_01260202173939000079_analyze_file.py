#!/usr/bin/env python3
"""
AST Parser for mapp_py Analysis Pipeline
Produces: py_ast_dump_hash, py_ast_parse_ok

Deterministic AST parsing with stable dump format.
"""

import ast
import hashlib
import sys
from pathlib import Path
from typing import Tuple, Optional


def parse_ast(source_code: str) -> Tuple[Optional[ast.AST], bool, Optional[str]]:
    """
    Parse Python source code into AST.

    Args:
        source_code: Python source code text

    Returns:
        Tuple of (ast_node, parse_ok, error_message)
    """
    try:
        tree = ast.parse(source_code)
        return tree, True, None
    except SyntaxError as e:
        return None, False, f"SyntaxError at line {e.lineno}: {e.msg}"
    except Exception as e:
        return None, False, f"{type(e).__name__}: {str(e)}"


def compute_ast_hash(tree: ast.AST) -> str:
    """
    Compute deterministic hash of AST structure.

    Uses ast.dump with stable parameters for reproducibility.

    Args:
        tree: AST node

    Returns:
        SHA256 hex digest of AST dump
    """
    # Stable dump: include_attributes=False, indent=None for canonical form
    ast_dump = ast.dump(tree, include_attributes=False, indent=None)

    # Hash the canonical dump
    return hashlib.sha256(ast_dump.encode("utf-8")).hexdigest()


def analyze_file(file_path: str, source_text: Optional[str] = None) -> dict:
    """
    Parse Python file and compute AST hash.

    Args:
        file_path: Path to Python file
        source_text: Optional pre-normalized source text (if already normalized)

    Returns:
        Dictionary with py_ast_dump_hash and py_ast_parse_ok
    """
    path = Path(file_path)

    if not path.exists():
        return {
            "py_ast_dump_hash": None,
            "py_ast_parse_ok": False,
            "error": f"File not found: {file_path}",
        }

    # Load source if not provided
    if source_text is None:
        try:
            source_text = path.read_text(encoding="utf-8")
        except Exception as e:
            return {
                "py_ast_dump_hash": None,
                "py_ast_parse_ok": False,
                "error": f"Failed to read file: {str(e)}",
            }

    # Parse AST
    tree, parse_ok, error_msg = parse_ast(source_text)

    if not parse_ok:
        return {"py_ast_dump_hash": None, "py_ast_parse_ok": False, "error": error_msg}

    # Compute hash
    ast_hash = compute_ast_hash(tree)

    return {
        "py_ast_dump_hash": ast_hash,
        "py_ast_parse_ok": True,
        "ast_tree": tree,  # Pass tree for downstream analyzers
    }


def main():
    """CLI entry point."""
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: analyze_file.py <file_path>", file=sys.stderr)
        sys.exit(1)

    file_path = sys.argv[1]
    result = analyze_file(file_path)
    
    # Handle --json flag
    if '--json' in sys.argv:
        idx = sys.argv.index('--json')
        out_path = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
        # Remove ast_tree before JSON serialization
        result_copy = {k: v for k, v in result.items() if k != 'ast_tree'}
        if out_path:
            with open(out_path, 'w') as f:
                json.dump(result_copy, f, indent=2, sort_keys=True)
        else:
            print(json.dumps(result_copy, indent=2, sort_keys=True))
        sys.exit(0)
    
    if result.get("error"):
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)
    
    print(f"AST Hash: {result['py_ast_dump_hash']}")
    print(f"Parse OK: {result['py_ast_parse_ok']}")


if __name__ == "__main__":
    main()
def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Parse Python file and compute deterministic AST hash"
    )
    parser.add_argument("file_path", help="Path to Python file")
    parser.add_argument("--show-tree", action="store_true", help="Print AST tree dump")

    args = parser.parse_args()

    result = analyze_file(args.file_path)

    if "error" in result:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        print(f"py_ast_parse_ok: {result['py_ast_parse_ok']}")
        sys.exit(1)

    print(f"py_ast_parse_ok: {result['py_ast_parse_ok']}")
    print(f"py_ast_dump_hash: {result['py_ast_dump_hash']}")

    if args.show_tree and "ast_tree" in result:
        print("\nAST Tree:")
        print(ast.dump(result["ast_tree"], indent=2))

    sys.exit(0)


if __name__ == "__main__":
    main()
