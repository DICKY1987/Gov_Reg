"""
ArgparseExtractor - AST-based extraction of argparse commands from Python files

This module provides utilities to extract command-line interface definitions from
Python scripts that use argparse. It uses AST parsing (similar to ComponentExtractor)
to detect argparse.ArgumentParser(), add_subparsers(), and add_parser() calls.

Usage:
    from src.capability_mapping.P_01260207201000000980_01999000042260130003_argparse_extractor import extract_argparse_commands
    
    result = extract_argparse_commands(Path('script.py'))
    if result['success']:
        for cmd in result['commands']:
            print(f"Command: {cmd['name']}")
            print(f"Help: {cmd['help']}")
"""

import ast
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class ArgparseVisitor(ast.NodeVisitor):
    """
    AST visitor that detects argparse patterns and extracts command definitions.
    
    Detects:
    - ArgumentParser() creation
    - add_subparsers() calls
    - add_parser() calls with command names and help text
    - add_argument() calls for arguments/options
    """
    
    def __init__(self):
        self.parser_found = False
        self.subparsers_var = None
        self.commands = []
        self.current_command = None
        
        # Track variable assignments to identify parser objects
        self.parser_vars: Set[str] = set()
        self.subparser_vars: Set[str] = set()
        
    def visit_Assign(self, node: ast.Assign) -> None:
        """Track variable assignments for ArgumentParser and subparsers."""
        if isinstance(node.value, ast.Call):
            func = node.value.func
            
            # Detect: parser = argparse.ArgumentParser()
            if self._is_argparse_call(func, 'ArgumentParser'):
                self.parser_found = True
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.parser_vars.add(target.id)
            
            # Detect: subparsers = parser.add_subparsers()
            elif self._is_method_call(func, 'add_subparsers'):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.subparser_vars.add(target.id)
                        self.subparsers_var = target.id
        
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call) -> None:
        """Visit function calls to detect add_parser() and add_argument()."""
        func = node.value if isinstance(node, ast.Assign) else node
        
        # Detect: subparsers.add_parser('command', help='description')
        if isinstance(func, ast.Call) and self._is_method_call(func.func, 'add_parser'):
            command_info = self._extract_command_from_add_parser(func)
            if command_info:
                self.commands.append(command_info)
        
        self.generic_visit(node)
    
    def _is_argparse_call(self, func: ast.AST, method_name: str) -> bool:
        """Check if func is argparse.MethodName or ArgumentParser."""
        if isinstance(func, ast.Attribute):
            # Check for argparse.ArgumentParser
            if (func.attr == method_name and 
                isinstance(func.value, ast.Name) and 
                func.value.id == 'argparse'):
                return True
        elif isinstance(func, ast.Name):
            # Check for ArgumentParser (imported as: from argparse import ArgumentParser)
            if func.id == method_name:
                return True
        return False
    
    def _is_method_call(self, func: ast.AST, method_name: str) -> bool:
        """Check if func is obj.method_name()."""
        if isinstance(func, ast.Attribute):
            return func.attr == method_name
        return False
    
    def _extract_command_from_add_parser(self, call_node: ast.Call) -> Optional[Dict[str, Any]]:
        """
        Extract command name and metadata from add_parser() call.
        
        Example:
            subparsers.add_parser('validate', help='Validate schema')
            → {'name': 'validate', 'help': 'Validate schema', 'arguments': []}
        """
        command_name = None
        help_text = None
        aliases = []
        
        # Extract positional argument (command name)
        if call_node.args:
            first_arg = call_node.args[0]
            if isinstance(first_arg, ast.Constant):
                command_name = first_arg.value
            elif isinstance(first_arg, ast.Str):  # Python 3.7 compatibility
                command_name = first_arg.s
        
        # Extract keyword arguments
        for keyword in call_node.keywords:
            if keyword.arg == 'help':
                if isinstance(keyword.value, ast.Constant):
                    help_text = keyword.value.value
                elif isinstance(keyword.value, ast.Str):  # Python 3.7 compatibility
                    help_text = keyword.value.s
            elif keyword.arg == 'aliases':
                # Extract list of aliases
                if isinstance(keyword.value, ast.List):
                    for elt in keyword.value.elts:
                        if isinstance(elt, ast.Constant):
                            aliases.append(elt.value)
                        elif isinstance(elt, ast.Str):  # Python 3.7 compatibility
                            aliases.append(elt.s)
        
        if command_name:
            return {
                'name': command_name,
                'help': help_text or '',
                'aliases': aliases,
                'arguments': []  # Could be extended to extract add_argument() calls
            }
        
        return None


class ArgparseExtractor:
    """
    High-level interface for extracting argparse commands from Python files.
    """
    
    def __init__(self):
        pass
    
    def extract(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract argparse commands from a Python file.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            Dict with:
                - success: bool
                - commands: List[Dict] (command definitions)
                - parser_found: bool
                - error: Optional[str]
        """
        return extract_argparse_commands(file_path)


def extract_argparse_commands(file_path: Path) -> Dict[str, Any]:
    """
    Extract argparse command definitions from a Python file using AST parsing.
    
    Args:
        file_path: Path to Python file
        
    Returns:
        Dict containing:
            - success: True if parsing succeeded
            - commands: List of command dictionaries
            - parser_found: True if ArgumentParser detected
            - error: Error message if parsing failed
            
    Example:
        >>> result = extract_argparse_commands(Path('cli.py'))
        >>> if result['success']:
        ...     for cmd in result['commands']:
        ...         print(f"{cmd['name']}: {cmd['help']}")
    """
    if not file_path.exists():
        return {
            'success': False,
            'commands': [],
            'parser_found': False,
            'error': f"File not found: {file_path}"
        }
    
    if not file_path.suffix == '.py':
        return {
            'success': False,
            'commands': [],
            'parser_found': False,
            'error': f"Not a Python file: {file_path}"
        }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        # Parse AST
        tree = ast.parse(source_code, filename=str(file_path))
        
        # Visit nodes
        visitor = ArgparseVisitor()
        visitor.visit(tree)
        
        return {
            'success': True,
            'commands': visitor.commands,
            'parser_found': visitor.parser_found,
            'error': None
        }
    
    except SyntaxError as e:
        return {
            'success': False,
            'commands': [],
            'parser_found': False,
            'error': f"Syntax error in {file_path}: {e}"
        }
    
    except Exception as e:
        return {
            'success': False,
            'commands': [],
            'parser_found': False,
            'error': f"Error parsing {file_path}: {e}"
        }


# Convenience function for testing
def main():
    """Test harness for ArgparseExtractor."""
    import sys
    if len(sys.argv) < 2:
        print("Usage: python argparse_extractor.py <file.py>")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    result = extract_argparse_commands(file_path)
    
    if result['success']:
        print(f"✓ Parsed successfully")
        print(f"  Parser found: {result['parser_found']}")
        print(f"  Commands found: {len(result['commands'])}")
        for cmd in result['commands']:
            print(f"\n  Command: {cmd['name']}")
            print(f"    Help: {cmd['help']}")
            if cmd['aliases']:
                print(f"    Aliases: {', '.join(cmd['aliases'])}")
    else:
        print(f"✗ Parsing failed: {result['error']}")
        sys.exit(1)


if __name__ == '__main__':
    main()
