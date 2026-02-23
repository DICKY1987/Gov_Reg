"""
TelemetryReader - Read and Query Unified Telemetry Events

Provides utilities to read, filter, and query telemetry JSONL files.

FILE_ID: 01999000042260125142
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator


class TelemetryReader:
    """
    Read and query unified telemetry events from JSONL files.
    
    Supports filtering by event type, severity, time range, and custom predicates.
    """
    
    def __init__(self, telemetry_path: Path):
        """
        Initialize telemetry reader.
        
        Args:
            telemetry_path: Path to events.jsonl file or directory containing it
        """
        self.telemetry_path = Path(telemetry_path)
        
        if self.telemetry_path.is_dir():
            self.telemetry_path = self.telemetry_path / "events.jsonl"
        
        if not self.telemetry_path.exists():
            raise FileNotFoundError(f"Telemetry file not found: {self.telemetry_path}")
    
    def read_all(self) -> List[Dict[str, Any]]:
        """
        Read all events from the telemetry file.
        
        Returns:
            List of event dicts
        """
        events = []
        with open(self.telemetry_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(json.loads(line))
        return events
    
    def iter_events(self) -> Iterator[Dict[str, Any]]:
        """
        Iterate over events lazily (memory efficient for large files).
        
        Yields:
            Event dicts one at a time
        """
        with open(self.telemetry_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)
    
    def filter_by_type(self, event_type: str) -> List[Dict[str, Any]]:
        """
        Filter events by event_type.
        
        Args:
            event_type: Event type to filter (e.g., "gate_result", "metric")
            
        Returns:
            List of matching events
        """
        return [e for e in self.iter_events() if e.get("event_type") == event_type]
    
    def filter_by_severity(self, severity: str) -> List[Dict[str, Any]]:
        """
        Filter events by severity.
        
        Args:
            severity: Severity to filter (info, warning, error, critical)
            
        Returns:
            List of matching events
        """
        return [e for e in self.iter_events() if e.get("severity") == severity]
    
    def filter_by_run_id(self, run_id: str) -> List[Dict[str, Any]]:
        """
        Filter events by run_id.
        
        Args:
            run_id: Run ID to filter
            
        Returns:
            List of matching events
        """
        return [e for e in self.iter_events() if e.get("run_id") == run_id]
    
    def filter_by_time_range(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter events by time range.
        
        Args:
            start: Optional start datetime (inclusive)
            end: Optional end datetime (inclusive)
            
        Returns:
            List of matching events
        """
        events = []
        for event in self.iter_events():
            timestamp_str = event.get("timestamp")
            if not timestamp_str:
                continue
            
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            
            if start and timestamp < start:
                continue
            if end and timestamp > end:
                continue
            
            events.append(event)
        
        return events
    
    def get_gate_results(self) -> List[Dict[str, Any]]:
        """
        Get all gate result events.
        
        Returns:
            List of gate result events
        """
        return self.filter_by_type("gate_result")
    
    def get_metrics(self) -> List[Dict[str, Any]]:
        """
        Get all metric events.
        
        Returns:
            List of metric events
        """
        return self.filter_by_type("metric")
    
    def get_errors(self) -> List[Dict[str, Any]]:
        """
        Get all error events (event_type="error" or severity="error"/"critical").
        
        Returns:
            List of error events
        """
        return [
            e for e in self.iter_events()
            if e.get("event_type") == "error" or e.get("severity") in ["error", "critical"]
        ]
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for the telemetry file.
        
        Returns:
            Dict with counts by type, severity, etc.
        """
        type_counts = {}
        severity_counts = {}
        total = 0
        
        for event in self.iter_events():
            total += 1
            
            event_type = event.get("event_type", "unknown")
            type_counts[event_type] = type_counts.get(event_type, 0) + 1
            
            severity = event.get("severity", "unknown")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            "total_events": total,
            "by_type": type_counts,
            "by_severity": severity_counts,
            "telemetry_path": str(self.telemetry_path)
        }
