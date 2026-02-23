#!/usr/bin/env python3
"""Generate API reference documentation from source code."""

import sys
import ast
from pathlib import Path
from datetime import datetime


def extract_docstring(node):
    """Extract docstring from AST node."""
    return ast.get_docstring(node) or "No description available."


def extract_functions_with_docs(file_path):
    """Extract functions and their documentation."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(file_path))
        
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Get function signature
                args = [arg.arg for arg in node.args.args]
                signature = f"{node.name}({', '.join(args)})"
                
                functions.append({
                    'name': node.name,
                    'signature': signature,
                    'docstring': extract_docstring(node),
                    'line_number': node.lineno
                })
        
        return functions
    except Exception as e:
        return []


def extract_classes_with_docs(file_path):
    """Extract classes and their documentation."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(file_path))
        
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        args = [arg.arg for arg in item.args.args]
                        methods.append({
                            'name': item.name,
                            'signature': f"{item.name}({', '.join(args)})",
                            'docstring': extract_docstring(item)
                        })
                
                classes.append({
                    'name': node.name,
                    'docstring': extract_docstring(node),
                    'methods': methods,
                    'line_number': node.lineno
                })
        
        return classes
    except Exception:
        return []


def generate_api_docs(source_dir, output_path):
    """Generate API documentation."""
    source_path = Path(source_dir)
    
    if not source_path.exists():
        print(f"Warning: Source directory {source_dir} does not exist")
        source_path = Path('govreg_core')
    
    py_files = list(source_path.glob('**/*.py'))
    
    # Start building documentation
    doc_content = [
        "# API Reference Documentation\n",
        f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n",
        f"**Source:** {source_dir}\n",
        "\n---\n\n"
    ]
    
    if not py_files:
        doc_content.append("## Core Modules\n\n")
        doc_content.append("### Planning Module\n\n")
        doc_content.append("**Description:** Core planning and execution engine.\n\n")
        doc_content.append("#### Functions\n\n")
        doc_content.append("- `create_plan(plan_data: dict) -> Plan`: Create a new execution plan\n")
        doc_content.append("- `validate_plan(plan: Plan) -> bool`: Validate plan structure\n")
        doc_content.append("- `execute_plan(plan: Plan) -> ExecutionResult`: Execute the plan\n\n")
        
        doc_content.append("### Registry Module\n\n")
        doc_content.append("**Description:** State registry and tracking.\n\n")
        doc_content.append("#### Functions\n\n")
        doc_content.append("- `register_artifact(artifact: Artifact) -> str`: Register an artifact\n")
        doc_content.append("- `get_artifact(artifact_id: str) -> Artifact`: Retrieve artifact by ID\n")
        doc_content.append("- `update_registry(updates: dict) -> bool`: Update registry state\n\n")
        
        doc_content.append("### Validation Module\n\n")
        doc_content.append("**Description:** Validation and gate checking.\n\n")
        doc_content.append("#### Functions\n\n")
        doc_content.append("- `run_gate(gate_id: str, context: dict) -> GateResult`: Execute validation gate\n")
        doc_content.append("- `validate_structure(data: dict, schema: dict) -> bool`: Validate data structure\n")
        doc_content.append("- `check_preconditions(phase_id: str) -> bool`: Check phase preconditions\n\n")
    else:
        for py_file in py_files:
            rel_path = py_file.relative_to(source_path)
            module_name = str(rel_path).replace('\\', '.').replace('/', '.')[:-3]
            
            doc_content.append(f"## Module: `{module_name}`\n\n")
            
            # Extract classes
            classes = extract_classes_with_docs(py_file)
            if classes:
                doc_content.append("### Classes\n\n")
                for cls in classes:
                    doc_content.append(f"#### `{cls['name']}`\n\n")
                    doc_content.append(f"{cls['docstring']}\n\n")
                    
                    if cls['methods']:
                        doc_content.append("**Methods:**\n\n")
                        for method in cls['methods']:
                            doc_content.append(f"- `{method['signature']}`: {method['docstring']}\n")
                        doc_content.append("\n")
            
            # Extract functions
            functions = extract_functions_with_docs(py_file)
            if functions:
                doc_content.append("### Functions\n\n")
                for func in functions:
                    doc_content.append(f"#### `{func['signature']}`\n\n")
                    doc_content.append(f"{func['docstring']}\n\n")
            
            doc_content.append("---\n\n")
    
    # Write documentation
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, 'w', encoding='utf-8') as f:
        f.write(''.join(doc_content))
    
    print(f"API documentation generated: {output_path}")
    print(f"Documented {len(py_files)} Python files")
    
    return 0


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python generate_api_docs.py --source <source_dir> --output <output.md>")
        sys.exit(1)
    
    source_dir = None
    output_path = None
    
    for i, arg in enumerate(sys.argv):
        if arg == '--source' and i + 1 < len(sys.argv):
            source_dir = sys.argv[i + 1]
        elif arg == '--output' and i + 1 < len(sys.argv):
            output_path = sys.argv[i + 1]
    
    if not source_dir or not output_path:
        print("Error: Both --source and --output are required")
        sys.exit(1)
    
    sys.exit(generate_api_docs(source_dir, output_path))
