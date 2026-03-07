"""Test dependency derivation in UET execution planner"""

from pathlib import Path

from src.acms.gap_registry import GapRecord, GapRegistry, GapSeverity, GapStatus
from src.acms.uet_execution_planner import UETExecutionPlanner
from src.acms.uet_submodule_io_contracts import GitWorkspaceRefV1


def test_task_dependency_derivation():
    """Test that task dependencies are derived from gap dependencies"""
    # Setup
    registry = GapRegistry(Path(":memory:"))
    planner = UETExecutionPlanner(registry, run_id="test-run")

    # Create gaps with dependencies
    gap1 = GapRecord(
        gap_id="gap-001",
        title="Gap 1",
        description="First gap",
        category="refactor",
        severity=GapSeverity.HIGH,
        status=GapStatus.DISCOVERED,
        discovered_at="2025-01-01T00:00:00Z",
        file_paths=["file1.py"],
        dependencies=[],  # No dependencies
    )

    gap2 = GapRecord(
        gap_id="gap-002",
        title="Gap 2",
        description="Second gap depends on first",
        category="refactor",
        severity=GapSeverity.MEDIUM,
        status=GapStatus.DISCOVERED,
        discovered_at="2025-01-01T00:00:00Z",
        file_paths=["file2.py"],
        dependencies=["gap-001"],  # Depends on gap1
    )

    gap3 = GapRecord(
        gap_id="gap-003",
        title="Gap 3",
        description="Third gap depends on second",
        category="refactor",
        severity=GapSeverity.LOW,
        status=GapStatus.DISCOVERED,
        discovered_at="2025-01-01T00:00:00Z",
        file_paths=["file3.py"],
        dependencies=["gap-002"],  # Depends on gap2
    )

    # Add to registry
    registry.add_gap(gap1)
    registry.add_gap(gap2)
    registry.add_gap(gap3)

    # Create workspace ref
    workspace_ref = GitWorkspaceRefV1(
        ws_id="test-ws", root_path="/test", branch_name="main"
    )

    # Create workstream with all three gaps
    workstream = planner._create_uet_workstream(
        category="refactor",
        gaps=[gap1, gap2, gap3],
        index=0,
        workspace_ref=workspace_ref,
    )

    # Verify workstream structure
    assert len(workstream.tasks) == 3
    assert workstream.ws_id.startswith("ws-acms-test-run-")

    # Verify task dependencies
    task1 = workstream.tasks[0]
    task2 = workstream.tasks[1]
    task3 = workstream.tasks[2]

    # Task 1 has no dependencies
    assert len(task1.dependencies) == 0

    # Task 2 depends on task 1
    assert len(task2.dependencies) == 1
    assert task1.task_id in task2.dependencies

    # Task 3 depends on task 2
    assert len(task3.dependencies) == 1
    assert task2.task_id in task3.dependencies


def test_workstream_dependency_derivation():
    """Test that workstream dependencies are derived from cross-workstream gap dependencies"""
    # Setup
    registry = GapRegistry(Path(":memory:"))
    planner = UETExecutionPlanner(registry, run_id="test-run")

    # Create gaps in two different categories
    gap1 = GapRecord(
        gap_id="gap-001",
        title="Gap 1 in category A",
        description="First gap",
        category="refactor",
        severity=GapSeverity.HIGH,
        status=GapStatus.DISCOVERED,
        discovered_at="2025-01-01T00:00:00Z",
        file_paths=["file1.py"],
        dependencies=[],
    )

    gap2 = GapRecord(
        gap_id="gap-002",
        title="Gap 2 in category B depends on gap 1",
        description="Second gap",
        category="testing",
        severity=GapSeverity.MEDIUM,
        status=GapStatus.DISCOVERED,
        discovered_at="2025-01-01T00:00:00Z",
        file_paths=["test_file1.py"],
        dependencies=["gap-001"],  # Cross-category dependency
    )

    # Add to registry
    registry.add_gap(gap1)
    registry.add_gap(gap2)

    # Create workspace ref
    workspace_ref = GitWorkspaceRefV1(
        ws_id="test-ws", root_path="/test", branch_name="main"
    )

    # Create first workstream (refactor)
    ws1 = planner._create_uet_workstream(
        category="refactor", gaps=[gap1], index=0, workspace_ref=workspace_ref
    )

    # Assign workstream to gap
    registry.assign_workstream(gap1.gap_id, ws1.ws_id)

    # Create second workstream (testing)
    ws2 = planner._create_uet_workstream(
        category="testing", gaps=[gap2], index=0, workspace_ref=workspace_ref
    )

    # Verify ws2 depends on ws1
    assert ws1.ws_id in ws2.dependencies, (
        f"Expected ws2 to depend on ws1. "
        f"ws1.ws_id={ws1.ws_id}, ws2.dependencies={ws2.dependencies}"
    )


def test_no_dependencies():
    """Test workstreams with no dependencies"""
    registry = GapRegistry(Path(":memory:"))
    planner = UETExecutionPlanner(registry, run_id="test-run")

    gap = GapRecord(
        gap_id="gap-001",
        title="Independent gap",
        description="No dependencies",
        category="refactor",
        severity=GapSeverity.LOW,
        status=GapStatus.DISCOVERED,
        discovered_at="2025-01-01T00:00:00Z",
        file_paths=["file1.py"],
        dependencies=[],
    )

    registry.add_gap(gap)

    workspace_ref = GitWorkspaceRefV1(
        ws_id="test-ws", root_path="/test", branch_name="main"
    )

    workstream = planner._create_uet_workstream(
        category="refactor", gaps=[gap], index=0, workspace_ref=workspace_ref
    )

    assert len(workstream.tasks) == 1
    assert len(workstream.tasks[0].dependencies) == 0
    assert len(workstream.dependencies) == 0
