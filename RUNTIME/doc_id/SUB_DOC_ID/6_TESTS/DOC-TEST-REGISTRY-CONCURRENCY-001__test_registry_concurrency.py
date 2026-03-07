#!/usr/bin/env python3
# DOC_LINK: DOC-TEST-REGISTRY-CONCURRENCY-001
"""
DOC-TEST-REGISTRY-CONCURRENCY-001
Tests for registry concurrency and locking.

Tests:
- 10 concurrent writers
- Deadlock detection
- Timeout behavior
- Lock cleanup on process exit
"""

import multiprocessing
import os
import pytest
import sys
import time
from importlib import util
from pathlib import Path
from tempfile import TemporaryDirectory

# Add parent directories to path
test_dir = Path(__file__).parent
sys.path.insert(0, str(test_dir.parent / "common"))

if os.name == "nt":
    pytest.skip("Registry locking uses fcntl on POSIX systems", allow_module_level=True)

_module_name = "DOC_CORE_COMMON_REGISTRY_1171__registry"
_module_path = test_dir.parent / "common" / "DOC-CORE-COMMON-REGISTRY-1171__registry.py"
_spec = util.spec_from_file_location(_module_name, _module_path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Unable to load module from {_module_path}")
_module = util.module_from_spec(_spec)
sys.modules[_module_name] = _module
_spec.loader.exec_module(_module)

from DOC_CORE_COMMON_REGISTRY_1171__registry import RegistryLock, registry_lock, RegistryLockError


@pytest.fixture
def temp_registry(tmp_path):
    """Create a temporary registry file."""
    registry_path = tmp_path / "test_registry.yaml"
    registry_path.write_text("categories: {}\ndocs: []\n")
    return registry_path


def write_to_registry_worker(registry_path, worker_id, result_queue):
    """Worker process that writes to registry."""
    try:
        lockfile_path = Path(str(registry_path) + ".lock")

        with registry_lock(registry_path, timeout=30):
            # Simulate work
            time.sleep(0.01)

            # Read current content
            with open(registry_path, 'r') as f:
                content = f.read()

            # Append worker ID
            with open(registry_path, 'a') as f:
                f.write(f"worker_{worker_id}_completed\n")

            result_queue.put(("success", worker_id))

    except RegistryLockError as e:
        result_queue.put(("error", worker_id, str(e)))
    except Exception as e:
        result_queue.put(("exception", worker_id, str(e)))


class TestRegistryLock:
    """Test suite for registry locking."""

    def test_basic_lock_acquisition(self, temp_registry):
        """Test that lock can be acquired and released."""
        lockfile = temp_registry.with_suffix('.lock')

        lock = RegistryLock(lockfile, timeout=5)
        assert lock.acquire()
        assert lock.acquired
        assert lockfile.exists()

        lock.release()
        assert not lock.acquired
        assert not lockfile.exists()

    def test_context_manager(self, temp_registry):
        """Test lock using context manager."""
        lockfile = temp_registry.with_suffix('.lock')

        with registry_lock(temp_registry, timeout=5):
            assert lockfile.exists()

        # Lock should be released after context
        assert not lockfile.exists()

    def test_lock_timeout(self, temp_registry):
        """Test that lock times out when held by another process."""
        lockfile = temp_registry.with_suffix('.lock')

        # Acquire lock in first instance
        lock1 = RegistryLock(lockfile, timeout=30)
        lock1.acquire()

        # Try to acquire with short timeout in second instance
        lock2 = RegistryLock(lockfile, timeout=1)

        with pytest.raises(RegistryLockError, match="Failed to acquire registry lock"):
            lock2.acquire()

        # Clean up
        lock1.release()

    def test_concurrent_writers(self, temp_registry):
        """Test 10 concurrent writers with locking."""
        num_workers = 10
        result_queue = multiprocessing.Queue()
        processes = []

        # Start worker processes
        for i in range(num_workers):
            p = multiprocessing.Process(
                target=write_to_registry_worker,
                args=(temp_registry, i, result_queue)
            )
            p.start()
            processes.append(p)

        # Wait for all processes
        for p in processes:
            p.join(timeout=60)  # 60s max wait

        # Collect results
        results = []
        while not result_queue.empty():
            results.append(result_queue.get())

        # Verify all workers completed successfully
        assert len(results) == num_workers

        success_count = sum(1 for r in results if r[0] == "success")
        assert success_count == num_workers, f"Only {success_count}/{num_workers} workers succeeded"

        # Verify registry content has all worker entries
        with open(temp_registry, 'r') as f:
            content = f.read()

        for i in range(num_workers):
            assert f"worker_{i}_completed" in content, f"Worker {i} did not write to registry"

    def test_deadlock_detection(self, temp_registry):
        """Test that stale locks are detected and cleaned."""
        lockfile = temp_registry.with_suffix('.lock')

        # Create a stale lock file (simulating a process that crashed 6 minutes ago)
        lockfile.parent.mkdir(parents=True, exist_ok=True)
        with open(lockfile, 'w') as f:
            # Write timestamp from 6 minutes ago (past 5-minute deadlock threshold)
            stale_time = time.time() - (6 * 60)
            f.write(f"pid=99999\ntime={stale_time}\n")

        # Should be able to acquire lock despite stale lockfile
        lock = RegistryLock(lockfile, timeout=5)
        assert lock.acquire()

        lock.release()

    def test_lock_cleanup_on_exception(self, temp_registry):
        """Test that lock is released even if exception occurs."""
        lockfile = temp_registry.with_suffix('.lock')

        try:
            with registry_lock(temp_registry, timeout=5):
                assert lockfile.exists()
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Lock should still be released
        assert not lockfile.exists()

    def test_multiple_sequential_locks(self, temp_registry):
        """Test acquiring lock multiple times sequentially."""
        lockfile = temp_registry.with_suffix('.lock')

        for i in range(5):
            with registry_lock(temp_registry, timeout=5):
                assert lockfile.exists()

            # Verify cleanup
            assert not lockfile.exists()

    def test_lock_file_permissions(self, temp_registry):
        """Test that lock file is created with correct permissions."""
        with registry_lock(temp_registry, timeout=5) as lock:
            lockfile = lock.lockfile_path
            assert lockfile.exists()

            # Verify file is readable
            with open(lockfile, 'r') as f:
                content = f.read()
                assert "pid=" in content
                assert "time=" in content


def test_registry_save_uses_lock(temp_registry, monkeypatch):
    """Test that Registry.save() uses locking."""
    from DOC_CORE_COMMON_REGISTRY_1171__registry import Registry

    lock_acquired = []

    # Mock registry_lock to track if it was called
    original_registry_lock = sys.modules['DOC_CORE_COMMON_REGISTRY_1171__registry'].registry_lock

    def mock_registry_lock(*args, **kwargs):
        lock_acquired.append(True)
        return original_registry_lock(*args, **kwargs)

    monkeypatch.setattr('DOC_CORE_COMMON_REGISTRY_1171__registry.registry_lock', mock_registry_lock)

    # Create registry and save
    registry = Registry(temp_registry)
    registry._data = {"test": "data"}
    registry.save()

    # Verify lock was acquired
    assert len(lock_acquired) > 0, "Registry.save() did not acquire lock"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
