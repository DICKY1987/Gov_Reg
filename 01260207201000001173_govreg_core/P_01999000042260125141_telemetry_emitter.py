"""
TelemetryEmitter - Unified Telemetry Event Emitter

Provides unified event emission for all telemetry types:
- Gate results
- Metrics
- Audit events
- Lifecycle events
- Errors and warnings

FILE_ID: 01999000042260125141
"""

import json
import uuid
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List
from P_01260207233100000010_canonical_hash import hash_canonical_data

# Platform-specific file locking
if sys.platform == 'win32':
    import msvcrt
    def lock_file(file_handle):
        msvcrt.locking(file_handle.fileno(), msvcrt.LK_LOCK, 1)
    def unlock_file(file_handle):
        msvcrt.locking(file_handle.fileno(), msvcrt.LK_UNLCK, 1)
else:
    import fcntl
    def lock_file(file_handle):
        fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX)
    def unlock_file(file_handle):
        fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)


class TelemetryEmitter:
    """
    Emit unified telemetry events to JSONL format.
    
    Supports run-scoped telemetry (via RunBundle) or fallback to default location.
    Uses file locking for concurrent writes (matches COUNTER_STORE.json.lock pattern).
    """
    
    def __init__(
        self,
        run_bundle=None,  # Type hint avoided to prevent import cycle
        fallback_dir: Path = Path(".state/telemetry")
    ):
        """
        Initialize telemetry emitter.
        
        Args:
            run_bundle: Optional RunBundle instance for run-scoped telemetry
            fallback_dir: Directory for telemetry if run_bundle not provided
        """
        self.run_bundle = run_bundle
        self.fallback_dir = Path(fallback_dir)
        
        if run_bundle:
            self.output_path = run_bundle.root / "telemetry" / "events.jsonl"
        else:
            self.fallback_dir.mkdir(parents=True, exist_ok=True)
            self.output_path = self.fallback_dir / "events.jsonl"
    
    def emit(
        self,
        event_type: str,
        payload: Dict[str, Any],
        severity: str = "info",
        source: Optional[str] = None,
        run_id: Optional[str] = None,
        phase_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Emit a telemetry event.
        
        Args:
            event_type: Type of event (gate_result, metric, scan, audit, lifecycle, error)
            payload: Event-specific data
            severity: Event severity (info, warning, error, critical)
            source: Emitting module name (auto-detected if None)
            run_id: Optional run ID
            phase_id: Optional phase ID
            correlation_id: Optional correlation ID for related events
            tags: Optional tags for filtering
            
        Returns:
            The emitted event dict
        """
        if source is None:
            import inspect
            frame = inspect.currentframe().f_back
            source = frame.f_globals.get('__name__', 'unknown')
        
        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": run_id or (self.run_bundle.run_id if self.run_bundle else None),
            "phase_id": phase_id,
            "source": source,
            "severity": severity,
            "payload": payload,
            "content_hash": hash_canonical_data(payload)
        }
        
        if correlation_id:
            event["correlation_id"] = correlation_id
        if tags:
            event["tags"] = tags
        
        self._write_event(event)
        return event
    
    def emit_gate_result(
        self,
        gate_id: str,
        passed: bool,
        violations: List[Dict[str, Any]],
        evidence_path: Optional[Path] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Emit a gate result event.
        
        Args:
            gate_id: Gate identifier (e.g., "DIR-G1", "FILE-G3")
            passed: Whether gate passed
            violations: List of violation dicts
            evidence_path: Optional path to gate evidence
            **kwargs: Additional fields for emit()
            
        Returns:
            The emitted event dict
        """
        payload = {
            "gate_id": gate_id,
            "passed": passed,
            "violation_count": len(violations),
            "violations": violations
        }
        
        if evidence_path:
            payload["evidence_path"] = str(evidence_path)
        
        severity = "info" if passed else "error"
        return self.emit(
            event_type="gate_result",
            payload=payload,
            severity=severity,
            **kwargs
        )
    
    def emit_metric(
        self,
        metric_name: str,
        value: float,
        unit: str,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Emit a metric event.
        
        Args:
            metric_name: Metric name (e.g., "file_count", "duration_sec")
            value: Metric value
            unit: Unit of measurement (e.g., "count", "seconds", "bytes")
            metadata: Optional additional metadata
            **kwargs: Additional fields for emit()
            
        Returns:
            The emitted event dict
        """
        payload = {
            "metric_name": metric_name,
            "value": value,
            "unit": unit
        }
        
        if metadata:
            payload["metadata"] = metadata
        
        return self.emit(
            event_type="metric",
            payload=payload,
            severity="info",
            **kwargs
        )
    
    def emit_error(
        self,
        error_message: str,
        error_type: Optional[str] = None,
        traceback: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Emit an error event.
        
        Args:
            error_message: Error message
            error_type: Optional error type/class
            traceback: Optional traceback string
            **kwargs: Additional fields for emit()
            
        Returns:
            The emitted event dict
        """
        payload = {
            "error_message": error_message
        }
        
        if error_type:
            payload["error_type"] = error_type
        if traceback:
            payload["traceback"] = traceback
        
        return self.emit(
            event_type="error",
            payload=payload,
            severity="error",
            **kwargs
        )
    
    def _write_event(self, event: Dict[str, Any]) -> None:
        """
        Write event to JSONL file with file locking.
        
        Uses platform-specific locking to prevent concurrent write corruption.
        """
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Append event as single JSON line
        event_line = json.dumps(event, separators=(',', ':')) + '\n'
        
        # Use file locking (same pattern as COUNTER_STORE.json.lock)
        lock_path = Path(str(self.output_path) + '.lock')
        
        with open(lock_path, 'w') as lock_handle:
            try:
                lock_file(lock_handle)
                
                with open(self.output_path, 'a', encoding='utf-8') as f:
                    f.write(event_line)
                
            finally:
                unlock_file(lock_handle)
