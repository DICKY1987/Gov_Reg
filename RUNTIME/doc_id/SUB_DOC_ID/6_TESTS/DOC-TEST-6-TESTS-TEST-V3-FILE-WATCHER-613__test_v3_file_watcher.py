"""
Unit tests for V3 File Watcher
BDD Spec: BDD-REGV3-FILE-WATCHER-007
"""
# DOC_ID: DOC-TEST-6-TESTS-TEST-V3-FILE-WATCHER-613

import unittest
import tempfile
import time
from importlib import util
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add parent directory to path
module_path = Path(__file__).resolve().parent.parent / "3_AUTOMATION_HOOKS" / "DOC-CORE-3-AUTOMATION-HOOKS-V3-FILE-WATCHER-521__v3_file_watcher.py"
spec = util.spec_from_file_location("v3_file_watcher", module_path)
if spec is None or spec.loader is None:
    raise ImportError(f"Unable to load module from {module_path}")
_module = util.module_from_spec(spec)
spec.loader.exec_module(_module)
V3FileHandler = _module.V3FileHandler


class TestV3FileWatcher(unittest.TestCase):
    """Test cases for V3 File Watcher"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = Path(self.temp_dir) / "test_registry_v3.db"
        self.temp_repo = Path(self.temp_dir)

    def test_file_modification_triggers_scan(self):
        """TC-FILEWATCHER-001: Test file modification detection"""
        handler = V3FileHandler(
            str(self.temp_db),
            str(self.temp_repo),
            debounce_seconds=1
        )

        # Create mock event for Python file
        event = Mock()
        event.is_directory = False
        event.src_path = str(Path(self.temp_repo) / "test.py")

        # Trigger modification
        handler.on_modified(event)

        # Verify file added to pending set
        self.assertEqual(len(handler.pending_files), 1)
        self.assertIn(event.src_path, handler.pending_files)

    def test_non_python_files_ignored(self):
        """TC-FILEWATCHER-002: Test file type filtering"""
        handler = V3FileHandler(
            str(self.temp_db),
            str(self.temp_repo),
            debounce_seconds=1
        )

        # Create mock event for text file
        event = Mock()
        event.is_directory = False
        event.src_path = str(Path(self.temp_repo) / "test.txt")

        # Trigger modification
        handler.on_modified(event)

        # Verify file NOT added to pending set
        self.assertEqual(len(handler.pending_files), 0)

    def test_multiple_files_batch_scan(self):
        """TC-FILEWATCHER-003: Test debounce logic"""
        handler = V3FileHandler(
            str(self.temp_db),
            str(self.temp_repo),
            debounce_seconds=1
        )

        # Create mock events for multiple Python files
        files = ["test1.py", "test2.py", "test3.py"]
        for filename in files:
            event = Mock()
            event.is_directory = False
            event.src_path = str(Path(self.temp_repo) / filename)
            handler.on_modified(event)

        # Verify all files added to pending set
        self.assertEqual(len(handler.pending_files), 3)

    def test_directory_changes_ignored(self):
        """Test that directory modifications are ignored"""
        handler = V3FileHandler(
            str(self.temp_db),
            str(self.temp_repo),
            debounce_seconds=1
        )

        # Create mock event for directory
        event = Mock()
        event.is_directory = True
        event.src_path = str(Path(self.temp_repo) / "subdir")

        # Trigger modification
        handler.on_modified(event)

        # Verify nothing added to pending set
        self.assertEqual(len(handler.pending_files), 0)

    def test_json_yaml_files_trigger_scan(self):
        """Test that JSON and YAML files trigger scans"""
        handler = V3FileHandler(
            str(self.temp_db),
            str(self.temp_repo),
            debounce_seconds=1
        )

        # Test JSON file
        event_json = Mock()
        event_json.is_directory = False
        event_json.src_path = str(Path(self.temp_repo) / "config.json")
        handler.on_modified(event_json)

        # Test YAML file
        event_yaml = Mock()
        event_yaml.is_directory = False
        event_yaml.src_path = str(Path(self.temp_repo) / "data.yaml")
        handler.on_modified(event_yaml)

        # Verify both files added
        self.assertEqual(len(handler.pending_files), 2)


if __name__ == "__main__":
    unittest.main()
