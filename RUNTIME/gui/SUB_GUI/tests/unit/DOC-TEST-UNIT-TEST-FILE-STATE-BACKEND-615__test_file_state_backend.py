# DOC_LINK: DOC-TEST-UNIT-TEST-FILE-STATE-BACKEND-615
"""Unit tests for FileStateBackend."""
# DOC_ID: DOC-TEST-UNIT-TEST-FILE-STATE-BACKEND-615

import json
import os
import tempfile
from pathlib import Path

import pytest

from ui_core.file_state_backend import FileStateBackend


@pytest.fixture
def temp_state_dir():
    """Create temporary state directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_state_files(temp_state_dir):
    """Create sample state files."""
    execution_results = {
        "run_id": "test-run-001",
        "results": [
            {
                "task_id": "task-1",
                "task_kind": "lint",
                "status": "completed",
                "tool_id": "ruff",
                "exit_code": 0,
                "error": None,
                "metadata": {},
            },
            {
                "task_id": "task-2",
                "task_kind": "test",
                "status": "failed",
                "tool_id": "pytest",
                "exit_code": 1,
                "error": "Test failed",
                "metadata": {},
            },
        ],
    }

    router_state = {
        "round_robin": {},
        "metrics": {
            "ruff": {
                "success_count": 10,
                "failure_count": 0,
                "total_latency_ms": 1500.0,
                "call_count": 10,
            },
            "pytest": {
                "success_count": 5,
                "failure_count": 5,
                "total_latency_ms": 50000.0,
                "call_count": 10,
            },
        },
    }

    (temp_state_dir / "execution_results.json").write_text(
        json.dumps(execution_results, indent=2)
    )
    (temp_state_dir / "router_state.json").write_text(
        json.dumps(router_state, indent=2)
    )

    return temp_state_dir


class TestFileStateBackend:
    """Tests for FileStateBackend."""

    def test_init_with_explicit_path(self, temp_state_dir):
        """Test initialization with explicit path."""
        backend = FileStateBackend(temp_state_dir)
        assert backend.state_dir == temp_state_dir

    def test_init_with_env_var(self, temp_state_dir, monkeypatch):
        """Test initialization with environment variable."""
        monkeypatch.setenv("STATE_DIR", str(temp_state_dir))
        backend = FileStateBackend()
        assert backend.state_dir == temp_state_dir

    def test_init_with_default(self):
        """Test initialization with default path."""
        backend = FileStateBackend()
        assert backend.state_dir == Path(".state")

    def test_get_pipeline_summary(self, sample_state_files):
        """Test getting pipeline summary."""
        backend = FileStateBackend(sample_state_files)
        summary = backend.get_pipeline_summary()

        assert summary.total_tasks == 2
        assert summary.completed_tasks == 1
        assert summary.failed_tasks == 1
        assert summary.status == "error"  # Has failures
        assert summary.active_workers == 2  # ruff and pytest

    def test_get_pipeline_summary_empty_dir(self, temp_state_dir):
        """Test pipeline summary with no state files."""
        backend = FileStateBackend(temp_state_dir)
        summary = backend.get_pipeline_summary()

        assert summary.total_tasks == 0
        assert summary.completed_tasks == 0
        assert summary.failed_tasks == 0
        assert summary.status == "idle"

    def test_get_tasks_all(self, sample_state_files):
        """Test getting all tasks."""
        backend = FileStateBackend(sample_state_files)
        tasks = backend.get_tasks()

        assert len(tasks) == 2
        assert tasks[0].task_id == "task-1"
        assert tasks[0].status == "completed"
        assert tasks[1].task_id == "task-2"
        assert tasks[1].status == "failed"

    def test_get_tasks_filtered(self, sample_state_files):
        """Test getting tasks filtered by status."""
        backend = FileStateBackend(sample_state_files)

        completed = backend.get_tasks(status="completed")
        assert len(completed) == 1
        assert completed[0].task_id == "task-1"

        failed = backend.get_tasks(status="failed")
        assert len(failed) == 1
        assert failed[0].task_id == "task-2"
        assert failed[0].error_message == "Test failed"

    def test_get_tasks_with_limit(self, sample_state_files):
        """Test getting tasks with limit."""
        backend = FileStateBackend(sample_state_files)
        tasks = backend.get_tasks(limit=1)

        assert len(tasks) == 1

    def test_get_task_by_id(self, sample_state_files):
        """Test getting single task by ID."""
        backend = FileStateBackend(sample_state_files)
        task = backend.get_task("task-1")

        assert task is not None
        assert task.task_id == "task-1"
        assert task.name == "lint"
        assert task.worker_id == "ruff"

    def test_get_task_nonexistent(self, sample_state_files):
        """Test getting non-existent task."""
        backend = FileStateBackend(sample_state_files)
        task = backend.get_task("nonexistent")

        assert task is None

    def test_get_executions(self, sample_state_files):
        """Test getting executions."""
        backend = FileStateBackend(sample_state_files)
        executions = backend.get_executions()

        assert len(executions) == 1
        assert executions[0].execution_id == "test-run-001"

    def test_get_executions_no_data(self, temp_state_dir):
        """Test getting executions with no data."""
        backend = FileStateBackend(temp_state_dir)
        executions = backend.get_executions()

        assert executions == []

    def test_get_patch_ledger(self, temp_state_dir):
        """Test getting patch ledger (not yet implemented)."""
        backend = FileStateBackend(temp_state_dir)
        patches = backend.get_patch_ledger()

        assert patches == []

    def test_get_run_id(self, sample_state_files):
        """Test getting current run ID."""
        backend = FileStateBackend(sample_state_files)
        run_id = backend.get_run_id()

        assert run_id == "test-run-001"

    def test_get_run_id_no_data(self, temp_state_dir):
        """Test getting run ID with no data."""
        backend = FileStateBackend(temp_state_dir)
        run_id = backend.get_run_id()

        assert run_id is None

    def test_get_tool_metrics(self, sample_state_files):
        """Test getting tool metrics."""
        backend = FileStateBackend(sample_state_files)
        metrics = backend.get_tool_metrics()

        assert "ruff" in metrics
        assert metrics["ruff"]["success_count"] == 10
        assert metrics["ruff"]["call_count"] == 10

        assert "pytest" in metrics
        assert metrics["pytest"]["failure_count"] == 5

    def test_get_tool_metrics_no_data(self, temp_state_dir):
        """Test getting tool metrics with no data."""
        backend = FileStateBackend(temp_state_dir)
        metrics = backend.get_tool_metrics()

        assert metrics == {}

    def test_nonexistent_state_dir(self):
        """Test backend with non-existent state directory."""
        backend = FileStateBackend("/nonexistent/path")

        # Should not crash, just return empty data
        summary = backend.get_pipeline_summary()
        assert summary.total_tasks == 0

        tasks = backend.get_tasks()
        assert tasks == []
