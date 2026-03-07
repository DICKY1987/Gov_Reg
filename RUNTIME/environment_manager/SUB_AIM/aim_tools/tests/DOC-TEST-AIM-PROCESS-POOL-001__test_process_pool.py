# DOC_LINK: DOC-TEST-AIM-PROCESS-POOL-001
"""Unit tests for ToolProcessPool.

Tests process pool functionality with mocked subprocesses.
Covers initialization, I/O operations, error handling, and cleanup.
"""
# DOC_ID: DOC-TEST-AIM-PROCESS-POOL-001

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import queue
import time

try:
    from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.aim.bridge import ToolProcessPool
    from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.aim.pool_interface import ProcessInstance
except ImportError:
    pytest.skip("UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK not available", allow_module_level=True)


@pytest.fixture
def mock_registry():
    """Mock AIM registry for testing."""
    return {
        "tools": {
            "aider": {
                "detectCommands": [["aider", "--yes-always"]],
                "capabilities": ["code_generation"]
            },
            "jules": {
                "detectCommands": [["jules"]],
                "capabilities": ["code_generation"]
            }
        }
    }


@pytest.fixture
def mock_process():
    """Create a mock subprocess.Popen instance."""
    proc = MagicMock()
    proc.stdin = MagicMock()
    proc.stdout = MagicMock()
    proc.stderr = MagicMock()
    proc.poll.return_value = None  # Process still running
    proc.returncode = None
    return proc


class TestToolProcessPoolInitialization:
    """Test pool initialization."""

    def test_pool_initialization_success(self, mock_registry, mock_process):
        """Test successful pool initialization."""
        with patch("aim.bridge.subprocess.Popen", return_value=mock_process):
            with patch("aim.bridge.threading.Thread"):
                pool = ToolProcessPool("aider", count=3, registry=mock_registry)

                assert pool.tool_id == "aider"
                assert pool.count == 3
                assert len(pool.instances) == 3
                assert all(isinstance(inst, ProcessInstance) for inst in pool.instances)

    def test_pool_initialization_invalid_tool(self, mock_registry):
        """Test initialization with invalid tool ID."""
        with pytest.raises(ValueError, match="not in AIM registry"):
            ToolProcessPool("invalid_tool", count=1, registry=mock_registry)

    def test_pool_spawns_correct_command(self, mock_registry, mock_process):
        """Test that correct command is spawned."""
        with patch("aim.bridge.subprocess.Popen", return_value=mock_process) as mock_popen:
            with patch("aim.bridge.threading.Thread"):
                pool = ToolProcessPool("aider", count=1, registry=mock_registry)

                # Verify Popen was called with correct command
                mock_popen.assert_called_once()
                call_args = mock_popen.call_args
                cmd = call_args[0][0]
                # Should have aider + --yes-always (added once)
                assert "aider" in cmd
                assert cmd.count("--yes-always") == 1

                # Verify stdin/stdout/stderr pipes
                kwargs = call_args[1]
                assert kwargs["stdin"] == __import__("subprocess").PIPE
                assert kwargs["stdout"] == __import__("subprocess").PIPE
                assert kwargs["stderr"] == __import__("subprocess").PIPE

    def test_pool_creates_io_threads(self, mock_registry, mock_process):
        """Test that I/O reader threads are created."""
        with patch("aim.bridge.subprocess.Popen", return_value=mock_process):
            with patch("aim.bridge.threading.Thread") as mock_thread:
                pool = ToolProcessPool("aider", count=2, registry=mock_registry)

                # Should create 2 threads per instance (stdout + stderr) * 2 instances = 4
                assert mock_thread.call_count == 4


class TestSendPrompt:
    """Test send_prompt functionality."""

    def test_send_prompt_success(self, mock_registry, mock_process):
        """Test successful prompt sending."""
        with patch("aim.bridge.subprocess.Popen", return_value=mock_process):
            with patch("aim.bridge.threading.Thread"):
                pool = ToolProcessPool("aider", count=1, registry=mock_registry)

                result = pool.send_prompt(0, "/add test.py")

                assert result == True
                mock_process.stdin.write.assert_called_once_with("/add test.py\n")
                mock_process.stdin.flush.assert_called_once()

    def test_send_prompt_invalid_index(self, mock_registry, mock_process):
        """Test sending to invalid instance index."""
        with patch("aim.bridge.subprocess.Popen", return_value=mock_process):
            with patch("aim.bridge.threading.Thread"):
                pool = ToolProcessPool("aider", count=2, registry=mock_registry)

                result = pool.send_prompt(5, "/add test.py")
                assert result == False

    def test_send_prompt_dead_process(self, mock_registry, mock_process):
        """Test sending to dead process."""
        with patch("aim.bridge.subprocess.Popen", return_value=mock_process):
            with patch("aim.bridge.threading.Thread"):
                pool = ToolProcessPool("aider", count=1, registry=mock_registry)

                # Mark instance as dead
                pool.instances[0].alive = False

                result = pool.send_prompt(0, "/add test.py")
                assert result == False

    def test_send_prompt_broken_pipe(self, mock_registry, mock_process):
        """Test handling of BrokenPipeError."""
        mock_process.stdin.write.side_effect = BrokenPipeError()

        with patch("aim.bridge.subprocess.Popen", return_value=mock_process):
            with patch("aim.bridge.threading.Thread"):
                pool = ToolProcessPool("aider", count=1, registry=mock_registry)

                result = pool.send_prompt(0, "/add test.py")

                assert result == False
                assert pool.instances[0].alive == False


