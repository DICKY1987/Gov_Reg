#!/usr/bin/env python3
"""
Integration Tests for SUB_DOC_ID Event System.

Tests full event emission flow from SUB_DOC_ID operations to event sinks.

Coverage:
- Scanner emits events during scan
- Assigner emits events during assignment
- Validators emit events during validation
- Events appear in JSONL file
- Coverage provider returns real data
- No performance regression (<5% overhead)
"""
# DOC_ID: DOC-CORE-SUB-DOC-ID-6-TESTS-TEST-EVENT-INTEGRATION-1116

import asyncio
import json
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "SSOT_System" / "SSOT_SYS_tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "1_CORE_OPERATIONS"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "2_VALIDATION_FIXING"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "common"))

from event_emitter import AsyncEventEmitter, set_global_emitter
from event_router import EventRouter
from event_sinks import JSONLSink


def test_scanner_event_integration():
    """Test that scanner emits events during scan operation."""
    print("\n" + "=" * 70)
    print("TEST 1: Scanner Event Integration")
    print("=" * 70)

    async def run_test():
        # Create temp directory
        temp_dir = Path(tempfile.mkdtemp())
        events_file = temp_dir / "events.jsonl"

        print(f"\n1. Setting up event system...")

        # Create event infrastructure
        sink = JSONLSink(events_file)
        router = EventRouter([sink])
        emitter = AsyncEventEmitter(router, queue_size=1000)

        # Start emitter
        await emitter.start()
        set_global_emitter(emitter)

        print("   ✓ Event system initialized")

        # Import scanner
        from doc_id_scanner import DocIDScanner

        # Create test directory
        print("\n2. Creating test repository...")
        test_repo = temp_dir / "test_repo"
        test_repo.mkdir()

        # Create 25 test files
        for i in range(25):
            (test_repo / f"file_{i:02d}.py").write_text(f"# Test file {i}\n")

        print(f"   ✓ Created {test_repo} with 25 files")

        # Run scanner
        print("\n3. Running scanner...")
        scanner = DocIDScanner(repo_root=test_repo)
        results = scanner.scan_repository()

        print(f"   ✓ Scanned {len(results)} files")

        # Wait for events
        print("\n4. Waiting for events to be processed...")
        await asyncio.sleep(0.5)
        await emitter.stop()

        # Read events
        print("\n5. Verifying events...")
        events = []
        with open(events_file, 'r') as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))

        print(f"   ✓ Found {len(events)} events")

        # Verify event types
        event_types = [e.get("step_id") for e in events]
        has_started = "SCAN_STARTED" in event_types
        has_completed = "SCAN_COMPLETED" in event_types

        print(f"   SCAN_STARTED: {'✓' if has_started else '✗'}")
        print(f"   SCAN_COMPLETED: {'✓' if has_completed else '✗'}")

        # Cleanup
        events_file.unlink()
        for file in test_repo.glob("*.py"):
            file.unlink()
        test_repo.rmdir()
        temp_dir.rmdir()

        return has_started and has_completed

    return asyncio.run(run_test())


def test_coverage_provider_integration():
    """Test that coverage provider returns real data."""
    print("\n" + "=" * 70)
    print("TEST 2: Coverage Provider Integration")
    print("=" * 70)

    try:
        from coverage_provider import DocIDCoverageProvider

        print("\n1. Creating coverage provider...")
        provider = DocIDCoverageProvider()

        print("\n2. Fetching coverage metrics...")
        start = time.time()
        metrics = provider.get_coverage_metrics()
        elapsed = time.time() - start

        print(f"   ✓ Metrics fetched in {elapsed:.3f}s")

        # Verify metrics structure
        print("\n3. Verifying metrics structure...")
        assert metrics.overall_percentage >= 0
        assert metrics.total_files >= 0
        assert metrics.covered_files >= 0
        assert metrics.covered_files <= metrics.total_files
        assert metrics.compliance_state in ["compliant", "partial", "non-compliant"]
        assert isinstance(metrics.by_file_type, dict)
        assert isinstance(metrics.by_rule, dict)

        print("   ✓ All fields valid")

        # Display metrics
        print("\n4. Coverage Metrics:")
        print(f"   Overall: {metrics.overall_percentage}%")
        print(f"   Compliance: {metrics.compliance_state}")
        print(f"   Total Files: {metrics.total_files}")
        print(f"   Covered Files: {metrics.covered_files}")

        print(f"\n   By File Type:")
        for file_type, coverage in metrics.by_file_type.items():
            print(f"   - {file_type}: {coverage.coverage_pct}%")

        print(f"\n   By Rule:")
        for rule_name, coverage in metrics.by_rule.items():
            print(f"   - {rule_name}: {coverage.compliance_pct}%")

        return True

    except Exception as e:
        print(f"   ✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_validator_event_integration():
    """Test that validators emit events."""
    print("\n" + "=" * 70)
    print("TEST 3: Validator Event Integration")
    print("=" * 70)

    async def run_test():
        # Create temp directory
        temp_dir = Path(tempfile.mkdtemp())
        events_file = temp_dir / "events.jsonl"

        print(f"\n1. Setting up event system...")

        # Create event infrastructure
        sink = JSONLSink(events_file)
        router = EventRouter([sink])
        emitter = AsyncEventEmitter(router, queue_size=1000)

        # Start emitter
        await emitter.start()
        set_global_emitter(emitter)

        print("   ✓ Event system initialized")

        # Import validator
        from validate_doc_id_coverage import validate_coverage

        # Run validator
        print("\n2. Running coverage validator...")
        passed, results = validate_coverage(baseline=0.0)  # Low baseline to ensure pass

        print(f"   ✓ Validation {'PASSED' if passed else 'FAILED'}")

        # Wait for events
        print("\n3. Waiting for events to be processed...")
        await asyncio.sleep(0.5)
        await emitter.stop()

        # Read events
        print("\n4. Verifying events...")
        events = []
        with open(events_file, 'r') as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))

        print(f"   ✓ Found {len(events)} events")

        # Verify event types
        event_types = [e.get("step_id") for e in events]
        has_started = "VALIDATION_STARTED" in event_types
        has_completed = "VALIDATION_COMPLETED" in event_types
        has_result = "VALIDATION_PASSED" in event_types or "VALIDATION_FAILED" in event_types

        print(f"   VALIDATION_STARTED: {'✓' if has_started else '✗'}")
        print(f"   VALIDATION_PASSED/FAILED: {'✓' if has_result else '✗'}")
        print(f"   VALIDATION_COMPLETED: {'✓' if has_completed else '✗'}")

        # Cleanup
        events_file.unlink()
        temp_dir.rmdir()

        return has_started and has_completed and has_result

    return asyncio.run(run_test())


