#!/usr/bin/env python3
"""
Compute conflict graph for parallel workstreams.
Analyzes write manifests to detect file-level conflicts and compute parallel execution groups.
Gates: GATE-PWE-003 (conflict graph build), GATE-PWE-004 (parallel group authorization)
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict, deque
import jsonschema


class ConflictGraphBuilder:
    def __init__(self, schema_dir: Path):
        self.schema_dir = schema_dir
        self.schemas = self._load_schemas()
        
    def _load_schemas(self) -> Dict[str, Any]:
        """Load required schemas"""
        schemas = {}
        schema_files = [
            "conflict_graph.schema.json",
            "write_manifest.schema.json"
        ]
        
        for schema_file in schema_files:
            schema_path = self.schema_dir / schema_file
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_name = schema_file.replace('.schema.json', '')
                schemas[schema_name] = json.load(f)
        
        return schemas
    
    def load_write_manifests(self, plan_data: Dict[str, Any], plan_dir: Path) -> Dict[str, Dict[str, Any]]:
        """Load all write manifests from plan"""
        manifests = {}
        pw_config = plan_data.get('parallel_workstreams', {})
        
        for ws in pw_config.get('workstreams', []):
            ws_id = ws['workstream_id']
            manifest_path = plan_dir / ws['write_manifest']
            
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifests[ws_id] = json.load(f)
        
        return manifests
    
    def detect_conflicts(self, manifests: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect file-level conflicts between workstreams"""
        edges = []
        workstream_ids = list(manifests.keys())
        
        for i, ws_a in enumerate(workstream_ids):
            for ws_b in workstream_ids[i+1:]:
                manifest_a = manifests[ws_a]
                manifest_b = manifests[ws_b]
                
                writes_a = set(manifest_a.get('declared_writes', []))
                writes_b = set(manifest_b.get('declared_writes', []))
                reads_a = set(manifest_a.get('declared_reads', []))
                reads_b = set(manifest_b.get('declared_reads', []))
                
                # Write-write conflicts
                ww_conflicts = writes_a & writes_b
                if ww_conflicts:
                    edges.append({
                        "source": ws_a,
                        "target": ws_b,
                        "conflict_type": "write_write",
                        "conflicting_files": sorted(list(ww_conflicts))
                    })
                
                # Write-read conflicts (A writes what B reads)
                wr_conflicts_ab = writes_a & reads_b
                if wr_conflicts_ab:
                    edges.append({
                        "source": ws_a,
                        "target": ws_b,
                        "conflict_type": "write_read",
                        "conflicting_files": sorted(list(wr_conflicts_ab))
                    })
                
                # Write-read conflicts (B writes what A reads)
                wr_conflicts_ba = writes_b & reads_a
                if wr_conflicts_ba:
                    edges.append({
                        "source": ws_b,
                        "target": ws_a,
                        "conflict_type": "write_read",
                        "conflicting_files": sorted(list(wr_conflicts_ba))
                    })
                
                # Exclusive resource conflicts
                locks_a = set(manifest_a.get('exclusive_locks', []))
                locks_b = set(manifest_b.get('exclusive_locks', []))
                lock_conflicts = locks_a & locks_b
                if lock_conflicts:
                    edges.append({
                        "source": ws_a,
                        "target": ws_b,
                        "conflict_type": "resource_lock",
                        "conflicting_files": sorted(list(lock_conflicts))
                    })
        
        return edges
    
    def add_dependency_edges(self, plan_data: Dict[str, Any], edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add explicit dependency edges from plan"""
        pw_config = plan_data.get('parallel_workstreams', {})
        
        for ws in pw_config.get('workstreams', []):
            ws_id = ws['workstream_id']
            for dep in ws.get('dependencies', []):
                edges.append({
                    "source": dep,
                    "target": ws_id,
                    "conflict_type": "dependency",
                    "conflicting_files": []
                })
        
        return edges
    
    def compute_parallel_groups(self, workstream_ids: List[str], edges: List[Dict[str, Any]], max_parallel: int) -> List[List[str]]:
        """Compute parallel execution groups using topological sort (Kahn's algorithm)"""
        # Build adjacency list and in-degree count
        graph = defaultdict(set)
        in_degree = {ws: 0 for ws in workstream_ids}
        
        for edge in edges:
            source = edge['source']
            target = edge['target']
            if target not in graph[source]:
                graph[source].add(target)
                in_degree[target] += 1
        
        # Find all nodes with no incoming edges
        parallel_groups = []
        remaining = set(workstream_ids)
        
        while remaining:
            # Get all nodes with in-degree 0
            ready = [ws for ws in remaining if in_degree[ws] == 0]
            
            if not ready:
                # Cycle detected or isolated nodes
                ready = list(remaining)
            
            # Limit group size by max_parallel
            group = ready[:max_parallel]
            parallel_groups.append(sorted(group))
            
            # Remove processed nodes and update in-degrees
            for ws in group:
                remaining.remove(ws)
                for neighbor in graph[ws]:
                    in_degree[neighbor] -= 1
        
        return parallel_groups
    
    def build_conflict_graph(self, plan_data: Dict[str, Any], plan_dir: Path, max_parallel: int = 4) -> Dict[str, Any]:
        """Build complete conflict graph"""
        # Load manifests
        manifests = self.load_write_manifests(plan_data, plan_dir)
        workstream_ids = list(manifests.keys())
        
        # Build nodes
        nodes = []
        for ws_id, manifest in manifests.items():
            nodes.append({
                "workstream_id": ws_id,
                "write_count": len(manifest.get('declared_writes', [])),
                "read_count": len(manifest.get('declared_reads', []))
            })
        
        # Detect conflicts
        edges = self.detect_conflicts(manifests)
        
        # Add dependency edges
        edges = self.add_dependency_edges(plan_data, edges)
        
        # Compute parallel groups
        parallel_groups = self.compute_parallel_groups(workstream_ids, edges, max_parallel)
        
        # Build graph object
        max_parallelism = max(len(group) for group in parallel_groups) if parallel_groups else 0
        
        conflict_graph = {
            "nodes": nodes,
            "edges": edges,
            "parallel_groups": parallel_groups,
            "analysis_metadata": {
                "total_workstreams": len(workstream_ids),
                "total_conflicts": len(edges),
                "max_parallelism": max_parallelism,
                "analysis_timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        # Validate against schema
        jsonschema.validate(
            instance=conflict_graph,
            schema=self.schemas['conflict_graph']
        )
        
        return conflict_graph
    
    def write_gate_result(self, gate_id: str, passed: bool, error: str, output_dir: Path):
        """Write gate result"""
        gate_dir = output_dir / "evidence" / "gates"
        gate_dir.mkdir(parents=True, exist_ok=True)
        
        result = {
            "gate_id": gate_id,
            "passed": passed,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": error
        }
        
        result_file = gate_dir / f"{gate_id}.result.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Compute conflict graph for parallel workstreams"
    )
    parser.add_argument(
        "--plan",
        required=True,
        type=Path,
        help="Path to plan JSON file"
    )
    parser.add_argument(
        "--schema-dir",
        type=Path,
        default=None,
        help="Path to schemas directory"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory for artifacts"
    )
    parser.add_argument(
        "--max-parallel",
        type=int,
        default=4,
        help="Maximum parallel workstreams per group"
    )
    
    args = parser.parse_args()
    
    # Auto-detect schema directory
    if args.schema_dir is None:
        script_dir = Path(__file__).parent
        args.schema_dir = script_dir.parent / "01260207201000001275_schemas"
    
    # Default output directory
    if args.output_dir is None:
        args.output_dir = args.plan.parent
    
    try:
        # Load plan
        with open(args.plan, 'r', encoding='utf-8') as f:
            plan_data = json.load(f)
        
        # Build conflict graph
        builder = ConflictGraphBuilder(args.schema_dir)
        conflict_graph = builder.build_conflict_graph(plan_data, args.plan.parent, args.max_parallel)
        
        # Write conflict graph
        artifact_dir = args.output_dir / "artifacts" / "conflict_graph"
        artifact_dir.mkdir(parents=True, exist_ok=True)
        
        graph_file = artifact_dir / "conflict_graph.json"
        with open(graph_file, 'w', encoding='utf-8') as f:
            json.dump(conflict_graph, f, indent=2)
        
        # Write parallel groups separately
        groups_file = artifact_dir / "parallel_groups.json"
        with open(groups_file, 'w', encoding='utf-8') as f:
            json.dump({
                "parallel_groups": conflict_graph['parallel_groups'],
                "max_parallelism": conflict_graph['analysis_metadata']['max_parallelism']
            }, f, indent=2)
        
        # Write gate results
        builder.write_gate_result("GATE-PWE-003", True, None, args.output_dir)
        
        # GATE-PWE-004: Authorize parallel groups (check max_parallel limit)
        max_parallelism = conflict_graph['analysis_metadata']['max_parallelism']
        if max_parallelism > args.max_parallel:
            builder.write_gate_result(
                "GATE-PWE-004",
                False,
                f"Max parallelism {max_parallelism} exceeds limit {args.max_parallel}",
                args.output_dir
            )
            print(f"GATE-PWE-004 FAILED: Max parallelism exceeds limit", file=sys.stderr)
            sys.exit(1)
        else:
            builder.write_gate_result("GATE-PWE-004", True, None, args.output_dir)
        
        print(f"✓ GATE-PWE-003: Conflict graph built successfully")
        print(f"✓ GATE-PWE-004: Parallel groups authorized (max={max_parallelism})")
        print(f"  Total workstreams: {conflict_graph['analysis_metadata']['total_workstreams']}")
        print(f"  Total conflicts: {conflict_graph['analysis_metadata']['total_conflicts']}")
        print(f"  Parallel groups: {len(conflict_graph['parallel_groups'])}")
        sys.exit(0)
        
    except Exception as e:
        print(f"FATAL ERROR: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
