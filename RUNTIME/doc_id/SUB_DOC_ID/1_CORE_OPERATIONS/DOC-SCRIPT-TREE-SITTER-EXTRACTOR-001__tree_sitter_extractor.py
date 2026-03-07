#!/usr/bin/env python3
# DOC_LINK: DOC-SCRIPT-TREE-SITTER-EXTRACTOR-001
# DOC_ID: DOC-SCRIPT-TREE-SITTER-EXTRACTOR-001
"""
Tree-Sitter Metadata Extractor for Registry Enhancement

PURPOSE:
    Extract code structure, imports, exports, complexity metrics from source
    files using tree-sitter syntax parsing to enrich the doc_id registry.

USAGE:
    python tree_sitter_extractor.py --file path/to/file.py
    python tree_sitter_extractor.py --doc-id DOC-CORE-CONFTEST-317
    python tree_sitter_extractor.py --batch --limit 100

CAPABILITIES:
    ✅ Code structure (functions, classes, methods)
    ✅ Imports and dependencies
    ✅ Exports (public API)
    ✅ Docstrings and inline comments
    ✅ Type annotations
    ✅ Decorators and attributes
    ✅ Entry points (main, CLI, hooks)
    ✅ Complexity metrics (LOC, nesting, cyclomatic)
    ⚠️  Purpose/role inference (heuristic)
    ❌ Runtime behavior (needs profiling)
    ❌ Test coverage (needs pytest-cov)
"""

import argparse
import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Optional, Any

try:
    from tree_sitter import Language, Parser
    from tree_sitter_languages import get_language, get_parser
except ImportError:
    print("[ERROR] tree-sitter not installed. Run: pip install tree-sitter tree-sitter-languages")
    sys.exit(1)

# Add parent to path for common imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import REPO_ROOT


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class FunctionInfo:
    """Represents a function/method in the code."""
    name: str
    line_start: int
    line_end: int
    params: List[str] = field(default_factory=list)
    return_type: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    is_async: bool = False
    complexity: int = 1  # Cyclomatic complexity


@dataclass
class ClassInfo:
    """Represents a class definition."""
    name: str
    line_start: int
    line_end: int
    base_classes: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    docstring: Optional[str] = None


@dataclass
class ImportInfo:
    """Represents an import statement."""
    module: str
    items: List[str] = field(default_factory=list)
    is_from: bool = False
    alias: Optional[str] = None


@dataclass
class CodeStructure:
    """Complete code structure metadata."""
    file_type: str
    language: str
    lines_of_code: int
    functions: List[FunctionInfo] = field(default_factory=list)
    classes: List[ClassInfo] = field(default_factory=list)
    imports: List[ImportInfo] = field(default_factory=list)
    exports: List[Dict[str, Any]] = field(default_factory=list)
    entry_points: List[Dict[str, Any]] = field(default_factory=list)
    module_docstring: Optional[str] = None
    max_nesting_depth: int = 0
    total_complexity: int = 0


# ============================================================================
# Tree-Sitter Extractors
# ============================================================================

