# DOC_ID: DOC-TEST-0630
"""
Unit Tests for Claude Log Parser
Created: 2026-01-04

Tests:
- Session metadata extraction
- File event parsing
- Intent signal detection
- Path normalization
- Repo scoping
- Error handling
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime

from claude_log_parser import ClaudeLogParser, FileEvent, IntentSignal


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_claude_log(temp_dir):
    """Create a sample Claude JSONL log file."""
    log_file = temp_dir / "claude_test.jsonl"

    entries = [
        # Session start
        {
            "type": "session_start",
            "timestamp": "2026-01-01T10:00:00.000Z",
            "sessionId": "session-001"
        },
        # Read file event
        {
            "type": "tool_use",
            "messageId": "msg-001",
            "timestamp": "2026-01-01T10:05:00.000Z",
            "tool": {
                "name": "read_file",
                "input": {
                    "file_path": "C:\\Users\\richg\\ALL_AI\\test_file.py"
                }
            }
        },
        # Edit file event
        {
            "type": "tool_use",
            "messageId": "msg-002",
            "timestamp": "2026-01-01T10:10:00.000Z",
            "tool": {
                "name": "edit_file",
                "input": {
                    "file_path": "C:\\Users\\richg\\ALL_AI\\test_file.py",
                    "old_string": "old code",
                    "new_string": "new code"
                }
            }
        },
        # Write file event
        {
            "type": "tool_use",
            "messageId": "msg-003",
            "timestamp": "2026-01-01T10:15:00.000Z",
            "tool": {
                "name": "write_file",
                "input": {
                    "file_path": "C:\\Users\\richg\\ALL_AI\\new_file.py",
                    "content": "print('hello')"
                }
            }
        },
        # User message with intent keywords
        {
            "type": "user_message",
            "messageId": "msg-004",
            "timestamp": "2026-01-01T10:20:00.000Z",
            "content": "Let's migrate this code to the new system and deprecate the old one"
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

def test_session_metadata_extraction(sample_claude_log):
    """Test session metadata is correctly extracted."""
    parser = ClaudeLogParser(sample_claude_log)
    metadata = parser.get_session_metadata()

    assert metadata['cli_agent'] == 'claude'
    assert metadata['log_file_path'] == str(sample_claude_log)
    assert 'session_id' in metadata
    assert 'start_time' in metadata
    assert 'record_count' in metadata
    assert metadata['record_count'] == 5


def test_session_id_generation(sample_claude_log):
    """Test session ID is consistently generated."""
    parser1 = ClaudeLogParser(sample_claude_log)
    parser2 = ClaudeLogParser(sample_claude_log)

    metadata1 = parser1.get_session_metadata()
    metadata2 = parser2.get_session_metadata()

    # Same file should generate same session ID
    assert metadata1['session_id'] == metadata2['session_id']


# ============================================================================
# FILE EVENT PARSING TESTS
# ============================================================================

def test_parse_file_events_count(sample_claude_log, repo_root):
    """Test correct number of file events parsed."""
    parser = ClaudeLogParser(sample_claude_log, repo_root)
    events = list(parser.parse_file_events())

    # Should parse 3 file events (read, edit, write)
    assert len(events) == 3


def test_parse_file_event_categories(sample_claude_log, repo_root):
    """Test file events are correctly categorized."""
    parser = ClaudeLogParser(sample_claude_log, repo_root)
    events = list(parser.parse_file_events())

    categories = [event.tool_category for event in events]
    assert 'view' in categories  # read_file
    assert 'edit' in categories  # edit_file
    assert 'create' in categories  # write_file


def test_file_event_structure(sample_claude_log, repo_root):
    """Test file event has all required fields."""
    parser = ClaudeLogParser(sample_claude_log, repo_root)
    events = list(parser.parse_file_events())

    event = events[0]
    assert hasattr(event, 'session_id')
    assert hasattr(event, 'file_path')
    assert hasattr(event, 'timestamp')
    assert hasattr(event, 'tool_name')
    assert hasattr(event, 'tool_category')
    assert hasattr(event, 'message_id')


def test_file_path_extraction(sample_claude_log, repo_root):
    """Test file paths are correctly extracted."""
    parser = ClaudeLogParser(sample_claude_log, repo_root)
    events = list(parser.parse_file_events())

    paths = [event.file_path for event in events]
    assert any('test_file.py' in path for path in paths)
    assert any('new_file.py' in path for path in paths)


# ============================================================================
# INTENT SIGNAL TESTS
# ============================================================================

def test_parse_intent_signals_count(sample_claude_log):
    """Test intent signals are detected."""
    parser = ClaudeLogParser(sample_claude_log)
    signals = list(parser.parse_intent_signals())

    # Should detect migration and deprecation intent
    assert len(signals) > 0


def test_intent_signal_detection(sample_claude_log):
    """Test specific intents are correctly detected."""
    parser = ClaudeLogParser(sample_claude_log)
    signals = list(parser.parse_intent_signals())

    # Should have at least one signal with migration and deprecation
    has_migration = any(s.migration_intent for s in signals)
    has_deprecation = any(s.deprecation_intent for s in signals)

    assert has_migration
    assert has_deprecation


def test_intent_signal_structure(sample_claude_log):
    """Test intent signal has all required fields."""
    parser = ClaudeLogParser(sample_claude_log)
    signals = list(parser.parse_intent_signals())

    if signals:
        signal = signals[0]
        assert hasattr(signal, 'prompt_hash')
        assert hasattr(signal, 'detected_keywords')
        assert hasattr(signal, 'migration_intent')
        assert hasattr(signal, 'deprecation_intent')
        assert hasattr(signal, 'removal_intent')
        assert hasattr(signal, 'timestamp')


def test_prompt_hashing(sample_claude_log):
    """Test prompts are hashed (not stored raw)."""
    parser = ClaudeLogParser(sample_claude_log)
    signals = list(parser.parse_intent_signals())

    if signals:
        signal = signals[0]
        # SHA256 hash should be 64 hex characters
        assert len(signal.prompt_hash) == 64
        assert all(c in '0123456789abcdef' for c in signal.prompt_hash)


# ============================================================================
# REPO SCOPING TESTS
# ============================================================================

def test_repo_scoping_filters_external_files(temp_dir):
    """Test files outside repo are filtered."""
    log_file = temp_dir / "scoped_test.jsonl"

    entries = [
        {
            "type": "tool_use",
            "messageId": "msg-001",
            "timestamp": "2026-01-01T10:00:00.000Z",
            "tool": {
                "name": "read_file",
                "input": {
                    "file_path": "C:\\Windows\\System32\\config.txt"  # Outside repo
                }
            }
        },
        {
            "type": "tool_use",
            "messageId": "msg-002",
            "timestamp": "2026-01-01T10:05:00.000Z",
            "tool": {
                "name": "read_file",
                "input": {
                    "file_path": "C:\\Users\\richg\\ALL_AI\\test.py"  # Inside repo
                }
            }
        }
    ]

    with open(log_file, 'w') as f:
        for entry in entries:
            f.write(json.dumps(entry) + '\n')

    repo_root = Path("C:\\Users\\richg\\ALL_AI")
    parser = ClaudeLogParser(log_file, repo_root)
    events = list(parser.parse_file_events())

    # Should only parse the file inside repo
    assert len(events) == 1
    assert 'test.py' in events[0].file_path


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

def test_malformed_json_handling(temp_dir):
    """Test parser handles malformed JSON gracefully."""
    log_file = temp_dir / "malformed.jsonl"

    with open(log_file, 'w') as f:
        f.write('{"valid": "json"}\n')
        f.write('this is not json\n')
        f.write('{"another": "valid"}\n')

    parser = ClaudeLogParser(log_file)

    # Should not crash, but continue parsing valid lines
    metadata = parser.get_session_metadata()
    assert metadata['record_count'] == 3  # Counts all lines, even malformed


def test_missing_fields_handling(temp_dir):
    """Test parser handles missing fields gracefully."""
    log_file = temp_dir / "missing_fields.jsonl"

    entries = [
        {"type": "tool_use"},  # Missing messageId, timestamp, tool
        {
            "type": "tool_use",
            "messageId": "msg-001",
            "timestamp": "2026-01-01T10:00:00.000Z",
            "tool": {}  # Missing name and input
        }
    ]

    with open(log_file, 'w') as f:
        for entry in entries:
            f.write(json.dumps(entry) + '\n')

    parser = ClaudeLogParser(log_file)
    events = list(parser.parse_file_events())

    # Should gracefully skip invalid events
    assert len(events) == 0


def test_empty_log_file(temp_dir):
    """Test parser handles empty log file."""
    log_file = temp_dir / "empty.jsonl"
    log_file.touch()

    parser = ClaudeLogParser(log_file)
    metadata = parser.get_session_metadata()
    events = list(parser.parse_file_events())
    signals = list(parser.parse_intent_signals())

    assert metadata['record_count'] == 0
    assert len(events) == 0
    assert len(signals) == 0


# ============================================================================
# EDGE CASES
# ============================================================================

def test_unicode_handling(temp_dir, repo_root):
    """Test parser handles Unicode characters."""
    log_file = temp_dir / "unicode.jsonl"

    entry = {
        "type": "user_message",
        "messageId": "msg-001",
        "timestamp": "2026-01-01T10:00:00.000Z",
        "content": "Let's migrate the código to the new système 日本語"
    }

    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    parser = ClaudeLogParser(log_file, repo_root)
    signals = list(parser.parse_intent_signals())

    # Should still detect "migrate" keyword
    assert any(s.migration_intent for s in signals)


def test_large_file_path(temp_dir, repo_root):
    """Test parser handles very long file paths."""
    log_file = temp_dir / "long_path.jsonl"

    # Create a very long path
    long_path = "C:\\Users\\richg\\ALL_AI\\" + "a" * 200 + "\\test.py"

    entry = {
        "type": "tool_use",
        "messageId": "msg-001",
        "timestamp": "2026-01-01T10:00:00.000Z",
        "tool": {
            "name": "read_file",
            "input": {"file_path": long_path}
        }
    }

    with open(log_file, 'w') as f:
        f.write(json.dumps(entry) + '\n')

    parser = ClaudeLogParser(log_file, repo_root)
    events = list(parser.parse_file_events())

    # Should parse even with long path
    assert len(events) == 1
