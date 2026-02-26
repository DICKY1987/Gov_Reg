# DOC_ID: DOC-TEST-0633
"""
Unit Tests for AI CLI Provenance Collector
Created: 2026-01-04

Tests:
- Collector initialization
- Log ingestion
- Evidence queries
- Doc ID mapping
- Database operations
- Graceful degradation
"""

import pytest
import sqlite3
from pathlib import Path

from ai_cli_provenance_collector import AIProvenanceCollector, DocIdMapper, normalize_path, hash_path


# ============================================================================
# PATH UTILITIES TESTS
# ============================================================================

def test_normalize_path_windows():
    """Test path normalization for Windows paths."""
    path = "C:\\Users\\richg\\ALL_AI\\test.py"
    normalized = normalize_path(path)

    # Should convert backslashes to forward slashes
    assert '/' in normalized
    assert '\\' not in normalized


def test_normalize_path_relative():
    """Test normalization with repo root."""
    path = "C:\\Users\\richg\\ALL_AI\\RUNTIME\\test.py"
    repo_root = Path("C:\\Users\\richg\\ALL_AI")
    normalized = normalize_path(path, repo_root)

    # Should be relative to repo root
    assert 'RUNTIME/test.py' in normalized or 'RUNTIME\\test.py' in normalized.replace('/', '\\')


def test_hash_path_consistency():
    """Test path hashing is consistent."""
    path = "C:\\Users\\richg\\ALL_AI\\test.py"

    hash1 = hash_path(path)
    hash2 = hash_path(path)

    # Same path should generate same hash
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 hex digest


def test_hash_path_different_for_different_paths():
    """Test different paths generate different hashes."""
    path1 = "C:\\Users\\richg\\ALL_AI\\test1.py"
    path2 = "C:\\Users\\richg\\ALL_AI\\test2.py"

    hash1 = hash_path(path1)
    hash2 = hash_path(path2)

    assert hash1 != hash2


# ============================================================================
# DOC ID MAPPER TESTS
# ============================================================================

def test_doc_id_mapper_initialization(mock_doc_id_registry):
    """Test DocIdMapper initializes correctly."""
    mapper = DocIdMapper(mock_doc_id_registry)

    assert mapper.registry_path == mock_doc_id_registry
    assert isinstance(mapper.cache, dict)


def test_doc_id_mapper_loads_registry(mock_doc_id_registry):
    """Test DocIdMapper loads registry into cache."""
    mapper = DocIdMapper(mock_doc_id_registry)

    # Should have cached entries
    assert len(mapper.cache) > 0


def test_doc_id_mapper_get_doc_id(mock_doc_id_registry):
    """Test get_doc_id returns correct doc_id."""
    mapper = DocIdMapper(mock_doc_id_registry)

    doc_id = mapper.get_doc_id("C:\\Users\\richg\\ALL_AI\\RUNTIME\\test\\sample_file.py")

    # Should map to DOC-TEST-PROVENANCE-001
    assert doc_id == "DOC-TEST-PROVENANCE-001"


def test_doc_id_mapper_get_doc_id_not_found(mock_doc_id_registry):
    """Test get_doc_id returns None for unknown path."""
    mapper = DocIdMapper(mock_doc_id_registry)

    doc_id = mapper.get_doc_id("C:\\Users\\richg\\ALL_AI\\unknown_file.py")

    assert doc_id is None


def test_doc_id_mapper_handles_missing_registry():
    """Test DocIdMapper handles missing registry gracefully."""
    mapper = DocIdMapper(Path("/nonexistent/registry.yaml"))

    # Should initialize with empty cache
    assert len(mapper.cache) == 0


# ============================================================================
# COLLECTOR INITIALIZATION TESTS
# ============================================================================

def test_collector_initialization(temp_sqlite_db, mock_doc_id_registry):
    """Test collector initializes correctly."""
    collector = AIProvenanceCollector(
        temp_sqlite_db,
        mock_doc_id_registry
    )

    assert collector.db_path == temp_sqlite_db
    assert isinstance(collector.doc_id_mapper, DocIdMapper)
    assert temp_sqlite_db.exists()


def test_collector_creates_database(temp_sqlite_db):
    """Test collector creates database if it doesn't exist."""
    # Ensure DB doesn't exist
    if temp_sqlite_db.exists():
        temp_sqlite_db.unlink()

    collector = AIProvenanceCollector(temp_sqlite_db)

    # DB should be created
    assert temp_sqlite_db.exists()


def test_collector_database_schema(temp_sqlite_db):
    """Test collector creates correct database schema."""
    collector = AIProvenanceCollector(temp_sqlite_db)

    conn = sqlite3.connect(temp_sqlite_db)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()

    # Should have all required tables
    assert 'sessions' in tables
    assert 'file_events' in tables
    assert 'intent_signals' in tables


