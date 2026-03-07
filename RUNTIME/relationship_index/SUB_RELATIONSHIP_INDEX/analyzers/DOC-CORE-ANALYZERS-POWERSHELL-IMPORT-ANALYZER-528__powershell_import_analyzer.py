# DOC_LINK: DOC-CORE-ANALYZERS-POWERSHELL-IMPORT-ANALYZER-528
"""
PowerShell Import Analyzer

Extracts dot-sourcing relationships from PowerShell files.

Handles:
- . "./script.ps1"
- . "path/to/script.ps1"
- . $PSScriptRoot/script.ps1
- . "$PSScriptRoot/script.ps1"

Resolves paths and looks up doc_ids via the registry.
"""
# DOC_ID: DOC-CORE-ANALYZERS-POWERSHELL-IMPORT-ANALYZER-528

import re
from pathlib import Path
from typing import List, Optional

from .base_analyzer import BaseAnalyzer, RelationshipEdge


class PowerShellImportAnalyzer(BaseAnalyzer):
    """
    Analyzes PowerShell files for dot-sourcing relationships.

    Uses regex patterns to detect dot-sourcing statements.
    This analyzer produces high-confidence edges (1.0) when the target
    file is found in the registry.
    """

    # Regex patterns for dot-sourcing
    # Pattern 1: . "path/to/file.ps1" or . 'path/to/file.ps1'
    DOT_SOURCE_QUOTED = re.compile(
        r'^\s*\.\s+["\']([^"\']+\.ps1)["\']',
        re.MULTILINE | re.IGNORECASE
    )

    # Pattern 2: . $PSScriptRoot/file.ps1 or . "$PSScriptRoot/file.ps1"
    DOT_SOURCE_PSSCRIPTROOT = re.compile(
        r'^\s*\.\s+["\']*\$PSScriptRoot[/\\]([^"\'\s]+\.ps1)["\']*',
        re.MULTILINE | re.IGNORECASE
    )

    def can_analyze(self, file_path: Path, file_type: str) -> bool:
        """
        Check if this analyzer can handle PowerShell files.

        Args:
            file_path: Path to the file
            file_type: File extension

        Returns:
            True if file is a PowerShell file (.ps1, .psm1, .psd1), False otherwise
        """
        return file_type.lower() in ["ps1", "psm1", "psd1"]

    def analyze(self, file_path: Path, source_doc_id: str) -> List[RelationshipEdge]:
        """
        Analyze a PowerShell file and extract dot-sourcing relationships.

        Args:
            file_path: Absolute path to the PowerShell file
            source_doc_id: Doc ID of the source file

        Returns:
            List of RelationshipEdge objects for each dot-sourcing statement

        Note:
            - Catches file read errors and returns empty list
            - Handles $PSScriptRoot variable substitution
            - Creates broken edges (confidence=0.0) for missing targets
        """
        edges = []

        try:
            # Read PowerShell file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find all dot-sourcing statements
            edges.extend(self._extract_quoted_dot_sources(content, file_path, source_doc_id))
            edges.extend(self._extract_psscriptroot_dot_sources(content, file_path, source_doc_id))

        except Exception as e:
            # File read error or unexpected error - log but don't raise
            pass

        return edges

    def _extract_quoted_dot_sources(
        self,
        content: str,
        source_path: Path,
        source_doc_id: str
    ) -> List[RelationshipEdge]:
        """
        Extract dot-sourcing statements with quoted paths.

        Handles:
        - . "path/to/file.ps1"
        - . 'path/to/file.ps1'

        Args:
            content: PowerShell file content
            source_path: Source file path
            source_doc_id: Source doc_id

        Returns:
            List of RelationshipEdge objects
        """
        edges = []

        for match in self.DOT_SOURCE_QUOTED.finditer(content):
            target_ref = match.group(1)  # Captured path
            lineno = content[:match.start()].count('\n') + 1

            # Normalize path separators
            target_ref = target_ref.replace("\\", "/")

            # Resolve to absolute path
            target_path = self.resolve_target_path(target_ref, source_path)

            # Lookup doc_id
            target_doc_id = None
            if target_path:
                target_doc_id = self.lookup_doc_id(target_path)

            # Create edge
            location = f"{source_path.name}:{lineno}"
            snippet = match.group(0).strip()  # Full matched line

            edge = self.create_edge(
                source_doc_id=source_doc_id,
                target_doc_id=target_doc_id,
                edge_type="dot_sources",
                extraction_method="powershell_ast",
                location=location,
                snippet=snippet
            )

            edges.append(edge)

        return edges

    def _extract_psscriptroot_dot_sources(
        self,
        content: str,
        source_path: Path,
        source_doc_id: str
    ) -> List[RelationshipEdge]:
        """
        Extract dot-sourcing statements with $PSScriptRoot variable.

        Handles:
        - . $PSScriptRoot/file.ps1
        - . "$PSScriptRoot/file.ps1"
        - . $PSScriptRoot\file.ps1

        Args:
            content: PowerShell file content
            source_path: Source file path
            source_doc_id: Source doc_id

        Returns:
            List of RelationshipEdge objects
        """
        edges = []

        for match in self.DOT_SOURCE_PSSCRIPTROOT.finditer(content):
            relative_path = match.group(1)  # Path after $PSScriptRoot/
            lineno = content[:match.start()].count('\n') + 1

            # Normalize path separators
            relative_path = relative_path.replace("\\", "/")

            # $PSScriptRoot = directory containing the source script
            script_dir = source_path.parent

            # Resolve to absolute path
            target_path = (script_dir / relative_path).resolve()

            # Check if target exists
            if not target_path.exists():
                target_path = None

            # Lookup doc_id
            target_doc_id = None
            if target_path:
                target_doc_id = self.lookup_doc_id(target_path)

            # Create edge
            location = f"{source_path.name}:{lineno}"
            snippet = match.group(0).strip()  # Full matched line

            edge = self.create_edge(
                source_doc_id=source_doc_id,
                target_doc_id=target_doc_id,
                edge_type="dot_sources",
                extraction_method="powershell_ast",
                location=location,
                snippet=snippet
            )

            edges.append(edge)

        return edges
