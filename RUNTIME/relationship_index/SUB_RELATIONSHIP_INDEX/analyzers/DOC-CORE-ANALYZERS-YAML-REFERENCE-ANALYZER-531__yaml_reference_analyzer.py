# DOC_LINK: DOC-CORE-ANALYZERS-YAML-REFERENCE-ANALYZER-531
"""
YAML Reference Analyzer
Extracts YAML anchor, alias, and file inclusion relationships.

Handles:
- Anchors: key: &anchor_name value
- Aliases: key: *anchor_name
- File includes: !include path/to/file.yaml (custom YAML tag)

Edge type: "references_yaml"
Confidence: 1.0 (YAML parser-based)
"""
# DOC_ID: DOC-CORE-ANALYZERS-YAML-REFERENCE-ANALYZER-531

import re
from pathlib import Path
from typing import List, Optional, Dict, Any
import yaml

from .base_analyzer import BaseAnalyzer, RelationshipEdge


class YAMLReferenceAnalyzer(BaseAnalyzer):
    """
    Extract YAML reference relationships from .yaml/.yml files.

    Supports:
    - YAML anchors and aliases (&anchor, *alias)
    - File includes (!include directive)
    - Cross-file references

    Confidence: 1.0 (YAML parser-based)
    """

    # Pattern for !include directives (custom YAML tag)
    INCLUDE_PATTERN = re.compile(
        r'!\s*include\s+["\']?([^"\'}\s]+)["\']?',
        re.MULTILINE
    )

    def can_analyze(self, file_path: Path, file_type: str) -> bool:
        """Check if this analyzer can process the file."""
        return file_type in ("yaml", "yml")

    def analyze(self, file_path: Path, source_doc_id: str) -> List[RelationshipEdge]:
        """
        Extract YAML reference relationships from file.

        Returns list of RelationshipEdge objects with:
        - Edge type: "references_yaml"
        - Confidence: 1.0 (parser-based)
        - Evidence: key path + snippet
        """
        edges = []

        try:
            content = file_path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, OSError):
            return []

        # Extract file includes (custom !include tag)
        include_edges = self._extract_includes(content, file_path, source_doc_id)
        edges.extend(include_edges)

        # Note: YAML anchors/aliases are internal to the file,
        # so we only extract cross-file relationships (!include)

        return edges

    def _extract_includes(
        self, content: str, file_path: Path, source_doc_id: str
    ) -> List[RelationshipEdge]:
        """Extract !include directives from YAML content."""
        edges = []

        for match in self.INCLUDE_PATTERN.finditer(content):
            include_path = match.group(1).strip()

            # Calculate line number
            line_number = content[:match.start()].count('\n') + 1

            # Resolve include path to doc_id
            target_doc_id = self._resolve_yaml_include(include_path, file_path)

            if target_doc_id:
                edge = self._create_edge(
                    source_doc_id=source_doc_id,
                    target_doc_id=target_doc_id,
                    line_number=line_number,
                    snippet=f"!include {include_path}",
                    extraction_method="yaml_include"
                )
                edges.append(edge)

        return edges

    def _resolve_yaml_include(self, include_path: str, source_file: Path) -> Optional[str]:
        """
        Resolve YAML include path to doc_id.

        Handles:
        - Relative paths: ./file.yaml, ../dir/file.yaml
        - Absolute repo paths: /config/base.yaml
        """
        # Resolve path relative to source file
        if include_path.startswith('/'):
            # Absolute path from repo root
            target_path = self.resolve_target_path(include_path[1:], source_file)
        else:
            # Relative path from source file
            target_path = self.resolve_target_path(include_path, source_file)

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
        """Create a RelationshipEdge for a YAML reference."""
        from datetime import datetime, timezone

        edge_type = "references_yaml"

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
                "snippet": snippet[:200],
                "extraction_method": extraction_method
            },
            analyzer_id=self.analyzer_id,
            last_verified=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            flags=flags
        )
