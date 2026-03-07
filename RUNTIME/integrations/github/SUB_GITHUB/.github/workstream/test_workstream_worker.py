"""Tests for Workstream and Worker state machines."""

import pytest
from core.state.workstream import WorkstreamState, WorkstreamStateMachine
from core.state.worker import WorkerState, WorkerStateMachine


class TestWorkstreamStateMachine:
    """Test workstream state machine."""

    def test_initial_state(self):
        ws = WorkstreamStateMachine("ws-001", "run-001")
        assert ws.current_state == WorkstreamState.PENDING

    def test_happy_path(self):
        ws = WorkstreamStateMachine("ws-001", "run-001")
        ws.mark_ready()
        ws.start()
        ws.begin_validation()
        ws.complete()
        assert ws.current_state == WorkstreamState.COMPLETED
        assert ws.is_terminal()

    def test_pause_resume(self):
        ws = WorkstreamStateMachine("ws-001", "run-001")
        ws.mark_ready()
        ws.start()
        ws.pause()
        assert ws.current_state == WorkstreamState.PAUSED
        ws.resume()
        assert ws.current_state == WorkstreamState.RUNNING

    def test_block_unblock(self):
        ws = WorkstreamStateMachine("ws-001", "run-001")
        ws.block("Dependency failed")
        assert ws.current_state == WorkstreamState.BLOCKED
        ws.unblock()
        assert ws.current_state == WorkstreamState.PENDING

    def test_progress_tracking(self):
        ws = WorkstreamStateMachine("ws-001", "run-001")
        ws.update_task_counts(total=10, completed=5)
        progress = ws.get_progress()
        assert progress["completion_percentage"] == 50.0


class TestWorkerStateMachine:
    """Test worker state machine."""

    def test_initial_state(self):
        worker = WorkerStateMachine("worker-001")
        assert worker.current_state == WorkerState.IDLE

    def test_task_assignment(self):
        worker = WorkerStateMachine("worker-001")
        worker.assign_task("task-001")
        assert worker.current_state == WorkerState.BUSY
        assert worker.current_task_id == "task-001"

    def test_complete_task(self):
        worker = WorkerStateMachine("worker-001")
        worker.assign_task("task-001")
        worker.complete_task()
        assert worker.current_state == WorkerState.IDLE
        assert worker.current_task_id is None

    def test_pause_resume(self):
        worker = WorkerStateMachine("worker-001")
        worker.pause()
        assert worker.current_state == WorkerState.PAUSED
        worker.resume()
        assert worker.current_state == WorkerState.IDLE

    def test_fail_recover(self):
        worker = WorkerStateMachine("worker-001")
        worker.assign_task("task-001")
        worker.fail("Network error")
        assert worker.current_state == WorkerState.FAILED
        assert worker.current_task_id is None
        worker.recover()
        assert worker.current_state == WorkerState.IDLE

    def test_shutdown(self):
        worker = WorkerStateMachine("worker-001")
        worker.shutdown()
        assert worker.current_state == WorkerState.SHUTDOWN
        assert worker.is_terminal()

    def test_heartbeat(self):
        worker = WorkerStateMachine("worker-001")
        worker.heartbeat()
        assert worker.is_healthy()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