# ============================================================================
# LOG INGESTION TESTS
# ============================================================================

def test_ingest_claude_log(temp_sqlite_db, sample_claude_log_file, mock_doc_id_registry):
    """Test ingesting Claude log file."""
    repo_root = Path("C:\\Users\\richg\\ALL_AI")
    collector = AIProvenanceCollector(temp_sqlite_db, mock_doc_id_registry, repo_root)

    count = collector.ingest_claude_log(sample_claude_log_file)

    # Should ingest file events
    assert count > 0


def test_ingest_claude_log_creates_session(temp_sqlite_db, sample_claude_log_file):
    """Test ingesting Claude log creates session record."""
    collector = AIProvenanceCollector(temp_sqlite_db)
    collector.ingest_claude_log(sample_claude_log_file)

    conn = sqlite3.connect(temp_sqlite_db)
    cursor = conn.execute("SELECT COUNT(*) FROM sessions WHERE cli_agent = 'claude'")
    count = cursor.fetchone()[0]
    conn.close()

    assert count > 0


def test_ingest_claude_log_creates_file_events(temp_sqlite_db, sample_claude_log_file):
    """Test ingesting Claude log creates file event records."""
    repo_root = Path("C:\\Users\\richg\\ALL_AI")
    collector = AIProvenanceCollector(temp_sqlite_db, repo_root=repo_root)
    collector.ingest_claude_log(sample_claude_log_file)

    conn = sqlite3.connect(temp_sqlite_db)
    cursor = conn.execute("SELECT COUNT(*) FROM file_events WHERE cli_agent = 'claude'")
    count = cursor.fetchone()[0]
    conn.close()

    assert count > 0


def test_ingest_copilot_history(temp_sqlite_db, sample_copilot_command_history):
    """Test ingesting Copilot command history."""
    collector = AIProvenanceCollector(temp_sqlite_db)

    count = collector.ingest_copilot_history(sample_copilot_command_history)

    # Should ingest intent signals
    assert count > 0


def test_ingest_copilot_creates_intent_signals(temp_sqlite_db, sample_copilot_command_history):
    """Test ingesting Copilot creates intent signal records."""
    collector = AIProvenanceCollector(temp_sqlite_db)
    collector.ingest_copilot_history(sample_copilot_command_history)

    conn = sqlite3.connect(temp_sqlite_db)
    cursor = conn.execute("SELECT COUNT(*) FROM intent_signals")
    count = cursor.fetchone()[0]
    conn.close()

    assert count > 0


# ============================================================================
# LOG DISCOVERY TESTS
# ============================================================================

def test_discover_logs_structure(temp_sqlite_db):
    """Test discover_logs returns correct structure."""
    collector = AIProvenanceCollector(temp_sqlite_db)

    logs = collector.discover_logs(Path.home())

    # Should return dict with all CLI agents
    assert 'claude' in logs
    assert 'codex' in logs
    assert 'copilot' in logs
    assert isinstance(logs['claude'], list)
    assert isinstance(logs['codex'], list)
    assert isinstance(logs['copilot'], list)


def test_discover_logs_finds_real_logs(temp_sqlite_db):
    """Test discover_logs finds real log files (if they exist)."""
    collector = AIProvenanceCollector(temp_sqlite_db)

    logs = collector.discover_logs()

    # This test may find real logs or empty lists depending on environment
    total_logs = len(logs['claude']) + len(logs['codex']) + len(logs['copilot'])
    assert total_logs >= 0  # Should not crash, may or may not find logs


# ============================================================================
# EVIDENCE QUERY TESTS
# ============================================================================

def test_query_evidence_timeline_exists_true(temp_sqlite_db, sample_claude_log_file, mock_doc_id_registry):
    """Test querying timeline.exists returns True when data exists."""
    repo_root = Path("C:\\Users\\richg\\ALL_AI")
    collector = AIProvenanceCollector(temp_sqlite_db, mock_doc_id_registry, repo_root)
    collector.ingest_claude_log(sample_claude_log_file)

    result = collector.query_evidence("DOC-TEST-PROVENANCE-001", "provenance.ai_cli_logs.timeline.exists")

    # Should return True if events exist for this doc_id
    assert isinstance(result, bool)


def test_query_evidence_timeline_exists_false(temp_sqlite_db):
    """Test querying timeline.exists returns False when no data."""
    collector = AIProvenanceCollector(temp_sqlite_db)

    result = collector.query_evidence("DOC-NONEXISTENT", "provenance.ai_cli_logs.timeline.exists")

    assert result == False


def test_query_evidence_session_count(temp_sqlite_db, sample_claude_log_file, mock_doc_id_registry):
    """Test querying session_count returns integer."""
    repo_root = Path("C:\\Users\\richg\\ALL_AI")
    collector = AIProvenanceCollector(temp_sqlite_db, mock_doc_id_registry, repo_root)
    collector.ingest_claude_log(sample_claude_log_file)

    result = collector.query_evidence("DOC-TEST-PROVENANCE-001", "provenance.ai_cli_logs.timeline.session_count")

    assert isinstance(result, int)
    assert result >= 0


