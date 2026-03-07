#!/usr/bin/env python3
"""
Test Event Emission from DocIDScanner.

Validates that doc_id_scanner.py emits events correctly during scan operations.

Tests:
- SCAN_STARTED event emitted
- SCAN_PROGRESS events emitted periodically
- SCAN_COMPLETED event with stats
- Events appear in JSONL file
- Event schema compliance
"""
# DOC_ID: DOC-CORE-SUB-DOC-ID-6-TESTS-TEST-SCANNER-EVENTS-1114

import asyncio
import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path
import pytest

# Add paths
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "SSOT_System" / "SSOT_SYS_tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "1_CORE_OPERATIONS"))

from event_emitter import AsyncEventEmitter, set_global_emitter
from event_router import EventRouter
from event_sinks import JSONLSink


@pytest.mark.asyncio
async def test_scanner_event_emission():
    """Test that scanner emits events during scan operation."""
    print("=" * 70)
    print("Testing Scanner Event Emission")
    print("=" * 70)

    # Create temp directory for events
    temp_dir = Path(tempfile.mkdtemp())
    events_file = temp_dir / "events.jsonl"

    print(f"\n1. Setting up event system...")
    print(f"   Events file: {events_file}")

    # Create event infrastructure
    sink = JSONLSink(events_file)
    router = EventRouter([sink])
    emitter = AsyncEventEmitter(router, queue_size=1000)

    # Start emitter
    await emitter.start()

    # Set as global emitter
    set_global_emitter(emitter)

    print("   ✓ Event system initialized")

    # Import scanner (after event system setup)
    print("\n2. Importing scanner...")
    from doc_id_scanner import DocIDScanner
    print("   ✓ Scanner imported")

    # Create test directory with some files
    print("\n3. Creating test directory with sample files...")
    test_repo = temp_dir / "test_repo"
    test_repo.mkdir()

    # Create sample Python files
    (test_repo / "file1.py").write_text("# Test file 1\nprint('hello')\n")
    (test_repo / "file2.py").write_text("# Test file 2\ndef test():\n    pass\n")
    (test_repo / "file3.py").write_text("# Test file 3\nclass Test:\n    pass\n")

    # Create subdirectory
    subdir = test_repo / "subdir"
    subdir.mkdir()
    (subdir / "file4.py").write_text("# Test file 4\n")
    (subdir / "file5.py").write_text("# Test file 5\n")

    print(f"   ✓ Created {test_repo} with 5 .py files")

    # Run scanner
    print("\n4. Running scanner (full scan)...")
    scanner = DocIDScanner(repo_root=test_repo)

    # Perform full scan
    results = scanner.scan_repository()

    print(f"   ✓ Scan completed")
    print(f"   Files scanned: {len(results)}")

    # Wait for events to be processed
    print("\n5. Waiting for event queue to flush...")
    await asyncio.sleep(0.5)

    # Stop emitter gracefully
    await emitter.stop()
    print("   ✓ Event system stopped")

    # Read events from file
    print("\n6. Reading events from JSONL...")
    events = []
    if events_file.exists():
        with open(events_file, 'r') as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))
        print(f"   ✓ Found {len(events)} events")
    else:
        print("   ✗ No events file created!")
        return False

    # Validate events
    print("\n7. Validating events...")

    # Check for required events
    event_types = [e.get("step_id") for e in events]

    has_scan_started = "SCAN_STARTED" in event_types
    has_scan_completed = "SCAN_COMPLETED" in event_types
    has_scan_progress = "SCAN_PROGRESS" in event_types  # May not appear for 5 files

    print(f"   SCAN_STARTED: {'✓' if has_scan_started else '✗'}")
    print(f"   SCAN_COMPLETED: {'✓' if has_scan_completed else '✗'}")
    print(f"   SCAN_PROGRESS: {'✓' if has_scan_progress else '- (not expected for 5 files)'}")

    # Validate event schema
    print("\n8. Validating event schema...")
    required_fields = ["event_id", "timestamp_utc", "subsystem", "step_id",
                       "subject", "summary", "severity", "trace_id", "run_id"]

    schema_valid = True
    for event in events:
        for field in required_fields:
            if field not in event:
                print(f"   ✗ Event {event.get('event_id')} missing field: {field}")
                schema_valid = False

    if schema_valid:
        print("   ✓ All events have required fields")

    # Check subsystem
    subsystems = set(e.get("subsystem") for e in events)
    if subsystems == {"SUB_DOC_ID"}:
        print("   ✓ All events from SUB_DOC_ID subsystem")
    else:
        print(f"   ✗ Unexpected subsystems: {subsystems}")

    # Display events
    print("\n9. Event Details:")
    print("-" * 70)
    for i, event in enumerate(events, 1):
        print(f"\n   Event {i}:")
        print(f"   - ID: {event.get('event_id')}")
        print(f"   - Step: {event.get('step_id')}")
        print(f"   - Summary: {event.get('summary')}")
        print(f"   - Severity: {event.get('severity')}")
        if event.get('details'):
            print(f"   - Details: {event.get('details')}")

    # Cleanup
    print("\n10. Cleaning up...")
    events_file.unlink()
    for file in test_repo.rglob("*"):
        if file.is_file():
            file.unlink()
    (test_repo / "subdir").rmdir()
    test_repo.rmdir()
    temp_dir.rmdir()
    print("   ✓ Cleanup complete")

    # Final verdict
    print("\n" + "=" * 70)
    if has_scan_started and has_scan_completed and schema_valid:
        print("✓ ALL TESTS PASSED")
        print("=" * 70)
        return True
    else:
        print("✗ SOME TESTS FAILED")
        print("=" * 70)
        return False


