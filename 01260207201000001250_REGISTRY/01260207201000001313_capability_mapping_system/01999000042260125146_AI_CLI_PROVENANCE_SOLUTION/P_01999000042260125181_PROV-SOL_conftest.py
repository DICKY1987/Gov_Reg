# DOC_ID: DOC-TEST-PROVENANCE-001
"""
Pytest Configuration for AI CLI Provenance Solution
Created: 2026-01-04

This file provides:
- Common test fixtures
- Path configuration for imports
- Test data factories
- Mock objects for external dependencies
"""

import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import pytest

# ============================================================================
# PATH SETUP
# ============================================================================

# Add solution root to Python path for imports
SOLUTION_ROOT = Path(__file__).parent
sys.path.insert(0, str(SOLUTION_ROOT))

# Parent directory paths (read-only integration)
PARENT_ROOT = SOLUTION_ROOT.parent
DOC_ID_REGISTRY_PATH = PARENT_ROOT / "RUNTIME" / "doc_id" / "SUB_DOC_ID" / "5_REGISTRY_DATA" / "DOC_ID_REGISTRY.yaml"
RELATIONSHIP_INDEX_PATH = PARENT_ROOT / "RUNTIME" / "relationship_index" / "SUB_RELATIONSHIP_INDEX" / "data" / "RELATIONSHIP_INDEX.json"


# ============================================================================
# TEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (may require external files)"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test (isolated, no external dependencies)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_logs: mark test as requiring real AI CLI logs"
    )


# ============================================================================
# COMMON FIXTURES - FILE SYSTEM
# ============================================================================

@pytest.fixture
def temp_dir():
    """Provide a temporary directory that's cleaned up after test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_sqlite_db(temp_dir):
    """Provide a temporary SQLite database path."""
    db_path = temp_dir / "test_ai_provenance.db"
    yield db_path
    # Cleanup happens automatically via temp_dir


# ============================================================================
# COMMON FIXTURES - SAMPLE DATA
# ============================================================================

@pytest.fixture
def sample_doc_id():
    """Provide a sample doc_id for testing."""
    return "DOC-TEST-PROVENANCE-001"


@pytest.fixture
def sample_file_path():
    """Provide a sample file path for testing."""
    return "C:\\Users\\richg\\ALL_AI\\RUNTIME\\test\\sample_file.py"


@pytest.fixture
def sample_claude_log_entry():
    """Provide a sample Claude JSONL log entry."""
    return {
        "type": "tool_use",
        "messageId": "msg-123-test",
        "timestamp": "2026-01-04T10:30:00.000Z",
        "tool": {
            "name": "edit_file",
            "input": {
                "file_path": "C:\\Users\\richg\\ALL_AI\\RUNTIME\\test\\sample_file.py",
                "old_string": "def old_function():",
                "new_string": "def new_function():"
            }
        }
    }


@pytest.fixture
def sample_codex_log_entry():
    """Provide a sample Codex JSONL log entry."""
    return {
        "type": "session_metadata",
        "session_id": "codex-session-456",
        "timestamp": "2026-01-03T14:20:00.000Z",
        "cwd": "C:\\Users\\richg\\ALL_AI\\RUNTIME",
        "model": "gpt-4",
        "provider": "openai"
    }


@pytest.fixture
def sample_copilot_command():
    """Provide a sample Copilot command history entry."""
    return {
        "timestamp": "2026-01-02T09:15:00.000Z",
        "prompt_hash": "abc123def456",
        "keywords": ["migrate", "deprecate"],
        "files_mentioned": ["sample_file.py"]
    }


@pytest.fixture
def sample_evidence_result():
    """Provide a sample evidence query result."""
    return {
        "provenance.ai_cli_logs.timeline.exists": True,
        "provenance.ai_cli_logs.timeline.session_count": 3,
        "provenance.ai_cli_logs.timeline.tool_use_count.view": 5,
        "provenance.ai_cli_logs.timeline.tool_use_count.edit": 2,
        "provenance.ai_cli_logs.timeline.tool_use_count.create": 1,
        "provenance.ai_cli_logs.timeline.cli_agents": ["claude", "codex"],
        "provenance.ai_cli_logs.timeline.intent_signals.migration_intent": True,
        "provenance.ai_cli_logs.timeline.intent_signals.deprecation_intent": False,
        "provenance.ai_cli_logs.timeline.intent_signals.removal_intent": False
    }


# ============================================================================
# COMMON FIXTURES - MOCK REGISTRIES
# ============================================================================

@pytest.fixture
def mock_doc_id_registry(temp_dir):
    """Create a mock DOC_ID_REGISTRY.yaml file."""
    registry_path = temp_dir / "DOC_ID_REGISTRY.yaml"
    registry_content = """