class TestReadResponse:
    """Test read_response functionality."""

    def test_read_response_success(self, mock_registry, mock_process):
        """Test successful response reading."""
        with patch("aim.bridge.subprocess.Popen", return_value=mock_process):
            with patch("aim.bridge.threading.Thread"):
                pool = ToolProcessPool("aider", count=1, registry=mock_registry)

                # Put test data in queue
                pool.instances[0].stdout_queue.put("Test response")

                response = pool.read_response(0, timeout=1.0)
                assert response == "Test response"

    def test_read_response_timeout(self, mock_registry, mock_process):
        """Test read_response with timeout."""
        with patch("aim.bridge.subprocess.Popen", return_value=mock_process):
            with patch("aim.bridge.threading.Thread"):
                pool = ToolProcessPool("aider", count=1, registry=mock_registry)

                # Don't put anything in queue
                response = pool.read_response(0, timeout=0.1)
                assert response is None

    def test_read_response_invalid_index(self, mock_registry, mock_process):
        """Test reading from invalid instance."""
        with patch("aim.bridge.subprocess.Popen", return_value=mock_process):
            with patch("aim.bridge.threading.Thread"):
                pool = ToolProcessPool("aider", count=1, registry=mock_registry)

                response = pool.read_response(99, timeout=1.0)
                assert response is None


class TestGetStatus:
    """Test status reporting."""

    def test_get_status_all_alive(self, mock_registry, mock_process):
        """Test status when all processes alive."""
        mock_process.poll.return_value = None  # Still running

        with patch("aim.bridge.subprocess.Popen", return_value=mock_process):
            with patch("aim.bridge.threading.Thread"):
                pool = ToolProcessPool("aider", count=2, registry=mock_registry)

                statuses = pool.get_status()

                assert len(statuses) == 2
                assert statuses[0]["index"] == 0
                assert statuses[0]["alive"] == True
                assert statuses[0]["return_code"] is None
                assert statuses[1]["index"] == 1
                assert statuses[1]["alive"] == True

    def test_get_status_some_dead(self, mock_registry):
        """Test status with mixed alive/dead processes."""
        # Create two different mock processes
        proc1 = MagicMock()
        proc1.poll.return_value = None  # Alive

        proc2 = MagicMock()
        proc2.poll.return_value = 1  # Dead with exit code 1

        with patch("aim.bridge.subprocess.Popen", side_effect=[proc1, proc2]):
            with patch("aim.bridge.threading.Thread"):
                pool = ToolProcessPool("aider", count=2, registry=mock_registry)

                statuses = pool.get_status()

                assert statuses[0]["alive"] == True
                assert statuses[0]["return_code"] is None
                assert statuses[1]["alive"] == False
                assert statuses[1]["return_code"] == 1


class TestCheckHealth:
    """Test health check functionality."""

    def test_check_health_all_alive(self, mock_registry, mock_process):
        """Test health check with all processes alive."""
        mock_process.poll.return_value = None

        with patch("aim.bridge.subprocess.Popen", return_value=mock_process):
            with patch("aim.bridge.threading.Thread"):
                pool = ToolProcessPool("aider", count=3, registry=mock_registry)

                health = pool.check_health()

                assert health["total"] == 3
                assert health["alive"] == 3
                assert health["dead"] == 0
                assert len(health["instances"]) == 3

    def test_check_health_mixed(self, mock_registry):
        """Test health check with mixed process states."""
        proc1 = MagicMock()
        proc1.poll.return_value = None

        proc2 = MagicMock()
        proc2.poll.return_value = 0

        with patch("aim.bridge.subprocess.Popen", side_effect=[proc1, proc2]):
            with patch("aim.bridge.threading.Thread"):
                pool = ToolProcessPool("aider", count=2, registry=mock_registry)

                health = pool.check_health()

                assert health["total"] == 2
                assert health["alive"] == 1
                assert health["dead"] == 1


