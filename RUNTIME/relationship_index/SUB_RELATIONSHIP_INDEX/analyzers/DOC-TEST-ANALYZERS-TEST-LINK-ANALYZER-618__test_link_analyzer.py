# DOC_LINK: DOC-TEST-ANALYZERS-TEST-LINK-ANALYZER-618
"""
Test Link Analyzer
Links test files to their implementation files via naming conventions and imports.

Handles:
- Naming convention: test_foo.py → foo.py
- Import analysis: Parse test imports to find tested modules
- BDD spec references: Parse stable IDs in test docstrings

Edge type: "tests"
Confidence: 1.0 (naming convention), 0.8 (import-based heuristic)
"""
# DOC_ID: DOC-TEST-ANALYZERS-TEST-LINK-ANALYZER-618

import ast
import re
from pathlib import Path
from typing import List, Optional

from .base_analyzer import BaseAnalyzer, RelationshipEdge


class TestLinkAnalyzer(BaseAnalyzer):
    """
    Link test files to implementation files.

    Strategies:
    1. Naming convention: test_module.py → module.py
    2. Import analysis: from module import X
    3. BDD spec references: Stable IDs in docstrings

    Confidence: 1.0 (naming), 0.8 (imports), 0.6 (heuristic)
    """

    # Pattern for test file naming
    TEST_PREFIX_PATTERN = re.compile(r'^test_(.+)\.py$')
    TEST_SUFFIX_PATTERN = re.compile(r'^(.+)_test\.py$')

    # Pattern for BDD spec IDs in docstrings
    BDD_SPEC_PATTERN = re.compile(r'DOC-SPEC-BDD-[A-Z0-9-]+-\d{3,}')

    def can_analyze(self, file_path: Path, file_type: str) -> bool:
        """Check if this is a Python test file."""
        if file_type != "py":
            return False

        filename = file_path.name

        # Check for test file naming patterns
        if filename.startswith('test_') or filename.endswith('_test.py'):
            return True

        # Check if file is in tests/ directory
        if 'tests' in [p.name.lower() for p in file_path.parents]:
            return True

        return False

    def analyze(self, file_path: Path, source_doc_id: str) -> List[RelationshipEdge]:
        """
        Extract test → implementation relationships.

        Returns list of RelationshipEdge objects with:
        - Edge type: "tests"
        - Confidence: 1.0 (naming), 0.8 (imports), 0.6 (heuristic)
        - Evidence: method + reasoning
        """
        edges = []

        # Strategy 1: Naming convention
        naming_edges = self._extract_by_naming(file_path, source_doc_id)
        edges.extend(naming_edges)

        # Strategy 2: Import analysis
        import_edges = self._extract_by_imports(file_path, source_doc_id)
        edges.extend(import_edges)

        # Strategy 3: BDD spec references
        bdd_edges = self._extract_bdd_specs(file_path, source_doc_id)
        edges.extend(bdd_edges)

        return edges

    def _extract_by_naming(self, file_path: Path, source_doc_id: str) -> List[RelationshipEdge]:
        """
        Link test files to implementations via naming convention.

        Patterns:
        - test_foo.py → foo.py
        - foo_test.py → foo.py
        """
        edges = []
        filename = file_path.name

        # Try prefix pattern: test_foo.py
        match = self.TEST_PREFIX_PATTERN.match(filename)
        if match:
            module_name = match.group(1)
            target_filename = f"{module_name}.py"
        else:
            # Try suffix pattern: foo_test.py
            match = self.TEST_SUFFIX_PATTERN.match(filename)
            if match:
                module_name = match.group(1)
                target_filename = f"{module_name}.py"
            else:
                return []

        # Search for implementation file
        # Look in common locations relative to test file
        search_paths = [
            # Same directory
            file_path.parent / target_filename,
            # Parent directory
            file_path.parent.parent / target_filename,
            # Sibling src/ or lib/ directory
            file_path.parent.parent / "src" / target_filename,
            file_path.parent.parent / "lib" / target_filename,
            # For tests/unit/test_foo.py → src/foo.py
            file_path.parent.parent.parent / "src" / target_filename,
            # For tests/test_foo.py → module/foo.py
            file_path.parent.parent / module_name / target_filename,
        ]

        for search_path in search_paths:
            if search_path.exists():
                target_doc_id = self.lookup_doc_id(search_path)

                if target_doc_id:
                    edge = self._create_edge(
                        source_doc_id=source_doc_id,
                        target_doc_id=target_doc_id,
                        line_number=1,
                        snippet=f"Test file naming: {filename} → {target_filename}",
                        extraction_method="test_naming_convention",
                        confidence_override=1.0
                    )
                    edges.append(edge)
                    break  # Only link to first match

        return edges

    def _extract_by_imports(self, file_path: Path, source_doc_id: str) -> List[RelationshipEdge]:
        """
        Link test files to implementations via import analysis.

        Strategy: Parse imports and link to imported modules
        """
        edges = []

        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content, filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError):
            return []

        # Extract imports from test file
        imported_modules = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.append((alias.name, node.lineno))

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_modules.append((node.module, node.lineno))

        # Resolve imports to doc_ids
        for module_name, line_no in imported_modules:
            # Skip standard library and third-party imports
            if self._is_stdlib_or_external(module_name):
                continue

            # Try to resolve module to file
            target_doc_id = self._resolve_module_name(module_name, file_path)

            if target_doc_id:
                edge = self._create_edge(
                    source_doc_id=source_doc_id,
                    target_doc_id=target_doc_id,
                    line_number=line_no,
                    snippet=f"import {module_name}",
                    extraction_method="test_import_analysis",
                    confidence_override=0.8
                )
                edges.append(edge)

        return edges

    def _extract_bdd_specs(self, file_path: Path, source_doc_id: str) -> List[RelationshipEdge]:
        """
        Extract BDD spec references from test docstrings.

        Looks for patterns like: DOC-SPEC-BDD-ORCH-001
        """
        edges = []

        try:
            content = file_path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, OSError):
            return []

        # Find all BDD spec IDs
        for match in self.BDD_SPEC_PATTERN.finditer(content):
            spec_id = match.group(0)
            line_number = content[:match.start()].count('\n') + 1

            # Check if spec_id exists in registry
            if spec_id in [doc.get("doc_id") for doc in self.registry.get_all_docs()]:
                edge = self._create_edge(
                    source_doc_id=source_doc_id,
                    target_doc_id=spec_id,
                    line_number=line_number,
                    snippet=f"BDD spec reference: {spec_id}",
                    extraction_method="test_bdd_reference",
                    confidence_override=0.9
                )
                edges.append(edge)

        return edges

    def _is_stdlib_or_external(self, module_name: str) -> bool:
        """Check if module is standard library or external package."""
        # Common stdlib modules
        stdlib_modules = {
            'os', 'sys', 'json', 'yaml', 'pathlib', 'datetime', 'time',
            'collections', 'itertools', 'functools', 're', 'unittest',
            'pytest', 'typing', 'abc', 'dataclasses', 'enum', 'logging',
            'argparse', 'subprocess', 'shutil', 'tempfile', 'hashlib',
            'base64', 'urllib', 'http', 'socket', 'threading', 'multiprocessing'
        }

        # Get top-level module name
        top_level = module_name.split('.')[0]

        return top_level in stdlib_modules

    def _resolve_module_name(self, module_name: str, source_file: Path) -> Optional[str]:
        """
        Resolve Python module name to doc_id.

        Example: "scheduler.core" → "scheduler/core.py" or "scheduler/core/__init__.py"
        """
        # Convert module name to possible file paths
        module_path = module_name.replace('.', '/')

        possible_paths = [
            f"{module_path}.py",
            f"{module_path}/__init__.py",
        ]

        # Search from source file location upward
        search_roots = [source_file.parent]
        for parent in source_file.parents:
            search_roots.append(parent)
            # Stop at repo root (has .git)
            if (parent / '.git').exists():
                break

        for root in search_roots:
            for possible_path in possible_paths:
                full_path = root / possible_path
                if full_path.exists():
                    target_doc_id = self.lookup_doc_id(full_path)
                    if target_doc_id:
                        return target_doc_id

        return None

    def _create_edge(
        self,
        source_doc_id: str,
        target_doc_id: str,
        line_number: int,
        snippet: str,
        extraction_method: str,
        confidence_override: Optional[float] = None
    ) -> RelationshipEdge:
        """Create a RelationshipEdge for a test link."""
        from datetime import datetime, timezone

        edge_type = "tests"

        # Check if target exists in registry first
        target_found = target_doc_id in [doc.get("doc_id") for doc in self.registry.get_all_docs()]

        # Get confidence from engine or use override
        if confidence_override is not None:
            confidence = confidence_override
            if not target_found:
                confidence = 0.0  # Override still respects broken edges
        else:
            confidence = self.confidence_engine.get_confidence(extraction_method, target_found=target_found)

        # Set flags
        if not target_found:
            flags = ["target_missing"]
        else:
            flags = []

        return RelationshipEdge(
            source_doc_id=source_doc_id,
            target_doc_id=target_doc_id,
            edge_type=edge_type,
            confidence=confidence,
            evidence={
                "location": f"line {line_number}",
                "snippet": snippet[:200],
                "extraction_method": extraction_method
            },
            analyzer_id=self.analyzer_id,
            last_verified=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            flags=flags
        )
