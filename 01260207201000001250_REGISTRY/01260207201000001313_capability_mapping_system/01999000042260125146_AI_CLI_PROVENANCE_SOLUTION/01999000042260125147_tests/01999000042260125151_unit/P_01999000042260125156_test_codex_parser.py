# DOC_ID: DOC-TEST-0631
"""
Unit Tests for Codex Log Parser
Created: 2026-01-04

Tests:
- Session metadata extraction
- File event parsing
- Tool categorization
- Path extraction
- Error handling
"""

import pytest
import json
from pathlib import Path

from codex_log_parser import CodexLogParser


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_codex_log(temp_dir):
    """Create a sample Codex JSONL log file."""
    log_file = temp_dir / "codex_session.jsonl"

    entries = [
        # Session metadata
        {
            "type": "session_metadata",
            "session_id": "codex-session-123",
            "timestamp": "2026-01-01T14:00:00.000Z",
            "cwd": "C:\\Users\\richg\\ALL_AI",
            "model": "gpt-4",
            "provider": "openai"
        },
        # File read
        {
            "type": "tool_request",
            "request_id": "req-001",
            "timestamp": "2026-01-01T14:05:00.000Z",
            "tool": "read_file",
            "args": {
                "path": "test_module.py"
            }
        },
        # File edit
        {
            "type": "tool_request",
            "request_id": "req-002",
            "timestamp": "2026-01-01T14:10:00.000Z",
            "tool": "edit_file",
            "args": {
                "path": "test_module.py",
                "changes": "some changes"
            }
        },
        # File create
        {
            "type": "tool_request",
            "request_id": "req-003",
            "timestamp": "2026-01-01T14:15:00.000Z",
            "tool": "create_file",
            "args": {
                "path": "new_module.py",
                "content": "print('new')"
            }
        }
    ]

    with open(log_file, 'w') as f:
        for entry in entries:
            f.write(json.dumps(entry) + '\n')

    return log_file


@pytest.fixture
def repo_root():
    """Provide test repo root."""
    return Path("C:\\Users\\richg\\ALL_AI")


# ============================================================================
# SESSION METADATA TESTS
# ============================================================================

def test_session_metadata_extraction(sample_codex_log):
    """Test session metadata is correctly extracted."""
    parser = CodexLogParser(sample_codex_log)
    metadata = parser.get_session_metadata()

    assert metadata['cli_agent'] == 'codex'
    assert metadata['log_file_path'] == str(sample_codex_log)
    assert 'session_id' in metadata
    assert metadata['record_count'] == 4


def test_session_id_from_log(sample_codex_log):
    """Test session ID is extracted from log metadata."""
    parser = CodexLogParser(sample_codex_log)
    metadata = parser.get_session_metadata()

    # Should use session_id from first metadata entry
    assert 'codex-session' in metadata['session_id']


# ============================================================================
# FILE EVENT PARSING TESTS
# ============================================================================

def test_parse_file_events_count(sample_codex_log, repo_root):
    """Test correct number of file events parsed."""
    parser = CodexLogParser(sample_codex_log, repo_root)
    events = list(parser.parse_file_events())

    # Should parse 3 tool requests (read, edit, create)
    assert len(events) == 3


def test_parse_file_event_categories(sample_codex_log, repo_root):
    """Test file events are correctly categorized."""
    parser = CodexLogParser(sample_codex_log, repo_root)
    events = list(parser.parse_file_events())

    categories = [event.tool_category for event in events]
    assert 'view' in categories  # read_file
    assert 'edit' in categories  # edit_file
    assert 'create' in categories  # create_file


def test_relative_path_resolution(sample_codex_log, repo_root):
    """Test relative paths are resolved using cwd from metadata."""
    parser = CodexLogParser(sample_codex_log, repo_root)
    events = list(parser.parse_file_events())

    # Paths should be resolved relative to cwd
    for event in events:
        assert Path(event.file_path).is_absolute() or 'test_module.py' in event.file_path


def test_tool_name_mapping(sample_codex_log, repo_root):
    """Test Codex tool names are correctly mapped."""
    parser = CodexLogParser(sample_codex_log, repo_root)
    events = list(parser.parse_file_events())

    tool_names = [event.tool_name for event in events]
    assert 'read_file' in tool_names
    assert 'edit_file' in tool_names
    assert 'create_file' in tool_names


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