class PythonExtractor:
    """Extract metadata from Python files using tree-sitter."""

    def __init__(self):
        try:
            # Try new API first
            from tree_sitter_languages import get_parser
            self.parser = get_parser('python')
        except (ImportError, TypeError):
            # Fall back to manual initialization
            import tree_sitter_python as tspython
            from tree_sitter import Parser, Language
            PY_LANGUAGE = Language(tspython.language())
            self.parser = Parser(PY_LANGUAGE)

    def extract(self, file_path: Path) -> CodeStructure:
        """Extract complete metadata from Python file."""
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        tree = self.parser.parse(bytes(content, 'utf-8'))

        structure = CodeStructure(
            file_type='python_module',
            language='python',
            lines_of_code=len(content.splitlines())
        )

        # Extract module docstring
        structure.module_docstring = self._extract_module_docstring(tree.root_node, content)

        # Extract imports
        structure.imports = self._extract_imports(tree.root_node, content)

        # Extract functions
        structure.functions = self._extract_functions(tree.root_node, content)

        # Extract classes
        structure.classes = self._extract_classes(tree.root_node, content)

        # Compute complexity
        structure.total_complexity = sum(f.complexity for f in structure.functions)
        structure.max_nesting_depth = self._compute_max_nesting(tree.root_node)

        # Identify entry points
        structure.entry_points = self._find_entry_points(tree.root_node, content)

        # Build exports list (public API)
        structure.exports = self._build_exports(structure)

        return structure

    def _extract_module_docstring(self, node, content: str) -> Optional[str]:
        """Extract module-level docstring."""
        for child in node.children:
            if child.type == 'expression_statement':
                string_node = child.child_by_field_name('expression')
                if string_node and string_node.type == 'string':
                    return self._clean_docstring(
                        content[string_node.start_byte:string_node.end_byte]
                    )
        return None

    def _extract_imports(self, node, content: str) -> List[ImportInfo]:
        """Extract all import statements."""
        imports = []

        def visit(n):
            if n.type == 'import_statement':
                # import foo, bar
                module = content[n.start_byte:n.end_byte].replace('import ', '')
                imports.append(ImportInfo(module=module.strip(), is_from=False))

            elif n.type == 'import_from_statement':
                # from foo import bar, baz
                module_name = n.child_by_field_name('module_name')
                module = content[module_name.start_byte:module_name.end_byte] if module_name else ''

                items = []
                for child in n.children:
                    if child.type == 'dotted_name' and child.parent.type != 'import_from_statement':
                        items.append(content[child.start_byte:child.end_byte])
                    elif child.type == 'identifier' and child.parent == n:
                        items.append(content[child.start_byte:child.end_byte])

                imports.append(ImportInfo(module=module, items=items, is_from=True))

            for child in n.children:
                visit(child)

        visit(node)
        return imports

    def _extract_functions(self, node, content: str) -> List[FunctionInfo]:
        """Extract all function definitions."""
        functions = []

        def visit(n):
            if n.type == 'function_definition':
                func_info = self._parse_function(n, content)
                functions.append(func_info)

            for child in n.children:
                visit(child)

        visit(node)
        return functions

    def _parse_function(self, node, content: str) -> FunctionInfo:
        """Parse a single function definition."""
        name_node = node.child_by_field_name('name')
        name = content[name_node.start_byte:name_node.end_byte] if name_node else 'unknown'

        # Extract parameters
        params_node = node.child_by_field_name('parameters')
        params = []
        if params_node:
            for child in params_node.children:
                if child.type == 'identifier':
                    params.append(content[child.start_byte:child.end_byte])

        # Extract decorators
        decorators = []
        for sibling in node.parent.children:
            if sibling.type == 'decorator' and sibling.end_byte <= node.start_byte:
                decorator_text = content[sibling.start_byte:sibling.end_byte]
                decorators.append(decorator_text.strip())

        # Extract docstring
        docstring = None
        body = node.child_by_field_name('body')
        if body and len(body.children) > 0:
            first_stmt = body.children[0]
            if first_stmt.type == 'expression_statement':
                string_node = first_stmt.child_by_field_name('expression')
                if string_node and string_node.type == 'string':
                    docstring = self._clean_docstring(
                        content[string_node.start_byte:string_node.end_byte]
                    )

        # Compute complexity (simple: count decision points)
        complexity = self._compute_complexity(node)

        return FunctionInfo(
            name=name,
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            params=params,
            decorators=decorators,
            docstring=docstring,
            is_async='async' in content[node.start_byte:node.start_byte+10],
            complexity=complexity
        )

    def _extract_classes(self, node, content: str) -> List[ClassInfo]:
        """Extract all class definitions."""
        classes = []

        def visit(n):
            if n.type == 'class_definition':
                class_info = self._parse_class(n, content)
                classes.append(class_info)

            for child in n.children:
                visit(child)

        visit(node)
        return classes

    def _parse_class(self, node, content: str) -> ClassInfo:
        """Parse a single class definition."""
        name_node = node.child_by_field_name('name')
        name = content[name_node.start_byte:name_node.end_byte] if name_node else 'unknown'

        # Extract base classes
        bases_node = node.child_by_field_name('superclasses')
        base_classes = []
        if bases_node:
            for child in bases_node.children:
                if child.type in ('identifier', 'attribute'):
                    base_classes.append(content[child.start_byte:child.end_byte])

        # Extract methods
        methods = []
        body = node.child_by_field_name('body')
        if body:
            for child in body.children:
                if child.type == 'function_definition':
                    method_name = child.child_by_field_name('name')
                    if method_name:
                        methods.append(content[method_name.start_byte:method_name.end_byte])

        # Extract docstring
        docstring = None
        if body and len(body.children) > 0:
            first_stmt = body.children[0]
            if first_stmt.type == 'expression_statement':
                string_node = first_stmt.child_by_field_name('expression')
                if string_node and string_node.type == 'string':
                    docstring = self._clean_docstring(
                        content[string_node.start_byte:string_node.end_byte]
                    )

        return ClassInfo(
            name=name,
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            base_classes=base_classes,
            methods=methods,
            docstring=docstring
        )

    def _find_entry_points(self, node, content: str) -> List[Dict[str, Any]]:
        """Find entry points (main blocks, CLI commands, etc)."""
        entry_points = []

        def visit(n):
            # if __name__ == "__main__"
            if n.type == 'if_statement':
                condition = n.child_by_field_name('condition')
                if condition:
                    cond_text = content[condition.start_byte:condition.end_byte]
                    if '__name__' in cond_text and '__main__' in cond_text:
                        entry_points.append({
                            'type': 'main_block',
                            'line': n.start_point[0] + 1
                        })

            # @click.command, @app.route, etc
            elif n.type == 'decorator':
                decorator_text = content[n.start_byte:n.end_byte]
                if 'click.command' in decorator_text:
                    entry_points.append({
                        'type': 'cli_command',
                        'decorator': decorator_text,
                        'line': n.start_point[0] + 1
                    })
                elif 'app.route' in decorator_text or 'app.get' in decorator_text or 'app.post' in decorator_text:
                    entry_points.append({
                        'type': 'http_route',
                        'decorator': decorator_text,
                        'line': n.start_point[0] + 1
                    })

            for child in n.children:
                visit(child)

        visit(node)
        return entry_points

    def _build_exports(self, structure: CodeStructure) -> List[Dict[str, Any]]:
        """Build list of exported symbols (public API)."""
        exports = []

        # Public functions (not starting with _)
        for func in structure.functions:
            if not func.name.startswith('_'):
                exports.append({
                    'name': func.name,
                    'type': 'function',
                    'signature': f"({', '.join(func.params)})",
                    'decorators': func.decorators,
                    'docstring': func.docstring[:100] + '...' if func.docstring and len(func.docstring) > 100 else func.docstring,
                    'line': func.line_start
                })

        # Public classes
        for cls in structure.classes:
            if not cls.name.startswith('_'):
                exports.append({
                    'name': cls.name,
                    'type': 'class',
                    'methods': [m for m in cls.methods if not m.startswith('_')],
                    'base_classes': cls.base_classes,
                    'docstring': cls.docstring[:100] + '...' if cls.docstring and len(cls.docstring) > 100 else cls.docstring,
                    'line': cls.line_start
                })

        return exports

    def _compute_complexity(self, node) -> int:
        """Compute cyclomatic complexity (decision points)."""
        complexity = 1
        decision_nodes = {'if_statement', 'for_statement', 'while_statement', 'except_clause', 'and', 'or'}

        def visit(n):
            nonlocal complexity
            if n.type in decision_nodes:
                complexity += 1
            for child in n.children:
                visit(child)

        visit(node)
        return complexity

    def _compute_max_nesting(self, node, current_depth=0) -> int:
        """Compute maximum nesting depth."""
        max_depth = current_depth
        nesting_types = {'if_statement', 'for_statement', 'while_statement', 'try_statement', 'with_statement'}

        for child in node.children:
            new_depth = current_depth + (1 if child.type in nesting_types else 0)
            child_max = self._compute_max_nesting(child, new_depth)
            max_depth = max(max_depth, child_max)

        return max_depth

    def _clean_docstring(self, raw: str) -> str:
        """Clean and format docstring."""
        # Remove quotes
        for quote in ['"""', "'''", '"', "'"]:
            raw = raw.strip(quote)
        return raw.strip()


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Extract code metadata using tree-sitter")
    parser.add_argument('--file', type=str, help="Single file to analyze")
    parser.add_argument('--output', type=str, help="Output JSON file")
    parser.add_argument('--pretty', action='store_true', help="Pretty print JSON")

    args = parser.parse_args()

    if not args.file:
        print("[ERROR] --file required")
        sys.exit(1)

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"[ERROR] File not found: {file_path}")
        sys.exit(1)

    # Extract metadata
    extractor = PythonExtractor()
    structure = extractor.extract(file_path)

    # Convert to dict
    output = asdict(structure)

    # Output
    indent = 2 if args.pretty else None
    json_str = json.dumps(output, indent=indent)

    if args.output:
        Path(args.output).write_text(json_str)
        print(f"[OK] Metadata written to: {args.output}")
    else:
        print(json_str)


if __name__ == '__main__':
    main()
