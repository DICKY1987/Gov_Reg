#!/usr/bin/env python3
"""
File Comparator - Phase B Script
Produces: py_overlap_similarity_max, py_overlap_best_match_file_id

Orchestrates both structural and semantic similarity to find best matches.
"""
import json
import sys
from pathlib import Path
from typing import List, Dict, Any


def load_similarity_scores(
    structural_file: Path, semantic_file: Path
) -> Dict[str, Any]:
    """Load pre-computed similarity scores from JSON files."""
    try:
        structural_scores = (
            json.loads(structural_file.read_text()) if structural_file.exists() else {}
        )
        semantic_scores = (
            json.loads(semantic_file.read_text()) if semantic_file.exists() else {}
        )

        return {"structural": structural_scores, "semantic": semantic_scores}
    except Exception as e:
        return {
            "error": f"Failed to load scores: {e}",
            "structural": {},
            "semantic": {},
        }


def compute_combined_similarity(
    structural_score: float, semantic_score: float
) -> float:
    """
    Combine structural and semantic similarity scores.

    Uses weighted average:
    - Structural: 40%
    - Semantic: 60%
    """
    return round((structural_score * 0.4) + (semantic_score * 0.6), 4)


def find_best_match(
    structural_scores: Dict[str, float], semantic_scores: Dict[str, float]
) -> dict:
    """
    Find the best matching file based on combined similarity.

    Returns dict with:
    - py_overlap_similarity_max: float
    - py_overlap_best_match_file_id: str
    - py_overlap_best_match_file_path: str
    - combined_scores: Dict[file, score]
    """
    # Get all candidate files
    all_files = set(structural_scores.keys()) | set(semantic_scores.keys())

    combined_scores = {}
    max_score = 0.0
    best_file = None

    for file_path in all_files:
        struct_score = structural_scores.get(file_path, 0.0)
        sem_score = semantic_scores.get(file_path, 0.0)

        combined = compute_combined_similarity(struct_score, sem_score)
        combined_scores[file_path] = combined

        if combined > max_score:
            max_score = combined
            best_file = file_path

    return {
        "py_overlap_similarity_max": max_score,
        "py_overlap_best_match_file_path": best_file,
        "combined_scores": combined_scores,
    }


def compare_files(
    target_file: Path, structural_scores_file: Path, semantic_scores_file: Path
) -> dict:
    """
    Compare target file with candidates and find best match.

    Returns dict with:
    - py_overlap_similarity_max: float
    - py_overlap_best_match_file_path: str
    - combined_scores: Dict
    - success: bool
    - error: Optional[str]
    """
    try:
        # Load pre-computed scores
        scores = load_similarity_scores(structural_scores_file, semantic_scores_file)

        if "error" in scores:
            raise Exception(scores["error"])

        structural = scores.get("structural", {})
        semantic = scores.get("semantic", {})

        # Find best match
        result = find_best_match(structural, semantic)

        return {**result, "success": True, "error": None}

    except Exception as e:
        return {
            "py_overlap_similarity_max": 0.0,
            "py_overlap_best_match_file_path": None,
            "combined_scores": {},
            "success": False,
            "error": f"File comparison failed: {e}",
        }


def main():
    """CLI entry point."""
    if len(sys.argv) < 4:
        print(
            "Usage: file_comparator.py <target_file> <structural_scores.json> <semantic_scores.json>",
            file=sys.stderr,
        )
        sys.exit(1)

    target_file = Path(sys.argv[1])
    structural_file = Path(sys.argv[2])
    semantic_file = Path(sys.argv[3])

    if not target_file.exists():
        print(f"Error: Target file not found: {target_file}", file=sys.stderr)
        sys.exit(1)

    result = compare_files(target_file, structural_file, semantic_file)

    if result["success"]:
        print(f"Max similarity: {result['py_overlap_similarity_max']}")
        print(f"Best match: {result['py_overlap_best_match_file_path']}")
        print(
            f"\nAll combined scores: {json.dumps(result['combined_scores'], indent=2)}"
        )
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
