#!/usr/bin/env python3
# DOC_ID: DOC-SCRIPT-0992
"""
SQLite Schema for AI CLI Provenance Storage
Created: 2026-01-04

Defines database schema for storing AI CLI provenance data:
- file_events: AI tool use events (view/edit/create)
- sessions: AI session metadata
- intent_signals: Detected intent keywords
- doc_id_mapping: File path → doc_id mapping cache

Schema Design Goals:
- Minimal storage: <1MB per 10K records
- Fast queries: O(log n) via indexes
- Incremental ingestion: Track watermarks
- Privacy: SHA256 hashes only, no raw prompts
"""

import sqlite3
from pathlib import Path
from typing import Optional
from datetime import datetime


# ============================================================================
# SCHEMA VERSION
# ============================================================================

SCHEMA_VERSION = "1.0"

# ============================================================================
# SQL SCHEMA DEFINITIONS
# ============================================================================

CREATE_TABLES_SQL = """
-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI CLI sessions
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    cli_agent TEXT NOT NULL,           -- claude, codex, copilot
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    log_file_path TEXT NOT NULL,
    record_count INTEGER DEFAULT 0
);

-- File events (AI tool use on specific files)
CREATE TABLE IF NOT EXISTS file_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    doc_id TEXT,                       -- Mapped from file_path via DOC_ID_REGISTRY
    file_path_hash TEXT NOT NULL,      -- SHA256(normalized_path)
    file_path_repo_relative TEXT,      -- Relative path within repo (for display)
    timestamp TIMESTAMP NOT NULL,
    cli_agent TEXT NOT NULL,
    tool_name TEXT NOT NULL,           -- read_file, edit_file, write_file, etc.
    tool_category TEXT NOT NULL,       -- view, edit, create
    message_id TEXT,                   -- Original message/event ID from log

    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- Intent signals (detected from prompts/commands)
CREATE TABLE IF NOT EXISTS intent_signals (
    signal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER,
    session_id TEXT NOT NULL,
    prompt_hash TEXT,                  -- SHA256(prompt) - no raw text
    detected_keywords TEXT,            -- JSON array of detected keywords
    migration_intent BOOLEAN DEFAULT 0,
    deprecation_intent BOOLEAN DEFAULT 0,
    removal_intent BOOLEAN DEFAULT 0,
    timestamp TIMESTAMP NOT NULL,

    FOREIGN KEY (event_id) REFERENCES file_events(event_id),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- Doc ID mapping cache (file_path → doc_id)
CREATE TABLE IF NOT EXISTS doc_id_mapping (
    file_path_hash TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL,
    file_path_repo_relative TEXT NOT NULL,
    last_verified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ingestion watermarks (track last processed log entry)
CREATE TABLE IF NOT EXISTS ingestion_watermarks (
    source_id TEXT PRIMARY KEY,        -- log file path or identifier
    last_processed_timestamp TIMESTAMP,
    last_processed_offset INTEGER,     -- Line number or byte offset
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- file_events indexes (most common queries)
CREATE INDEX IF NOT EXISTS idx_file_events_doc_id
    ON file_events(doc_id);

CREATE INDEX IF NOT EXISTS idx_file_events_timestamp
    ON file_events(timestamp);

CREATE INDEX IF NOT EXISTS idx_file_events_session_id
    ON file_events(session_id);

CREATE INDEX IF NOT EXISTS idx_file_events_file_path_hash
    ON file_events(file_path_hash);

CREATE INDEX IF NOT EXISTS idx_file_events_tool_category
    ON file_events(tool_category);

-- sessions indexes
CREATE INDEX IF NOT EXISTS idx_sessions_cli_agent
    ON sessions(cli_agent);

CREATE INDEX IF NOT EXISTS idx_sessions_start_time
    ON sessions(start_time);

-- intent_signals indexes
CREATE INDEX IF NOT EXISTS idx_intent_signals_session_id
    ON intent_signals(session_id);

CREATE INDEX IF NOT EXISTS idx_intent_signals_migration
    ON intent_signals(migration_intent) WHERE migration_intent = 1;

CREATE INDEX IF NOT EXISTS idx_intent_signals_deprecation
    ON intent_signals(deprecation_intent) WHERE deprecation_intent = 1;

CREATE INDEX IF NOT EXISTS idx_intent_signals_removal
    ON intent_signals(removal_intent) WHERE removal_intent = 1;

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View: File activity summary by doc_id
CREATE VIEW IF NOT EXISTS v_file_activity_summary AS
SELECT
    doc_id,
    COUNT(DISTINCT session_id) AS session_count,
    MIN(timestamp) AS first_seen,
    MAX(timestamp) AS last_seen,
    SUM(CASE WHEN tool_category = 'view' THEN 1 ELSE 0 END) AS view_count,
    SUM(CASE WHEN tool_category = 'edit' THEN 1 ELSE 0 END) AS edit_count,
    SUM(CASE WHEN tool_category = 'create' THEN 1 ELSE 0 END) AS create_count,
    GROUP_CONCAT(DISTINCT cli_agent) AS cli_agents
FROM file_events
WHERE doc_id IS NOT NULL
GROUP BY doc_id;

-- View: Intent signals by doc_id
CREATE VIEW IF NOT EXISTS v_intent_signals_by_doc AS
SELECT
    fe.doc_id,
    MAX(isig.migration_intent) AS has_migration_intent,
    MAX(isig.deprecation_intent) AS has_deprecation_intent,
    MAX(isig.removal_intent) AS has_removal_intent,
    GROUP_CONCAT(DISTINCT isig.detected_keywords) AS all_keywords
FROM file_events fe
LEFT JOIN intent_signals isig ON fe.event_id = isig.event_id
WHERE fe.doc_id IS NOT NULL
GROUP BY fe.doc_id;

-- View: Session summary
CREATE VIEW IF NOT EXISTS v_session_summary AS
SELECT
    s.session_id,
    s.cli_agent,
    s.start_time,
    s.end_time,
    COUNT(fe.event_id) AS event_count,
    COUNT(DISTINCT fe.doc_id) AS file_count
FROM sessions s
LEFT JOIN file_events fe ON s.session_id = fe.session_id
GROUP BY s.session_id;
"""


