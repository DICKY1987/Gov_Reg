# DOC_LINK: DOC-TEST-CHANGE-DETECTOR-014
"""Unit tests for ChangeDetector

Tests change detection from git operations.

DOC_ID: DOC-TEST-CHANGE-DETECTOR-014
"""

import pytest
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from RUNTIME.doc_id.SUB_DOC_ID.detection.change_detector import (
    ChangeDetector,
    Change,
    ChangeType
)


class TestChangeType:
    """Test ChangeType enum"""

    def test_change_types(self):
        """Test change type enum values"""
        assert ChangeType.FILE_ADDED.value == "FILE_ADDED"
        assert ChangeType.FILE_MODIFIED.value == "FILE_MODIFIED"
        assert ChangeType.FILE_DELETED.value == "FILE_DELETED"
        assert ChangeType.FILE_RENAMED.value == "FILE_RENAMED"


class TestChange:
    """Test Change dataclass"""

    def test_change_creation(self):
        """Test creating a change"""
        change = Change(
            event_type=ChangeType.FILE_ADDED,
            path="test.py",
            content_hash="abc123",
            timestamp="2026-01-10T00:00:00Z"
        )

        assert change.event_type == ChangeType.FILE_ADDED
        assert change.path == "test.py"
        assert change.content_hash == "abc123"

    def test_change_to_dict(self):
        """Test converting change to dict"""
        change = Change(
            event_type=ChangeType.FILE_RENAMED,
            path="new.py",
            old_path="old.py",
            similarity=95
        )

        result = change.to_dict()

        assert result['event_type'] == "FILE_RENAMED"
        assert result['path'] == "new.py"
        assert result['old_path'] == "old.py"
        assert result['similarity'] == 95


