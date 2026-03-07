"""Execution Scheduler - WS-03-01C

Schedules and executes tasks with dependency resolution.
Handles parallel and sequential execution.
"""

# DOC_ID: DOC-CORE-ENGINE-SCHEDULER-158

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from patterns.decisions.decision_registry import Decision, DecisionRegistry


class Task:
    """Represents a task to be executed"""

    def __init__(
        self,
        task_id: str,
        task_kind: str,
        depends_on: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.task_id = task_id
        self.task_kind = task_kind
        self.depends_on = depends_on or []
        self.metadata = metadata or {}
        self.status = "pending"  # pending, ready, running, completed, failed
        self.result = None
        self.error = None
        self.selected_tool: Optional[str] = None
        self.exit_code: Optional[int] = None
        self.output_patch_id: Optional[str] = None
        self.error_log: Optional[str] = None
        self.result_metadata: Dict[str, Any] = {}

    def __repr__(self):
        return f"Task({self.task_id}, {self.task_kind}, status={self.status})"


class ExecutionScheduler:
    """Schedules and executes tasks with dependency management"""

    def __init__(self, decision_registry: Optional[DecisionRegistry] = None):
        self.tasks: Dict[str, Task] = {}
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_deps: Dict[str, Set[str]] = defaultdict(set)
        self.decision_registry = decision_registry

    def add_task(self, task: Task):
        """Add a task to the scheduler"""
        self.tasks[task.task_id] = task

        # Build dependency graph
        for dep_id in task.depends_on:
            self.dependency_graph[task.task_id].add(dep_id)
            self.reverse_deps[dep_id].add(task.task_id)

    def add_tasks(self, tasks: List[Task]):
        """Add multiple tasks"""
        for task in tasks:
            self.add_task(task)

    def get_ready_tasks(self) -> List[Task]:
        """
        Get all tasks that are ready to execute.
        A task is ready if all its dependencies are completed.
        """
        ready = []

        for task_id, task in sorted(self.tasks.items()):
            if task.status != "pending":
                continue

            # Check if all dependencies are satisfied
            deps = self.dependency_graph.get(task_id, set())

            all_deps_met = True
            for dep_id in deps:
                dep_task = self.tasks.get(dep_id)
                if not dep_task or dep_task.status != "completed":
                    all_deps_met = False
                    break

            if all_deps_met:
                task.status = "ready"
                ready.append(task)

        return ready

    def detect_cycles(self) -> Optional[List[str]]:
        """
        Detect circular dependencies.

        Returns:
            List of task IDs in cycle, or None if no cycle
        """
        visited = set()
        rec_stack = set()
        path = []

        def dfs(task_id: str) -> Optional[List[str]]:
            visited.add(task_id)
            rec_stack.add(task_id)
            path.append(task_id)

            for dep_id in self.dependency_graph.get(task_id, set()):
                if dep_id not in visited:
                    cycle = dfs(dep_id)
                    if cycle:
                        return cycle
                elif dep_id in rec_stack:
                    # Found cycle
                    cycle_start = path.index(dep_id)
                    return path[cycle_start:] + [dep_id]

            # Backtrack: remove from path and recursion stack
            path.pop()
            rec_stack.remove(task_id)
            return None

        for task_id in self.tasks:
            if task_id not in visited:
                cycle = dfs(task_id)
                if cycle:
                    return cycle

        return None

    def get_execution_order(self) -> List[List[str]]:
        """
        Get topological ordering of tasks grouped by execution level.
        Tasks in the same level can be executed in parallel.

        Returns:
            List of levels, where each level is a list of task IDs
        """
        # Check for cycles first
        cycle = self.detect_cycles()
        if cycle:
            raise ValueError(f"Circular dependency detected: {' -> '.join(cycle)}")

        levels = []
        remaining = set(self.tasks.keys())

        # Cache dependency counts for O(1) checking
        dep_count = {}
        for task_id in self.tasks.keys():
            deps = self.dependency_graph.get(task_id, set())
            dep_count[task_id] = len(deps)

        while remaining:
            # Find tasks with no unfulfilled dependencies (count == 0)
            current_level = [
                task_id for task_id in remaining if dep_count[task_id] == 0
            ]

            if not current_level:
                # Should not happen if no cycles
                raise ValueError("Unable to resolve dependencies")

            levels.append(current_level)

            # Remove completed tasks from remaining and update dependency counts
            for task_id in current_level:
                remaining.remove(task_id)

                # Decrement dependency count for all tasks that depend on this one
                for dependent_id in remaining:
                    deps = self.dependency_graph.get(dependent_id, set())
                    if task_id in deps:
                        dep_count[dependent_id] -= 1

        return levels

    def get_parallel_batches(self, max_parallel: int = 5) -> List[List[str]]:
        """
        Get batches of tasks that can be executed in parallel.

        Args:
            max_parallel: Maximum number of tasks per batch

        Returns:
            List of batches, where each batch is a list of task IDs
        """
        levels = self.get_execution_order()
        batches = []

        for level in levels:
            # Split large levels into smaller batches
            for i in range(0, len(level), max_parallel):
                batch = level[i : i + max_parallel]
                batches.append(batch)

        return batches

    def mark_completed(self, task_id: str, result: Any = None):
        """Mark a task as completed"""
        task = self.tasks.get(task_id)
        if task:
            task.status = "completed"
            task.result = result

    def mark_failed(self, task_id: str, error: str):
        """Mark a task as failed"""
        task = self.tasks.get(task_id)
        if task:
            task.status = "failed"
            task.error = error

    def mark_running(self, task_id: str):
        """Mark a task as running"""
        task = self.tasks.get(task_id)
        if task:
            task.status = "running"

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        return self.tasks.get(task_id)

    def get_dependent_tasks(self, task_id: str) -> List[str]:
        """Get tasks that depend on this task"""
        return list(self.reverse_deps.get(task_id, set()))

    def can_execute(self, task_id: str) -> bool:
        """Check if a task can be executed (all deps satisfied)"""
        task = self.tasks.get(task_id)
        if not task or task.status != "pending":
            return False

        deps = self.dependency_graph.get(task_id, set())
        for dep_id in deps:
            dep_task = self.tasks.get(dep_id)
            if not dep_task or dep_task.status != "completed":
                return False

        return True

    def get_blocking_tasks(self, task_id: str) -> List[str]:
        """Get tasks that are blocking this task from executing"""
        blocking = []
        deps = self.dependency_graph.get(task_id, set())

        for dep_id in deps:
            dep_task = self.tasks.get(dep_id)
            if not dep_task or dep_task.status != "completed":
                blocking.append(dep_id)

        return blocking

    def get_stats(self) -> Dict[str, int]:
        """Get statistics about tasks"""
        stats = {
            "total": len(self.tasks),
            "pending": 0,
            "ready": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
        }

        for task in self.tasks.values():
            stats[task.status] += 1

        return stats

    def is_complete(self) -> bool:
        """Check if all tasks are completed or failed"""
        for task in self.tasks.values():
            if task.status not in ["completed", "failed"]:
                return False
        return True

    def has_failures(self) -> bool:
        """Check if any tasks have failed"""
        for task in self.tasks.values():
            if task.status == "failed":
                return True
        return False


def create_task_from_spec(spec: Dict[str, Any]) -> Task:
    """Create a Task from a workstream task specification"""
    return Task(
        task_id=spec.get("id", ""),
        task_kind=spec.get("kind", "unknown"),
        depends_on=spec.get("depends_on", []),
        metadata={
            "description": spec.get("name", ""),
            "constraints": spec.get("constraints", {}),
            "outputs": spec.get("outputs", []),
        },
    )
