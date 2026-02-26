# DOC_ID: DOC-TEST-0632
"""
Unit Tests for Copilot Log Parser
Created: 2026-01-04

Tests:
- Intent signal extraction from command history
- Keyword detection
- Prompt hashing
- Error handling
"""

import pytest
import json
from pathlib import Path

from copilot_log_parser import CopilotCommandHistoryParser


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_copilot_history(temp_dir):
    """Create a sample Copilot command history JSON file."""
    history_file = temp_dir / "command-history-state.json"

    data = {
        "commands": [
            {
                "timestamp": "2026-01-01T09:00:00.000Z",
                "prompt": "Create a new feature for user authentication",
                "files_mentioned": ["auth.py", "user_model.py"]
            },
            {
                "timestamp": "2026-01-02T10:00:00.000Z",
                "prompt": "Migrate the old authentication system to the new framework",
                "files_mentioned": ["old_auth.py"]
            },
            {
                "timestamp": "2026-01-03T11:00:00.000Z",
                "prompt": "Deprecate the legacy API endpoints and remove unused code",
                "files_mentioned": ["api.py"]
            },
            {
                "timestamp": "2026-01-04T12:00:00.000Z",
                "prompt": "Fix the login bug",
                "files_mentioned": []
            }
        ]
    }

    history_file.write_text(json.dumps(data, indent=2))
    return history_file


# ============================================================================
# INTENT SIGNAL TESTS
# ============================================================================

def test_parse_intent_signals_count(sample_copilot_history):
    """Test correct number of intent signals extracted."""
    parser = CopilotCommandHistoryParser(sample_copilot_history)
    signals = list(parser.parse_intent_signals())

    # Should extract signals from all 4 commands
    assert len(signals) == 4


def test_migration_intent_detection(sample_copilot_history):
    """Test migration intent is correctly detected."""
    parser = CopilotCommandHistoryParser(sample_copilot_history)
    signals = list(parser.parse_intent_signals())

    # Second command has "migrate" keyword
    migration_signals = [s for s in signals if s.migration_intent]
    assert len(migration_signals) >= 1
    assert 'migrate' in migration_signals[0].detected_keywords


def test_deprecation_intent_detection(sample_copilot_history):
    """Test deprecation intent is correctly detected."""
    parser = CopilotCommandHistoryParser(sample_copilot_history)
    signals = list(parser.parse_intent_signals())

    # Third command has "deprecate" keyword
    deprecation_signals = [s for s in signals if s.deprecation_intent]
    assert len(deprecation_signals) >= 1
    assert 'deprecate' in deprecation_signals[0].detected_keywords


def test_removal_intent_detection(sample_copilot_history):
    """Test removal intent is correctly detected."""
    parser = CopilotCommandHistoryParser(sample_copilot_history)
    signals = list(parser.parse_intent_signals())

    # Third command has "remove" keyword
    removal_signals = [s for s in signals if s.removal_intent]
    assert len(removal_signals) >= 1
    assert 'remove' in removal_signals[0].detected_keywords


def test_no_intent_detection(sample_copilot_history):
    """Test commands without intent keywords return false."""
    parser = CopilotCommandHistoryParser(sample_copilot_history)
    signals = list(parser.parse_intent_signals())

    # Fourth command ("Fix the login bug") should have no intents
    no_intent_signals = [s for s in signals if not (s.migration_intent or s.deprecation_intent or s.removal_intent)]
    assert len(no_intent_signals) >= 1


# ============================================================================
# PROMPT HASHING TESTS
# ============================================================================

def test_prompt_hashing(sample_copilot_history):
    """Test prompts are hashed (not stored raw)."""
    parser = CopilotCommandHistoryParser(sample_copilot_history)
    signals = list(parser.parse_intent_signals())

    for signal in signals:
        # SHA256 hash should be 64 hex characters
        assert len(signal.prompt_hash) == 64
        assert all(c in '0123456789abcdef' for c in signal.prompt_hash)


def test_same_prompt_same_hash(temp_dir):
    """Test same prompt generates same hash."""
    history_file = temp_dir / "same_prompts.json"

    data = {
        "commands": [
            {"timestamp": "2026-01-01T09:00:00.000Z", "prompt": "Identical prompt"},
            {"timestamp": "2026-01-02T10:00:00.000Z", "prompt": "Identical prompt"}
        ]
    }

    history_file.write_text(json.dumps(data))

    parser = CopilotCommandHistoryParser(history_file)
    signals = list(parser.parse_intent_signals())

    # Same prompt should generate same hash
    assert signals[0].prompt_hash == signals[1].prompt_hash


def test_different_prompts_different_hashes(temp_dir):
    """Test different prompts generate different hashes."""
    history_file = temp_dir / "diff_prompts.json"

    data = {
        "commands": [
            {"timestamp": "2026-01-01T09:00:00.000Z", "prompt": "First prompt"},
            {"timestamp": "2026-01-02T10:00:00.000Z", "prompt": "Second prompt"}
        ]
    }

    history_file.write_text(json.dumps(data))

    parser = CopilotCommandHistoryParser(history_file)
    signals = list(parser.parse_intent_signals())

    # Different prompts should generate different hashes
    assert signals[0].prompt_hash != signals[1].prompt_hash


