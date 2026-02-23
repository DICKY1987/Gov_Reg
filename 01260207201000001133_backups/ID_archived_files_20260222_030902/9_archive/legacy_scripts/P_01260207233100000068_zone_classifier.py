"""Zone classifier for directory governance system.

FILE_ID: 01260207233100000068
PURPOSE: Classify directories into zones (staging/governed/excluded) based on depth and patterns
PHASE: PH-02A Foundation
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Literal
from dataclasses import dataclass

ZoneType = Literal["staging", "governed", "excluded"]

DEFAULT_EXCLUSIONS = [
    ".git/**",
    ".venv/**",
    "**/__pycache__/**",
    "**/node_modules/**",
    "**/build/**",
    "**/dist/**",
    "**/.pytest_cache/**",
    "**/.mypy_cache/**",
    "**/.ruff_cache/**",
    "**/venv/**",
    "**/env/**",
]


@dataclass
class ZoneClassification:
    """Result of zone classification."""
    zone: ZoneType
    depth: int
    relative_path: str
    is_excluded: bool
    matched_exclusion: str | None


class ZoneClassifier:
    """Classifies directories into governance zones.
    
    Zones:
        - staging: depth=0 (project root), minimal governance
        - governed: depth>=1, mandatory .dir_id and registry
        - excluded: matches exclusion patterns, no governance
    """
    
    def __init__(self, exclusions: List[str] | None = None):
        """Initialize classifier.
        
        Args:
            exclusions: List of glob patterns for excluded paths
        """
        self.exclusions = exclusions or DEFAULT_EXCLUSIONS
    
    def compute_depth(self, relative_path: str) -> int:
        """Compute directory depth in tree.
        
        Args:
            relative_path: Path relative to project root (forward slashes)
            
        Returns:
            int: Depth (0=root, 1=immediate child, etc.)
            
        Examples:
            >>> compute_depth("src")
            1
            >>> compute_depth("src/module_a")
            2
            >>> compute_depth("src/module_a/submodule_b")
            3
        """
        if not relative_path or relative_path == ".":
            return 0
        
        # Normalize path separators to forward slash
        normalized = relative_path.replace("\\", "/")
        
        # Count path segments
        parts = [p for p in normalized.split("/") if p and p != "."]
        return len(parts)
    
    def matches_exclusion(self, relative_path: str) -> tuple[bool, str | None]:
        """Check if path matches any exclusion pattern.
        
        Args:
            relative_path: Path relative to project root
            
        Returns:
            tuple: (is_excluded, matched_pattern)
        """
        normalized = relative_path.replace("\\", "/")
        path_with_slashes = f"/{normalized}/"
        
        for pattern in self.exclusions:
            # Handle ** globstar patterns
            if "**" in pattern:
                # Extract the meaningful part between ** markers
                # E.g., "**/__pycache__/**" -> extract "__pycache__"
                #       ".git/**" -> extract ".git"
                #       "**/build/**" -> extract "build"
                
                # Strip ** and slashes to get the component to match
                component = pattern.replace("**", "").strip("/")
                
                if component:
                    # Check if this component appears in the path
                    if f"/{component}/" in path_with_slashes or normalized.startswith(component + "/") or normalized == component:
                        return True, pattern
                else:
                    # Pattern is all **, shouldn't happen but handle gracefully
                    continue
            else:
                # Simple pattern without globstar
                pattern_clean = pattern.strip("/")
                
                # Exact match or prefix match
                if normalized == pattern_clean or normalized.startswith(pattern_clean + "/"):
                    return True, pattern
                
                # Check if pattern is a path component
                if f"/{pattern_clean}/" in path_with_slashes:
                    return True, pattern
        
        return False, None
    
    def compute_zone(self, relative_path: str, depth: int | None = None) -> ZoneType:
        """Compute governance zone for a directory.
        
        Args:
            relative_path: Path relative to project root
            depth: Optional pre-computed depth (will compute if None)
            
        Returns:
            ZoneType: Zone classification
            
        Logic:
            1. If matches exclusion pattern → excluded
            2. If depth=0 → staging
            3. If depth>=1 → governed
        """
        # Check exclusions first
        is_excluded, _ = self.matches_exclusion(relative_path)
        if is_excluded:
            return "excluded"
        
        # Compute depth if not provided
        if depth is None:
            depth = self.compute_depth(relative_path)
        
        # Zone based on depth
        if depth == 0:
            return "staging"
        else:
            return "governed"
    
    def classify(self, relative_path: str) -> ZoneClassification:
        """Classify a directory into a zone.
        
        Args:
            relative_path: Path relative to project root
            
        Returns:
            ZoneClassification: Complete classification result
        """
        depth = self.compute_depth(relative_path)
        is_excluded, matched_exclusion = self.matches_exclusion(relative_path)
        
        if is_excluded:
            zone = "excluded"
        elif depth == 0:
            zone = "staging"
        else:
            zone = "governed"
        
        return ZoneClassification(
            zone=zone,
            depth=depth,
            relative_path=relative_path,
            is_excluded=is_excluded,
            matched_exclusion=matched_exclusion
        )
    
    def is_governed(self, relative_path: str) -> bool:
        """Check if path should be governed (requires .dir_id).
        
        Args:
            relative_path: Path relative to project root
            
        Returns:
            bool: True if governed zone
        """
        zone = self.compute_zone(relative_path)
        return zone == "governed"
    
    def should_skip(self, relative_path: str) -> bool:
        """Check if path should be completely skipped (excluded zone).
        
        Args:
            relative_path: Path relative to project root
            
        Returns:
            bool: True if excluded zone
        """
        zone = self.compute_zone(relative_path)
        return zone == "excluded"


def create_default_classifier() -> ZoneClassifier:
    """Create classifier with default exclusions.
    
    Returns:
        ZoneClassifier: Ready-to-use classifier
    """
    return ZoneClassifier()


# Module-level singleton for convenience
_default_classifier = None

def get_classifier() -> ZoneClassifier:
    """Get or create default classifier singleton.
    
    Returns:
        ZoneClassifier: Default classifier instance
    """
    global _default_classifier
    if _default_classifier is None:
        _default_classifier = create_default_classifier()
    return _default_classifier


# Convenience functions
def compute_depth(relative_path: str) -> int:
    """Compute directory depth (convenience wrapper)."""
    return get_classifier().compute_depth(relative_path)


def compute_zone(relative_path: str) -> ZoneType:
    """Compute zone (convenience wrapper)."""
    return get_classifier().compute_zone(relative_path)


def is_governed(relative_path: str) -> bool:
    """Check if governed (convenience wrapper)."""
    return get_classifier().is_governed(relative_path)


def should_skip(relative_path: str) -> bool:
    """Check if excluded (convenience wrapper)."""
    return get_classifier().should_skip(relative_path)


if __name__ == "__main__":
    # Quick test
    classifier = create_default_classifier()
    
    test_paths = [
        ".",
        "src",
        "src/module_a",
        "src/module_a/submodule_b",
        ".git",
        ".git/hooks",
        ".venv/lib/python3.10",
        "__pycache__",
        "src/__pycache__",
        "node_modules",
        "build",
    ]
    
    print("Zone Classification Tests:")
    print("-" * 60)
    for path in test_paths:
        result = classifier.classify(path)
        print(f"{path:30s} → {result.zone:10s} (depth={result.depth})")
