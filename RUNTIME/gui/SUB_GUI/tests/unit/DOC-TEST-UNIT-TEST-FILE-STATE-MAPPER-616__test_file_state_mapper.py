# DOC_LINK: DOC-TEST-UNIT-TEST-FILE-STATE-MAPPER-616
"""Unit tests for FileStateMapper."""
# DOC_ID: DOC-TEST-UNIT-TEST-FILE-STATE-MAPPER-616

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from ui_core.file_state_mapper import FileStateMapper
from ui_core.pattern_client import PatternStatus


@pytest.fixture
def temp_state_dir():
    """Create temporary state directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_execution_results():
    """Sample execution results data."""
    return {
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
                "task_kind": "format",
                "status": "in_progress",
                "tool_id": "black",
                "exit_code": None,
                "error": None,
                "metadata": {},
            },
            {
                "task_id": "task-3",
                "task_kind": "test",
                "status": "failed",
                "tool_id": "pytest",
                "exit_code": 1,
                "error": "AssertionError: test failed",
                "metadata": {},
            },
        ],
    }


@pytest.fixture
def sample_router_state():
    """Sample router state data."""
    return {
        "round_robin": {},
        "metrics": {
            "ruff": {
                "success_count": 10,
                "failure_count": 0,
                "total_latency_ms": 1500.0,
                "call_count": 10,
            },
            "black": {
                "success_count": 8,
                "failure_count": 2,
                "total_latency_ms": 2000.0,
                "call_count": 10,
            },
            "pytest": {
                "success_count": 15,
                "failure_count": 5,
                "total_latency_ms": 45000.0,
                "call_count": 20,
            },
        },
    }


@pytest.fixture
def sample_routing_decisions():
    """Sample routing decisions data."""
    return {
        "run_id": "test-run-001",
        "decisions": [
            {"task_id": "task-1", "tool_id": "ruff", "run_id": "test-run-001"},
            {"task_id": "task-2", "tool_id": "black", "run_id": "test-run-001"},
        ],
    }


@pytest.fixture
def sample_adapter_assignments():
    """Sample adapter assignments data."""
    return {
        "run_id": "test-run-001",
        "assignments": [
            {"task_id": "task-1", "task_kind": "lint", "tool_id": "ruff", "run_id": "test-run-001"},
            {"task_id": "task-2", "task_kind": "format", "tool_id": "black", "run_id": "test-run-001"},
        ],
    }


@pytest.fixture
def populated_state_dir(
    temp_state_dir,
    sample_execution_results,
    sample_router_state,
    sample_routing_decisions,
    sample_adapter_assignments,
):
    """State directory with sample data files."""
    (temp_state_dir / "execution_results.json").write_text(
        json.dumps(sample_execution_results, indent=2)
    )
    (temp_state_dir / "router_state.json").write_text(
        json.dumps(sample_router_state, indent=2)
    )
    (temp_state_dir / "routing_decisions.json").write_text(
        json.dumps(sample_routing_decisions, indent=2)
    )
    (temp_state_dir / "adapter_assignments.json").write_text(
        json.dumps(sample_adapter_assignments, indent=2)
    )
    return temp_state_dir


class TestFileStateMapper:
    """Tests for FileStateMapper."""

    def test_init_with_path(self, temp_state_dir):
        """Test initialization with Path object."""
        mapper = FileStateMapper(temp_state_dir)
        assert mapper.state_dir == temp_state_dir

    def test_init_with_string(self, temp_state_dir):
        """Test initialization with string path."""
        mapper = FileStateMapper(str(temp_state_dir))
        assert mapper.state_dir == temp_state_dir

    def test_read_missing_file(self, temp_state_dir):
        """Test reading non-existent file returns empty dict."""
        mapper = FileStateMapper(temp_state_dir)
        result = mapper._read_json_file("nonexistent.json")
        assert result == {}

    def test_read_malformed_json(self, temp_state_dir):
        """Test reading malformed JSON returns empty dict."""
        bad_file = temp_state_dir / "bad.json"
        bad_file.write_text("{ invalid json")

        mapper = FileStateMapper(temp_state_dir)
        result = mapper._read_json_file("bad.json")
        assert result == {}

    def test_read_valid_json(self, temp_state_dir):
        """Test reading valid JSON file."""
        data = {"key": "value"}
        file_path = temp_state_dir / "test.json"
        file_path.write_text(json.dumps(data))

        mapper = FileStateMapper(temp_state_dir)
        result = mapper._read_json_file("test.json")
        assert result == data

    def test_get_pipeline_summary_empty(self, temp_state_dir):
        """Test pipeline summary with no data."""
        mapper = FileStateMapper(temp_state_dir)
        summary = mapper.get_pipeline_summary()

        assert summary.total_tasks == 0
        assert summary.running_tasks == 0
        assert summary.completed_tasks == 0
        assert summary.failed_tasks == 0
        assert summary.active_workers == 0
        assert summary.status == "idle"
        assert isinstance(summary.last_update, datetime)

    def test_get_pipeline_summary_with_data(self, populated_state_dir):
        """Test pipeline summary with sample data."""
        mapper = FileStateMapper(populated_state_dir)
        summary = mapper.get_pipeline_summary()

        assert summary.total_tasks == 3
        assert summary.running_tasks == 1
        assert summary.completed_tasks == 1
        assert summary.failed_tasks == 1
        assert summary.active_workers == 3  # ruff, black, pytest all have call_count > 0
        assert summary.status == "error"  # Has failed tasks
        assert isinstance(summary.last_update, datetime)

    def test_get_tasks_all(self, populated_state_dir):
        """Test getting all tasks."""
        mapper = FileStateMapper(populated_state_dir)
        tasks = mapper.get_tasks()

        assert len(tasks) == 3
        assert tasks[0].task_id == "task-1"
        assert tasks[0].name == "lint"
        assert tasks[0].status == "completed"
        assert tasks[0].worker_id == "ruff"
        assert tasks[0].error_message is None

    def test_get_tasks_filtered_by_status(self, populated_state_dir):
        """Test getting tasks filtered by status."""
        mapper = FileStateMapper(populated_state_dir)

        completed_tasks = mapper.get_tasks(status="completed")
        assert len(completed_tasks) == 1
        assert completed_tasks[0].task_id == "task-1"

        failed_tasks = mapper.get_tasks(status="failed")
        assert len(failed_tasks) == 1
        assert failed_tasks[0].task_id == "task-3"
        assert failed_tasks[0].error_message == "AssertionError: test failed"

    def test_get_tasks_with_limit(self, populated_state_dir):
        """Test getting tasks with limit."""
        mapper = FileStateMapper(populated_state_dir)
        tasks = mapper.get_tasks(limit=2)

        assert len(tasks) == 2

    def test_get_task_by_id(self, populated_state_dir):
        """Test getting single task by ID."""
        mapper = FileStateMapper(populated_state_dir)

        task = mapper.get_task("task-2")
        assert task is not None
        assert task.task_id == "task-2"
        assert task.name == "format"
        assert task.status == "in_progress"
        assert task.worker_id == "black"

    def test_get_task_nonexistent(self, populated_state_dir):
        """Test getting non-existent task returns None."""
        mapper = FileStateMapper(populated_state_dir)
        task = mapper.get_task("nonexistent")
        assert task is None

    def test_get_executions(self, populated_state_dir):
        """Test getting executions."""
        mapper = FileStateMapper(populated_state_dir)
        executions = mapper.get_executions()

        assert len(executions) == 1
        assert executions[0].execution_id == "test-run-001"
        assert executions[0].status == "running"

    def test_get_executions_no_data(self, temp_state_dir):
        """Test getting executions with no data."""
        mapper = FileStateMapper(temp_state_dir)
        executions = mapper.get_executions()
        assert executions == []

    def test_get_patch_ledger(self, temp_state_dir):
        """Test getting patch ledger (not yet implemented)."""
        mapper = FileStateMapper(temp_state_dir)
        patches = mapper.get_patch_ledger()
        assert patches == []

    def test_get_tool_metrics(self, populated_state_dir):
        """Test getting tool metrics."""
        mapper = FileStateMapper(populated_state_dir)
        metrics = mapper.get_tool_metrics()

        assert "ruff" in metrics
        assert metrics["ruff"]["success_count"] == 10
        assert metrics["ruff"]["call_count"] == 10

        assert "pytest" in metrics
        assert metrics["pytest"]["failure_count"] == 5

    def test_get_tool_metrics_no_data(self, temp_state_dir):
        """Test getting tool metrics with no data."""
        mapper = FileStateMapper(temp_state_dir)
        metrics = mapper.get_tool_metrics()
        assert metrics == {}

    def test_get_routing_decisions(self, populated_state_dir):
        """Test getting routing decisions."""
        mapper = FileStateMapper(populated_state_dir)
        decisions = mapper.get_routing_decisions()

        assert len(decisions) == 2
        assert decisions[0]["task_id"] == "task-1"
        assert decisions[0]["tool_id"] == "ruff"

    def test_get_adapter_assignments(self, populated_state_dir):
        """Test getting adapter assignments."""
        mapper = FileStateMapper(populated_state_dir)
        assignments = mapper.get_adapter_assignments()

        assert len(assignments) == 2
        assert assignments[0]["task_id"] == "task-1"
        assert assignments[0]["task_kind"] == "lint"
        assert assignments[0]["tool_id"] == "ruff"

    def test_get_pattern_runs(self, populated_state_dir):
        """Test getting pattern runs."""
        mapper = FileStateMapper(populated_state_dir)
        runs = mapper.get_pattern_runs()

        assert len(runs) == 1
        run = runs[0]

        assert run.run_id == "test-run-001"
        assert run.pattern_id == "phase5_execution"
        assert run.status == PatternStatus.FAILED  # Has failed tasks
        assert run.progress == 1.0 / 3.0
        assert isinstance(run.start_time, datetime)
        assert run.current_phase == "format"  # First in_progress task

    def test_get_pattern_runs_all_completed(self, temp_state_dir):
        """Test pattern run status when all tasks completed."""
        data = {
            "run_id": "test-run-002",
            "results": [
                {"task_id": "t1", "task_kind": "test", "status": "completed", "tool_id": "tool1", "error": None},
                {"task_id": "t2", "task_kind": "test", "status": "completed", "tool_id": "tool2", "error": None},
            ],
        }
        (temp_state_dir / "execution_results.json").write_text(json.dumps(data))

        mapper = FileStateMapper(temp_state_dir)
        runs = mapper.get_pattern_runs()

        assert runs[0].status == PatternStatus.COMPLETED
        assert runs[0].progress == 1.0

    def test_get_pattern_runs_in_progress(self, temp_state_dir):
        """Test pattern run status when tasks in progress."""
        data = {
            "run_id": "test-run-003",
            "results": [
                {"task_id": "t1", "task_kind": "test", "status": "completed", "tool_id": "tool1", "error": None},
                {"task_id": "t2", "task_kind": "test", "status": "in_progress", "tool_id": "tool2", "error": None},
            ],
        }
        (temp_state_dir / "execution_results.json").write_text(json.dumps(data))

        mapper = FileStateMapper(temp_state_dir)
        runs = mapper.get_pattern_runs()

        assert runs[0].status == PatternStatus.RUNNING
        assert runs[0].progress == 0.5

    def test_get_run_id(self, populated_state_dir):
        """Test getting current run ID."""
        mapper = FileStateMapper(populated_state_dir)
        run_id = mapper.get_run_id()
        assert run_id == "test-run-001"

    def test_get_run_id_no_data(self, temp_state_dir):
        """Test getting run ID with no data."""
        mapper = FileStateMapper(temp_state_dir)
        run_id = mapper.get_run_id()
        assert run_id is None

    def test_task_info_mapping_with_missing_fields(self, temp_state_dir):
        """Test TaskInfo mapping handles missing fields."""
        data = {
            "run_id": "test",
            "results": [
                {
                    "task_id": "incomplete-task",
                    # Missing: task_kind, status, tool_id, error
                }
            ],
        }
        (temp_state_dir / "execution_results.json").write_text(json.dumps(data))

        mapper = FileStateMapper(temp_state_dir)
        tasks = mapper.get_tasks()

        assert len(tasks) == 1
        task = tasks[0]
        assert task.task_id == "incomplete-task"
        assert task.name == "Unknown Task"
        assert task.status == "unknown"
        assert task.worker_id is None
        assert task.error_message is None
        assert task.start_time is None
        assert task.end_time is None
