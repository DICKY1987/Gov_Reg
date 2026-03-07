# DOC_LINK: DOC-CORE-DOC-ID-COVERAGE-CLIENT-003
"""Doc ID Coverage Client for querying Doc ID registry metrics.

Reads DOC_ID_REGISTRY.yaml and calculates coverage statistics for GUI panels.
"""

# DOC_ID: DOC-CORE-DOC-ID-COVERAGE-CLIENT-003

import logging
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class CoverageMetrics:
    """Doc ID coverage metrics."""

    total_files: int
    covered_files: int
    coverage_percentage: float
    by_category: Dict[str, int]
    by_file_type: Dict[str, Dict[str, int]]  # file_type -> {covered, total}
    uncovered_files: List[str]

    @property
    def overall_status(self) -> str:
        """Get overall compliance status."""
        if self.coverage_percentage >= 95:
            return "compliant"
        elif self.coverage_percentage >= 70:
            return "partially_compliant"
        else:
            return "non_compliant"


@dataclass
class RegistryStats:
    """Statistics from Doc ID registry."""

    total_docs: int
    version: str
    last_updated: str
    categories: Dict[str, Dict]  # category -> {count, prefix, description}


class DocIdCoverageClient:
    """Client for querying Doc ID coverage metrics.

    Reads DOC_ID_REGISTRY.yaml and calculates coverage statistics:
    - Overall coverage percentage
    - Breakdown by category (core, guide, config, etc.)
    - Breakdown by file type (.py, .yaml, .md)
    - List of uncovered files
    """

    def __init__(self, registry_path: Optional[str | Path] = None):
        """Initialize coverage client.

        Args:
            registry_path: Path to DOC_ID_REGISTRY.yaml.
                          If None, uses default location.
        """
        if registry_path is None:
            # Default to SUB_DOC_ID registry
            registry_path = Path("SUB_DOC_ID") / "5_REGISTRY_DATA" / "DOC_ID_REGISTRY.yaml"

        self.registry_path = Path(registry_path)
        self._cache = None

        if not self.registry_path.exists():
            logger.warning(f"Registry not found: {self.registry_path}")

    def _load_registry(self) -> Optional[dict]:
        """Load and parse registry YAML.

        Returns:
            Parsed registry dict, or None if file doesn't exist
        """
        if self._cache is not None:
            return self._cache

        if not self.registry_path.exists():
            return None

        try:
            with open(self.registry_path, "r", encoding="utf-8") as f:
                self._cache = yaml.safe_load(f)
            return self._cache
        except (yaml.YAMLError, IOError) as e:
            logger.error(f"Failed to load registry: {e}")
            return None

    def get_registry_stats(self) -> RegistryStats:
        """Get overall registry statistics.

        Returns:
            RegistryStats with totals and category breakdown
        """
        registry = self._load_registry()
        if not registry:
            return RegistryStats(
                total_docs=0,
                version="unknown",
                last_updated="unknown",
                categories={},
            )

        metadata = registry.get("metadata", {})
        categories = registry.get("categories", {})

        # Extract category info
        category_info = {}
        for cat_name, cat_data in categories.items():
            category_info[cat_name] = {
                "count": cat_data.get("count", 0),
                "prefix": cat_data.get("prefix", ""),
                "description": cat_data.get("description", ""),
            }

        return RegistryStats(
            total_docs=metadata.get("total_docs", 0),
            version=metadata.get("version", "unknown"),
            last_updated=metadata.get("last_updated", "unknown"),
            categories=category_info,
        )

    def get_coverage_metrics(self, scope_path: Optional[str] = None) -> CoverageMetrics:
        """Calculate coverage metrics.

        Args:
            scope_path: Optional path to limit coverage calculation

        Returns:
            CoverageMetrics with coverage statistics
        """
        registry = self._load_registry()
        if not registry:
            return CoverageMetrics(
                total_files=0,
                covered_files=0,
                coverage_percentage=0.0,
                by_category={},
                by_file_type={},
                uncovered_files=[],
            )

        docs = registry.get("docs", [])

        # Count by category
        category_counts = Counter(doc.get("category", "unknown") for doc in docs)

        # Estimate file types from doc entries (simplified)
        # In reality, would need to inspect actual files on disk
        file_type_stats = {
            ".py": {"covered": 0, "total": 0},
            ".yaml": {"covered": 0, "total": 0},
            ".md": {"covered": 0, "total": 0},
            ".json": {"covered": 0, "total": 0},
        }

        # Approximate file type distribution based on categories
        # This is a simplified heuristic - real implementation would scan filesystem
        for doc in docs:
            category = doc.get("category", "")
            # Heuristic: core/error/patterns likely .py, config likely .yaml, guide likely .md
            if category in ["core", "error", "patterns", "engine", "aim", "pm"]:
                file_type_stats[".py"]["covered"] += 1
                file_type_stats[".py"]["total"] += 1
            elif category in ["config"]:
                file_type_stats[".yaml"]["covered"] += 1
                file_type_stats[".yaml"]["total"] += 1
            elif category in ["guide", "spec"]:
                file_type_stats[".md"]["covered"] += 1
                file_type_stats[".md"]["total"] += 1
            elif category in ["script"]:
                # Mix of .py and .sh
                file_type_stats[".py"]["covered"] += 1
                file_type_stats[".py"]["total"] += 1

        # Calculate totals
        total_files = len(docs)
        covered_files = len(docs)  # All docs in registry are "covered"
        coverage_pct = (covered_files / total_files * 100) if total_files > 0 else 0.0

        # For uncovered files, would need to scan filesystem and compare
        # For now, return empty list (placeholder)
        uncovered_files = []

        return CoverageMetrics(
            total_files=total_files,
            covered_files=covered_files,
            coverage_percentage=coverage_pct,
            by_category=dict(category_counts),
            by_file_type=file_type_stats,
            uncovered_files=uncovered_files,
        )

    def get_uncovered_files(self, scope_path: Optional[str] = None) -> List[str]:
        """Get list of files without doc_ids.

        Args:
            scope_path: Optional path to limit search

        Returns:
            List of file paths without doc_ids
        """
        # Placeholder - would need filesystem scanning
        # Compare registry entries to actual files on disk
        return []

    def get_category_coverage(self, category: str) -> Dict:
        """Get coverage for specific category.

        Args:
            category: Category name (e.g., "core", "guide")

        Returns:
            Dict with category-specific metrics
        """
        stats = self.get_registry_stats()
        category_info = stats.categories.get(category, {})

        return {
            "category": category,
            "count": category_info.get("count", 0),
            "prefix": category_info.get("prefix", ""),
            "description": category_info.get("description", ""),
        }

    def clear_cache(self):
        """Clear the internal cache to force fresh registry read."""
        self._cache = None


# Convenience function
def create_coverage_client(
    registry_path: Optional[str] = None
) -> DocIdCoverageClient:
    """Factory function to create DocIdCoverageClient.

    Args:
        registry_path: Path to DOC_ID_REGISTRY.yaml

    Returns:
        Configured DocIdCoverageClient instance
    """
    return DocIdCoverageClient(registry_path=registry_path)
