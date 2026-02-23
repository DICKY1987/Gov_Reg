#!/usr/bin/env python3
"""
I/O Surface Analyzer for mapp_py Analysis Pipeline
Produces: py_io_surface_signature, py_file_operations, py_security_sensitive_apis

Analyzes file I/O, network operations, and security-sensitive API calls.
"""

import ast
import json
import hashlib
import sys
from typing import List, Set, Dict, Any, Optional


# Security-sensitive API patterns
SECURITY_SENSITIVE_APIS = {
    'exec', 'eval', 'compile', '__import__',
    'os.system', 'subprocess.call', 'subprocess.run', 'subprocess.Popen',
    'pickle.loads', 'pickle.load',
    'socket.socket', 'socket.create_connection',
    'ctypes', 'cffi',
    'sqlalchemy.text', 'sqlite3.execute',
}

# File operation patterns
FILE_OPERATIONS = {
    'open', 'read', 'write', 'close',
    'os.open', 'os.read', 'os.write', 'os.close',
    'os.remove', 'os.unlink', 'os.rename', 'os.rmdir',
    'shutil.copy', 'shutil.move', 'shutil.rmtree',
    'pathlib.Path.read_text', 'pathlib.Path.write_text',
    'pathlib.Path.read_bytes', 'pathlib.Path.write_bytes',
}


class IOSurfaceAnalyzer(ast.NodeVisitor):
    """Analyze I/O surface from Python AST."""

    def __init__(self):
        self.file_ops: List[Dict[str, Any]] = []
        self.security_apis: List[Dict[str, Any]] = []
        self.io_patterns: Set[str] = set()

    def visit_Call(self, node: ast.Call):
        """Analyze function calls for I/O and security patterns."""
        func_name = self._get_func_name(node.func)

        # Check file operations
        if self._matches_pattern(func_name, FILE_OPERATIONS):
            self.file_ops.append({
                'function': func_name,
                'line': node.lineno,
                'type': self._classify_file_op(func_name)
            })
            self.io_patterns.add('file_io')

        # Check security-sensitive APIs
        if self._matches_pattern(func_name, SECURITY_SENSITIVE_APIS):
            self.security_apis.append({
                'function': func_name,
                'line': node.lineno,
                'category': self._classify_security_api(func_name)
            })
            self.io_patterns.add('security_sensitive')

        self.generic_visit(node)

    def visit_With(self, node: ast.With):
        """Analyze context managers (often used for file I/O)."""
        for item in node.items:
            if isinstance(item.context_expr, ast.Call):
                func_name = self._get_func_name(item.context_expr.func)
                if func_name in ('open', 'pathlib.Path.open'):
                    self.file_ops.append({
                        'function': func_name,
                        'line': node.lineno,
                        'type': 'file_open_context'
                    })
                    self.io_patterns.add('file_io')

        self.generic_visit(node)

    def _get_func_name(self, node: ast.expr) -> str:
        """Extract function name from call node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return ast.unparse(node)
        else:
            return ast.unparse(node)

    def _matches_pattern(self, func_name: str, patterns: Set[str]) -> bool:
        """Check if function name matches any pattern."""
        # Exact match
        if func_name in patterns:
            return True

        # Partial match (e.g., 'os.system' matches if func_name is 'system' and we imported os)
        for pattern in patterns:
            if '.' in pattern:
                _, method = pattern.rsplit('.', 1)
                if func_name == method or func_name.endswith('.' + method):
                    return True

        return False

    def _classify_file_op(self, func_name: str) -> str:
        """Classify type of file operation."""
        if 'read' in func_name.lower():
            return 'read'
        elif 'write' in func_name.lower():
            return 'write'
        elif any(x in func_name.lower() for x in ['remove', 'unlink', 'rmdir', 'rmtree']):
            return 'delete'
        elif any(x in func_name.lower() for x in ['copy', 'move', 'rename']):
            return 'modify'
        elif 'open' in func_name.lower():
            return 'open'
        else:
            return 'other'

    def _classify_security_api(self, func_name: str) -> str:
        """Classify type of security-sensitive API."""
        if any(x in func_name.lower() for x in ['exec', 'eval', 'compile']):
            return 'code_execution'
        elif 'subprocess' in func_name.lower() or 'system' in func_name.lower():
            return 'command_execution'
        elif 'pickle' in func_name.lower():
            return 'deserialization'
        elif 'socket' in func_name.lower():
            return 'network'
        elif any(x in func_name.lower() for x in ['ctypes', 'cffi']):
            return 'foreign_function'
        elif 'sql' in func_name.lower():
            return 'sql_execution'
        else:
            return 'other'


def analyze_io_surface(tree: ast.AST) -> Dict[str, Any]:
    """
    Analyze I/O surface from AST.

    Args:
        tree: AST tree

    Returns:
        Dictionary with I/O surface analysis results
    """
    analyzer = IOSurfaceAnalyzer()
    analyzer.visit(tree)

    # Build I/O signature (deterministic)
    signature_data = {
        'patterns': sorted(analyzer.io_patterns),
        'file_ops_count': len(analyzer.file_ops),
        'security_apis_count': len(analyzer.security_apis)
    }
    signature_json = json.dumps(signature_data, sort_keys=True, separators=(',', ':'))
    io_signature = hashlib.sha256(signature_json.encode('utf-8')).hexdigest()

    return {
        'py_io_surface_signature': io_signature,
        'py_file_operations': sorted(analyzer.file_ops, key=lambda x: x['line']),
        'py_security_sensitive_apis': sorted(analyzer.security_apis, key=lambda x: x['line'])
    }


def analyze_file(file_path: str, ast_tree: Optional[ast.AST] = None) -> dict:
    """
    Analyze file I/O surface.

    Args:
        file_path: Path to Python file
        ast_tree: Optional pre-parsed AST tree

    Returns:
        Dictionary with I/O surface analysis results
    """
    if ast_tree is None:
        # Parse AST if not provided
        from pathlib import Path
        try:
            source = Path(file_path).read_text(encoding='utf-8')
            ast_tree = ast.parse(source)
        except Exception as e:
            return {
                'py_io_surface_signature': None,
                'py_file_operations': None,
                'py_security_sensitive_apis': None,
                'error': f'{type(e).__name__}: {str(e)}'
            }

    return analyze_io_surface(ast_tree)


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Analyze Python file I/O surface and security-sensitive APIs'
    )
    parser.add_argument('file_path', help='Path to Python file')
    parser.add_argument('--verbose', action='store_true',
                       help='Show detailed I/O operations')

    args = parser.parse_args()

    result = analyze_file(args.file_path)

    if 'error' in result:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        sys.exit(1)

    print(f"I/O Surface Signature: {result['py_io_surface_signature']}")
    print(f"File Operations: {len(result['py_file_operations'])}")
    print(f"Security-Sensitive APIs: {len(result['py_security_sensitive_apis'])}")

    if args.verbose:
        if result['py_file_operations']:
            print("\nFile Operations:")
            for op in result['py_file_operations']:
                print(f"  Line {op['line']}: {op['function']} ({op['type']})")

        if result['py_security_sensitive_apis']:
            print("\nSecurity-Sensitive APIs:")
            for api in result['py_security_sensitive_apis']:
                print(f"  Line {api['line']}: {api['function']} ({api['category']})")

    sys.exit(0)


if __name__ == '__main__':
    main()