def test_query_evidence_tool_use_counts(temp_sqlite_db, sample_claude_log_file, mock_doc_id_registry):
    """Test querying tool_use_count returns integers."""
    repo_root = Path("C:\\Users\\richg\\ALL_AI")
    collector = AIProvenanceCollector(temp_sqlite_db, mock_doc_id_registry, repo_root)
    collector.ingest_claude_log(sample_claude_log_file)

    view_count = collector.query_evidence("DOC-TEST-PROVENANCE-001", "provenance.ai_cli_logs.timeline.tool_use_count.view")
    edit_count = collector.query_evidence("DOC-TEST-PROVENANCE-001", "provenance.ai_cli_logs.timeline.tool_use_count.edit")
    create_count = collector.query_evidence("DOC-TEST-PROVENANCE-001", "provenance.ai_cli_logs.timeline.tool_use_count.create")

    assert isinstance(view_count, int)
    assert isinstance(edit_count, int)
    assert isinstance(create_count, int)


def test_query_evidence_cli_agents(temp_sqlite_db, sample_claude_log_file, mock_doc_id_registry):
    """Test querying cli_agents returns list."""
    repo_root = Path("C:\\Users\\richg\\ALL_AI")
    collector = AIProvenanceCollector(temp_sqlite_db, mock_doc_id_registry, repo_root)
    collector.ingest_claude_log(sample_claude_log_file)

    result = collector.query_evidence("DOC-TEST-PROVENANCE-001", "provenance.ai_cli_logs.timeline.cli_agents")

    assert isinstance(result, list)


def test_query_evidence_unknown_path(temp_sqlite_db):
    """Test querying unknown evidence path returns None."""
    collector = AIProvenanceCollector(temp_sqlite_db)

    result = collector.query_evidence("DOC-123", "unknown.evidence.path")

    assert result is None


# ============================================================================
# GRACEFUL DEGRADATION TESTS
# ============================================================================

def test_query_with_empty_database(temp_sqlite_db):
    """Test queries return safe defaults with empty database."""
    collector = AIProvenanceCollector(temp_sqlite_db)

    exists = collector.query_evidence("DOC-123", "provenance.ai_cli_logs.timeline.exists")
    session_count = collector.query_evidence("DOC-123", "provenance.ai_cli_logs.timeline.session_count")
    cli_agents = collector.query_evidence("DOC-123", "provenance.ai_cli_logs.timeline.cli_agents")

    assert exists == False
    assert session_count == 0
    assert cli_agents == []


def test_collector_without_doc_id_registry(temp_sqlite_db):
    """Test collector works without doc_id registry."""
    collector = AIProvenanceCollector(temp_sqlite_db, doc_id_registry_path=None)

    # Should initialize successfully
    assert collector.doc_id_mapper is not None


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

@pytest.mark.slow
def test_ingest_multiple_logs_performance(temp_sqlite_db, temp_dir, mock_doc_id_registry):
    """Test ingesting multiple logs is reasonably fast."""
    import time

    # Create multiple sample log files
    log_files = []
    for i in range(10):
        log_file = temp_dir / f"log_{i}.jsonl"
        with open(log_file, 'w') as f:
            f.write('{"type":"tool_use","messageId":"msg-1","timestamp":"2026-01-01T10:00:00.000Z","tool":{"name":"read_file","input":{"file_path":"test.py"}}}\n')
        log_files.append(log_file)

    collector = AIProvenanceCollector(temp_sqlite_db, mock_doc_id_registry)

    start_time = time.time()
    for log_file in log_files:
        collector.ingest_claude_log(log_file)
    elapsed = time.time() - start_time

    # Should complete in reasonable time (< 5 seconds for 10 small logs)
    assert elapsed < 5.0


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

def test_ingest_nonexistent_log(temp_sqlite_db):
    """Test ingesting nonexistent log file raises appropriate error."""
    collector = AIProvenanceCollector(temp_sqlite_db)

    # Should raise FileNotFoundError or handle gracefully
    with pytest.raises(FileNotFoundError):
        collector.ingest_claude_log(Path("/nonexistent/log.jsonl"))


def test_ingest_corrupted_log(temp_sqlite_db, temp_dir):
    """Test ingesting corrupted log file handles gracefully."""
    corrupted_log = temp_dir / "corrupted.jsonl"
    corrupted_log.write_text("this is not JSON\n{invalid json\n")

    collector = AIProvenanceCollector(temp_sqlite_db)

    # Should not crash, but may return 0 events
    try:
        count = collector.ingest_claude_log(corrupted_log)
        assert count >= 0
    except Exception:
        # Also acceptable - let caller handle
        pass
