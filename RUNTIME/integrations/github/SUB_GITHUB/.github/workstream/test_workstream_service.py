"""Tests for WorkstreamService."""

import tempfile
from pathlib import Path

import pytest

from core.state.sqlite_store import SQLiteStateStore
from core.workstream_service import WorkstreamService
from core.workstreams.workstream_service_impl import WorkstreamServiceImpl


class TestWorkstreamServiceProtocol:
    """Test WorkstreamService protocol compliance."""

    # DOC_ID: DOC-TEST-INTERFACES-TEST-WORKSTREAM-SERVICE-127

    def test_impl_implements_protocol(self):
        """WorkstreamServiceImpl implements protocol."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = SQLiteStateStore(Path(tmpdir) / "test.db")
            service = WorkstreamServiceImpl(store)
            assert isinstance(service, WorkstreamService)


class TestWorkstreamServiceImpl:
    """Test WorkstreamServiceImpl."""

    @pytest.fixture
    def service(self):
        """Create service with temp state store."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = SQLiteStateStore(Path(tmpdir) / "test.db")
            yield WorkstreamServiceImpl(store)

    def test_create_workstream(self, service):
        """Create workstream."""
        ws_id = service.create({"name": "Test WS"})

        assert ws_id.startswith("ws-")

        ws = service.load(ws_id)
        assert ws["name"] == "Test WS"
        assert ws["status"] == "pending"

    def test_execute_workstream(self, service):
        """Execute workstream."""
        ws_id = service.create({"name": "Test"})
        run_id = service.execute(ws_id)

        assert run_id.startswith("run-")

        status = service.get_status(ws_id)
        assert status["status"] == "running"
        assert status["run_id"] == run_id

    def test_dry_run(self, service):
        """Dry run execution."""
        ws_id = service.create({"name": "Test"})
        run_id = service.execute(ws_id, dry_run=True)

        status = service.get_status(ws_id)
        assert status["status"] == "dry_run"

    def test_list_all(self, service):
        """List all workstreams."""
        service.create({"name": "WS1"})
        service.create({"name": "WS2"})

        all_ws = service.list_all()
        assert len(all_ws) == 2

    def test_list_by_status(self, service):
        """List workstreams by status."""
        ws1 = service.create({"name": "WS1"})
        service.create({"name": "WS2"})
        service.execute(ws1)

        running = service.list_all(status="running")
        assert len(running) == 1
        assert running[0]["status"] == "running"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
