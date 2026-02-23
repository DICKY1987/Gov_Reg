#!/usr/bin/env python3
"""Identify integration points across modules for testing."""

import os
import sys
import json
import ast
from pathlib import Path
from datetime import datetime


def find_python_files(directory):
    """Find all Python files in directory."""
    path = Path(directory)
    if not path.exists():
        return []
    return list(path.glob('**/*.py'))


def extract_imports(file_path):
    """Extract imports from a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(file_path))
        
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        return imports
    except Exception as e:
        return []


def extract_functions(file_path):
    """Extract function definitions from a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(file_path))
        
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
        return functions
    except Exception:
        return []


def identify_integration_points(directory, output_path):
    """Identify integration points and save results."""
    files = find_python_files(directory)
    
    integration_data = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'directory': str(directory),
        'total_files': len(files),
        'modules': [],
        'integration_points': []
    }
    
    module_map = {}
    
    for file_path in files:
        rel_path = str(file_path.relative_to(directory))
        imports = extract_imports(file_path)
        functions = extract_functions(file_path)
        
        module_info = {
            'path': rel_path,
            'imports': imports,
            'functions': functions,
            'function_count': len(functions)
        }
        integration_data['modules'].append(module_info)
        module_map[rel_path] = imports
    
    # Identify integration points
    for module_path, imports in module_map.items():
        for other_module in module_map.keys():
            if module_path != other_module:
                other_name = Path(other_module).stem
                if other_name in imports or any(other_name in imp for imp in imports):
                    integration_data['integration_points'].append({
                        'source': module_path,
                        'target': other_module,
                        'type': 'direct_import'
                    })
    
    integration_data['integration_count'] = len(integration_data['integration_points'])
    
    # Save results
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(integration_data, f, indent=2)
    
    print(f"Integration points identified: {integration_data['integration_count']}")
    print(f"Total modules: {integration_data['total_files']}")
    print(f"Results saved to: {output_path}")
    
    return 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python identify_integration_points.py <directory> [output_path]")
        sys.exit(1)
    
    directory = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else '.state/integration_points.json'
    
    sys.exit(identify_integration_points(directory, output_path))
