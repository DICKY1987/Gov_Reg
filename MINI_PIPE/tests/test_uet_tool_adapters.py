"""
Unit Tests for UET Contract-Compliant Tool Adapters

Tests for contracts/uet_tool_adapters.py
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.acms.uet_submodule_io_contracts import ToolRunRequestV1, ToolRunResultV1
from src.acms.uet_tool_adapters import (
    build_aider_tool_request,
    build_error_event,
    run_aider,
    run_pytest,
    run_tool,
)


class TestBuildAiderToolRequest:
    """Tests for build_aider_tool_request()"""

    def test_basic_request_structure(self, tmp_path):
        """Test building a basic Aider request."""
        prompt_file = str(tmp_path / "prompt.txt")
        workspace_root = str(tmp_path)

        request = build_aider_tool_request(
            model_name="gpt-4",
            prompt_file=prompt_file,
            file_scope=["src/module.py"],
            workspace_root=workspace_root,
        )

        assert request.tool_id == "aider"
        assert request.cmd[0] == "aider"
        assert "--no-auto-commits" in request.cmd
        assert "--yes" in request.cmd
        assert "--model" in request.cmd
        assert "gpt-4" in request.cmd
        assert "--message-file" in request.cmd
        assert prompt_file in request.cmd
        assert "src/module.py" in request.cmd
        assert request.cwd == workspace_root
        assert request.env["AIDER_NO_AUTO_COMMITS"] == "1"

    def test_multiple_files(self, tmp_path):
        """Test Aider request with multiple files."""
        request = build_aider_tool_request(
            model_name="gpt-4",
            prompt_file="/tmp/prompt.txt",
            file_scope=["src/a.py", "src/b.py", "tests/test_a.py"],
            workspace_root=str(tmp_path),
        )

        assert "src/a.py" in request.cmd
        assert "src/b.py" in request.cmd
        assert "tests/test_a.py" in request.cmd

    def test_custom_timeout(self, tmp_path):
        """Test custom timeout setting."""
        request = build_aider_tool_request(
            model_name="gpt-4",
            prompt_file="/tmp/prompt.txt",
            file_scope=["src/module.py"],
            workspace_root=str(tmp_path),
            timeout_seconds=3600,
        )

        assert request.timeout_seconds == 3600

    def test_context_included(self, tmp_path):
        """Test context is preserved in request."""
        context = {
            "run_id": "run-001",
            "ws_id": "ws-acms-001",
            "task_id": "task-003",
        }

        request = build_aider_tool_request(
            model_name="gpt-4",
            prompt_file="/tmp/prompt.txt",
            file_scope=["src/module.py"],
            workspace_root=str(tmp_path),
            context=context,
        )

        assert request.context == context


class TestRunTool:
    """Tests for run_tool() - the core execution function"""

    def test_successful_execution(self, tmp_path):
        """Test successful tool execution."""
        request = ToolRunRequestV1(
            tool_id="python",
            cmd=["python", "-c", "print('hello')"],
            cwd=str(tmp_path),
            env={},
            timeout_seconds=10,
        )

        result = run_tool(request)

        assert result.success
        assert result.exit_code == 0
        assert "hello" in result.stdout
        assert result.stderr == ""
        assert not result.timed_out
        assert result.duration_seconds > 0

    def test_nonzero_exit_code(self, tmp_path):
        """Test tool with non-zero exit code."""
        # Use a command that fails on all platforms
        request = ToolRunRequestV1(
            tool_id="false",
            cmd=["python", "-c", "import sys; sys.exit(1)"],
            cwd=str(tmp_path),
            env={},
            timeout_seconds=10,
        )

        result = run_tool(request)

        assert not result.success
        assert result.exit_code == 1
        assert not result.timed_out

    def test_timeout_handling(self, tmp_path):
        """Test timeout is properly handled."""
        # Command that sleeps for 10 seconds
        request = ToolRunRequestV1(
            tool_id="sleep",
            cmd=["python", "-c", "import time; time.sleep(10)"],
            cwd=str(tmp_path),
            env={},
            timeout_seconds=1,  # 1 second timeout
        )

        result = run_tool(request)

        assert not result.success
        assert result.exit_code == -1
        assert result.timed_out
        assert "timed out" in result.stderr.lower()

    def test_binary_not_found(self, tmp_path):
        """Test handling of missing binary."""
        request = ToolRunRequestV1(
            tool_id="nonexistent",
            cmd=["this-binary-does-not-exist-xyz123"],
            cwd=str(tmp_path),
            env={},
            timeout_seconds=10,
        )

        result = run_tool(request)

        assert not result.success
        assert result.exit_code == -2
        assert "not found" in result.stderr.lower()

    def test_invalid_working_directory(self):
        """Test handling of invalid working directory."""
        request = ToolRunRequestV1(
            tool_id="test",
            cmd=["echo", "hello"],
            cwd="/this/path/does/not/exist/xyz123",
            env={},
            timeout_seconds=10,
        )

        result = run_tool(request)

        assert not result.success
        assert result.exit_code == -3
        assert "does not exist" in result.stderr

    def test_empty_command_list(self, tmp_path):
        """Test handling of empty command list."""
        request = ToolRunRequestV1(
            tool_id="test",
            cmd=[],
            cwd=str(tmp_path),
            env={},
            timeout_seconds=10,
        )

        result = run_tool(request)

        assert not result.success
        assert result.exit_code == -3
        assert "empty command" in result.stderr.lower()

    def test_never_raises_exceptions(self, tmp_path):
        """Test that run_tool NEVER raises exceptions."""
        # Try various problematic inputs
        problematic_requests = [
            ToolRunRequestV1("test", [], str(tmp_path), {}, 10),
            ToolRunRequestV1("test", ["nonexistent"], str(tmp_path), {}, 10),
            ToolRunRequestV1("test", ["echo"], "/invalid/path", {}, 10),
        ]

        for request in problematic_requests:
            try:
                result = run_tool(request)
                # Should always return a result, never raise
                assert isinstance(result, ToolRunResultV1)
                assert not result.success
                assert result.exit_code < 0
            except Exception as e:
                pytest.fail(f"run_tool raised exception: {e}")


class TestRunAider:
    """Tests for run_aider() - Aider-specific adapter"""

    def test_validates_tool_id(self, tmp_path):
        """Test that run_aider validates tool_id."""
        request = ToolRunRequestV1(
            tool_id="not-aider",  # Wrong tool_id
            cmd=["echo", "test"],
            cwd=str(tmp_path),
            env={},
            timeout_seconds=10,
        )

        result = run_aider(request)

        assert not result.success
        assert result.exit_code == -3
        assert "expected tool_id='aider'" in result.stderr.lower()

    @patch("src.acms.uet_tool_adapters.run_tool")
    def test_calls_run_tool(self, mock_run_tool, tmp_path):
        """Test that run_aider delegates to run_tool."""
        mock_result = ToolRunResultV1(
            tool_id="aider",
            exit_code=0,
            stdout="success",
            stderr="",
            duration_seconds=1.0,
        )
        mock_run_tool.return_value = mock_result

        request = build_aider_tool_request(
            model_name="gpt-4",
            prompt_file="/tmp/prompt.txt",
            file_scope=["src/module.py"],
            workspace_root=str(tmp_path),
        )

        result = run_aider(request)

        mock_run_tool.assert_called_once_with(request)
        assert result == mock_result


class TestRunPytest:
    """Tests for run_pytest() helper"""

    @patch("src.acms.uet_tool_adapters.run_tool")
    def test_pytest_request_structure(self, mock_run_tool, tmp_path):
        """Test pytest request building."""
        mock_run_tool.return_value = ToolRunResultV1(
            tool_id="pytest",
            exit_code=0,
            stdout="",
            stderr="",
            duration_seconds=1.0,
        )

        result = run_pytest(
            test_paths=["tests/"],
            workspace_root=str(tmp_path),
        )

        # Extract the request that was passed to run_tool
        call_args = mock_run_tool.call_args
        request = call_args[0][0]

        assert request.tool_id == "pytest"
        assert "pytest" in request.cmd
        assert "-v" in request.cmd
        assert "tests/" in request.cmd
        assert request.cwd == str(tmp_path)


class TestBuildErrorEvent:
    """Tests for build_error_event() helper"""

    def test_basic_error_event(self):
        from src.acms.uet_submodule_io_contracts import ErrorSeverity

        error = build_error_event(
            message="Something went wrong",
            severity=ErrorSeverity.ERROR,
        )

        assert error.message == "Something went wrong"
        assert error.severity == ErrorSeverity.ERROR
        assert error.error_id.startswith("err-")
        assert error.timestamp is not None

    def test_error_with_context(self):
        """Test error event with context."""
        from src.acms.uet_submodule_io_contracts import ErrorSeverity

        error = build_error_event(
            message="Tool failed",
            severity=ErrorSeverity.WARNING,
            error_code="TOOL_FAILURE",
            context={"tool_id": "aider", "exit_code": 1},
        )

        assert error.error_code == "TOOL_FAILURE"
        assert error.context["tool_id"] == "aider"
        assert error.context["exit_code"] == 1


class TestToolProfiles:
    """Tests for tool profile loading"""

    def test_load_tool_profiles(self):
        """Test loading tool profiles from config."""
        from src.acms.uet_tool_adapters import load_tool_profiles

        # Should load from config/tool_profiles.json
        try:
            profiles = load_tool_profiles()
            assert "aider" in profiles
            assert "pytest" in profiles
        except FileNotFoundError:
            pytest.skip("Tool profiles not found (expected in fresh install)")

    def test_get_tool_profile(self):
        """Test getting a specific tool profile."""
        from src.acms.uet_tool_adapters import get_tool_profile

        try:
            profile = get_tool_profile("aider")
            assert profile["tool_id"] == "aider"
            assert profile["contract_version"] == "AIDER_CONTRACT_V1"
        except (FileNotFoundError, KeyError):
            pytest.skip("Tool profiles not configured")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
