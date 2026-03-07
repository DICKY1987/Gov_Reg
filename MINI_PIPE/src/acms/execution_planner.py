"""Execution Planner Module

Clusters gaps into workstreams with dependency resolution and prioritization.
Supports PHASE_2_GAP_CONSOLIDATION_AND_CLUSTERING.
"""

import heapq
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from src.acms.gap_registry import GapRecord, GapRegistry, GapSeverity


@dataclass
class Workstream:
    """Clustered workstream definition"""

    workstream_id: str
    name: str
    description: str
    gap_ids: List[str] = field(default_factory=list)
    priority_score: float = 0.0
    dependencies: List[str] = field(default_factory=list)
    estimated_effort: str = "medium"
    file_scope: Set[str] = field(default_factory=set)
    categories: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workstream_id": self.workstream_id,
            "name": self.name,
            "description": self.description,
            "gap_ids": self.gap_ids,
            "priority_score": self.priority_score,
            "dependencies": self.dependencies,
            "estimated_effort": self.estimated_effort,
            "file_scope": list(self.file_scope),
            "categories": list(self.categories),
            "metadata": self.metadata,
        }


class ExecutionPlanner:
    """Clusters gaps into executable workstreams"""

    def __init__(self, gap_registry: GapRegistry):
        self.gap_registry = gap_registry
        self.workstreams: Dict[str, Workstream] = {}
        self._cluster_counter = 0

    def cluster_gaps(
        self,
        max_files_per_workstream: int = 10,
        category_based: bool = True,
    ) -> List[Workstream]:
        """Cluster gaps into workstreams"""
        unresolved = self.gap_registry.get_unresolved()

        if category_based:
            return self._cluster_by_category(unresolved, max_files_per_workstream)
        else:
            return self._cluster_by_file_proximity(unresolved, max_files_per_workstream)

    def _cluster_by_category(
        self,
        gaps: List[GapRecord],
        max_files: int,
    ) -> List[Workstream]:
        """Cluster gaps by category"""
        category_groups: Dict[str, List[GapRecord]] = {}

        for gap in gaps:
            category = gap.category
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(gap)

        workstreams = []
        for category, category_gaps in category_groups.items():
            file_groups = self._split_by_file_count(category_gaps, max_files)

            for idx, group in enumerate(file_groups):
                ws_id = self._generate_workstream_id(category)
                ws = self._create_workstream(ws_id, category, group, idx)
                workstreams.append(ws)
                self.workstreams[ws_id] = ws

        return workstreams

    def _cluster_by_file_proximity(
        self,
        gaps: List[GapRecord],
        max_files: int,
    ) -> List[Workstream]:
        """Cluster gaps by file proximity"""
        from collections import defaultdict

        file_to_gaps: Dict[str, List[GapRecord]] = defaultdict(list)

        for gap in gaps:
            for file_path in gap.file_paths:
                file_to_gaps[file_path].append(gap)

        visited_gaps: Set[str] = set()
        workstreams = []

        for file_path, file_gaps in file_to_gaps.items():
            unvisited = [g for g in file_gaps if g.gap_id not in visited_gaps]
            if not unvisited:
                continue

            ws_id = self._generate_workstream_id("file_proximity")
            cluster = self._expand_cluster(
                unvisited[0], file_to_gaps, visited_gaps, max_files
            )

            ws = self._create_workstream(ws_id, "file_proximity", cluster, 0)
            workstreams.append(ws)
            self.workstreams[ws_id] = ws

        return workstreams

    def _expand_cluster(
        self,
        seed_gap: GapRecord,
        file_to_gaps: Dict[str, List[GapRecord]],
        visited: Set[str],
        max_files: int,
    ) -> List[GapRecord]:
        """Expand cluster from seed gap using priority queue for O(n log n) performance"""
        cluster = [seed_gap]
        visited.add(seed_gap.gap_id)
        files_covered: Set[str] = set(seed_gap.file_paths)

        # Priority queue: (priority, gap_id, gap)
        # Priority is negative of overlap count (for max-heap behavior)
        candidate_heap: List[tuple] = []
        gap_index = {}  # Track gaps already in heap

        # Add initial candidates from seed gap's files
        for file_path in seed_gap.file_paths:
            for gap in file_to_gaps.get(file_path, []):
                if gap.gap_id not in visited and gap.gap_id not in gap_index:
                    overlap = len(set(gap.file_paths) & files_covered)
                    heapq.heappush(candidate_heap, (-overlap, gap.gap_id, gap))
                    gap_index[gap.gap_id] = True

        while candidate_heap and len(files_covered) < max_files:
            # Get gap with highest overlap (most negative priority)
            _, gap_id, gap = heapq.heappop(candidate_heap)

            if gap_id in visited:
                continue

            new_files = set(gap.file_paths) - files_covered
            if len(files_covered) + len(new_files) <= max_files:
                cluster.append(gap)
                visited.add(gap_id)
                files_covered.update(gap.file_paths)

                # Add new candidates from newly added files
                for file_path in new_files:
                    for candidate_gap in file_to_gaps.get(file_path, []):
                        if (
                            candidate_gap.gap_id not in visited
                            and candidate_gap.gap_id not in gap_index
                        ):
                            overlap = len(set(candidate_gap.file_paths) & files_covered)
                            heapq.heappush(
                                candidate_heap,
                                (-overlap, candidate_gap.gap_id, candidate_gap),
                            )
                            gap_index[candidate_gap.gap_id] = True

        return cluster

    def _split_by_file_count(
        self,
        gaps: List[GapRecord],
        max_files: int,
    ) -> List[List[GapRecord]]:
        """Split gaps into groups respecting file limit"""
        groups = []
        current_group = []
        current_files: Set[str] = set()

        for gap in gaps:
            gap_files = set(gap.file_paths)
            combined_files = current_files | gap_files

            if len(combined_files) <= max_files:
                current_group.append(gap)
                current_files = combined_files
            else:
                if current_group:
                    groups.append(current_group)
                current_group = [gap]
                current_files = gap_files

        if current_group:
            groups.append(current_group)

        return groups

    def _create_workstream(
        self,
        ws_id: str,
        base_name: str,
        gaps: List[GapRecord],
        index: int,
    ) -> Workstream:
        """Create workstream from gap cluster"""
        all_files: Set[str] = set()
        categories: Set[str] = set()
        gap_ids = []

        for gap in gaps:
            gap_ids.append(gap.gap_id)
            all_files.update(gap.file_paths)
            categories.add(gap.category)
            self.gap_registry.assign_workstream(gap.gap_id, ws_id)

        name = f"{base_name}_{index}" if index > 0 else base_name
        description = f"Workstream for {base_name} addressing {len(gaps)} gaps"

        ws = Workstream(
            workstream_id=ws_id,
            name=name,
            description=description,
            gap_ids=gap_ids,
            file_scope=all_files,
            categories=categories,
        )

        ws.priority_score = self._calculate_priority(gaps)
        ws.dependencies = self._extract_dependencies(gaps)
        ws.estimated_effort = self._estimate_effort(gaps, len(all_files))

        return ws

    def _calculate_priority(self, gaps: List[GapRecord]) -> float:
        """Calculate workstream priority score"""
        severity_weights = {
            GapSeverity.CRITICAL: 10.0,
            GapSeverity.HIGH: 5.0,
            GapSeverity.MEDIUM: 2.0,
            GapSeverity.LOW: 1.0,
            GapSeverity.INFO: 0.5,
        }

        total_score = sum(severity_weights.get(g.severity, 1.0) for g in gaps)
        return total_score / max(len(gaps), 1)

    def _extract_dependencies(self, gaps: List[GapRecord]) -> List[str]:
        """Extract workstream dependencies from gaps"""
        deps: Set[str] = set()
        gap_ids_in_ws = {g.gap_id for g in gaps}

        for gap in gaps:
            for dep_id in gap.dependencies:
                dep_gap = self.gap_registry.get_gap(dep_id)
                if dep_gap and dep_gap.gap_id not in gap_ids_in_ws:
                    if dep_gap.workstream_id:
                        deps.add(dep_gap.workstream_id)

        return list(deps)

    def _estimate_effort(self, gaps: List[GapRecord], file_count: int) -> str:
        """Estimate workstream effort"""
        if file_count > 15 or len(gaps) > 10:
            return "high"
        elif file_count > 5 or len(gaps) > 5:
            return "medium"
        else:
            return "low"

    def _generate_workstream_id(self, prefix: str) -> str:
        """Generate unique workstream ID"""
        self._cluster_counter += 1
        return f"WS_{prefix.upper()}_{self._cluster_counter:04d}"

    def get_prioritized_workstreams(self) -> List[Workstream]:
        """Get workstreams sorted by priority"""
        return sorted(
            self.workstreams.values(),
            key=lambda ws: ws.priority_score,
            reverse=True,
        )

    def save_workstreams(self, output_path: Path) -> None:
        """Save workstream definitions to JSON"""
        data = {
            "version": "1.0",
            "generated_at": datetime.now(UTC).isoformat(),
            "workstreams": [ws.to_dict() for ws in self.workstreams.values()],
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
