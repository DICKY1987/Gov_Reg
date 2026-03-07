# DOC_LINK: DOC-TEST-ROLLBACK-MANAGER-007
"""Unit tests for RollbackManager

Tests snapshot creation, file backup, and rollback operations.

DOC_ID: DOC-TEST-ROLLBACK-MANAGER-007
"""

import pytest
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from RUNTIME.doc_id.SUB_DOC_ID.orchestrator.state.rollback_manager import (
    RollbackManager,
    Snapshot
)


class TestSnapshot:
    """Test Snapshot dataclass"""

    def test_snapshot_creation(self):
        """Test creating a snapshot"""
        snapshot = Snapshot(
            snapshot_id="test_snapshot_001",
            snapshot_path=Path("/tmp/snapshots/test_snapshot_001"),
            created_at="2026-01-10T00:00:00Z",
            context="test"
        )

        assert snapshot.snapshot_id == "test_snapshot_001"
        assert snapshot.context == "test"
        assert len(snapshot.files_snapshot) == 0


class TestRollbackManager:
    """Test RollbackManager"""

    def test_initialization(self):
        """Test rollback manager initialization"""
        with TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            mgr = RollbackManager(repo_root=repo_root)

            assert mgr.repo_root == repo_root
            assert mgr.snapshot_dir.exists()
            assert mgr.current_snapshot is None

    def test_create_snapshot(self):
        """Test creating a snapshot"""
        with TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            mgr = RollbackManager(repo_root=repo_root)

            snapshot_id = mgr.create_snapshot('test')

            assert snapshot_id.startswith('snapshot_test_')
            assert mgr.current_snapshot is not None
            assert mgr.current_snapshot.snapshot_id == snapshot_id
            assert mgr.current_snapshot.context == 'test'
            assert mgr.current_snapshot.snapshot_path.exists()

    def test_snapshot_file(self):
        """Test snapshotting a single file"""
        with TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            mgr = RollbackManager(repo_root=repo_root)

            # Create a test file
            test_file = repo_root / 'test.txt'
            test_file.write_text('original content')

            # Create snapshot and snapshot the file
            mgr.create_snapshot('test')
            mgr.snapshot_file(test_file)

            # Verify file was snapshotted
            assert len(mgr.current_snapshot.files_snapshot) == 1
            assert 'test.txt' in mgr.current_snapshot.files_snapshot

            # Verify snapshot file exists
            snapshot_file = mgr.current_snapshot.snapshot_path / 'test.txt'
            assert snapshot_file.exists()
            assert snapshot_file.read_text() == 'original content'

    def test_snapshot_file_relative_path(self):
        """Test snapshotting a file with relative path"""
        with TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            mgr = RollbackManager(repo_root=repo_root)

            # Create subdirectory and file
            subdir = repo_root / 'subdir'
            subdir.mkdir()
            test_file = subdir / 'test.txt'
            test_file.write_text('content')

            # Snapshot with relative path
            mgr.create_snapshot('test')
            mgr.snapshot_file(Path('subdir/test.txt'))

            assert 'subdir/test.txt' in mgr.current_snapshot.files_snapshot

    def test_snapshot_nonexistent_file(self):
        """Test snapshotting a file that doesn't exist (should not error)"""
        with TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            mgr = RollbackManager(repo_root=repo_root)

            mgr.create_snapshot('test')
            mgr.snapshot_file(Path('nonexistent.txt'))  # Should not raise

            assert len(mgr.current_snapshot.files_snapshot) == 0

    def test_snapshot_directory(self):
        """Test snapshotting all files in a directory"""
        with TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            mgr = RollbackManager(repo_root=repo_root)

            # Create directory with files
            testdir = repo_root / 'testdir'
            testdir.mkdir()
            (testdir / 'file1.txt').write_text('content1')
            (testdir / 'file2.txt').write_text('content2')
            (testdir / 'subdir').mkdir()
            (testdir / 'subdir' / 'file3.txt').write_text('content3')

            # Snapshot directory
            mgr.create_snapshot('test')
            mgr.snapshot_directory(testdir)

            assert len(mgr.current_snapshot.files_snapshot) == 3

    def test_snapshot_directory_with_patterns(self):
        """Test snapshotting directory with glob patterns"""
        with TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            mgr = RollbackManager(repo_root=repo_root)

            # Create directory with mixed files
            testdir = repo_root / 'testdir'
            testdir.mkdir()
            (testdir / 'file1.txt').write_text('txt')
            (testdir / 'file2.json').write_text('json')
            (testdir / 'file3.txt').write_text('txt')

            # Snapshot only .txt files
            mgr.create_snapshot('test')
            mgr.snapshot_directory(testdir, patterns=['*.txt'])

            assert len(mgr.current_snapshot.files_snapshot) == 2
            assert all('txt' in f for f in mgr.current_snapshot.files_snapshot)

    def test_rollback(self):
        """Test rollback restores files"""
        with TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            mgr = RollbackManager(repo_root=repo_root)

            # Create original file
            test_file = repo_root / 'test.txt'
            test_file.write_text('original')

            # Create snapshot
            mgr.create_snapshot('test')
            mgr.snapshot_file(test_file)

            # Modify file
            test_file.write_text('modified')
            assert test_file.read_text() == 'modified'

            # Rollback
            result = mgr.rollback()

            assert result is True
            assert test_file.read_text() == 'original'

    def test_rollback_multiple_files(self):
        """Test rollback with multiple files"""
        with TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            mgr = RollbackManager(repo_root=repo_root)

            # Create files
            file1 = repo_root / 'file1.txt'
            file2 = repo_root / 'file2.txt'
            file1.write_text('content1_original')
            file2.write_text('content2_original')

            # Snapshot
            mgr.create_snapshot('test')
            mgr.snapshot_file(file1)
            mgr.snapshot_file(file2)

            # Modify both files
            file1.write_text('content1_modified')
            file2.write_text('content2_modified')

            # Rollback
            mgr.rollback()

            assert file1.read_text() == 'content1_original'
            assert file2.read_text() == 'content2_original'

    def test_commit_snapshot(self):
        """Test committing snapshot removes it"""
        with TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            mgr = RollbackManager(repo_root=repo_root)

            # Create snapshot
            mgr.create_snapshot('test')
            snapshot_path = mgr.current_snapshot.snapshot_path

            assert snapshot_path.exists()

            # Commit
            mgr.commit_snapshot()

            assert not snapshot_path.exists()
            assert mgr.current_snapshot is None

    def test_record_operation(self):
        """Test recording operations"""
        with TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            mgr = RollbackManager(repo_root=repo_root)

            mgr.create_snapshot('test')

            mgr.record_operation({
                'action': 'mint_id',
                'target': 'file.txt',
                'result': 'DOC-TEST-001'
            })

            assert len(mgr.operations) == 1
            assert mgr.operations[0]['action'] == 'mint_id'
            assert 'timestamp' in mgr.operations[0]

    def test_rollback_without_snapshot_raises(self):
        """Test rollback without snapshot raises error"""
        with TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            mgr = RollbackManager(repo_root=repo_root)

            with pytest.raises(RuntimeError) as exc_info:
                mgr.rollback()

            assert "No active snapshot" in str(exc_info.value)

    def test_snapshot_file_without_snapshot_raises(self):
        """Test snapshotting file without active snapshot raises error"""
        with TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            mgr = RollbackManager(repo_root=repo_root)

            test_file = repo_root / 'test.txt'
            test_file.write_text('content')

            with pytest.raises(RuntimeError) as exc_info:
                mgr.snapshot_file(test_file)

            assert "No active snapshot" in str(exc_info.value)


__doc_id__ = 'DOC-TEST-ROLLBACK-MANAGER-007'
