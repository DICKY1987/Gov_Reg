"""
Unit tests for V3 Pre-Commit Hook
BDD Spec: BDD-REGV3-PRECOMMIT-008
"""
# DOC_ID: DOC-TEST-6-TESTS-TEST-V3-PRE-COMMIT-614

import unittest
import tempfile
import sqlite3
from importlib import util
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path
module_path = Path(__file__).resolve().parent.parent / "3_AUTOMATION_HOOKS" / "DOC-CORE-3-AUTOMATION-HOOKS-V3-PRE-COMMIT-522__v3_pre_commit.py"
spec = util.spec_from_file_location("v3_pre_commit", module_path)
if spec is None or spec.loader is None:
    raise ImportError(f"Unable to load module from {module_path}")
_module = util.module_from_spec(spec)
spec.loader.exec_module(_module)
check_v3_database_exists = _module.check_v3_database_exists
check_schema_integrity = _module.check_schema_integrity
check_doc_id_conflicts = _module.check_doc_id_conflicts


class TestV3PreCommit(unittest.TestCase):
    """Test cases for V3 Pre-Commit Hook"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = Path(self.temp_dir) / "test_registry_v3.db"

    def create_valid_database(self):
        """Create a valid test database with required tables"""
        conn = sqlite3.connect(str(self.temp_db))
        cursor = conn.cursor()

        # Create required tables
        cursor.execute("""
            CREATE TABLE code_symbols (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE code_edges (
                id INTEGER PRIMARY KEY,
                from_id INTEGER,
                to_id INTEGER
            )
        """)

        conn.commit()
        conn.close()

    def test_validation_passes(self):
        """TC-PRECOMMIT-001: Test validation passes with valid database"""
        self.create_valid_database()

        # Check database exists
        self.assertTrue(check_v3_database_exists(self.temp_db))

        # Check schema integrity
        schema_ok, schema_issues = check_schema_integrity(self.temp_db)
        self.assertTrue(schema_ok)
        self.assertEqual(len(schema_issues), 0)

        # Check doc_id conflicts (should pass with no view)
        conflicts_ok, conflict_issues = check_doc_id_conflicts(self.temp_db)
        self.assertTrue(conflicts_ok)
        self.assertEqual(len(conflict_issues), 0)

    def test_schema_violation_blocks_commit(self):
        """TC-PRECOMMIT-002: Test commit blocked on schema violation"""
        # Create database without required tables
        conn = sqlite3.connect(str(self.temp_db))
        conn.close()

        # Check schema integrity (should fail)
        schema_ok, schema_issues = check_schema_integrity(self.temp_db)
        self.assertFalse(schema_ok)
        self.assertGreater(len(schema_issues), 0)
        self.assertTrue(any("code_symbols" in issue for issue in schema_issues))

    def test_conflict_blocks_commit(self):
        """TC-PRECOMMIT-003: Test commit blocked on doc_id conflicts"""
        self.create_valid_database()

        # Create conflict view with data
        conn = sqlite3.connect(str(self.temp_db))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE VIEW vw_doc_id_conflicts AS
            SELECT 'DOC-123' as doc_id, 2 as file_count
        """)

        conn.commit()
        conn.close()

        # Check doc_id conflicts (should fail)
        conflicts_ok, conflict_issues = check_doc_id_conflicts(self.temp_db)
        self.assertFalse(conflicts_ok)
        self.assertGreater(len(conflict_issues), 0)
        self.assertTrue(any("DOC-123" in issue for issue in conflict_issues))

    def test_missing_database_graceful(self):
        """TC-PRECOMMIT-004: Test graceful degradation"""
        # Use non-existent database path
        non_existent_db = Path(self.temp_dir) / "non_existent.db"

        # Check database exists (should return False)
        self.assertFalse(check_v3_database_exists(non_existent_db))

    def test_database_connection_error(self):
        """Test handling of database connection errors"""
        # Use invalid database path
        invalid_db = Path("/invalid/path/to/database.db")

        # Check schema integrity (should return False with error)
        schema_ok, schema_issues = check_schema_integrity(invalid_db)
        self.assertFalse(schema_ok)
        self.assertGreater(len(schema_issues), 0)
        self.assertTrue(any("error" in issue.lower() for issue in schema_issues))


if __name__ == "__main__":
    unittest.main()
