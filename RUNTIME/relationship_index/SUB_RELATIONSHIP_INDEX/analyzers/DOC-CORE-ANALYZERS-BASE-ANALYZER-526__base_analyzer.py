# DOC_LINK: DOC-CORE-ANALYZERS-BASE-ANALYZER-526
"""
Base Analyzer

Abstract base class for all relationship analyzers.

Each analyzer is responsible for:
1. Detecting if it can analyze a given file type
2. Extracting relationships from files
3. Resolving relative paths to absolute paths
4. Looking up doc_ids for target files
"""
# DOC_ID: DOC-CORE-ANALYZERS-BASE-ANALYZER-526

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class RelationshipEdge:
    """
    Represents a single relationship edge between two files.

    Attributes:
        source_doc_id: Source file doc_id
        target_doc_id: Target file doc_id (may be None if target not found)
        edge_type: Type of relationship ("imports", "references_schema", "dot_sources")
        confidence: Confidence score (1.0 = verified, 0.0 = broken)
        evidence: Evidence supporting this relationship
        analyzer_id: ID of the analyzer that discovered this edge
        flags: List of flags (e.g., ["target_missing"])
        last_verified: Timestamp when edge was verified
    """
    source_doc_id: str
    target_doc_id: Optional[str]
    edge_type: str
    confidence: float
    evidence: Dict[str, str]
    analyzer_id: str
    flags: List[str]
    last_verified: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "source": self.source_doc_id,
            "target": self.target_doc_id if self.target_doc_id else "",
            "type": self.edge_type,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "analyzer_id": self.analyzer_id,
            "flags": self.flags,
            "last_verified": self.last_verified
        }


class BaseAnalyzer(ABC):
    """
    Abstract base class for relationship analyzers.

    Concrete analyzers must implement:
    - can_analyze(): Check if analyzer can handle a file type
    - analyze(): Extract relationships from a file
    """

    def __init__(self, doc_id_registry, confidence_engine):
        """
        Initialize the analyzer.

        Args:
            doc_id_registry: DocIDRegistry instance for doc_id lookups
            confidence_engine: ConfidenceEngine instance for confidence scoring
        """
        self.registry = doc_id_registry
        self.confidence_engine = confidence_engine
        # Convert PythonImportAnalyzer -> python_import_analyzer
        class_name = self.__class__.__name__
        # Remove "Analyzer" suffix and convert to snake_case
        name_without_analyzer = class_name.replace("Analyzer", "")
        # Insert underscores before capitals and convert to lowercase
        import re
        snake_case = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name_without_analyzer).lower()
        self.analyzer_id = f"{snake_case}_analyzer"

    @abstractmethod
    def can_analyze(self, file_path: Path, file_type: str) -> bool:
        """
        Check if this analyzer can handle the given file type.

        Args:
            file_path: Path to the file
            file_type: File extension or type (e.g., "py", "json", "ps1")

        Returns:
            True if analyzer can handle this file type, False otherwise
        """
        pass

    @abstractmethod
    def analyze(self, file_path: Path, source_doc_id: str) -> List[RelationshipEdge]:
        """
        Analyze a file and extract relationships.

        Args:
            file_path: Absolute path to the file to analyze
            source_doc_id: Doc ID of the source file

        Returns:
            List of RelationshipEdge objects discovered in the file

        Raises:
            Exception: If file cannot be parsed (analyzer should catch and log)
        """
        pass

    def resolve_target_path(self, target_ref: str, source_path: Path) -> Optional[Path]:
        """
        Resolve a target reference to an absolute path.

        Handles relative paths (./file, ../file) and absolute paths.

        Args:
            target_ref: Target reference string (e.g., "./module.py", "../schema.json")
            source_path: Absolute path to the source file

        Returns:
            Absolute Path to target file, or None if cannot be resolved
        """
        try:
            # If target_ref is already absolute, use it
            target_path = Path(target_ref)
            if target_path.is_absolute():
                if target_path.exists():
                    return target_path.resolve()
                return None

            # Relative path: resolve relative to source file's directory
            source_dir = source_path.parent
            resolved = (source_dir / target_ref).resolve()

            if resolved.exists():
                return resolved

            return None

        except Exception:
            return None

    def lookup_doc_id(self, target_path: Path) -> Optional[str]:
        """
        Look up the doc_id for a target file path.

        Args:
            target_path: Absolute path to the target file

        Returns:
            Doc ID if found in registry, None otherwise
        """
        try:
            # Convert absolute to relative path from repo root
            # Registry stores relative paths like "SUB_DOC_ID/README.md"
            if target_path.is_absolute():
                try:
                    repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent  # analyzers/ -> SUB_RELATIONSHIP_INDEX/ -> relationship_index/ -> RUNTIME/ -> ALL_AI/
                    target_path = target_path.relative_to(repo_root)
                except ValueError:
                    # Path is outside repo
                    return None

            # Normalize path separators for registry lookup
            path_str = str(target_path).replace("\\", "/")

            # Try lookup by path (registry should handle normalization)
            doc_id = self.registry.lookup_by_path(path_str)
            return doc_id

        except Exception:
            return None

    def create_edge(
        self,
        source_doc_id: str,
        target_doc_id: Optional[str],
        edge_type: str,
        extraction_method: str,
        location: str,
        snippet: str
    ) -> RelationshipEdge:
        """
        Create a RelationshipEdge with proper confidence and flags.

        Args:
            source_doc_id: Source file doc_id
            target_doc_id: Target file doc_id (None if not found)
            edge_type: Relationship type
            extraction_method: Method used to extract this relationship
            location: Location in source file (e.g., "file.py:15")
            snippet: Code snippet showing the relationship

        Returns:
            RelationshipEdge object
        """
        # Determine if target was found
        target_found = target_doc_id is not None

        # Get confidence from confidence engine
        confidence = self.confidence_engine.get_confidence(
            extraction_method=extraction_method,
            target_found=target_found
        )

        # Determine flags
        flags = []
        if not target_found:
            flags.extend(self.confidence_engine.get_flags_for_broken_edge())

        # Build evidence
        evidence = {
            "location": location,
            "snippet": snippet,
            "extraction_method": extraction_method
        }

        # Get current timestamp
        now = datetime.now(timezone.utc).isoformat()

        return RelationshipEdge(
            source_doc_id=source_doc_id,
            target_doc_id=target_doc_id,
            edge_type=edge_type,
            confidence=confidence,
            evidence=evidence,
            analyzer_id=self.analyzer_id,
            flags=flags,
            last_verified=now
        )

    def get_repo_root(self) -> Path:
        """
        Get the repository root directory.

        This is used to resolve relative paths and for doc_id lookups.

        Returns:
            Path to repository root (parent of SUB_RELATIONSHIP_INDEX)
        """
        # Go up from SUB_RELATIONSHIP_INDEX/analyzers/ to repo root
        current_file = Path(__file__).resolve()
        repo_root = current_file.parent.parent.parent.parent.parent  # analyzers/ -> SUB_RELATIONSHIP_INDEX/ -> relationship_index/ -> RUNTIME/ -> ALL_AI/
        return repo_root
