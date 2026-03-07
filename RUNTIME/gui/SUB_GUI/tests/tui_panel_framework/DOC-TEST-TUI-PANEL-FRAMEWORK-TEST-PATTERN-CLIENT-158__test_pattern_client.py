# DOC_LINK: DOC-TEST-TUI-PANEL-FRAMEWORK-TEST-PATTERN-CLIENT-158
"""Tests for pattern client."""

from tui_app.core.pattern_client import (
    InMemoryPatternStateStore,
    PatternClient,
    PatternEvent,
    PatternRun,
    PatternStatus,
)


def test_inmemory_pattern_store_get_recent_runs():
    """Test getting recent runs from in-memory store."""
    # DOC_ID: DOC-TEST-TUI-PANEL-FRAMEWORK-TEST-PATTERN-CLIENT-158
    store = InMemoryPatternStateStore()
    runs = store.get_recent_runs()

    assert isinstance(runs, list)
    assert len(runs) > 0
    assert all(isinstance(run, PatternRun) for run in runs)


def test_inmemory_pattern_store_get_run_events():
    """Test getting run events from in-memory store."""
    store = InMemoryPatternStateStore()
    events = store.get_run_events("run-001")

    assert isinstance(events, list)
    assert len(events) > 0
    assert all(isinstance(event, PatternEvent) for event in events)


def test_inmemory_pattern_store_get_active_patterns():
    """Test getting active patterns from in-memory store."""
    store = InMemoryPatternStateStore()
    active = store.get_active_patterns()

    assert isinstance(active, list)
    assert all(run.status == PatternStatus.RUNNING for run in active)


def test_pattern_client_get_recent_runs():
    """Test PatternClient get_recent_runs."""
    store = InMemoryPatternStateStore()
    client = PatternClient(store)

    runs = client.get_recent_runs(limit=2)
    assert isinstance(runs, list)
    assert len(runs) <= 2


def test_pattern_client_get_run_events():
    """Test PatternClient get_run_events."""
    store = InMemoryPatternStateStore()
    client = PatternClient(store)

    events = client.get_run_events("run-001")
    assert isinstance(events, list)
    assert all(event.run_id == "run-001" for event in events)


def test_pattern_client_get_active_patterns():
    """Test PatternClient get_active_patterns."""
    store = InMemoryPatternStateStore()
    client = PatternClient(store)

    active = client.get_active_patterns()
    assert isinstance(active, list)
