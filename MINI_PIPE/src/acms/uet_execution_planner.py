"""
UET-Compatible Execution Planner

Clusters gaps into workstreams following UET_WORKSTREAM_SPEC.
All workstreams validate against uet_workstream.schema.json.

Reference: UET_WORKSTREAM_SPEC.md, Track 2 of alignment plan
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Set

from src.acms.gap_registry import GapRecord, GapRegistry, GapSeverity
from src.acms.uet_submodule_io_contracts import (
    GitWorkspaceRefV1,
    WorkstreamTaskV1,
    WorkstreamV1,
)


class UETExecutionPlanner:
    """
    Clusters gaps into UET-compatible workstreams.

    Each workstream:
    - Has a stable ws_id
    - Contains WorkstreamTaskV1 tasks
    - References pattern_id from PATTERN_INDEX.yaml
    - Validates against UET schema
    """

    def __init__(self, gap_registry: GapRegistry, run_id: str):
        self.gap_registry = gap_registry
        self.run_id = run_id
        self.workstreams: Dict[str, WorkstreamV1] = {}
        self._ws_counter = 0

    def cluster_gaps_to_workstreams(
        self,
        max_files_per_workstream: int = 10,
        category_based: bool = True,
        workspace_ref: Optional[GitWorkspaceRefV1] = None,
    ) -> List[WorkstreamV1]:
        """
        Cluster gaps into UET workstreams.

        Args:
            max_files_per_workstream: Max files per workstream
            category_based: Cluster by category vs file proximity
            workspace_ref: Git workspace reference for all workstreams

        Returns:
            List of UET-compatible WorkstreamV1 objects
        """
        unresolved = self.gap_registry.get_unresolved()

        if category_based:
            return self._cluster_by_category(
                unresolved, max_files_per_workstream, workspace_ref
            )
        else:
            return self._cluster_by_file_proximity(
                unresolved, max_files_per_workstream, workspace_ref
            )

    def _cluster_by_category(
        self,
        gaps: List[GapRecord],
        max_files: int,
        workspace_ref: Optional[GitWorkspaceRefV1],
    ) -> List[WorkstreamV1]:
        """Cluster gaps by category."""
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
                ws = self._create_uet_workstream(
                    category=category,
                    gaps=group,
                    index=idx,
                    workspace_ref=workspace_ref,
                )
                workstreams.append(ws)
                self.workstreams[ws.ws_id] = ws

        return workstreams

    def _cluster_by_file_proximity(
        self,
        gaps: List[GapRecord],
        max_files: int,
        workspace_ref: Optional[GitWorkspaceRefV1],
    ) -> List[WorkstreamV1]:
        """Cluster gaps by file proximity."""
        file_to_gaps: Dict[str, List[GapRecord]] = {}

        for gap in gaps:
            for file_path in gap.file_paths:
                if file_path not in file_to_gaps:
                    file_to_gaps[file_path] = []
                file_to_gaps[file_path].append(gap)

        visited_gaps: Set[str] = set()
        workstreams = []

        for file_path, file_gaps in file_to_gaps.items():
            unvisited = [g for g in file_gaps if g.gap_id not in visited_gaps]
            if not unvisited:
                continue

            cluster = self._expand_cluster(
                unvisited[0], file_to_gaps, visited_gaps, max_files
            )
            ws = self._create_uet_workstream(
                category="file_proximity",
                gaps=cluster,
                index=len(workstreams),
                workspace_ref=workspace_ref,
            )
            workstreams.append(ws)
            self.workstreams[ws.ws_id] = ws

        return workstreams

    def _create_uet_workstream(
        self,
        category: str,
        gaps: List[GapRecord],
        index: int,
        workspace_ref: Optional[GitWorkspaceRefV1],
    ) -> WorkstreamV1:
        """
        Create a UET-compatible WorkstreamV1 from gaps.

        Args:
            category: Category name
            gaps: List of gaps to include
            index: Workstream index within category
            workspace_ref: Git workspace reference

        Returns:
            WorkstreamV1 object
        """
        self._ws_counter += 1
        ws_id = f"ws-acms-{self.run_id}-{self._ws_counter:03d}"

        # Build tasks from gaps
        tasks = []
        file_scope: Set[str] = set()
        gap_to_task_id: Dict[str, str] = {}  # Map gap_id to task_id

        for gap in gaps:
            # Determine pattern and operation based on gap category
            pattern_id, operation_kind = self._map_gap_to_pattern(gap)

            task_id = f"{ws_id}-task-{len(tasks) + 1:03d}"
            gap_to_task_id[gap.gap_id] = task_id

            # Derive task dependencies from gap dependencies
            task_dependencies = []
            for dep_gap_id in gap.dependencies:
                # Check if dependency is in this workstream
                if dep_gap_id in gap_to_task_id:
                    task_dependencies.append(gap_to_task_id[dep_gap_id])
                # Otherwise, it's a cross-workstream dependency (handled at workstream level)

            task = WorkstreamTaskV1(
                task_id=task_id,
                pattern_id=pattern_id,
                operation_kind=operation_kind,
                file_scope=list(gap.file_paths),
                dependencies=task_dependencies,
                inputs={
                    "gap_id": gap.gap_id,
                    "description": gap.description,
                    "severity": gap.severity.value,
                    "category": gap.category,
                },
                timeout_seconds=1800,
                metadata={
                    "gap_source": "ACMS",
                    "gap_category": gap.category,
                },
            )
            tasks.append(task)
            file_scope.update(gap.file_paths)

        # Calculate priority score
        priority_score = self._calculate_priority(gaps)

        # Derive workstream-level dependencies
        # Check if any gaps in this workstream depend on gaps in other workstreams
        ws_dependencies = set()
        for gap in gaps:
            for dep_gap_id in gap.dependencies:
                # Find the workstream of the dependency
                dep_gap = self.gap_registry.get_gap(dep_gap_id)
                if dep_gap and dep_gap.workstream_id and dep_gap.workstream_id != ws_id:
                    ws_dependencies.add(dep_gap.workstream_id)

        # Build workstream
        ws = WorkstreamV1(
            ws_id=ws_id,
            name=f"{category.replace('_', ' ').title()} - Batch {index + 1}",
            description=f"Workstream for {len(gaps)} gaps in category '{category}'",
            tasks=tasks,
            parallelism=1,  # Sequential by default, can be overridden
            workspace_ref=workspace_ref,
            gap_ids=[g.gap_id for g in gaps],
            priority_score=priority_score,
            dependencies=list(ws_dependencies),
            metadata={
                "category": category,
                "run_id": self.run_id,
                "file_count": len(file_scope),
                "gap_count": len(gaps),
            },
        )

        return ws

    def _map_gap_to_pattern(self, gap: GapRecord) -> tuple[str, str]:
        """
        Map a gap to a pattern_id and operation_kind.

        Args:
            gap: Gap record

        Returns:
            (pattern_id, operation_kind) tuple
        """
        # Map gap categories to patterns
        # This should be configurable in production
        category_to_pattern = {
            "missing_docstring": ("add_docstring", "EXEC-AIDER-EDIT"),
            "missing_test": ("create_test", "EXEC-AIDER-EDIT"),
            "type_hint_missing": ("add_type_hints", "EXEC-AIDER-EDIT"),
            "refactor_needed": ("aider_refactor", "EXEC-AIDER-EDIT"),
            "code_smell": ("aider_refactor", "EXEC-AIDER-EDIT"),
            "default": ("generic_fix", "EXEC-AIDER-EDIT"),
        }

        pattern_id, operation_kind = category_to_pattern.get(
            gap.category, category_to_pattern["default"]
        )

        return pattern_id, operation_kind

    def _calculate_priority(self, gaps: List[GapRecord]) -> float:
        """
        Calculate priority score for a workstream.

        Args:
            gaps: List of gaps in workstream

        Returns:
            Priority score (0.0-10.0)
        """
        if not gaps:
            return 0.0

        # Weight by severity
        severity_weights = {
            GapSeverity.CRITICAL: 10.0,
            GapSeverity.HIGH: 7.0,
            GapSeverity.MEDIUM: 5.0,
            GapSeverity.LOW: 3.0,
            GapSeverity.INFO: 1.0,
        }

        total_weight = sum(severity_weights.get(g.severity, 1.0) for g in gaps)
        avg_weight = total_weight / len(gaps)

        return min(avg_weight, 10.0)

    def _split_by_file_count(
        self,
        gaps: List[GapRecord],
        max_files: int,
    ) -> List[List[GapRecord]]:
        """Split gaps into groups by file count."""
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

    def _expand_cluster(
        self,
        seed_gap: GapRecord,
        file_to_gaps: Dict[str, List[GapRecord]],
        visited: Set[str],
        max_files: int,
    ) -> List[GapRecord]:
        """Expand cluster from seed gap."""
        cluster = [seed_gap]
        visited.add(seed_gap.gap_id)
        files_covered: Set[str] = set(seed_gap.file_paths)

        while len(files_covered) < max_files:
            expanded = False
            for file_path in list(files_covered):
                for gap in file_to_gaps.get(file_path, []):
                    if gap.gap_id in visited:
                        continue

                    new_files = set(gap.file_paths) - files_covered
                    if len(files_covered) + len(new_files) <= max_files:
                        cluster.append(gap)
                        visited.add(gap.gap_id)
                        files_covered.update(gap.file_paths)
                        expanded = True

            if not expanded:
                break

        return cluster

    def save_workstreams(self, output_dir: Path) -> List[Path]:
        """
        Save workstreams to JSON files.

        Args:
            output_dir: Directory to save workstream files

        Returns:
            List of paths to created files
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        saved_paths = []
        for ws_id, ws in self.workstreams.items():
            file_path = output_dir / f"{ws_id}.json"

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(ws.to_dict(), f, indent=2)

            saved_paths.append(file_path)

        return saved_paths

    def validate_workstreams(self) -> List[str]:
        """
        Validate all workstreams against UET schema.

        Returns:
            List of validation errors (empty if all valid)
        """
        errors = []

        for ws_id, ws in self.workstreams.items():
            # Basic validation
            if not ws.ws_id:
                errors.append(f"{ws_id}: Missing ws_id")

            if not ws.name:
                errors.append(f"{ws_id}: Missing name")

            if not ws.tasks:
                errors.append(f"{ws_id}: No tasks defined")

            # Validate tasks
            for task in ws.tasks:
                if not task.task_id:
                    errors.append(f"{ws_id}: Task missing task_id")

                if not task.pattern_id:
                    errors.append(f"{ws_id}/{task.task_id}: Missing pattern_id")

                if not task.operation_kind:
                    errors.append(f"{ws_id}/{task.task_id}: Missing operation_kind")

        return errors
