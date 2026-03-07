"""Performance benchmarks for MINI_PIPE optimizations

Run with: pytest tests/performance/test_wave1_benchmarks.py --benchmark-only
"""

import pytest
from collections import defaultdict
from src.acms.gap_registry import GapRecord, GapSeverity, GapStatus


class TestWave1Benchmarks:
    """Benchmarks for Wave 1 optimizations"""

    @pytest.fixture
    def sample_gaps(self):
        """Create sample gaps for testing"""
        gaps = []
        for i in range(100):
            gap = GapRecord(
                gap_id=f"GAP-{i:03d}",
                title=f"Test Gap {i}",
                category="test",
                description=f"Test gap {i}",
                severity=GapSeverity.MEDIUM,
                status=GapStatus.DISCOVERED,
                file_paths=[f"file{i % 10}.py", f"file{(i+1) % 10}.py"],
                discovered_at="2025-12-07T00:00:00Z",
            )
            gaps.append(gap)
        return gaps

    def test_benchmark_set_membership(self, benchmark):
        """Benchmark set vs list membership checks"""
        statuses_list = ["PENDING", "RUNNING", "SUCCESS", "SKIPPED"]
        statuses_set = {"PENDING", "RUNNING", "SUCCESS", "SKIPPED"}

        test_values = ["PENDING", "RUNNING", "SUCCESS", "SKIPPED", "FAILED"] * 100

        def check_with_set():
            return sum(1 for status in test_values if status in statuses_set)

        result = benchmark(check_with_set)
        assert result == 400

    def test_benchmark_defaultdict_vs_manual(self, benchmark, sample_gaps):
        """Benchmark defaultdict vs manual dict initialization"""

        def manual_dict_build():
            file_to_gaps = {}
            for gap in sample_gaps:
                for file_path in gap.file_paths:
                    if file_path not in file_to_gaps:
                        file_to_gaps[file_path] = []
                    file_to_gaps[file_path].append(gap)
            return file_to_gaps

        result = benchmark(manual_dict_build)
        assert len(result) == 10

    def test_benchmark_defaultdict_optimized(self, benchmark, sample_gaps):
        """Benchmark optimized defaultdict approach"""

        def defaultdict_build():
            file_to_gaps = defaultdict(list)
            for gap in sample_gaps:
                for file_path in gap.file_paths:
                    file_to_gaps[file_path].append(gap)
            return file_to_gaps

        result = benchmark(defaultdict_build)
        assert len(result) == 10


class TestRouterStateBenchmarks:
    """Benchmarks for router state I/O batching"""

    def test_benchmark_dirty_flag_overhead(self, benchmark):
        """Measure overhead of dirty flag checking"""

        class DirtyFlagStore:
            def __init__(self):
                self._dirty = False
                self._data = {}

            def update(self, key, value):
                self._data[key] = value
                self._dirty = True

            def save_if_dirty(self):
                if not self._dirty:
                    return
                # Simulate save operation
                _ = str(self._data)
                self._dirty = False

        def dirty_flag_pattern():
            store = DirtyFlagStore()
            for i in range(100):
                store.update(f"key_{i}", i)
            store.save_if_dirty()
            return store

        result = benchmark(dirty_flag_pattern)
        assert len(result._data) == 100
        assert not result._dirty


if __name__ == "__main__":
    pytest.main([__file__, "--benchmark-only", "-v"])
