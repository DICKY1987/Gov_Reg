# DOC_LINK: DOC-CORE-ANALYZERS-SCHEMA-REFERENCE-ANALYZER-530
"""
Schema Reference Analyzer

Extracts schema reference relationships from JSON files.

Handles:
- JSON Schema $ref fields
- Relative paths (./schema.json, ../schemas/common.json)
- Skips internal references (#/definitions/Foo)

Resolves $ref paths to files and looks up doc_ids via the registry.
"""
# DOC_ID: DOC-CORE-ANALYZERS-SCHEMA-REFERENCE-ANALYZER-530

import json
from pathlib import Path
from typing import List, Optional, Any, Dict

from .base_analyzer import BaseAnalyzer, RelationshipEdge


class SchemaReferenceAnalyzer(BaseAnalyzer):
    """
    Analyzes JSON files for schema reference relationships ($ref fields).

    This analyzer is deterministic and produces high-confidence edges (1.0)
    when the target file is found in the registry.
    """

    def can_analyze(self, file_path: Path, file_type: str) -> bool:
        """
        Check if this analyzer can handle JSON files.

        Args:
            file_path: Path to the file
            file_type: File extension

        Returns:
            True if file is a JSON file (.json), False otherwise
        """
        return file_type.lower() == "json"

    def analyze(self, file_path: Path, source_doc_id: str) -> List[RelationshipEdge]:
        """
        Analyze a JSON file and extract $ref relationships.

        Args:
            file_path: Absolute path to the JSON file
            source_doc_id: Doc ID of the source file

        Returns:
            List of RelationshipEdge objects for each $ref found

        Note:
            - Catches JSON parse errors and returns empty list
            - Skips internal refs (#/definitions/...)
            - Creates broken edges (confidence=0.0) for missing targets
        """
        edges = []

        try:
            # Read and parse JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Recursively find all $ref fields
            refs = self._extract_refs(data, json_path="$")

            # Process each $ref
            for ref_info in refs:
                ref_value = ref_info["value"]
                json_path = ref_info["json_path"]

                # Skip internal references (#/definitions/...)
                if ref_value.startswith("#"):
                    continue

                # Extract file path from $ref (may include #fragment)
                file_ref = ref_value.split("#")[0]
                if not file_ref:
                    # Empty before #, means internal ref
                    continue

                # Resolve $ref to file path
                target_path = self.resolve_target_path(file_ref, file_path)

                # Lookup doc_id
                target_doc_id = None
                if target_path:
                    target_doc_id = self.lookup_doc_id(target_path)

                # Create edge
                location = f"{file_path.name}:{json_path}"
                snippet = f"$ref: {ref_value}"

                edge = self.create_edge(
                    source_doc_id=source_doc_id,
                    target_doc_id=target_doc_id,
                    edge_type="references_schema",
                    extraction_method="json_schema_ref",
                    location=location,
                    snippet=snippet
                )

                edges.append(edge)

        except json.JSONDecodeError as e:
            # JSON file is malformed - can't parse
            # Log warning but don't raise
            pass

        except Exception as e:
            # Unexpected error - log but don't raise
            pass

        return edges

    def _extract_refs(self, obj: Any, json_path: str) -> List[Dict[str, str]]:
        """
        Recursively extract all $ref fields from a JSON structure.

        Args:
            obj: JSON object (dict, list, or primitive)
            json_path: Current JSON path (e.g., "$.schemas[0].$ref")

        Returns:
            List of dicts with keys:
            - value: $ref value (e.g., "./common.json#/definitions/Person")
            - json_path: JSON path to the $ref field
        """
        refs = []

        if isinstance(obj, dict):
            # Check if this dict has a $ref field
            if "$ref" in obj:
                refs.append({
                    "value": obj["$ref"],
                    "json_path": f"{json_path}.$ref"
                })

            # Recursively process all values in the dict
            for key, value in obj.items():
                child_path = f"{json_path}.{key}"
                refs.extend(self._extract_refs(value, child_path))

        elif isinstance(obj, list):
            # Recursively process all items in the list
            for i, item in enumerate(obj):
                child_path = f"{json_path}[{i}]"
                refs.extend(self._extract_refs(item, child_path))

        # Primitives (str, int, bool, None) have no refs
        return refs
