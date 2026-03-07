# DOC_LINK: DOC-CORE-GRAPH-INDEX-710
"""
Graph Index - In-Memory Queryable Graph

Loads relationship index into memory as a directed graph with adjacency lists
for efficient querying.

Features:
- O(1) lookup for direct dependencies/dependents
- DFS/BFS for transitive queries
- Cycle detection
- Impact analysis
"""
# DOC_ID: DOC-CORE-GRAPH-INDEX-710

from pathlib import Path
from typing import List, Dict, Set, Optional, Any
from collections import defaultdict, deque
import json


class GraphIndex:
    """
    In-memory graph representation of relationship index.

    Provides efficient querying via adjacency lists:
    - forward[node] = [edges where node is source]
    - reverse[node] = [edges where node is target]

    Supports:
    - Dependency queries (what this depends on)
    - Dependent queries (what depends on this)
    - Transitive closure
    - Cycle detection
    - Path finding
    """

    def __init__(self, index_path: Path):
        """
        Load relationship index and build graph structures.

        Args:
            index_path: Path to RELATIONSHIP_INDEX.json
        """
        self.index_path = index_path

        # Core data structures
        self.nodes: Dict[str, Dict[str, Any]] = {}  # doc_id -> node metadata
        self.edges: List[Dict[str, Any]] = []       # All edges

        # Adjacency lists for fast lookups
        self.forward: Dict[str, List[Dict]] = defaultdict(list)  # source -> [edges]
        self.reverse: Dict[str, List[Dict]] = defaultdict(list)  # target -> [edges]

        # Load and build
        self._load_index()
        self._build_adjacency_lists()

    def _load_index(self):
        """Load relationship index from JSON file."""
        print(f"Loading index from {self.index_path}...")

        with open(self.index_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Load nodes
        for node in data.get("nodes", []):
            doc_id = node["doc_id"]
            self.nodes[doc_id] = node

        # Load edges
        self.edges = data.get("edges", [])

        print(f"✓ Loaded {len(self.nodes)} nodes, {len(self.edges)} edges")

    def _build_adjacency_lists(self):
        """Build forward and reverse adjacency lists for fast lookups."""
        print("Building adjacency lists...")

        for edge in self.edges:
            source = edge["source"]
            target = edge["target"]

            # Forward: source -> targets
            self.forward[source].append(edge)

            # Reverse: target <- sources
            self.reverse[target].append(edge)

        print(f"✓ Built adjacency lists ({len(self.forward)} sources, {len(self.reverse)} targets)")

    def get_dependencies(self,
                        doc_id: str,
                        edge_type: Optional[str] = None,
                        transitive: bool = False,
                        max_depth: Optional[int] = None) -> List[str]:
        """
        Find what this doc_id depends on.

        Args:
            doc_id: Source document ID
            edge_type: Filter by edge type (imports, documents, etc.)
            transitive: Include recursive dependencies
            max_depth: Max depth for transitive search (None = unlimited)

        Returns:
            List of doc_ids this document depends on
        """
        if doc_id not in self.nodes:
            return []

        if not transitive:
            # Direct dependencies only
            edges = self.forward.get(doc_id, [])
            if edge_type:
                edges = [e for e in edges if e["type"] == edge_type]
            return [e["target"] for e in edges]

        # Transitive dependencies (DFS)
        visited = set()
        result = []

        def dfs(current: str, depth: int):
            if max_depth is not None and depth > max_depth:
                return

            for edge in self.forward.get(current, []):
                if edge_type and edge["type"] != edge_type:
                    continue

                target = edge["target"]
                if target not in visited:
                    visited.add(target)
                    result.append(target)
                    dfs(target, depth + 1)

        dfs(doc_id, 0)
        return result

    def get_dependents(self,
                      doc_id: str,
                      edge_type: Optional[str] = None,
                      transitive: bool = False,
                      max_depth: Optional[int] = None) -> List[str]:
        """
        Find what depends on this doc_id (reverse lookup).

        Args:
            doc_id: Target document ID
            edge_type: Filter by edge type
            transitive: Include recursive dependents
            max_depth: Max depth for transitive search

        Returns:
            List of doc_ids that depend on this document
        """
        if doc_id not in self.nodes:
            return []

        if not transitive:
            # Direct dependents only
            edges = self.reverse.get(doc_id, [])
            if edge_type:
                edges = [e for e in edges if e["type"] == edge_type]
            return [e["source"] for e in edges]

        # Transitive dependents (DFS on reverse graph)
        visited = set()
        result = []

        def dfs(current: str, depth: int):
            if max_depth is not None and depth > max_depth:
                return

            for edge in self.reverse.get(current, []):
                if edge_type and edge["type"] != edge_type:
                    continue

                source = edge["source"]
                if source not in visited:
                    visited.add(source)
                    result.append(source)
                    dfs(source, depth + 1)

        dfs(doc_id, 0)
        return result

    def find_path(self, source: str, target: str) -> Optional[List[str]]:
        """
        Find shortest path from source to target using BFS.

        Args:
            source: Starting doc_id
            target: Target doc_id

        Returns:
            List of doc_ids forming path, or None if no path exists
        """
        if source not in self.nodes or target not in self.nodes:
            return None

        if source == target:
            return [source]

        # BFS with path tracking
        queue = deque([(source, [source])])
        visited = {source}

        while queue:
            current, path = queue.popleft()

            for edge in self.forward.get(current, []):
                next_node = edge["target"]

                if next_node == target:
                    return path + [next_node]

                if next_node not in visited:
                    visited.add(next_node)
                    queue.append((next_node, path + [next_node]))

        return None  # No path found

    def find_cycles(self) -> List[List[str]]:
        """
        Detect circular dependencies using DFS.

        Returns:
            List of cycles, each cycle is a list of doc_ids
        """
        cycles = []
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node: str):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for edge in self.forward.get(node, []):
                neighbor = edge["target"]

                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)

            path.pop()
            rec_stack.remove(node)

        # Check all nodes (graph might be disconnected)
        for node in self.nodes:
            if node not in visited:
                dfs(node)

        return cycles

    def impact_analysis(self, doc_id: str, max_depth: int = 3) -> Dict[str, Any]:
        """
        Analyze impact of changing this doc_id.

        Args:
            doc_id: Document to analyze
            max_depth: Max depth for transitive analysis

        Returns:
            {
                "doc_id": "...",
                "direct_dependents": [...],
                "transitive_dependents": [...],
                "total_impact": N,
                "depth_distribution": {1: 5, 2: 10, 3: 3},
                "risk_level": "high|medium|low"
            }
        """
        if doc_id not in self.nodes:
            return {
                "error": f"doc_id '{doc_id}' not found",
                "total_impact": 0
            }

        direct = self.get_dependents(doc_id, transitive=False)
        transitive = self.get_dependents(doc_id, transitive=True, max_depth=max_depth)

        # Calculate depth distribution
        depth_dist = defaultdict(int)
        visited = {doc_id: 0}
        queue = deque([(doc_id, 0)])

        while queue:
            current, depth = queue.popleft()
            if depth >= max_depth:
                continue

            for edge in self.reverse.get(current, []):
                dependent = edge["source"]
                if dependent not in visited:
                    visited[dependent] = depth + 1
                    depth_dist[depth + 1] += 1
                    queue.append((dependent, depth + 1))

        total = len(transitive)

        # Risk assessment
        if total > 50:
            risk = "high"
        elif total > 10:
            risk = "medium"
        else:
            risk = "low"

        return {
            "doc_id": doc_id,
            "direct_dependents": direct,
            "transitive_dependents": transitive,
            "total_impact": total,
            "depth_distribution": dict(depth_dist),
            "risk_level": risk
        }

    def get_node_info(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a node."""
        return self.nodes.get(doc_id)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get graph statistics.

        Returns:
            {
                "total_nodes": N,
                "total_edges": M,
                "avg_out_degree": X,
                "avg_in_degree": Y,
                "isolated_nodes": [...]
            }
        """
        total_nodes = len(self.nodes)
        total_edges = len(self.edges)

        out_degrees = [len(self.forward.get(n, [])) for n in self.nodes]
        in_degrees = [len(self.reverse.get(n, [])) for n in self.nodes]

        isolated = [n for n in self.nodes
                   if len(self.forward.get(n, [])) == 0
                   and len(self.reverse.get(n, [])) == 0]

        return {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "avg_out_degree": sum(out_degrees) / total_nodes if total_nodes > 0 else 0,
            "avg_in_degree": sum(in_degrees) / total_nodes if total_nodes > 0 else 0,
            "max_out_degree": max(out_degrees) if out_degrees else 0,
            "max_in_degree": max(in_degrees) if in_degrees else 0,
            "isolated_nodes": len(isolated)
        }