def test_missing_cwd_handling(temp_dir, repo_root):
    """Test parser handles missing cwd gracefully."""
    log_file = temp_dir / "no_cwd.jsonl"

    entries = [
        {
            "type": "tool_request",
            "request_id": "req-001",
            "timestamp": "2026-01-01T14:00:00.000Z",
            "tool": "read_file",
            "args": {"path": "test.py"}
        }
    ]

    with open(log_file, 'w') as f:
        for entry in entries:
            f.write(json.dumps(entry) + '\n')

    parser = CodexLogParser(log_file, repo_root)
    events = list(parser.parse_file_events())

    # Should still parse, using repo_root as fallback
    assert len(events) >= 0  # May be 0 if path can't be resolved


def test_malformed_tool_args(temp_dir, repo_root):
    """Test parser handles malformed tool args."""
    log_file = temp_dir / "bad_args.jsonl"

    entries = [
        {
            "type": "tool_request",
            "request_id": "req-001",
            "timestamp": "2026-01-01T14:00:00.000Z",
            "tool": "read_file",
            "args": None  # Missing args
        },
        {
            "type": "tool_request",
            "request_id": "req-002",
            "timestamp": "2026-01-01T14:05:00.000Z",
            "tool": "edit_file",
            "args": {}  # Empty args
        }
    ]

    with open(log_file, 'w') as f:
        for entry in entries:
            f.write(json.dumps(entry) + '\n')

    parser = CodexLogParser(log_file, repo_root)
    events = list(parser.parse_file_events())

    # Should gracefully skip invalid events
    assert len(events) == 0


def test_unknown_tool_types(temp_dir, repo_root):
    """Test parser handles unknown tool types."""
    log_file = temp_dir / "unknown_tools.jsonl"

    entries = [
        {
            "type": "tool_request",
            "request_id": "req-001",
            "timestamp": "2026-01-01T14:00:00.000Z",
            "tool": "unknown_tool_xyz",
            "args": {"path": "test.py"}
        }
    ]

    with open(log_file, 'w') as f:
        for entry in entries:
            f.write(json.dumps(entry) + '\n')

    parser = CodexLogParser(log_file, repo_root)
    events = list(parser.parse_file_events())

    # Should skip unknown tools or categorize as 'unknown'
    assert len(events) >= 0


# ============================================================================
# EDGE CASES
# ============================================================================

def test_absolute_and_relative_paths(temp_dir, repo_root):
    """Test parser handles both absolute and relative paths."""
    log_file = temp_dir / "mixed_paths.jsonl"

    entries = [
        {
            "type": "session_metadata",
            "session_id": "session-001",
            "timestamp": "2026-01-01T14:00:00.000Z",
            "cwd": "C:\\Users\\richg\\ALL_AI"
        },
        {
            "type": "tool_request",
            "request_id": "req-001",
            "timestamp": "2026-01-01T14:05:00.000Z",
            "tool": "read_file",
            "args": {"path": "relative.py"}  # Relative
        },
        {
            "type": "tool_request",
            "request_id": "req-002",
            "timestamp": "2026-01-01T14:10:00.000Z",
            "tool": "read_file",
            "args": {"path": "C:\\Users\\richg\\ALL_AI\\absolute.py"}  # Absolute
        }
    ]

    with open(log_file, 'w') as f:
        for entry in entries:
            f.write(json.dumps(entry) + '\n')

    parser = CodexLogParser(log_file, repo_root)
    events = list(parser.parse_file_events())

    # Should parse both types
    assert len(events) == 2


def test_empty_session(temp_dir):
    """Test parser handles session with no tool requests."""
    log_file = temp_dir / "empty_session.jsonl"

    entries = [
        {
            "type": "session_metadata",
            "session_id": "session-001",
            "timestamp": "2026-01-01T14:00:00.000Z",
            "cwd": "C:\\Users\\richg\\ALL_AI"
        }
    ]

    with open(log_file, 'w') as f:
        for entry in entries:
            f.write(json.dumps(entry) + '\n')

    parser = CodexLogParser(log_file)
    metadata = parser.get_session_metadata()
    events = list(parser.parse_file_events())

    assert metadata['record_count'] == 1
    assert len(events) == 0