# ============================================================================
# SCHEMA MANAGEMENT CLASS
# ============================================================================

class AIProvenanceSchema:
    """Manages SQLite schema for AI provenance storage."""

    def __init__(self, db_path: Path):
        """Initialize schema manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def initialize(self) -> None:
        """Create all tables, indexes, and views."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript(CREATE_TABLES_SQL)

            # Record schema version
            conn.execute(
                "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
                (SCHEMA_VERSION,)
            )

            conn.commit()
        finally:
            conn.close()

    def get_version(self) -> Optional[str]:
        """Get current schema version.

        Returns:
            Schema version string or None if not initialized
        """
        if not self.db_path.exists():
            return None

        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("SELECT version FROM schema_version ORDER BY applied_at DESC LIMIT 1")
            row = cursor.fetchone()
            return row[0] if row else None
        except sqlite3.OperationalError:
            return None
        finally:
            conn.close()

    def verify_schema(self) -> bool:
        """Verify schema integrity.

        Returns:
            True if schema is valid and complete
        """
        required_tables = [
            'schema_version',
            'sessions',
            'file_events',
            'intent_signals',
            'doc_id_mapping',
            'ingestion_watermarks'
        ]

        required_views = [
            'v_file_activity_summary',
            'v_intent_signals_by_doc',
            'v_session_summary'
        ]

        conn = sqlite3.connect(self.db_path)
        try:
            # Check tables
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = {row[0] for row in cursor.fetchall()}

            for table in required_tables:
                if table not in tables:
                    return False

            # Check views
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='view'"
            )
            views = {row[0] for row in cursor.fetchall()}

            for view in required_views:
                if view not in views:
                    return False

            return True

        finally:
            conn.close()

    def get_stats(self) -> dict:
        """Get database statistics.

        Returns:
            Dictionary with table counts and sizes
        """
        conn = sqlite3.connect(self.db_path)
        try:
            stats = {}

            # Table counts
            for table in ['sessions', 'file_events', 'intent_signals', 'doc_id_mapping']:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f"{table}_count"] = cursor.fetchone()[0]

            # Database size
            stats['db_size_bytes'] = self.db_path.stat().st_size if self.db_path.exists() else 0
            stats['db_size_mb'] = stats['db_size_bytes'] / (1024 * 1024)

            return stats

        finally:
            conn.close()

    def reset(self) -> None:
        """Drop all tables and recreate schema (DESTRUCTIVE)."""
        conn = sqlite3.connect(self.db_path)
        try:
            # Drop all tables
            tables = ['intent_signals', 'file_events', 'sessions', 'doc_id_mapping',
                     'ingestion_watermarks', 'schema_version']
            for table in tables:
                conn.execute(f"DROP TABLE IF EXISTS {table}")

            # Drop all views
            views = ['v_file_activity_summary', 'v_intent_signals_by_doc', 'v_session_summary']
            for view in views:
                conn.execute(f"DROP VIEW IF EXISTS {view}")

            conn.commit()
        finally:
            conn.close()

        # Recreate schema
        self.initialize()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_database(db_path: Path) -> AIProvenanceSchema:
    """Create and initialize a new AI provenance database.

    Args:
        db_path: Path to database file

    Returns:
        Initialized schema manager
    """
    schema = AIProvenanceSchema(db_path)
    schema.initialize()
    return schema


def verify_database(db_path: Path) -> bool:
    """Verify database schema is valid.

    Args:
        db_path: Path to database file

    Returns:
        True if schema is valid
    """
    if not db_path.exists():
        return False

    schema = AIProvenanceSchema(db_path)
    return schema.verify_schema()


# ============================================================================
# MAIN (for testing)
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python sqlite_schema.py <db_path>")
        print("       python sqlite_schema.py --test")
        sys.exit(1)

    if sys.argv[1] == "--test":
        # Create test database
        test_db = Path("test_ai_provenance.db")
        print(f"Creating test database: {test_db}")

        schema = create_database(test_db)
        print(f"✅ Database created")

        version = schema.get_version()
        print(f"✅ Schema version: {version}")

        valid = schema.verify_schema()
        print(f"✅ Schema valid: {valid}")

        stats = schema.get_stats()
        print(f"✅ Stats: {stats}")

        print(f"\nTest database created at: {test_db.absolute()}")
        print(f"Size: {stats['db_size_bytes']} bytes")

    else:
        db_path = Path(sys.argv[1])
        schema = create_database(db_path)
        print(f"✅ Database created: {db_path}")
        print(f"✅ Schema version: {schema.get_version()}")
        print(f"✅ Schema valid: {schema.verify_schema()}")