def test_performance_no_regression():
    """Test that event emission adds <5% overhead."""
    print("\n" + "=" * 70)
    print("TEST 4: Performance - No Regression (<5% overhead)")
    print("=" * 70)

    async def run_test():
        from doc_id_scanner import DocIDScanner

        # Create temp directory
        temp_dir = Path(tempfile.mkdtemp())
        test_repo = temp_dir / "test_repo"
        test_repo.mkdir()

        # Create 50 test files
        for i in range(50):
            (test_repo / f"file_{i:02d}.py").write_text(f"# Test file {i}\n")

        # Test 1: Without event system (baseline)
        print("\n1. Baseline scan (no events)...")
        set_global_emitter(None)  # Disable events

        start = time.time()
        scanner = DocIDScanner(repo_root=test_repo)
        results1 = scanner.scan_repository()
        baseline_time = time.time() - start

        print(f"   ✓ Baseline: {baseline_time:.3f}s ({len(results1)} files)")

        # Test 2: With event system
        print("\n2. Scan with events...")

        # Setup event system
        events_file = temp_dir / "events.jsonl"
        sink = JSONLSink(events_file)
        router = EventRouter([sink])
        emitter = AsyncEventEmitter(router, queue_size=1000)
        await emitter.start()
        set_global_emitter(emitter)

        start = time.time()
        scanner = DocIDScanner(repo_root=test_repo)
        results2 = scanner.scan_repository()
        await asyncio.sleep(0.1)  # Let events flush
        await emitter.stop()
        event_time = time.time() - start

        print(f"   ✓ With events: {event_time:.3f}s ({len(results2)} files)")

        # Calculate overhead
        overhead_pct = ((event_time - baseline_time) / baseline_time * 100)

        print(f"\n3. Overhead Analysis:")
        print(f"   Baseline: {baseline_time:.3f}s")
        print(f"   With Events: {event_time:.3f}s")
        print(f"   Overhead: {overhead_pct:+.1f}%")

        # Cleanup
        if events_file.exists():
            events_file.unlink()
        for file in test_repo.glob("*.py"):
            file.unlink()
        test_repo.rmdir()
        temp_dir.rmdir()

        # Verify overhead is <5%
        passed = overhead_pct < 5.0

        if passed:
            print(f"   ✓ PASS: Overhead {overhead_pct:.1f}% < 5%")
        else:
            print(f"   ✗ FAIL: Overhead {overhead_pct:.1f}% >= 5%")

        return passed

    return asyncio.run(run_test())


def main():
    """Run all integration tests."""
    print("\n" + "=" * 70)
    print("SUB_DOC_ID Event Integration Tests")
    print("=" * 70)

    tests = [
        ("Scanner Event Integration", test_scanner_event_integration),
        ("Coverage Provider Integration", test_coverage_provider_integration),
        ("Validator Event Integration", test_validator_event_integration),
        ("Performance - No Regression", test_performance_no_regression),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n✗ {test_name} FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")

    all_passed = all(passed for _, passed in results)

    print("\n" + "=" * 70)
    if all_passed:
        print("✓ ALL TESTS PASSED")
        print("=" * 70)
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
