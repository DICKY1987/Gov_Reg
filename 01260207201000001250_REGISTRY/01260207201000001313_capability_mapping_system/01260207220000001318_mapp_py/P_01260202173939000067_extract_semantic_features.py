#!/usr/bin/env python3
"""
Semantic Similarity Analyzer - Phase B Script
Produces: py_semantic_similarity_scores (per-file semantic overlap)

Compares semantic content between files using token-based analysis.
"""
import hashlib
import json
import sys
from pathlib import Path
from typing import List, Dict, Set, Any
from collections import Counter
import re


def tokenize_identifiers(source_text: str) -> List[str]:
    """Extract all identifiers (variable/function/class names) from source."""
    # Simple regex-based tokenization
    # Matches Python identifiers
    pattern = r"\b[a-zA-Z_][a-zA-Z0-9_]*\b"
    tokens = re.findall(pattern, source_text)

    # Filter out Python keywords
    keywords = {
        "False",
        "None",
        "True",
        "and",
        "as",
        "assert",
        "async",
        "await",
        "break",
        "class",
        "continue",
        "def",
        "del",
        "elif",
        "else",
        "except",
        "finally",
        "for",
        "from",
        "global",
        "if",
        "import",
        "in",
        "is",
        "lambda",
        "nonlocal",
        "not",
        "or",
        "pass",
        "raise",
        "return",
        "try",
        "while",
        "with",
        "yield",
    }

    return [t for t in tokens if t not in keywords]


def extract_semantic_features(file_path: Path) -> Dict[str, Any]:
    """Extract semantic features from a Python file."""
    try:
        source_text = file_path.read_text(encoding="utf-8")

        # Tokenize identifiers
        tokens = tokenize_identifiers(source_text)
        token_freq = Counter(tokens)

        # Extract unique identifiers
        unique_identifiers = set(tokens)

        # Extract string literals (simple pattern)
        string_pattern = r'["\']([^"\'\\]*(?:\\.[^"\'\\]*)*)["\']'
        strings = re.findall(string_pattern, source_text)
        unique_strings = set(strings)

        # Extract comments
        comment_pattern = r"#.*$"
        comments = re.findall(comment_pattern, source_text, re.MULTILINE)

        return {
            "tokens": tokens,
            "token_frequencies": dict(token_freq),
            "unique_identifiers": unique_identifiers,
            "unique_strings": unique_strings,
            "comments": comments,
            "total_tokens": len(tokens),
            "unique_token_count": len(unique_identifiers),
        }

    except Exception as e:
        return {
            "error": str(e),
            "tokens": [],
            "token_frequencies": {},
            "unique_identifiers": set(),
            "unique_strings": set(),
            "comments": [],
            "total_tokens": 0,
            "unique_token_count": 0,
        }


def compute_cosine_similarity(freq1: Dict[str, int], freq2: Dict[str, int]) -> float:
    """Compute cosine similarity between two token frequency distributions."""
    if not freq1 or not freq2:
        return 0.0

    # Get all tokens
    all_tokens = set(freq1.keys()) | set(freq2.keys())

    # Compute dot product and magnitudes
    dot_product = sum(freq1.get(t, 0) * freq2.get(t, 0) for t in all_tokens)

    mag1 = sum(v**2 for v in freq1.values()) ** 0.5
    mag2 = sum(v**2 for v in freq2.values()) ** 0.5

    if mag1 == 0 or mag2 == 0:
        return 0.0

    return dot_product / (mag1 * mag2)


def compute_jaccard_similarity(set1: Set, set2: Set) -> float:
    """Compute Jaccard similarity between two sets."""
    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0

    intersection = len(set1 & set2)
    union = len(set1 | set2)

    return intersection / union if union > 0 else 0.0


def compute_semantic_similarity(features1: Dict, features2: Dict) -> float:
    """
    Compute semantic similarity score between two files.

    Combines:
    - Token frequency similarity (cosine) (50%)
    - Unique identifier overlap (Jaccard) (30%)
    - String literal overlap (Jaccard) (20%)
    """
    # Token frequency similarity
    freq1 = features1.get("token_frequencies", {})
    freq2 = features2.get("token_frequencies", {})
    token_sim = compute_cosine_similarity(freq1, freq2)

    # Identifier overlap
    ids1 = features1.get("unique_identifiers", set())
    ids2 = features2.get("unique_identifiers", set())
    id_sim = compute_jaccard_similarity(ids1, ids2)

    # String literal overlap
    strs1 = features1.get("unique_strings", set())
    strs2 = features2.get("unique_strings", set())
    str_sim = compute_jaccard_similarity(strs1, strs2)

    # Weighted average
    total_sim = (token_sim * 0.5) + (id_sim * 0.3) + (str_sim * 0.2)

    return round(total_sim, 4)


def analyze_semantic_similarity(target_file: Path, candidate_files: List[Path]) -> dict:
    """
    Analyze semantic similarity between target file and candidates.

    Returns dict with:
    - py_semantic_similarity_scores: Dict[file_path, score]
    - py_semantic_similarity_max: float
    - py_semantic_similarity_max_file: str
    - success: bool
    - error: Optional[str]
    """
    try:
        # Extract features from target
        target_features = extract_semantic_features(target_file)

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

            candidate_features = extract_semantic_features(candidate)

            if "error" not in candidate_features:
                score = compute_semantic_similarity(target_features, candidate_features)
                scores[str(candidate)] = score

                if score > max_score:
                    max_score = score
                    max_file = str(candidate)

        return {
            "py_semantic_similarity_scores": scores,
            "py_semantic_similarity_max": max_score,
            "py_semantic_similarity_max_file": max_file,
            "success": True,
            "error": None,
        }

    except Exception as e:
        return {
            "py_semantic_similarity_scores": {},
            "py_semantic_similarity_max": 0.0,
            "py_semantic_similarity_max_file": None,
            "success": False,
            "error": f"Semantic similarity analysis failed: {e}",
        }


def main():
    """CLI entry point."""
    if len(sys.argv) < 3:
        print(
            "Usage: semantic_similarity.py <target_file> <candidate_file1> [candidate_file2 ...]",
            file=sys.stderr,
        )
        sys.exit(1)

    target_file = Path(sys.argv[1])
    candidate_files = [Path(f) for f in sys.argv[2:]]

    if not target_file.exists():
        print(f"Error: Target file not found: {target_file}", file=sys.stderr)
        sys.exit(1)

    result = analyze_semantic_similarity(target_file, candidate_files)

    if result["success"]:
        print(f"Max similarity: {result['py_semantic_similarity_max']}")
        print(f"Most similar file: {result['py_semantic_similarity_max_file']}")
        print(
            f"\nAll scores: {json.dumps(result['py_semantic_similarity_scores'], indent=2)}"
        )
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
