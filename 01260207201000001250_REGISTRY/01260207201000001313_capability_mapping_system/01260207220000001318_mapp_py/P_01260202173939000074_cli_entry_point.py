#!/usr/bin/env python3
"""
Canonical Ranker - Phase C Script
Produces: py_canonical_score

Ranks files within similarity clusters to identify canonical versions.
"""
import json
import sys
from pathlib import Path
from typing import List, Dict, Any


def compute_canonical_score(file_metrics: Dict[str, Any]) -> float:
    """
    Compute canonical score (0-100) for a file.

    Higher score = more likely to be the canonical version.

    Scoring factors:
    - Quality score (40%)
    - Documentation completeness (20%)
    - Test coverage (20%)
    - File age/stability (10%) - older = more canonical
    - Fewer dependencies (10%)
    """
    score = 0.0

    # 1. Quality score (40 points)
    quality = file_metrics.get("py_quality_score", 0)
    score += (quality / 100.0) * 40.0

    # 2. Documentation (20 points)
    components = file_metrics.get("py_components_list", [])
    if components:
        with_docs = sum(1 for c in components if c.get("docstring"))
        doc_ratio = with_docs / len(components)
        score += doc_ratio * 20.0

    # 3. Test coverage (20 points)
    coverage = file_metrics.get("py_test_coverage_pct")
    if coverage:
        score += (coverage / 100.0) * 20.0

    # 4. Stability proxy - fewer external deps = more canonical (10 points)
    external_deps = file_metrics.get("py_external_imports_count", 0)
    if external_deps == 0:
        score += 10.0
    elif external_deps < 5:
        score += (1.0 - (external_deps / 5.0)) * 10.0

    # 5. Completeness - has main/interface (10 points)
    deliverable = file_metrics.get("py_deliverable_kind", "")
    if deliverable in ("LIBRARY", "SERVICE"):
        score += 10.0
    elif deliverable in ("SCRIPT",):
        score += 5.0

    return round(score, 2)


def rank_cluster(
    cluster_files: List[str], all_metrics: Dict[str, Dict]
) -> Dict[str, float]:
    """
    Rank all files in a cluster by canonical score.

    Args:
        cluster_files: List of file paths in cluster
        all_metrics: Dict[file_path] = metrics dict

    Returns:
        Dict[file_path] = canonical_score
    """
    rankings = {}

    for file_path in cluster_files:
        metrics = all_metrics.get(file_path, {})
        score = compute_canonical_score(metrics)
        rankings[file_path] = score

    return rankings


def rank_all_clusters(clusters: List[List[str]], metrics_file: Path) -> dict:
    """
    Rank all files within their clusters.

    Returns dict with:
    - file_to_canonical_score: Dict[file_path, score]
    - cluster_rankings: Dict[cluster_id, List[(file, score)]]
    - success: bool
    - error: Optional[str]
    """
    try:
        # Load all metrics
        all_metrics = json.loads(metrics_file.read_text())

        file_scores = {}
        cluster_rankings = {}

        for i, cluster in enumerate(clusters):
            cluster_id = f"cluster_{i}"

            # Rank this cluster
            rankings = rank_cluster(cluster, all_metrics)

            # Store scores
            file_scores.update(rankings)

            # Store sorted cluster rankings
            sorted_rankings = sorted(rankings.items(), key=lambda x: x[1], reverse=True)
            cluster_rankings[cluster_id] = sorted_rankings

        return {
            "file_to_canonical_score": file_scores,
            "cluster_rankings": cluster_rankings,
            "success": True,
            "error": None,
        }

    except Exception as e:
        return {
            "file_to_canonical_score": {},
            "cluster_rankings": {},
            "success": False,
            "error": f"Canonical ranking failed: {e}",
        }


def main():
    """CLI entry point."""
    if len(sys.argv) < 3:
        print(
            "Usage: canonical_ranker.py <clusters.json> <all_metrics.json>",
            file=sys.stderr,
        )
        sys.exit(1)

    clusters_file = Path(sys.argv[1])
    metrics_file = Path(sys.argv[2])

    if not clusters_file.exists():
        print(f"Error: Clusters file not found: {clusters_file}", file=sys.stderr)
        sys.exit(1)

    if not metrics_file.exists():
        print(f"Error: Metrics file not found: {metrics_file}", file=sys.stderr)
        sys.exit(1)

    # Load clusters
    clusters = json.loads(clusters_file.read_text())

    result = rank_all_clusters(clusters, metrics_file)

    if result["success"]:
        print("Canonical rankings by cluster:")
        for cluster_id, rankings in result["cluster_rankings"].items():
            print(f"\n{cluster_id}:")
            for file_path, score in rankings[:3]:  # Top 3
                print(f"  {score:6.2f} - {file_path}")
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
