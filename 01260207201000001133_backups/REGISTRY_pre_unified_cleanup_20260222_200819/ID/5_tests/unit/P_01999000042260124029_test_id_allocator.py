"""Unit tests for ID Allocator module.

FILE_ID: 01999000042260124029
DOC_ID: P_01999000042260124029
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Import the module to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from P_01999000042260124027_id_allocator import (
    allocate_single_id,
    allocate_batch_ids,
    peek_next_id,
    get_allocation_stats,
    reserve_id_range,
    ID_COUNTER_PATH
)


@pytest.fixture
def temp_counter_file(tmp_path, monkeypatch):
    """Create a temporary ID counter file for testing."""
    counter_file = tmp_path / "test_counter.json"
    
    initial_data = {
        "next_id": 500,
        "prefix": "01999000042260124",
        "last_allocated": 100,
        "allocation_history": [],
        "schema_version": "1.1"
    }
    
    with open(counter_file, "w") as f:
        json.dump(initial_data, f)
    
    # Monkey-patch the ID_COUNTER_PATH
    monkeypatch.setattr("P_01999000042260124027_id_allocator.ID_COUNTER_PATH", counter_file)
    
    return counter_file


def test_allocate_single_id(temp_counter_file):
    """Test single ID allocation."""
    file_id = allocate_single_id("Test purpose")

    assert file_id == "01999000042260124101"  # 17-char prefix + 3-digit suffix

    # Verify counter was incremented
    with open(temp_counter_file) as f:
        counter = json.load(f)

    assert counter["last_allocated"] == 101
    assert len(counter["allocation_history"]) == 1
    assert counter["allocation_history"][0]["id"] == file_id


def test_allocate_batch_ids(temp_counter_file):
    """Test batch ID allocation."""
    ids = allocate_batch_ids(5, "Batch test")

    assert len(ids) == 5
    assert ids[0] == "01999000042260124101"  # 17-char prefix + 3-digit suffix
    assert ids[4] == "01999000042260124105"
    
    # Verify counter was incremented
    with open(temp_counter_file) as f:
        counter = json.load(f)
    
    assert counter["last_allocated"] == 105
    assert len(counter["allocation_history"]) == 1


def test_peek_next_id(temp_counter_file):
    """Test peeking at next ID without allocating."""
    next_id = peek_next_id()

    assert next_id == "01999000042260124101"  # 17-char prefix + 3-digit suffix
    
    # Verify counter was NOT incremented
    with open(temp_counter_file) as f:
        counter = json.load(f)
    
    assert counter["last_allocated"] == 100


def test_get_allocation_stats(temp_counter_file):
    """Test getting allocation statistics."""
    # Allocate a few IDs first
    allocate_single_id("Test 1")
    allocate_single_id("Test 2")

    stats = get_allocation_stats()

    assert stats["next_available_id"] == "01999000042260124103"  # 17-char prefix + 3-digit suffix
    assert stats["total_allocated"] == 102
    assert len(stats["recent_allocations"]) == 2


def test_reserve_id_range(temp_counter_file):
    """Test reserving an ID range."""
    reserve_id_range(200, 210, "Reserved for future feature")
    
    # Verify counter was updated
    with open(temp_counter_file) as f:
        counter = json.load(f)
    
    assert counter["last_allocated"] == 210
    assert len(counter["allocation_history"]) == 1
    assert counter["allocation_history"][0]["reserved"] is True


def test_concurrent_allocation(temp_counter_file):
    """Test that concurrent allocations don't conflict."""
    import threading
    
    results = []
    
    def allocate():
        file_id = allocate_single_id("Concurrent test")
        results.append(file_id)
    
    threads = [threading.Thread(target=allocate) for _ in range(10)]
    
    for t in threads:
        t.start()
    
    for t in threads:
        t.join()
    
    # All IDs should be unique
    assert len(results) == 10
    assert len(set(results)) == 10


def test_batch_allocation_validation(temp_counter_file):
    """Test that batch allocation validates count."""
    with pytest.raises(ValueError, match="Count must be >= 1"):
        allocate_batch_ids(0, "Invalid")
    
    with pytest.raises(ValueError, match="Count must be >= 1"):
        allocate_batch_ids(-1, "Invalid")


def test_reserve_overlapping_range_fails(temp_counter_file):
    """Test that reserving an overlapping range fails."""
    with pytest.raises(ValueError, match="overlaps with already allocated"):
        reserve_id_range(50, 150, "Overlapping")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
