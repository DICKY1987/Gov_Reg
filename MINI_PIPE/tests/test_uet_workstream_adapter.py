"""
Unit Tests for UET Workstream Adapter

Tests for contracts/uet_workstream_adapter.py
"""

import json
import tempfile
from pathlib import Path

import pytest

from src.acms.uet_submodule_io_contracts import GitWorkspaceRefV1, WorkstreamV1
from src.acms.uet_workstream_adapter import (
    UETWorkstreamAdapter,
    load_workstream_for_run,
    workstream_file_to_execution_requests,
)


@pytest.fixture
def sample_workstream_data():
    """Sample workstream data for testing."""
    return {
        "ws_id": "ws-test-001",
        "name": "Test Workstream",
        "description": "A test workstream for unit tests",
        "tasks": [
            {
                "task_id": "task-001",
                "pattern_id": "aider_refactor",
                "operation_kind": "EXEC-AIDER-EDIT",
                "file_scope": ["src/module.py"],
                "dependencies": [],
                "inputs": {"description": "Refactor module"},
                "timeout_seconds": 1800,
                "metadata": {"gap_category": "code_smell"},
            }
        ],
        "parallelism": 1,
        "workspace_ref": {
            "ws_id": "workspace-main",
            "root_path": "/path/to/repo",
            "branch_name": "main",
            "commit_sha": "abc123",
            "created_at": "2025-12-07T00:00:00Z",
        },
        "gap_ids": ["gap-001"],
        "priority_score": 7.5,
        "dependencies": [],
        "metadata": {"run_id": "run-001", "category": "refactoring"},
        "created_at": "2025-12-07T00:00:00Z",
    }


@pytest.fixture
def sample_workspace():
    """Sample workspace reference for testing."""
    return GitWorkspaceRefV1(
        ws_id="workspace-test",
        root_path="/test/repo",
        branch_name="test-branch",
    )