documents:
  - doc_id: DOC-TEST-PROVENANCE-001
    file_path: C:\\Users\\richg\\ALL_AI\\RUNTIME\\test\\sample_file.py
    status: ACTIVE
    created: 2025-12-01T00:00:00Z

  - doc_id: DOC-TEST-PROVENANCE-002
    file_path: C:\\Users\\richg\\ALL_AI\\RUNTIME\\test\\another_file.py
    status: ACTIVE
    created: 2025-12-15T00:00:00Z
"""
    registry_path.write_text(registry_content)
    yield registry_path


@pytest.fixture
def mock_relationship_index(temp_dir):
    """Create a mock RELATIONSHIP_INDEX.json file."""
    index_path = temp_dir / "RELATIONSHIP_INDEX.json"
    index_data = {
        "nodes": [
            {"doc_id": "DOC-TEST-PROVENANCE-001", "file_path": "sample_file.py"},
            {"doc_id": "DOC-TEST-PROVENANCE-002", "file_path": "another_file.py"}
        ],
        "edges": [
            {
                "source": "DOC-TEST-PROVENANCE-001",
                "target": "DOC-TEST-PROVENANCE-002",
                "type": "imports",
                "confidence": 0.95
            }
        ]
    }
    index_path.write_text(json.dumps(index_data, indent=2))
    yield index_path


# ============================================================================
# COMMON FIXTURES - SAMPLE LOG FILES
# ============================================================================

@pytest.fixture
def sample_claude_log_file(temp_dir):
    """Create a sample Claude JSONL log file."""
    log_file = temp_dir / "claude_project.jsonl"
    log_entries = [
        {
            "type": "tool_use",
            "messageId": "msg-001",
            "timestamp": "2026-01-01T10:00:00.000Z",
            "tool": {"name": "read_file", "input": {"file_path": "sample_file.py"}}
        },
        {
            "type": "tool_use",
            "messageId": "msg-002",
            "timestamp": "2026-01-02T11:00:00.000Z",
            "tool": {"name": "edit_file", "input": {"file_path": "sample_file.py"}}
        },
        {
            "type": "tool_use",
            "messageId": "msg-003",
            "timestamp": "2026-01-03T12:00:00.000Z",
            "tool": {"name": "write_file", "input": {"file_path": "new_file.py"}}
        }
    ]

    with open(log_file, 'w') as f:
        for entry in log_entries:
            f.write(json.dumps(entry) + '\n')

    yield log_file


@pytest.fixture
def sample_copilot_command_history(temp_dir):
    """Create a sample Copilot command history file."""
    history_file = temp_dir / "command-history-state.json"
    history_data = {
        "commands": [
            {
                "timestamp": "2026-01-01T09:00:00.000Z",
                "prompt_hash": "hash001",
                "keywords": ["create", "new feature"]
            },
            {
                "timestamp": "2026-01-02T10:00:00.000Z",
                "prompt_hash": "hash002",
                "keywords": ["migrate", "deprecate", "old code"]
            }
        ]
    }
    history_file.write_text(json.dumps(history_data, indent=2))
    yield history_file


# ============================================================================
# COMMON FIXTURES - MOCK COLLECTORS
# ============================================================================

@pytest.fixture
def mock_ai_cli_collector():
    """Provide a mock AI CLI provenance collector."""
    class MockCollector:
        def __init__(self):
            self.calls = []

        def query(self, doc_id: str, evidence_path: str) -> Any:
            """Mock query method that returns test data."""
            self.calls.append({"doc_id": doc_id, "evidence_path": evidence_path})

            # Return appropriate mock data based on evidence path
            if evidence_path.endswith(".exists"):
                return True
            elif evidence_path.endswith(".session_count"):
                return 3
            elif evidence_path.endswith(".edit"):
                return 2
            elif evidence_path.endswith(".view"):
                return 5
            elif evidence_path.endswith(".cli_agents"):
                return ["claude", "codex"]
            else:
                return None

    return MockCollector()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

@pytest.fixture
def assert_evidence_schema():
    """Provide a helper function to validate evidence schema compliance."""
    def _assert_evidence_schema(evidence_dict: Dict[str, Any], required_paths: List[str]):
        """Assert that evidence dictionary contains required paths."""
        for path in required_paths:
            assert path in evidence_dict, f"Missing required evidence path: {path}"

    return _assert_evidence_schema


@pytest.fixture
def create_iso_timestamp():
    """Provide a helper function to create ISO8601 timestamps."""
    def _create_iso_timestamp(offset_days: int = 0) -> str:
        """Create ISO8601 timestamp with optional day offset."""
        from datetime import timedelta
        dt = datetime.utcnow() + timedelta(days=offset_days)
        return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    return _create_iso_timestamp


# ============================================================================
# PYTEST HOOKS
# ============================================================================

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Auto-mark integration tests
        if "integration" in item.nodeid or "test_integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)

        # Auto-mark unit tests
        if "test_unit" in item.nodeid or "/unit/" in item.nodeid:
            item.add_marker(pytest.mark.unit)

        # Auto-mark tests requiring logs
        if "requires_logs" in item.fixturenames:
            item.add_marker(pytest.mark.requires_logs)
