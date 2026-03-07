#!/usr/bin/env python3
"""
I/O Surface Analyzer - Phase A Core Script
Produces: py_file_operations_list, py_network_calls_list, py_security_surface_hash

Analyzes file I/O, network operations, and security-sensitive calls.
"""
import ast
import hashlib
import json
import sys
from pathlib import Path
from typing import List, Dict, Set, Any


# Security-sensitive patterns
FILE_IO_FUNCTIONS = {
    "open",
    "read",
    "write",
    "readlines",
    "writelines",
    "Path.read_text",
    "Path.write_text",
    "Path.read_bytes",
    "Path.write_bytes",
    "os.open",
    "os.read",
    "os.write",
    "os.remove",
    "os.unlink",
    "os.rmdir",
    "shutil.copy",
    "shutil.move",
    "shutil.rmtree",
    "shutil.copytree",
}

NETWORK_FUNCTIONS = {
    "urllib.request.urlopen",
    "urllib.request.urlretrieve",
    "http.client.HTTPConnection",
    "http.client.HTTPSConnection",
    "socket.socket",
    "socket.create_connection",
    "requests.get",
    "requests.post",
    "requests.put",
    "requests.delete",
    "httpx.get",
    "httpx.post",
    "aiohttp.ClientSession",
}

SECURITY_SENSITIVE = {
    "eval",
    "exec",
    "compile",
    "__import__",
    "subprocess.run",
    "subprocess.call",
    "subprocess.Popen",
    "os.system",
    "os.popen",
    "os.execv",
    "os.spawn",
    "pickle.loads",
    "pickle.load",
    "marshal.loads",
    "input",
    "getpass.getpass",
}


class IOSurfaceVisitor(ast.NodeVisitor):
    """Extract I/O operations from Python AST."""

    def __init__(self):
        self.file_ops = []
        self.network_calls = []
        self.security_calls = []

    def visit_Call(self, node: ast.Call):
        """Analyze function calls."""
        func_name = self._get_call_name(node.func)

        if func_name:
            call_info = {
                "function": func_name,
                "lineno": node.lineno,
                "col_offset": node.col_offset,
                "args_count": len(node.args),
                "kwargs_count": len(node.keywords),
            }

            # Classify the call
            if self._is_file_operation(func_name):
                call_info["category"] = "file_io"
                self.file_ops.append(call_info)

            if self._is_network_call(func_name):
                call_info["category"] = "network"
                self.network_calls.append(call_info)

            if self._is_security_sensitive(func_name):
                call_info["category"] = "security"
                self.security_calls.append(call_info)

        self.generic_visit(node)

    def _get_call_name(self, node: ast.expr) -> str:
        """Extract function call name."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return ast.unparse(node)
        elif isinstance(node, ast.Call):
            return self._get_call_name(node.func)
        return ""

    def _is_file_operation(self, func_name: str) -> bool:
        """Check if function is file I/O related."""
        for pattern in FILE_IO_FUNCTIONS:
            if func_name == pattern or func_name.endswith("." + pattern):
                return True
        return False

    def _is_network_call(self, func_name: str) -> bool:
        """Check if function is network-related."""
        for pattern in NETWORK_FUNCTIONS:
            if func_name == pattern or pattern in func_name:
                return True
        return False

    def _is_security_sensitive(self, func_name: str) -> bool:
        """Check if function is security-sensitive."""
        for pattern in SECURITY_SENSITIVE:
            if func_name == pattern or func_name.endswith("." + pattern):
                return True
        return False


def analyze_io_surface(file_path: Path) -> dict:
    """
    Analyze I/O surface of a Python file.

    Returns dict with:
    - py_file_operations_list: List[Dict]
    - py_network_calls_list: List[Dict]
    - py_security_calls_list: List[Dict]
    - py_security_surface_hash: str
    - success: bool
    - error: Optional[str]
    """
    try:
        source_text = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source_text, filename=str(file_path))

        visitor = IOSurfaceVisitor()
        visitor.visit(tree)

        # Sort by line number for deterministic ordering
        file_ops = sorted(
            visitor.file_ops, key=lambda c: (c["lineno"], c["col_offset"])
        )
        network_calls = sorted(
            visitor.network_calls, key=lambda c: (c["lineno"], c["col_offset"])
        )
        security_calls = sorted(
            visitor.security_calls, key=lambda c: (c["lineno"], c["col_offset"])
        )

        # Compute security surface hash (all security-relevant operations)
        all_security = file_ops + network_calls + security_calls
        canonical_json = json.dumps(all_security, sort_keys=True, separators=(",", ":"))
        security_hash = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

        return {
            "py_file_operations_list": file_ops,
            "py_file_operations_count": len(file_ops),
            "py_network_calls_list": network_calls,
            "py_network_calls_count": len(network_calls),
            "py_security_calls_list": security_calls,
            "py_security_calls_count": len(security_calls),
            "py_security_surface_hash": security_hash,
            "success": True,
            "error": None,
        }

    except SyntaxError as e:
        return {
            "py_file_operations_list": [],
            "py_file_operations_count": 0,
            "py_network_calls_list": [],
            "py_network_calls_count": 0,
            "py_security_calls_list": [],
            "py_security_calls_count": 0,
            "py_security_surface_hash": None,
            "success": False,
            "error": f"Syntax error: {e}",
        }

    except Exception as e:
        return {
            "py_file_operations_list": [],
            "py_file_operations_count": 0,
            "py_network_calls_list": [],
            "py_network_calls_count": 0,
            "py_security_calls_list": [],
            "py_security_calls_count": 0,
            "py_security_surface_hash": None,
            "success": False,
            "error": f"I/O surface analysis failed: {e}",
        }


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: io_surface_analyzer.py <file_path>", file=sys.stderr)
        sys.exit(1)

    file_path = Path(sys.argv[1])

    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    result = analyze_io_surface(file_path)

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
        print(f"File operations: {result['py_file_operations_count']}")
        print(f"Network calls: {result['py_network_calls_count']}")
        print(f"Security-sensitive calls: {result['py_security_calls_count']}")
        print(f"Security surface hash: {result['py_security_surface_hash']}")
        print(
            f"\nFile operations: {json.dumps(result['py_file_operations_list'], indent=2)}"
        )
        print(
            f"\nNetwork calls: {json.dumps(result['py_network_calls_list'], indent=2)}"
        )
        print(
            f"\nSecurity calls: {json.dumps(result['py_security_calls_list'], indent=2)}"
        )
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
