# DOC_LINK: DOC-TEST-TUI-PANEL-FRAMEWORK-TEST-STATE-CLIENT-159
"""Tests for state client."""

from tui_app.core.state_client import (
    InMemoryStateBackend,
    PipelineSummary,
    StateClient,
    TaskInfo,
)


def test_inmemory_backend_get_pipeline_summary():
    """Test getting pipeline summary from in-memory backend."""
    # DOC_ID: DOC-TEST-TUI-PANEL-FRAMEWORK-TEST-STATE-CLIENT-159
    backend = InMemoryStateBackend()
    summary = backend.get_pipeline_summary()

    assert isinstance(summary, PipelineSummary)
    assert summary.total_tasks > 0
    assert summary.status in ["idle", "running", "paused", "error"]


def test_inmemory_backend_get_tasks():
    """Test getting tasks from in-memory backend."""
    backend = InMemoryStateBackend()
    tasks = backend.get_tasks()

    assert isinstance(tasks, list)
    assert len(tasks) > 0
    assert all(isinstance(task, TaskInfo) for task in tasks)


def test_inmemory_backend_get_task():
    """Test getting specific task from in-memory backend."""
    backend = InMemoryStateBackend()
    task = backend.get_task("task-001")

    assert task is not None
    assert task.task_id == "task-001"


def test_inmemory_backend_get_nonexistent_task():
    """Test getting nonexistent task."""
    backend = InMemoryStateBackend()
    task = backend.get_task("nonexistent")

    assert task is None


def test_state_client_get_pipeline_summary():
    """Test StateClient get_pipeline_summary."""
    backend = InMemoryStateBackend()
    client = StateClient(backend)

    summary = client.get_pipeline_summary()
    assert isinstance(summary, PipelineSummary)


def test_state_client_get_tasks():
    """Test StateClient get_tasks."""
    backend = InMemoryStateBackend()
    client = StateClient(backend)

    tasks = client.get_tasks(limit=2)
    assert isinstance(tasks, list)
    assert len(tasks) <= 2


def test_state_client_get_task():
    """Test StateClient get_task."""
    backend = InMemoryStateBackend()
    client = StateClient(backend)

    task = client.get_task("task-001")
    assert task is not None
    assert task.task_id == "task-001"


def test_inmemory_backend_get_executions():
    """Test getting executions from in-memory backend."""
    backend = InMemoryStateBackend()
    executions = backend.get_executions()

    assert executions
    assert executions[0].execution_id.startswith("exec")


def test_inmemory_backend_get_patch_ledger():
    """Test getting patch ledger entries from in-memory backend."""
    backend = InMemoryStateBackend()
    patches = backend.get_patch_ledger()

    assert patches
    assert patches[0].patch_id.startswith("patch")
