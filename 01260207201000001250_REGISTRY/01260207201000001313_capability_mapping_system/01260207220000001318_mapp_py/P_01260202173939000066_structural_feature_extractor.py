#!/usr/bin/env python3
"""
Structural Similarity Analyzer - Phase B Script
Produces: py_structural_similarity_scores (per-file structural overlap)

Compares AST structure between files to detect similar code patterns.
"""
import ast
import hashlib
import json
import sys
from pathlib import Path
from typing import List, Dict, Set, Any, Tuple


class StructuralFeatureExtractor(ast.NodeVisitor):
    """Extract structural features from AST."""

    def __init__(self):
        self.node_types = []
        self.depth_histogram = {}
        self.control_flow_patterns = []
        self.current_depth = 0

    def generic_visit(self, node: ast.AST):
        """Track node types and depth."""
        node_type = type(node).__name__
        self.node_types.append(node_type)

        # Track depth histogram
        self.depth_histogram[self.current_depth] = (
            self.depth_histogram.get(self.current_depth, 0) + 1
        )

        # Track control flow patterns
        if isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
            self.control_flow_patterns.append(
                {"type": node_type, "depth": self.current_depth}
            )

        self.current_depth += 1
        super().generic_visit(node)
        self.current_depth -= 1

    def get_features(self) -> Dict[str, Any]:
        """Get extracted structural features."""
        from collections import Counter

        node_freq = Counter(self.node_types)

        return {
            "node_type_counts": dict(node_freq),
            "total_nodes": len(self.node_types),
            "depth_histogram": self.depth_histogram,
            "max_depth": max(self.depth_histogram.keys())
            if self.depth_histogram
            else 0,
            "control_flow_patterns": self.control_flow_patterns,
            "control_flow_count": len(self.control_flow_patterns),
        }


def extract_structural_features(file_path: Path) -> Dict[str, Any]:
    """Extract structural features from a Python file."""
    try:
        source_text = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source_text, filename=str(file_path))

        extractor = StructuralFeatureExtractor()
        extractor.visit(tree)

        return extractor.get_features()

    except Exception as e:
        return {
            "error": str(e),
            "node_type_counts": {},
            "total_nodes": 0,
            "depth_histogram": {},
            "max_depth": 0,
            "control_flow_patterns": [],
            "control_flow_count": 0,
        }


def compute_jaccard_similarity(set1: Set, set2: Set) -> float:
    """Compute Jaccard similarity between two sets."""
    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0

    intersection = len(set1 & set2)
    union = len(set1 | set2)

    return intersection / union if union > 0 else 0.0


def compute_structural_similarity(features1: Dict, features2: Dict) -> float:
    """
    Compute structural similarity score between two files.

    Combines:
    - Node type distribution similarity (40%)
    - Depth histogram similarity (30%)
    - Control flow pattern similarity (30%)
    """
    # Node type similarity
    nodes1 = set(features1.get("node_type_counts", {}).keys())
    nodes2 = set(features2.get("node_type_counts", {}).keys())
    node_sim = compute_jaccard_similarity(nodes1, nodes2)

    # Depth similarity (compare max depths)
    depth1 = features1.get("max_depth", 0)
    depth2 = features2.get("max_depth", 0)
    max_depth = max(depth1, depth2)
    depth_sim = 1.0 - (abs(depth1 - depth2) / max_depth) if max_depth > 0 else 1.0

    # Control flow similarity
    cf1 = set(p["type"] for p in features1.get("control_flow_patterns", []))
    cf2 = set(p["type"] for p in features2.get("control_flow_patterns", []))
    cf_sim = compute_jaccard_similarity(cf1, cf2)

    # Weighted average
    total_sim = (node_sim * 0.4) + (depth_sim * 0.3) + (cf_sim * 0.3)

    return round(total_sim, 4)


def analyze_structural_similarity(
    target_file: Path, candidate_files: List[Path]
) -> dict:
    """
    Analyze structural similarity between target file and candidates.

    Returns dict with:
    - py_structural_similarity_scores: Dict[file_path, score]
    - py_structural_similarity_max: float
    - py_structural_similarity_max_file: str
    - success: bool
    - error: Optional[str]
    """
    try:
        # Extract features from target
        target_features = extract_structural_features(target_file)

        if "error" in target_features:
            raise Exception(
                f"Failed to extract target features: {target_features['error']}"
            )

        scores = {}
        max_score = 0.0
        max_file = None

        # Compare with each candidate
        for candidate in candidate_files:
            if candidate == target_file:
                continue

            candidate_features = extract_structural_features(candidate)

            if "error" not in candidate_features:
                score = compute_structural_similarity(
                    target_features, candidate_features
                )
                scores[str(candidate)] = score

                if score > max_score:
                    max_score = score
                    max_file = str(candidate)

        return {
            "py_structural_similarity_scores": scores,
            "py_structural_similarity_max": max_score,
            "py_structural_similarity_max_file": max_file,
            "success": True,
            "error": None,
        }

    except Exception as e:
        return {
            "py_structural_similarity_scores": {},
            "py_structural_similarity_max": 0.0,
            "py_structural_similarity_max_file": None,
            "success": False,
            "error": f"Structural similarity analysis failed: {e}",
        }


def main():
    """CLI entry point."""
    if len(sys.argv) < 3:
        print(
            "Usage: structural_similarity.py <target_file> <candidate_file1> [candidate_file2 ...]",
            file=sys.stderr,
        )
        sys.exit(1)

    target_file = Path(sys.argv[1])
    candidate_files = [Path(f) for f in sys.argv[2:]]

    if not target_file.exists():
        print(f"Error: Target file not found: {target_file}", file=sys.stderr)
        sys.exit(1)

    result = analyze_structural_similarity(target_file, candidate_files)

    if result["success"]:
        print(f"Max similarity: {result['py_structural_similarity_max']}")
        print(f"Most similar file: {result['py_structural_similarity_max_file']}")
        print(
            f"\nAll scores: {json.dumps(result['py_structural_similarity_scores'], indent=2)}"
        )
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