@pytest.mark.asyncio
async def test_scanner_with_many_files():
    """Test scanner with enough files to trigger SCAN_PROGRESS events."""
    print("\n\n" + "=" * 70)
    print("Testing Scanner with 150+ Files (to trigger progress events)")
    print("=" * 70)

    # Create temp directory for events
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

    # Create test directory with 150 files
    print("\n2. Creating test directory with 150 files...")
    test_repo = temp_dir / "test_repo_large"
    test_repo.mkdir()

    # Create 150 Python files
    for i in range(150):
        file_path = test_repo / f"file_{i:03d}.py"
        file_path.write_text(f"# Test file {i}\nprint('test {i}')\n")

    print(f"   ✓ Created {test_repo} with 150 .py files")

    # Run scanner
    print("\n3. Running scanner (full scan)...")
    scanner = DocIDScanner(repo_root=test_repo)

    results = scanner.scan_repository()

    print(f"   ✓ Scan completed")
    print(f"   Files scanned: {len(results)}")

    # Wait for events to be processed
    print("\n4. Waiting for event queue to flush...")
    await asyncio.sleep(0.5)
    await emitter.stop()

    # Read events
    print("\n5. Reading events from JSONL...")
    events = []
    with open(events_file, 'r') as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))

    print(f"   ✓ Found {len(events)} events")

    # Check for progress events
    progress_events = [e for e in events if e.get("step_id") == "SCAN_PROGRESS"]

    print(f"\n6. Progress Events: {len(progress_events)}")
    if len(progress_events) > 0:
        print("   ✓ SCAN_PROGRESS events emitted")
        for pe in progress_events:
            details = pe.get("details", {})
            print(f"   - Progress: {details.get('files_scanned')}/{details.get('total_files')} "
                  f"({details.get('progress_pct')}%)")
    else:
        print("   ✗ No SCAN_PROGRESS events found!")

    # Cleanup
    print("\n7. Cleaning up...")
    events_file.unlink()
    for file in test_repo.glob("*.py"):
        file.unlink()
    test_repo.rmdir()
    temp_dir.rmdir()
    print("   ✓ Cleanup complete")

    # Final verdict
    print("\n" + "=" * 70)
    if len(progress_events) > 0:
        print("✓ PROGRESS EVENT TEST PASSED")
        print("=" * 70)
        return True
    else:
        print("✗ PROGRESS EVENT TEST FAILED")
        print("=" * 70)
        return False


async def main():
    """Run all tests."""
    print("DocIDScanner Event Emission Tests\n")

    # Test 1: Basic event emission
    test1_passed = await test_scanner_event_emission()

    # Test 2: Progress events with many files
    test2_passed = await test_scanner_with_many_files()

    # Summary
    print("\n\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Test 1 (Basic events): {'✓ PASSED' if test1_passed else '✗ FAILED'}")
    print(f"Test 2 (Progress events): {'✓ PASSED' if test2_passed else '✗ FAILED'}")

    if test1_passed and test2_passed:
        print("\n✓ ALL TESTS PASSED")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
