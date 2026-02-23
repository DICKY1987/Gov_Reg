"""
Zone Classifier Module - Directory ID Package v1.0

Provides zone classification and depth computation for directory governance.

**Zone Model**:
- STAGING: depth=0 (project root), no ID enforcement
- GOVERNED: depth≥1, mandatory .dir_id + registry entries
- EXCLUDED: patterns like .git/, __pycache__/, .venv/ - completely ignored

Author: Gov_Reg System
Created: 2026-02-13
File ID: 01999000042260125067
"""

from pathlib import Path
from typing import Literal, List
import re

ZoneType = Literal["staging", "governed", "excluded"]

# Default exclusion patterns
DEFAULT_EXCLUSIONS = [
    ".git/**",
    ".venv/**",
    "**/__pycache__/**",
    "**/node_modules/**",
    "**/htmlcov/**",
    "**/.pytest_cache/**",
    "**/build/**",
    "**/dist/**",
    "**/.state/**",
    "**/evidence/**",
]


def compute_depth(relative_path: str) -> int:
    """
    Compute directory depth from project root.
    
    Args:
        relative_path: Path relative to project root (e.g., "src/module_a")
    
    Returns:
        Depth as integer (0 for root, 1 for immediate child, etc.)
    
    Examples:
        >>> compute_depth(".")
        0
        >>> compute_depth("src")
        1
        >>> compute_depth("src/module_a/submodule_b")
        3
    """
    if relative_path in (".", "", "/"):
        return 0
    
    # Normalize path separators
    normalized = relative_path.replace("\\", "/").strip("/")
    if not normalized:
        return 0
    
    # Count path components
    parts = [p for p in normalized.split("/") if p and p != "."]
    return len(parts)


def matches_exclusion_pattern(relative_path: str, patterns: List[str]) -> bool:
    """
    Check if path matches any exclusion pattern.
    
    Args:
        relative_path: Path relative to project root
        patterns: List of glob patterns (e.g., [".git/**", "**/__pycache__/**"])
    
    Returns:
        True if path matches any exclusion pattern
    
    Examples:
        >>> matches_exclusion_pattern(".git/hooks", [".git/**"])
        True
        >>> matches_exclusion_pattern("src/__pycache__/test.pyc", ["**/__pycache__/**"])
        True
        >>> matches_exclusion_pattern("src/module_a", [".git/**"])
        False
    """
    # Normalize path
    normalized = relative_path.replace("\\", "/")
    
    for pattern in patterns:
        # Convert glob to regex
        regex_pattern = pattern.replace("**", ".*").replace("*", "[^/]*")
        regex_pattern = "^" + regex_pattern + "$"
        
        if re.match(regex_pattern, normalized):
            return True
    
    return False


def compute_zone(
    depth: int,
    relative_path: str,
    exclusions: List[str] | None = None
) -> ZoneType:
    """
    Determine governance zone for a path.
    
    Args:
        depth: Directory depth (from compute_depth)
        relative_path: Path relative to project root
        exclusions: Optional list of exclusion patterns (uses defaults if None)
    
    Returns:
        Zone type: "staging" | "governed" | "excluded"
    
    Rules:
        - depth=0 → staging (no ID enforcement)
        - matches exclusion → excluded (ignored)
        - depth≥1 → governed (mandatory IDs)
    
    Examples:
        >>> compute_zone(0, ".", [])
        'staging'
        >>> compute_zone(1, "src", [])
        'governed'
        >>> compute_zone(2, ".git/hooks", [".git/**"])
        'excluded'
    """
    if exclusions is None:
        exclusions = DEFAULT_EXCLUSIONS
    
    # Check exclusions first (highest priority)
    if matches_exclusion_pattern(relative_path, exclusions):
        return "excluded"
    
    # Depth-based classification
    if depth == 0:
        return "staging"
    else:
        return "governed"


class ZoneClassifier:
    """
    Stateful zone classifier with configurable exclusions.
    
    Usage:
        classifier = ZoneClassifier(project_root=Path("."), exclusions=custom_patterns)
        zone = classifier.classify_path(Path("src/module_a"))
    """
    
    def __init__(
        self,
        project_root: Path,
        exclusions: List[str] | None = None
    ):
        """
        Initialize zone classifier.
        
        Args:
            project_root: Absolute path to project root
            exclusions: Optional list of exclusion patterns
        """
        self.project_root = project_root.resolve()
        self.exclusions = exclusions if exclusions is not None else DEFAULT_EXCLUSIONS
    
    def classify_path(self, abs_path: Path) -> tuple[int, ZoneType]:
        """
        Classify an absolute path.
        
        Args:
            abs_path: Absolute path to classify
        
        Returns:
            Tuple of (depth, zone_type)
        
        Raises:
            ValueError: If abs_path is not under project_root
        """
        abs_path = abs_path.resolve()
        
        try:
            relative = abs_path.relative_to(self.project_root)
        except ValueError:
            raise ValueError(
                f"Path {abs_path} is not under project root {self.project_root}"
            )
        
        relative_str = str(relative).replace("\\", "/")
        depth = compute_depth(relative_str)
        zone = compute_zone(depth, relative_str, self.exclusions)
        
        return depth, zone
    
    def is_governed(self, abs_path: Path) -> bool:
        """Check if path is in governed zone."""
        _, zone = self.classify_path(abs_path)
        return zone == "governed"
    
    def is_excluded(self, abs_path: Path) -> bool:
        """Check if path is excluded."""
        _, zone = self.classify_path(abs_path)
        return zone == "excluded"
    
    def is_staging(self, abs_path: Path) -> bool:
        """Check if path is in staging zone."""
        _, zone = self.classify_path(abs_path)
        return zone == "staging"


if __name__ == "__main__":
    import doctest
    doctest.testmod()
    
    # Example usage
    print("Zone Classifier - Examples")
    print("=" * 40)
    
    classifier = ZoneClassifier(project_root=Path("."))
    
    test_paths = [
        ".",
        "src",
        "src/module_a",
        "src/module_a/submodule_b",
        ".git/hooks",
        ".venv/lib/python3.10",
        "src/__pycache__/test.pyc",
    ]
    
    for path_str in test_paths:
        try:
            depth, zone = classifier.classify_path(Path(path_str))
            print(f"{path_str:40} → depth={depth}, zone={zone}")
        except Exception as e:
            print(f"{path_str:40} → ERROR: {e}")
