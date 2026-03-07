# DOC_LINK: DOC-CORE-ANALYZERS-MARKDOWN-LINK-ANALYZER-527
"""
Markdown Link Analyzer
Extracts Markdown link relationships from .md files.

Handles:
- Inline links: [text](path/to/file.md)
- Reference links: [text][ref] + [ref]: path
- Relative paths: ./file.md, ../dir/file.md
- Absolute repo paths: /PHASE_1/doc.md

Edge type: "documents"
Confidence: 0.8 (regex-based with context)
"""
# DOC_ID: DOC-CORE-ANALYZERS-MARKDOWN-LINK-ANALYZER-527

import re
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

from .base_analyzer import BaseAnalyzer, RelationshipEdge


class MarkdownLinkAnalyzer(BaseAnalyzer):
    """
    Extract Markdown link relationships from .md files.

    Supports:
    - Inline links: [text](path)
    - Reference links: [text][ref] with [ref]: path definitions
    - Relative and absolute paths within repository

    Confidence: 0.8 (regex-based, context-aware)
    """

    # Inline link pattern: [text](path)
    INLINE_LINK_PATTERN = re.compile(
        r'\[([^\]]+)\]\(([^)]+)\)',
        re.MULTILINE
    )

    # Reference link pattern: [text][ref]
    REFERENCE_LINK_PATTERN = re.compile(
        r'\[([^\]]+)\]\[([^\]]+)\]',
        re.MULTILINE
    )

    # Reference definition pattern: [ref]: path
    REFERENCE_DEF_PATTERN = re.compile(
        r'^\[([^\]]+)\]:\s*(.+)$',
        re.MULTILINE
    )

    def can_analyze(self, file_path: Path, file_type: str) -> bool:
        """Check if this analyzer can process the file."""
        return file_type == "md"

    def analyze(self, file_path: Path, source_doc_id: str) -> List[RelationshipEdge]:
        """
        Extract Markdown link relationships from file.

        Returns list of RelationshipEdge objects with:
        - Edge type: "documents"
        - Confidence: 0.8 (regex-based)
        - Evidence: line number + snippet
        """
        edges = []

        try:
            content = file_path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, OSError) as e:
            return []

        # Extract reference definitions first (for resolving reference links)
        reference_defs = self._extract_reference_definitions(content)

        # Extract inline links
        inline_edges = self._extract_inline_links(content, file_path, source_doc_id)
        edges.extend(inline_edges)

        # Extract reference links
        reference_edges = self._extract_reference_links(
            content, file_path, source_doc_id, reference_defs
        )
        edges.extend(reference_edges)

        return edges

    def _extract_reference_definitions(self, content: str) -> dict:
        """
        Extract reference link definitions from Markdown content.

        Returns: {ref_id: target_path}
        """
        references = {}

        for match in self.REFERENCE_DEF_PATTERN.finditer(content):
            ref_id = match.group(1).strip()
            target = match.group(2).strip()

            # Remove surrounding quotes if present
            target = target.strip('"').strip("'")

            references[ref_id] = target

        return references

    def _extract_inline_links(
        self, content: str, file_path: Path, source_doc_id: str
    ) -> List[RelationshipEdge]:
        """Extract inline Markdown links [text](path)."""
        edges = []

        for match in self.INLINE_LINK_PATTERN.finditer(content):
            link_text = match.group(1)
            target_path = match.group(2).strip()

            # Skip external URLs, anchors, and mailto links
            if self._is_external_or_anchor(target_path):
                continue

            # Calculate line number
            line_number = content[:match.start()].count('\n') + 1

            # Resolve target path to doc_id
            target_doc_id = self._resolve_markdown_path(target_path, file_path)

            if target_doc_id:
                edge = self._create_edge(
                    source_doc_id=source_doc_id,
                    target_doc_id=target_doc_id,
                    line_number=line_number,
                    snippet=f"[{link_text}]({target_path})",
                    extraction_method="markdown_inline_link"
                )
                edges.append(edge)

        return edges

    def _extract_reference_links(
        self, content: str, file_path: Path, source_doc_id: str, reference_defs: dict
    ) -> List[RelationshipEdge]:
        """Extract reference-style Markdown links [text][ref]."""
        edges = []

        for match in self.REFERENCE_LINK_PATTERN.finditer(content):
            link_text = match.group(1)
            ref_id = match.group(2).strip()

            # Look up reference definition
            if ref_id not in reference_defs:
                continue

            target_path = reference_defs[ref_id]

            # Skip external URLs, anchors, and mailto links
            if self._is_external_or_anchor(target_path):
                continue

            # Calculate line number
            line_number = content[:match.start()].count('\n') + 1

            # Resolve target path to doc_id
            target_doc_id = self._resolve_markdown_path(target_path, file_path)

            if target_doc_id:
                edge = self._create_edge(
                    source_doc_id=source_doc_id,
                    target_doc_id=target_doc_id,
                    line_number=line_number,
                    snippet=f"[{link_text}][{ref_id}]",
                    extraction_method="markdown_reference_link"
                )
                edges.append(edge)

        return edges

    def _is_external_or_anchor(self, path: str) -> bool:
        """
        Check if path is external URL, anchor, or mailto link.

        Returns True if should be skipped.
        """
        # Check for URL schemes
        parsed = urlparse(path)
        if parsed.scheme in ('http', 'https', 'ftp', 'mailto', 'tel'):
            return True

        # Check for anchor-only links
        if path.startswith('#'):
            return True

        return False

    def _resolve_markdown_path(self, link_path: str, source_file: Path) -> Optional[str]:
        """
        Resolve Markdown link path to doc_id.

        Handles:
        - Relative paths: ./file.md, ../dir/file.md
        - Absolute repo paths: /PHASE_1/doc.md
        - Paths with anchors: file.md#section (strip anchor)
        """
        # Strip anchor if present
        if '#' in link_path:
            link_path = link_path.split('#')[0]

        # Strip query parameters if present
        if '?' in link_path:
            link_path = link_path.split('?')[0]

        # Skip empty paths
        if not link_path:
            return None

        # Resolve path relative to source file
        if link_path.startswith('/'):
            # Absolute path from repo root - handled by resolve_target_path
            target_path = self.resolve_target_path(link_path[1:], source_file)
        else:
            # Relative path from source file
            target_path = self.resolve_target_path(link_path, source_file)

        if not target_path:
            return None

        # Look up doc_id
        return self.lookup_doc_id(target_path)

    def _create_edge(
        self,
        source_doc_id: str,
        target_doc_id: str,
        line_number: int,
        snippet: str,
        extraction_method: str
    ) -> RelationshipEdge:
        """Create a RelationshipEdge for a Markdown link."""
        from datetime import datetime, timezone

        edge_type = "documents"

        # Check if target exists in registry first
        target_found = target_doc_id in [doc.get("doc_id") for doc in self.registry.get_all_docs()]

        # Get confidence from engine
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
                "snippet": snippet[:200],  # Limit snippet length
                "extraction_method": extraction_method
            },
            analyzer_id=self.analyzer_id,
            last_verified=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            flags=flags
        )