class TestUETWorkstreamAdapter:
    """Tests for UETWorkstreamAdapter class"""

    def test_load_workstream_from_file(self, tmp_path, sample_workstream_data):
        """Test loading a workstream from JSON file."""
        # Create workstream file
        ws_file = tmp_path / "ws-test-001.json"
        with open(ws_file, "w") as f:
            json.dump(sample_workstream_data, f)

        # Load it
        adapter = UETWorkstreamAdapter()
        workstream = adapter.load_workstream(ws_file)

        assert workstream.ws_id == "ws-test-001"
        assert workstream.name == "Test Workstream"
        assert len(workstream.tasks) == 1
        assert workstream.tasks[0].task_id == "task-001"
        assert workstream.workspace_ref is not None
        assert workstream.workspace_ref.root_path == "/path/to/repo"

    def test_load_workstream_missing_file(self, tmp_path):
        """Test that loading missing file raises error."""
        adapter = UETWorkstreamAdapter()

        with pytest.raises(FileNotFoundError):
            adapter.load_workstream(tmp_path / "nonexistent.json")

    def test_load_workstream_invalid_json(self, tmp_path):
        """Test that invalid JSON raises error."""
        ws_file = tmp_path / "invalid.json"
        ws_file.write_text("{ invalid json }")

        adapter = UETWorkstreamAdapter()

        with pytest.raises(ValueError, match="Invalid JSON"):
            adapter.load_workstream(ws_file)

    def test_load_workstreams_from_directory(self, tmp_path, sample_workstream_data):
        """Test loading multiple workstreams from directory."""
        # Create multiple workstream files
        for i in range(3):
            ws_data = sample_workstream_data.copy()
            ws_data["ws_id"] = f"ws-test-{i:03d}"

            ws_file = tmp_path / f"ws-test-{i:03d}.json"
            with open(ws_file, "w") as f:
                json.dump(ws_data, f)

        # Load all
        adapter = UETWorkstreamAdapter()
        workstreams = adapter.load_workstreams_from_directory(tmp_path)

        assert len(workstreams) == 3
        assert workstreams[0].ws_id == "ws-test-000"
        assert workstreams[1].ws_id == "ws-test-001"
        assert workstreams[2].ws_id == "ws-test-002"

    def test_workstream_to_execution_requests(
        self, tmp_path, sample_workstream_data, sample_workspace
    ):
        """Test converting workstream to execution requests."""
        # Create and load workstream
        ws_file = tmp_path / "ws-test-001.json"
        with open(ws_file, "w") as f:
            json.dump(sample_workstream_data, f)

        adapter = UETWorkstreamAdapter()
        workstream = adapter.load_workstream(ws_file)

        # Convert to requests
        requests = adapter.workstream_to_execution_requests(workstream)

        assert len(requests) == 1
        request = requests[0]

        assert request.operation_kind == "EXEC-AIDER-EDIT"
        assert request.pattern_id == "aider_refactor"
        assert request.file_scope == ["src/module.py"]
        assert request.workspace.root_path == "/path/to/repo"
        assert request.context["ws_id"] == "ws-test-001"
        assert request.context["task_id"] == "task-001"
        assert request.inputs["description"] == "Refactor module"

    def test_workspace_override(
        self, tmp_path, sample_workstream_data, sample_workspace
    ):
        """Test that workspace override works."""
        # Create workstream
        ws_file = tmp_path / "ws-test-001.json"
        with open(ws_file, "w") as f:
            json.dump(sample_workstream_data, f)

        adapter = UETWorkstreamAdapter()
        workstream = adapter.load_workstream(ws_file)

        # Convert with override
        requests = adapter.workstream_to_execution_requests(
            workstream,
            workspace_override=sample_workspace,
        )

        # Should use override workspace
        assert requests[0].workspace.ws_id == "workspace-test"
        assert requests[0].workspace.root_path == "/test/repo"

    def test_get_workstream_by_id(self, tmp_path, sample_workstream_data):
        """Test retrieving loaded workstream by ID."""
        ws_file = tmp_path / "ws-test-001.json"
        with open(ws_file, "w") as f:
            json.dump(sample_workstream_data, f)

        adapter = UETWorkstreamAdapter()
        adapter.load_workstream(ws_file)

        # Retrieve it
        ws = adapter.get_workstream_by_id("ws-test-001")
        assert ws is not None
        assert ws.ws_id == "ws-test-001"

        # Non-existent ID
        ws = adapter.get_workstream_by_id("ws-nonexistent")
        assert ws is None

    def test_list_loaded_workstreams(self, tmp_path, sample_workstream_data):
        """Test listing loaded workstream IDs."""
        # Create multiple workstreams
        for i in range(3):
            ws_data = sample_workstream_data.copy()
            ws_data["ws_id"] = f"ws-test-{i:03d}"

            ws_file = tmp_path / f"ws-test-{i:03d}.json"
            with open(ws_file, "w") as f:
                json.dump(ws_data, f)

        adapter = UETWorkstreamAdapter()
        adapter.load_workstreams_from_directory(tmp_path)

        ids = adapter.list_loaded_workstreams()
        assert len(ids) == 3
        assert "ws-test-000" in ids
        assert "ws-test-001" in ids
        assert "ws-test-002" in ids


class TestConvenienceFunctions:
    """Tests for convenience functions"""

    def test_workstream_file_to_execution_requests(
        self, tmp_path, sample_workstream_data, sample_workspace
    ):
        """Test workstream_file_to_execution_requests convenience function."""
        # Remove workspace_ref from sample data so override is used
        sample_workstream_data_no_ws = sample_workstream_data.copy()
        sample_workstream_data_no_ws["workspace_ref"] = None

        ws_file = tmp_path / "ws-test-001.json"
        with open(ws_file, "w") as f:
            json.dump(sample_workstream_data_no_ws, f)

        requests = workstream_file_to_execution_requests(ws_file, sample_workspace)

        assert len(requests) == 1
        assert requests[0].operation_kind == "EXEC-AIDER-EDIT"
        # Should use provided workspace
        assert requests[0].workspace.ws_id == "workspace-test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
