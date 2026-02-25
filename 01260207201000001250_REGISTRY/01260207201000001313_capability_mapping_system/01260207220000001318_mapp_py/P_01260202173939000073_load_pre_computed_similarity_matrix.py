#!/usr/bin/env python3
"""
Similarity Clusterer - Phase C Script
Produces: py_overlap_group_id

Groups similar files into clusters for deduplication.
"""
import hashlib
import json
import sys
from pathlib import Path
from typing import List, Dict, Set, Any


def load_similarity_matrix(matrix_file: Path) -> Dict[str, Dict[str, float]]:
    """Load pre-computed similarity matrix."""
    try:
        return json.loads(matrix_file.read_text())
    except Exception as e:
        raise Exception(f"Failed to load similarity matrix: {e}")


def cluster_by_threshold(
    similarity_matrix: Dict[str, Dict[str, float]], threshold: float = 0.7
) -> List[Set[str]]:
    """
    Cluster files by similarity threshold using simple connected components.

    Args:
        similarity_matrix: Dict[file1][file2] = similarity_score
        threshold: Minimum similarity to consider files related (default 0.7)

    Returns:
        List of clusters (sets of file paths)
    """
    # Build adjacency list
    adjacency = {}
    for file1, similarities in similarity_matrix.items():
        if file1 not in adjacency:
            adjacency[file1] = set()

        for file2, score in similarities.items():
            if score >= threshold:
                adjacency[file1].add(file2)
                if file2 not in adjacency:
                    adjacency[file2] = set()
                adjacency[file2].add(file1)

    # Find connected components (clusters)
    visited = set()
    clusters = []

    def dfs(node: str, cluster: Set[str]):
        """Depth-first search to find cluster."""
        if node in visited:
            return
        visited.add(node)
        cluster.add(node)

        for neighbor in adjacency.get(node, set()):
            dfs(neighbor, cluster)

    # Visit all nodes
    for file_path in adjacency.keys():
        if file_path not in visited:
            cluster = set()
            dfs(file_path, cluster)
            if cluster:
                clusters.append(cluster)

    return clusters


def assign_cluster_ids(clusters: List[Set[str]]) -> Dict[str, str]:
    """
    Assign stable cluster IDs to each file.

    Cluster ID is hash of sorted file paths in cluster.
    """
    file_to_cluster = {}

    for cluster in clusters:
        # Sort files for deterministic ordering
        sorted_files = sorted(cluster)

        # Hash the cluster membership
        cluster_str = "|".join(sorted_files)
        cluster_id = hashlib.sha256(cluster_str.encode("utf-8")).hexdigest()[:16]

        # Assign to all files in cluster
        for file_path in cluster:
            file_to_cluster[file_path] = cluster_id

    return file_to_cluster


def cluster_files(similarity_matrix_file: Path, threshold: float = 0.7) -> dict:
    """
    Cluster similar files and assign group IDs.

    Returns dict with:
    - clusters: List[Set[str]] (list of clusters)
    - file_to_cluster: Dict[file_path, cluster_id]
    - cluster_count: int
    - success: bool
    - error: Optional[str]
    """
    try:
        # Load similarity matrix
        similarity_matrix = load_similarity_matrix(similarity_matrix_file)

        # Cluster files
        clusters = cluster_by_threshold(similarity_matrix, threshold)

        # Assign cluster IDs
        file_to_cluster = assign_cluster_ids(clusters)

        return {
            "clusters": [list(c) for c in clusters],  # Convert sets to lists for JSON
            "file_to_cluster": file_to_cluster,
            "cluster_count": len(clusters),
            "success": True,
            "error": None,
        }

    except Exception as e:
        return {
            "clusters": [],
            "file_to_cluster": {},
            "cluster_count": 0,
            "success": False,
            "error": f"Clustering failed: {e}",
        }


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print(
            "Usage: similarity_clusterer.py <similarity_matrix.json> [threshold]",
            file=sys.stderr,
        )
        print("  threshold: 0.0-1.0, default 0.7", file=sys.stderr)
        sys.exit(1)

    matrix_file = Path(sys.argv[1])
    threshold = float(sys.argv[2]) if len(sys.argv) > 2 else 0.7

    if not matrix_file.exists():
        print(f"Error: Similarity matrix not found: {matrix_file}", file=sys.stderr)
        sys.exit(1)

    result = cluster_files(matrix_file, threshold)

    if result["success"]:
        print(f"Found {result['cluster_count']} clusters")
        print(
            f"\nCluster assignments: {json.dumps(result['file_to_cluster'], indent=2)}"
        )
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
