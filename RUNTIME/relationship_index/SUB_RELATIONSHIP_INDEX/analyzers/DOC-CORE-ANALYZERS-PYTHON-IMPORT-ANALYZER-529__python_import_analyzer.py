# DOC_LINK: DOC-CORE-ANALYZERS-PYTHON-IMPORT-ANALYZER-529
"""
Python Import Analyzer

Extracts import relationships from Python files using AST parsing.

Handles:
- import module
- from module import name
- from ..relative import name
- from . import name

Resolves module names to file paths and looks up doc_ids via the registry.
"""
# DOC_ID: DOC-CORE-ANALYZERS-PYTHON-IMPORT-ANALYZER-529

import ast
from pathlib import Path
from typing import List, Optional, Set
import sys
import os

from .base_analyzer import BaseAnalyzer, RelationshipEdge


class PythonImportAnalyzer(BaseAnalyzer):
    """
    Analyzes Python files for import relationships using AST parsing.

    This analyzer is deterministic and produces high-confidence edges (1.0)
    when the target file is found in the registry.
    """

    def can_analyze(self, file_path: Path, file_type: str) -> bool:
        """
        Check if this analyzer can handle Python files.

        Args:
            file_path: Path to the file
            file_type: File extension

        Returns:
            True if file is a Python file (.py), False otherwise
        """
        return file_type.lower() == "py"

    def analyze(self, file_path: Path, source_doc_id: str) -> List[RelationshipEdge]:
        """
        Analyze a Python file and extract import relationships.

        Args:
            file_path: Absolute path to the Python file
            source_doc_id: Doc ID of the source file

        Returns:
            List of RelationshipEdge objects for each import statement

        Note:
            - Catches AST parse errors and returns empty list
            - Skips stdlib and external dependencies (not in repo)
            - Creates broken edges (confidence=0.0) for missing targets
        """
        edges = []

        try:
            # Read and parse the Python file
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()

            tree = ast.parse(source_code, filename=str(file_path))

            # Extract import statements
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    # import module1, module2
                    for alias in node.names:
                        module_name = alias.name
                        edge = self._handle_import(
                            source_doc_id=source_doc_id,
                            source_path=file_path,
                            module_name=module_name,
                            lineno=node.lineno,
                            snippet=f"import {module_name}"
                        )
                        if edge:
                            edges.append(edge)

                elif isinstance(node, ast.ImportFrom):
                    # from module import name1, name2
                    module_name = node.module or ""  # node.module is None for "from . import"
                    level = node.level  # 0 = absolute, 1 = ., 2 = .., etc.

                    # Build full import statement for snippet
                    if level > 0:
                        prefix = "." * level
                        full_module = f"{prefix}{module_name}" if module_name else prefix
                    else:
                        full_module = module_name

                    imported_names = [alias.name for alias in node.names]
                    snippet = f"from {full_module} import {', '.join(imported_names)}"

                    edge = self._handle_from_import(
                        source_doc_id=source_doc_id,
                        source_path=file_path,
                        module_name=module_name,
                        level=level,
                        lineno=node.lineno,
                        snippet=snippet
                    )
                    if edge:
                        edges.append(edge)

        except SyntaxError as e:
            # Python file has syntax errors - can't parse
            # Log warning but don't raise (allow pipeline to continue)
            pass

        except Exception as e:
            # Unexpected error - log but don't raise
            pass

        return edges

    def _handle_import(
        self,
        source_doc_id: str,
        source_path: Path,
        module_name: str,
        lineno: int,
        snippet: str
    ) -> Optional[RelationshipEdge]:
        """
        Handle an absolute import statement (import module).

        Args:
            source_doc_id: Source file doc_id
            source_path: Source file path
            module_name: Module being imported (e.g., "os", "mypackage.module")
            lineno: Line number in source file
            snippet: Code snippet

        Returns:
            RelationshipEdge if target found in repo, None if external/stdlib
        """
        # Try to resolve module name to file path
        target_path = self._resolve_module_to_path(module_name, source_path, is_relative=False)

        if target_path is None:
            # Module is stdlib or external - skip
            return None

        # Lookup doc_id for target
        target_doc_id = self.lookup_doc_id(target_path)

        # Create edge
        location = f"{source_path.name}:{lineno}"
        return self.create_edge(
            source_doc_id=source_doc_id,
            target_doc_id=target_doc_id,
            edge_type="imports",
            extraction_method="python_ast_import",
            location=location,
            snippet=snippet
        )

    def _handle_from_import(
        self,
        source_doc_id: str,
        source_path: Path,
        module_name: str,
        level: int,
        lineno: int,
        snippet: str
    ) -> Optional[RelationshipEdge]:
        """
        Handle a from-import statement (from module import name).

        Args:
            source_doc_id: Source file doc_id
            source_path: Source file path
            module_name: Module being imported (may be empty for relative imports)
            level: Import level (0=absolute, 1=., 2=.., etc.)
            lineno: Line number
            snippet: Code snippet

        Returns:
            RelationshipEdge if target found in repo, None if external/stdlib
        """
        # Resolve module to file path
        is_relative = level > 0
        target_path = self._resolve_module_to_path(module_name, source_path, is_relative, level)

        if target_path is None:
            # Module is stdlib or external - skip
            return None

        # Lookup doc_id
        target_doc_id = self.lookup_doc_id(target_path)

        # Create edge
        location = f"{source_path.name}:{lineno}"
        return self.create_edge(
            source_doc_id=source_doc_id,
            target_doc_id=target_doc_id,
            edge_type="imports",
            extraction_method="python_ast_import",
            location=location,
            snippet=snippet
        )

    def _resolve_module_to_path(
        self,
        module_name: str,
        source_path: Path,
        is_relative: bool,
        level: int = 0
    ) -> Optional[Path]:
        """
        Resolve a Python module name to a file path.

        Args:
            module_name: Module name (e.g., "mypackage.module", "module", "")
            source_path: Source file path
            is_relative: True for relative imports (from . import)
            level: Relative import level (1=., 2=.., etc.)

        Returns:
            Absolute Path to module file, or None if stdlib/external

        Strategy:
            1. For relative imports: resolve relative to source file's package
            2. For absolute imports: search from repo root
            3. Check if target is in repo (has doc_id potential)
            4. Try both module.py and module/__init__.py
        """
        repo_root = self.get_repo_root()

        if is_relative:
            # Relative import: from ..module import name
            # Go up 'level' directories from source file's directory
            current_dir = source_path.parent
            for _ in range(level):
                current_dir = current_dir.parent
                if current_dir == repo_root or current_dir == current_dir.parent:
                    # Reached repo root or filesystem root
                    break

            # Now resolve module_name from current_dir
            if module_name:
                # from ..module import name
                module_parts = module_name.split('.')
            else:
                # from .. import name (module_name is empty)
                # This imports from the parent package's __init__.py
                module_parts = []

        else:
            # Absolute import: import mypackage.module
            # Resolve from repo root
            current_dir = repo_root
            module_parts = module_name.split('.')

        # Try to find the module file
        # Two possibilities: module.py or module/__init__.py
        for candidate in self._get_module_candidates(current_dir, module_parts):
            if candidate.exists() and candidate.is_relative_to(repo_root):
                return candidate.resolve()

        # Module not found in repo - likely stdlib or external
        return None

    def _get_module_candidates(self, base_dir: Path, module_parts: List[str]) -> List[Path]:
        """
        Get candidate file paths for a module.

        Args:
            base_dir: Base directory to search from
            module_parts: Module name split by dots (e.g., ["mypackage", "module"])

        Returns:
            List of candidate paths to try
        """
        candidates = []

        if not module_parts:
            # Empty module name (from .. import) - look for __init__.py
            candidates.append(base_dir / "__init__.py")
        else:
            # Build path from module parts
            module_dir = base_dir
            for part in module_parts[:-1]:
                module_dir = module_dir / part

            last_part = module_parts[-1]

            # Try module.py
            candidates.append(module_dir / f"{last_part}.py")

            # Try module/__init__.py
            candidates.append(module_dir / last_part / "__init__.py")

        return candidates

    def _is_stdlib_module(self, module_name: str) -> bool:
        """
        Check if a module is part of Python's standard library.

        Args:
            module_name: Top-level module name (e.g., "os", "sys", "pathlib")

        Returns:
            True if module is stdlib, False otherwise

        Note:
            This is a heuristic check, not exhaustive.
        """
        # Common stdlib modules
        stdlib_modules = {
            'abc', 'argparse', 'ast', 'asyncio', 'base64', 'collections',
            'copy', 'csv', 'datetime', 'enum', 'functools', 'hashlib',
            'io', 'itertools', 'json', 'logging', 'math', 'os', 'pathlib',
            'pickle', 're', 'shutil', 'subprocess', 'sys', 'tempfile',
            'threading', 'time', 'typing', 'unittest', 'urllib', 'uuid',
            'warnings', 'weakref', 'xml', 'yaml', 'zipfile'
        }

        top_level = module_name.split('.')[0]
        return top_level in stdlib_modules
