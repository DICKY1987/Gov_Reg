#!/usr/bin/env python3
"""
DOC-TOOL-DAG-VALIDATOR-001: DAG Validation Tool
Phase: PH-ENH-005
Purpose: Validate workflow DAGs for cycles, connectivity, and correctness
"""

import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict, deque


class DAGValidator:
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def validate_dag(self, dag: Dict) -> Tuple[bool, List[str], List[str]]:
        """Validate a DAG structure"""
        self.errors = []
        self.warnings = []
        
        # Basic structure validation
        if not self._validate_structure(dag):
            return False, self.errors, self.warnings
        
        nodes = {node["node_id"]: node for node in dag["nodes"]}
        edges = dag["edges"]
        
        # Build adjacency list
        graph = defaultdict(list)
        reverse_graph = defaultdict(list)
        
        for edge in edges:
            from_node = edge["from_node"]
            to_node = edge["to_node"]
            
            if from_node not in nodes:
                self.errors.append(f"Edge references unknown source node: {from_node}")
            if to_node not in nodes:
                self.errors.append(f"Edge references unknown target node: {to_node}")
            
            graph[from_node].append(to_node)
            reverse_graph[to_node].append(from_node)
        
        if self.errors:
            return False, self.errors, self.warnings
        
        # Validate acyclic
        is_acyclic, cycles = self._check_acyclic(nodes, graph)
        if not is_acyclic:
            self.errors.append(f"DAG contains cycles: {cycles}")
        
        # Validate connectivity
        is_connected = self._check_connected(nodes, graph, reverse_graph)
        if not is_connected:
            self.warnings.append("DAG has disconnected nodes")
        
        # Validate start/end nodes
        start_nodes = [n for n, node in nodes.items() if node["type"] == "start"]
        end_nodes = [n for n, node in nodes.items() if node["type"] == "end"]
        
        if len(start_nodes) == 0:
            self.errors.append("DAG must have at least one start node")
        elif len(start_nodes) > 1:
            self.warnings.append(f"DAG has multiple start nodes: {start_nodes}")
        
        if len(end_nodes) == 0:
            self.errors.append("DAG must have at least one end node")
        elif len(end_nodes) > 1:
            self.warnings.append(f"DAG has multiple end nodes: {end_nodes}")
        
        # Compute topological order
        if is_acyclic:
            topo_order = self._topological_sort(nodes, graph)
            dag.setdefault("validation", {})
            dag["validation"]["topological_order"] = topo_order
        
        # Update validation section
        dag["validation"]["is_acyclic"] = is_acyclic
        dag["validation"]["is_connected"] = is_connected
        dag["validation"]["has_single_start"] = len(start_nodes) == 1
        dag["validation"]["has_single_end"] = len(end_nodes) == 1
        dag["validation"]["validation_errors"] = self.errors
        dag["validation"]["validated_at"] = "2026-02-08T03:00:00Z"
        
        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings
    
    def _validate_structure(self, dag: Dict) -> bool:
        """Validate basic DAG structure"""
        if "nodes" not in dag:
            self.errors.append("DAG missing 'nodes' field")
            return False
        
        if "edges" not in dag:
            self.errors.append("DAG missing 'edges' field")
            return False
        
        if not isinstance(dag["nodes"], list):
            self.errors.append("'nodes' must be an array")
            return False
        
        if not isinstance(dag["edges"], list):
            self.errors.append("'edges' must be an array")
            return False
        
        if len(dag["nodes"]) == 0:
            self.errors.append("DAG must have at least one node")
            return False
        
        # Check for duplicate node IDs
        node_ids = [node.get("node_id") for node in dag["nodes"]]
        if len(node_ids) != len(set(node_ids)):
            duplicates = [nid for nid in node_ids if node_ids.count(nid) > 1]
            self.errors.append(f"Duplicate node IDs: {set(duplicates)}")
            return False
        
        return True
    
    def _check_acyclic(self, nodes: Dict, graph: Dict[str, List[str]]) -> Tuple[bool, List[List[str]]]:
        """Check if graph is acyclic using DFS"""
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {node_id: WHITE for node_id in nodes}
        cycles = []
        
        def dfs(node: str, path: List[str]) -> bool:
            if color[node] == BLACK:
                return True
            if color[node] == GRAY:
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return False
            
            color[node] = GRAY
            path.append(node)
            
            for neighbor in graph.get(node, []):
                if not dfs(neighbor, path):
                    return False
            
            path.pop()
            color[node] = BLACK
            return True
        
        for node_id in nodes:
            if color[node_id] == WHITE:
                if not dfs(node_id, []):
                    return False, cycles
        
        return True, []
    
    def _check_connected(self, nodes: Dict, graph: Dict[str, List[str]], 
                        reverse_graph: Dict[str, List[str]]) -> bool:
        """Check if all nodes are reachable"""
        if not nodes:
            return True
        
        # Start from first node
        start_node = next(iter(nodes))
        visited = set()
        queue = deque([start_node])
        
        while queue:
            node = queue.popleft()
            if node in visited:
                continue
            visited.add(node)
            
            # Explore both forward and backward edges
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    queue.append(neighbor)
            
            for neighbor in reverse_graph.get(node, []):
                if neighbor not in visited:
                    queue.append(neighbor)
        
        return len(visited) == len(nodes)
    
    def _topological_sort(self, nodes: Dict, graph: Dict[str, List[str]]) -> List[str]:
        """Compute topological ordering using Kahn's algorithm"""
        in_degree = {node_id: 0 for node_id in nodes}
        
        for node_id in nodes:
            for neighbor in graph.get(node_id, []):
                in_degree[neighbor] += 1
        
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        topo_order = []
        
        while queue:
            node = queue.popleft()
            topo_order.append(node)
            
            for neighbor in graph.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return topo_order


def main():
    # Example DAG validation
    sample_dag = {
        "dag_id": "DAG-TRACK-B-001",
        "nodes": [
            {"node_id": "START", "type": "start"},
            {"node_id": "PH-ENH-001", "type": "task", "phase_id": "PH-ENH-001"},
            {"node_id": "PH-ENH-002", "type": "task", "phase_id": "PH-ENH-002"},
            {"node_id": "PH-ENH-003", "type": "task", "phase_id": "PH-ENH-003"},
            {"node_id": "END", "type": "end"}
        ],
        "edges": [
            {"from_node": "START", "to_node": "PH-ENH-001"},
            {"from_node": "PH-ENH-001", "to_node": "PH-ENH-002"},
            {"from_node": "PH-ENH-002", "to_node": "PH-ENH-003"},
            {"from_node": "PH-ENH-003", "to_node": "END"}
        ],
        "validation": {}
    }
    
    validator = DAGValidator()
    is_valid, errors, warnings = validator.validate_dag(sample_dag)
    
    print(f"\n✅ PH-ENH-005 DAG Validator Ready")
    print(f"\nSample DAG Validation:")
    print(f"  Valid: {is_valid}")
    print(f"  Errors: {len(errors)}")
    print(f"  Warnings: {len(warnings)}")
    
    if is_valid:
        print(f"  Topological Order: {sample_dag['validation']['topological_order']}")
        print(f"  Acyclic: {sample_dag['validation']['is_acyclic']}")
        print(f"  Connected: {sample_dag['validation']['is_connected']}")


if __name__ == "__main__":
    main()
