#!/usr/bin/env python3
# DOC_LINK: DOC-TEST-TESTS-TEST-WATCH-MODE-631
"""
Test Suite for Watch Mode

Tests the pfa_watch.py file monitoring functionality.
"""
# DOC_ID: DOC-TEST-TESTS-TEST-WATCH-MODE-631

import unittest
import sys
import time
from pathlib import Path
import tempfile
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'tools'))

try:
    from pfa_watch import SchemaChangeHandler
except ImportError:
    SchemaChangeHandler = None
except ImportError:
    SchemaChangeHandler = None


class TestWatchModeHandler(unittest.TestCase):
    """Test cases for watch mode file handler"""

    def setUp(self):
        """Set up test fixtures"""
        if SchemaChangeHandler is None:
            self.skipTest("pfa_watch module not available (watchdog not installed)")

        self.test_dir = Path(tempfile.mkdtemp())
        (self.test_dir / 'schemas' / 'source').mkdir(parents=True)

        self.handler = SchemaChangeHandler(
            orchestrator=self.test_dir,
            debounce_seconds=0.1,  # Short for testing
            quick=True,
            dry_run=True
        )

    def tearDown(self):
        """Clean up"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_handler_init(self):
        """Test handler initialization"""
        self.assertIsNotNone(self.handler)
        self.assertEqual(self.handler.debounce_seconds, 0.1)
        self.assertTrue(self.handler.quick)
        self.assertTrue(self.handler.dry_run)

    def test_debounce_tracking(self):
        """Test debounce timestamp tracking"""
        # Initial state
        self.assertEqual(len(self.handler.last_modified), 0)

        # Simulate file modification
        filename = 'test.yaml'
        now = time.time()
        self.handler.last_modified[filename] = now

        # Check tracking
        self.assertIn(filename, self.handler.last_modified)
        self.assertEqual(self.handler.last_modified[filename], now)


class TestWatchModeIntegration(unittest.TestCase):
    """Integration tests for watch mode"""

    def test_watch_script_exists(self):
        """Test that watch script exists"""
        script_path = Path(__file__).parent.parent / 'tools' / 'pfa_watch.py'
        self.assertTrue(script_path.exists(), "pfa_watch.py should exist")

    def test_watch_script_executable(self):
        """Test that watch script is executable Python"""
        script_path = Path(__file__).parent.parent / 'tools' / 'pfa_watch.py'

        content = script_path.read_text(encoding='utf-8')
        self.assertTrue(content.startswith('#!/usr/bin/env python3') or
                       content.startswith('"""'),
                       "Should be valid Python script")


if __name__ == '__main__':
    unittest.main()
