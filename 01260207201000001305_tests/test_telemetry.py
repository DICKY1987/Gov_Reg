"""
Unit tests for TelemetryEmitter and TelemetryReader - Phase C

Tests event emission, file locking, and reading.

FILE_ID: 01999000042260125148
"""

import pytest
import json
import sys
import tempfile
from pathlib import Path

# Add govreg_core to path
sys.path.insert(0, str(Path(__file__).parent.parent / "01260207201000001173_govreg_core"))

from P_01999000042260125141_telemetry_emitter import TelemetryEmitter
from P_01999000042260125142_telemetry_reader import TelemetryReader


def test_telemetry_emit_basic():
    """Test basic event emission."""
    with tempfile.TemporaryDirectory() as tmpdir:
        emitter = TelemetryEmitter(fallback_dir=Path(tmpdir))
        
        event = emitter.emit(
            event_type="test",
            payload={"test_key": "test_value"},
            severity="info",
            source="test_module"
        )
        
        assert event["event_type"] == "test"
        assert event["severity"] == "info"
        assert event["source"] == "test_module"
        assert "event_id" in event
        assert "timestamp" in event
        assert "content_hash" in event


def test_telemetry_emit_gate_result():
    """Test gate result emission."""
    with tempfile.TemporaryDirectory() as tmpdir:
        emitter = TelemetryEmitter(fallback_dir=Path(tmpdir))
        
        event = emitter.emit_gate_result(
            gate_id="DIR-G1",
            passed=False,
            violations=[{"file": "test.py", "issue": "missing DIR_ID"}]
        )
        
        assert event["event_type"] == "gate_result"
        assert event["payload"]["gate_id"] == "DIR-G1"
        assert event["payload"]["passed"] == False
        assert event["severity"] == "error"


def test_telemetry_emit_metric():
    """Test metric emission."""
    with tempfile.TemporaryDirectory() as tmpdir:
        emitter = TelemetryEmitter(fallback_dir=Path(tmpdir))
        
        event = emitter.emit_metric(
            metric_name="file_count",
            value=42,
            unit="count"
        )
        
        assert event["event_type"] == "metric"
        assert event["payload"]["metric_name"] == "file_count"
        assert event["payload"]["value"] == 42
        assert event["payload"]["unit"] == "count"


def test_telemetry_reader_read_all():
    """Test reading all events."""
    with tempfile.TemporaryDirectory() as tmpdir:
        emitter = TelemetryEmitter(fallback_dir=Path(tmpdir))
        
        # Emit multiple events
        emitter.emit("test", {"data": 1}, "info")
        emitter.emit("test", {"data": 2}, "info")
        emitter.emit("error", {"msg": "fail"}, "error")
        
        reader = TelemetryReader(Path(tmpdir) / "events.jsonl")
        events = reader.read_all()
        
        assert len(events) == 3


def test_telemetry_reader_filter_by_type():
    """Test filtering by event type."""
    with tempfile.TemporaryDirectory() as tmpdir:
        emitter = TelemetryEmitter(fallback_dir=Path(tmpdir))
        
        emitter.emit("test", {"data": 1}, "info")
        emitter.emit("metric", {"value": 42}, "info")
        emitter.emit("error", {"msg": "fail"}, "error")
        
        reader = TelemetryReader(Path(tmpdir) / "events.jsonl")
        metrics = reader.filter_by_type("metric")
        
        assert len(metrics) == 1
        assert metrics[0]["event_type"] == "metric"


def test_telemetry_reader_filter_by_severity():
    """Test filtering by severity."""
    with tempfile.TemporaryDirectory() as tmpdir:
        emitter = TelemetryEmitter(fallback_dir=Path(tmpdir))
        
        emitter.emit("test", {"data": 1}, "info")
        emitter.emit("test", {"data": 2}, "warning")
        emitter.emit("test", {"data": 3}, "error")
        
        reader = TelemetryReader(Path(tmpdir) / "events.jsonl")
        errors = reader.filter_by_severity("error")
        
        assert len(errors) == 1
        assert errors[0]["severity"] == "error"


def test_telemetry_reader_summary():
    """Test summary statistics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        emitter = TelemetryEmitter(fallback_dir=Path(tmpdir))
        
        emitter.emit("test", {"data": 1}, "info")
        emitter.emit("metric", {"value": 42}, "info")
        emitter.emit("error", {"msg": "fail"}, "error")
        
        reader = TelemetryReader(Path(tmpdir) / "events.jsonl")
        summary = reader.get_summary()
        
        assert summary["total_events"] == 3
        assert summary["by_type"]["test"] == 1
        assert summary["by_type"]["metric"] == 1
        assert summary["by_severity"]["error"] == 1


def test_telemetry_content_hash_deterministic():
    """Test content hash is deterministic."""
    with tempfile.TemporaryDirectory() as tmpdir:
        emitter = TelemetryEmitter(fallback_dir=Path(tmpdir))
        
        event1 = emitter.emit("test", {"key": "value"}, "info")
        event2 = emitter.emit("test", {"key": "value"}, "info")
        
        # Same payload should produce same content hash
        assert event1["content_hash"] == event2["content_hash"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
