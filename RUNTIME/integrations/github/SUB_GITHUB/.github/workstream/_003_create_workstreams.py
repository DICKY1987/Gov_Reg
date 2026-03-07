"""
Migration 003: Create workstreams table.

Reference: DOC-SSOT-STATE-MACHINES-001 §6.2
"""

def up(conn):
    """Create workstreams table with foreign key to runs."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS workstreams (
            workstream_id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL,
            state TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            completed_at TEXT,
            metadata TEXT,
            progress_percentage REAL DEFAULT 0.0,

            FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE,
            CHECK (state IN ('PENDING', 'INITIALIZING', 'RUNNING', 'PAUSED',
                           'BLOCKED', 'COMPLETED', 'FAILED', 'CANCELLED', 'ABANDONED')),
            CHECK (progress_percentage >= 0.0 AND progress_percentage <= 100.0)
        )
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_workstreams_run_id
        ON workstreams(run_id)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_workstreams_state
        ON workstreams(state)
    """)


def down(conn):
    """Drop workstreams table."""
    conn.execute("DROP TABLE IF EXISTS workstreams")