class TestShutdown:
    """Test shutdown functionality."""

    def test_shutdown_graceful(self, mock_registry, mock_process):
        """Test graceful shutdown."""
        # Process exits gracefully after terminate
        def poll_side_effect():
            """Return None first time, then 0 (exited)."""
            if not hasattr(poll_side_effect, 'called'):
                poll_side_effect.called = 0
            poll_side_effect.called += 1
            return None if poll_side_effect.called <= 2 else 0

        mock_process.poll.side_effect = poll_side_effect

        with patch("aim.bridge.subprocess.Popen", return_value=mock_process):
            with patch("aim.bridge.threading.Thread"):
                pool = ToolProcessPool("aider", count=1, registry=mock_registry)

                pool.shutdown(timeout=1.0)

                mock_process.terminate.assert_called_once()
                # Should not kill since process exits gracefully
                assert mock_process.kill.call_count == 0

    def test_shutdown_force_kill(self, mock_registry, mock_process):
        """Test shutdown with force kill."""
        # Process doesn't exit gracefully
        mock_process.poll.return_value = None  # Never exits

        with patch("aim.bridge.subprocess.Popen", return_value=mock_process):
            with patch("aim.bridge.threading.Thread"):
                with patch("aim.bridge.time.time", side_effect=[0, 0, 10]):  # Simulate timeout
                    pool = ToolProcessPool("aider", count=1, registry=mock_registry)

                    pool.shutdown(timeout=1.0)

                    mock_process.terminate.assert_called_once()
                    mock_process.kill.assert_called_once()
                    mock_process.wait.assert_called()

    def test_shutdown_multiple_instances(self, mock_registry):
        """Test shutdown with multiple instances."""
        proc1 = MagicMock()
        proc2 = MagicMock()

        # Start as running, then set to exited after terminate
        calls = {'proc1': 0, 'proc2': 0}

        def proc1_poll():
            calls['proc1'] += 1
            return 0 if calls['proc1'] > 1 else None

        def proc2_poll():
            calls['proc2'] += 1
            return 0 if calls['proc2'] > 1 else None

        proc1.poll = proc1_poll
        proc2.poll = proc2_poll

        with patch("aim.bridge.subprocess.Popen", side_effect=[proc1, proc2]):
            with patch("aim.bridge.threading.Thread"):
                pool = ToolProcessPool("aider", count=2, registry=mock_registry)
                pool.shutdown(timeout=1.0)

                # Should call terminate on both instances
                proc1.terminate.assert_called()
                proc2.terminate.assert_called()


class TestRestartInstance:
    """Test instance restart functionality."""

    def test_restart_instance_success(self, mock_registry):
        """Test successful instance restart."""
        old_proc = MagicMock()
        old_proc.poll.return_value = None  # Still running (will be killed)

        new_proc = MagicMock()
        new_proc.poll.return_value = None  # Alive

        with patch("aim.bridge.subprocess.Popen", side_effect=[old_proc, new_proc]):
            with patch("aim.bridge.threading.Thread"):
                pool = ToolProcessPool("aider", count=1, registry=mock_registry)

                # Restart the instance
                result = pool.restart_instance(0)

                assert result == True
                # Should kill the old process since it was still running
                old_proc.kill.assert_called_once()
                old_proc.wait.assert_called_once()

    def test_restart_instance_invalid_index(self, mock_registry, mock_process):
        """Test restart with invalid index."""
        with patch("aim.bridge.subprocess.Popen", return_value=mock_process):
            with patch("aim.bridge.threading.Thread"):
                pool = ToolProcessPool("aider", count=1, registry=mock_registry)

                result = pool.restart_instance(99)
                assert result == False


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_registry(self):
        """Test with empty registry."""
        with pytest.raises(ValueError):
            ToolProcessPool("aider", count=1, registry={"tools": {}})

    def test_zero_count(self, mock_registry, mock_process):
        """Test pool with zero instances."""
        with patch("aim.bridge.subprocess.Popen", return_value=mock_process):
            with patch("aim.bridge.threading.Thread"):
                pool = ToolProcessPool("aider", count=0, registry=mock_registry)

                assert len(pool.instances) == 0
                assert pool.check_health()["total"] == 0

    def test_large_count(self, mock_registry, mock_process):
        """Test pool with many instances."""
        with patch("aim.bridge.subprocess.Popen", return_value=mock_process):
            with patch("aim.bridge.threading.Thread"):
                pool = ToolProcessPool("aider", count=10, registry=mock_registry)

                assert len(pool.instances) == 10
                assert pool.check_health()["total"] == 10