# ============================================================================
# KEYWORD DETECTION TESTS
# ============================================================================

def test_keyword_case_insensitive(temp_dir):
    """Test keyword detection is case-insensitive."""
    history_file = temp_dir / "case_test.json"

    data = {
        "commands": [
            {"timestamp": "2026-01-01T09:00:00.000Z", "prompt": "MIGRATE this code"},
            {"timestamp": "2026-01-02T10:00:00.000Z", "prompt": "Deprecate the old system"},
            {"timestamp": "2026-01-03T11:00:00.000Z", "prompt": "remove unused files"}
        ]
    }

    history_file.write_text(json.dumps(data))

    parser = CopilotCommandHistoryParser(history_file)
    signals = list(parser.parse_intent_signals())

    # All intents should be detected despite case differences
    assert any(s.migration_intent for s in signals)
    assert any(s.deprecation_intent for s in signals)
    assert any(s.removal_intent for s in signals)


def test_multiple_keywords_in_one_prompt(temp_dir):
    """Test multiple intent keywords in single prompt."""
    history_file = temp_dir / "multiple_keywords.json"

    data = {
        "commands": [
            {
                "timestamp": "2026-01-01T09:00:00.000Z",
                "prompt": "Migrate to new system, deprecate old one, and remove legacy code"
            }
        ]
    }

    history_file.write_text(json.dumps(data))

    parser = CopilotCommandHistoryParser(history_file)
    signals = list(parser.parse_intent_signals())

    # Should detect all three intents
    assert signals[0].migration_intent
    assert signals[0].deprecation_intent
    assert signals[0].removal_intent
    assert len(signals[0].detected_keywords) >= 3


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

def test_empty_history_file(temp_dir):
    """Test parser handles empty command history."""
    history_file = temp_dir / "empty.json"
    history_file.write_text(json.dumps({"commands": []}))

    parser = CopilotCommandHistoryParser(history_file)
    signals = list(parser.parse_intent_signals())

    assert len(signals) == 0


def test_missing_commands_key(temp_dir):
    """Test parser handles missing 'commands' key."""
    history_file = temp_dir / "no_commands.json"
    history_file.write_text(json.dumps({}))

    parser = CopilotCommandHistoryParser(history_file)
    signals = list(parser.parse_intent_signals())

    assert len(signals) == 0


def test_malformed_command_entries(temp_dir):
    """Test parser handles malformed command entries."""
    history_file = temp_dir / "malformed.json"

    data = {
        "commands": [
            {},  # Empty command
            {"timestamp": "2026-01-01T09:00:00.000Z"},  # Missing prompt
            {"prompt": "Valid prompt"},  # Missing timestamp
            {"timestamp": "2026-01-02T10:00:00.000Z", "prompt": "migrate code"}  # Valid
        ]
    }

    history_file.write_text(json.dumps(data))

    parser = CopilotCommandHistoryParser(history_file)
    signals = list(parser.parse_intent_signals())

    # Should skip invalid entries and parse valid ones
    assert len(signals) >= 1


def test_invalid_json_file(temp_dir):
    """Test parser handles invalid JSON."""
    history_file = temp_dir / "invalid.json"
    history_file.write_text("this is not valid JSON")

    parser = CopilotCommandHistoryParser(history_file)

    # Should handle gracefully (return empty list or raise specific error)
    try:
        signals = list(parser.parse_intent_signals())
        assert len(signals) == 0
    except json.JSONDecodeError:
        # Also acceptable - let caller handle
        pass


# ============================================================================
# EDGE CASES
# ============================================================================

def test_unicode_in_prompts(temp_dir):
    """Test parser handles Unicode characters in prompts."""
    history_file = temp_dir / "unicode.json"

    data = {
        "commands": [
            {"timestamp": "2026-01-01T09:00:00.000Z", "prompt": "Migrate código to new système 日本語"}
        ]
    }

    history_file.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')

    parser = CopilotCommandHistoryParser(history_file)
    signals = list(parser.parse_intent_signals())

    # Should still detect "Migrate" keyword
    assert signals[0].migration_intent


def test_very_long_prompt(temp_dir):
    """Test parser handles very long prompts."""
    history_file = temp_dir / "long_prompt.json"

    long_prompt = "migrate " + "a" * 10000 + " to new system"

    data = {
        "commands": [
            {"timestamp": "2026-01-01T09:00:00.000Z", "prompt": long_prompt}
        ]
    }

    history_file.write_text(json.dumps(data))

    parser = CopilotCommandHistoryParser(history_file)
    signals = list(parser.parse_intent_signals())

    # Should parse and detect intent
    assert signals[0].migration_intent
    assert len(signals[0].prompt_hash) == 64  # Hash should still be fixed length


def test_special_characters_in_prompts(temp_dir):
    """Test parser handles special characters."""
    history_file = temp_dir / "special_chars.json"

    data = {
        "commands": [
            {"timestamp": "2026-01-01T09:00:00.000Z", "prompt": "Migrate <code> & \"deprecate\" the old system!"}
        ]
    }

    history_file.write_text(json.dumps(data))

    parser = CopilotCommandHistoryParser(history_file)
    signals = list(parser.parse_intent_signals())

    # Should detect both keywords despite special characters
    assert signals[0].migration_intent
    assert signals[0].deprecation_intent