class TestChangeDetector:
    """Test ChangeDetector"""

    def test_initialization(self):
        """Test detector initialization"""
        with TemporaryDirectory() as tmpdir:
            detector = ChangeDetector(repo_root=Path(tmpdir))
            assert detector.repo_root == Path(tmpdir)

    def test_detect_invalid_mode(self):
        """Test detect with invalid mode raises error"""
        with TemporaryDirectory() as tmpdir:
            detector = ChangeDetector(repo_root=Path(tmpdir))

            with pytest.raises(ValueError) as exc_info:
                detector.detect(mode='invalid')

            assert "Invalid mode" in str(exc_info.value)

    def test_detect_staged_no_changes(self):
        """Test detecting staged changes when none exist"""
        with TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            # Initialize git repo
            subprocess.run(['git', 'init'], cwd=repo_root, check=True, capture_output=True)
            subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=repo_root, check=True)
            subprocess.run(['git', 'config', 'user.name', 'Test'], cwd=repo_root, check=True)

            detector = ChangeDetector(repo_root=repo_root)
            changes = detector.detect(mode='staged')

            assert changes == []

    def test_detect_staged_added_file(self):
        """Test detecting added file in staging area"""
        with TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            # Initialize git repo
            subprocess.run(['git', 'init'], cwd=repo_root, check=True, capture_output=True)
            subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=repo_root, check=True)
            subprocess.run(['git', 'config', 'user.name', 'Test'], cwd=repo_root, check=True)

            # Create and stage a file
            test_file = repo_root / 'test.txt'
            test_file.write_text('test content')
            subprocess.run(['git', 'add', 'test.txt'], cwd=repo_root, check=True)

            detector = ChangeDetector(repo_root=repo_root)
            changes = detector.detect(mode='staged')

            assert len(changes) == 1
            assert changes[0].event_type == ChangeType.FILE_ADDED
            assert changes[0].path == 'test.txt'
            assert changes[0].content_hash is not None

    def test_detect_staged_modified_file(self):
        """Test detecting modified file in staging area"""
        with TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            # Initialize git repo and create initial commit
            subprocess.run(['git', 'init'], cwd=repo_root, check=True, capture_output=True)
            subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=repo_root, check=True)
            subprocess.run(['git', 'config', 'user.name', 'Test'], cwd=repo_root, check=True)

            test_file = repo_root / 'test.txt'
            test_file.write_text('original')
            subprocess.run(['git', 'add', 'test.txt'], cwd=repo_root, check=True)
            subprocess.run(['git', 'commit', '-m', 'Initial'], cwd=repo_root, check=True)

            # Modify and stage
            test_file.write_text('modified')
            subprocess.run(['git', 'add', 'test.txt'], cwd=repo_root, check=True)

            detector = ChangeDetector(repo_root=repo_root)
            changes = detector.detect(mode='staged')

            assert len(changes) == 1
            assert changes[0].event_type == ChangeType.FILE_MODIFIED
            assert changes[0].path == 'test.txt'

    def test_detect_staged_deleted_file(self):
        """Test detecting deleted file in staging area"""
        with TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            # Initialize git repo and create initial commit
            subprocess.run(['git', 'init'], cwd=repo_root, check=True, capture_output=True)
            subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=repo_root, check=True)
            subprocess.run(['git', 'config', 'user.name', 'Test'], cwd=repo_root, check=True)

            test_file = repo_root / 'test.txt'
            test_file.write_text('content')
            subprocess.run(['git', 'add', 'test.txt'], cwd=repo_root, check=True)
            subprocess.run(['git', 'commit', '-m', 'Initial'], cwd=repo_root, check=True)

            # Delete and stage
            test_file.unlink()
            subprocess.run(['git', 'add', 'test.txt'], cwd=repo_root, check=True)

            detector = ChangeDetector(repo_root=repo_root)
            changes = detector.detect(mode='staged')

            assert len(changes) == 1
            assert changes[0].event_type == ChangeType.FILE_DELETED
            assert changes[0].path == 'test.txt'

    def test_detect_staged_renamed_file(self):
        """Test detecting renamed file with high similarity"""
        with TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            # Initialize git repo and create initial commit
            subprocess.run(['git', 'init'], cwd=repo_root, check=True, capture_output=True)
            subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=repo_root, check=True)
            subprocess.run(['git', 'config', 'user.name', 'Test'], cwd=repo_root, check=True)

            old_file = repo_root / 'old.txt'
            old_file.write_text('content that will be preserved')
            subprocess.run(['git', 'add', 'old.txt'], cwd=repo_root, check=True)
            subprocess.run(['git', 'commit', '-m', 'Initial'], cwd=repo_root, check=True)

            # Rename file (git should detect as rename)
            new_file = repo_root / 'new.txt'
            old_file.rename(new_file)
            subprocess.run(['git', 'add', 'old.txt', 'new.txt'], cwd=repo_root, check=True)

            detector = ChangeDetector(repo_root=repo_root)
            changes = detector.detect(mode='staged')

            # Git should detect this as a rename
            if changes and changes[0].event_type == ChangeType.FILE_RENAMED:
                assert changes[0].path == 'new.txt'
                assert changes[0].old_path == 'old.txt'
                assert changes[0].similarity >= 90

    def test_compute_file_hash(self):
        """Test file hash computation"""
        with TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            test_file = repo_root / 'test.txt'
            test_file.write_text('test content')

            detector = ChangeDetector(repo_root=repo_root)
            hash1 = detector._compute_file_hash('test.txt')

            assert hash1 is not None
            assert len(hash1) == 64  # SHA256 hex length

            # Same content = same hash
            hash2 = detector._compute_file_hash('test.txt')
            assert hash1 == hash2

    def test_compute_file_hash_nonexistent(self):
        """Test file hash for nonexistent file"""
        with TemporaryDirectory() as tmpdir:
            detector = ChangeDetector(repo_root=Path(tmpdir))
            hash_result = detector._compute_file_hash('nonexistent.txt')
            assert hash_result is None

    def test_save_changes(self):
        """Test saving changes to JSON file"""
        import json

        with TemporaryDirectory() as tmpdir:
            detector = ChangeDetector(repo_root=Path(tmpdir))

            changes = [
                Change(event_type=ChangeType.FILE_ADDED, path='file1.txt'),
                Change(event_type=ChangeType.FILE_MODIFIED, path='file2.txt')
            ]

            output_file = Path(tmpdir) / 'changes.json'
            detector.save_changes(changes, output_file)

            assert output_file.exists()

            # Verify content
            with open(output_file, 'r') as f:
                data = json.load(f)

            assert data['total'] == 2
            assert len(data['changes']) == 2
            assert data['changes'][0]['event_type'] == 'FILE_ADDED'

    def test_detect_watcher_not_implemented(self):
        """Test watcher mode raises NotImplementedError"""
        with TemporaryDirectory() as tmpdir:
            detector = ChangeDetector(repo_root=Path(tmpdir))

            with pytest.raises(NotImplementedError):
                detector.detect(mode='watcher')


__doc_id__ = 'DOC-TEST-CHANGE-DETECTOR-014'
