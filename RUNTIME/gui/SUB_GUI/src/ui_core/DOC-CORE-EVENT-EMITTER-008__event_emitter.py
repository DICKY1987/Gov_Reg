# DOC_LINK: DOC-CORE-EVENT-EMITTER-008
"""Event Emitter Utility - Thread-safe automation event emission.

Provides utilities for subsystems to emit automation events to the central event log.
Events are written to logs/events/events.jsonl in JSONL format.
"""

# DOC_ID: DOC-CORE-EVENT-EMITTER-008

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Optional

# Try to import fcntl (Unix only), ignore on Windows
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

logger = logging.getLogger(__name__)

# Global lock for thread-safe file writes
_write_lock = Lock()

# Event severity levels
class EventSeverity:
    """Standard event severity levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    NOTICE = "NOTICE"
    WARN = "WARN"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


def emit_automation_event(
    subsystem: str,
    summary: str,
    subject: str,
    severity: str = EventSeverity.INFO,
    step_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    automation_chain_id: Optional[str] = None,
    sequence_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
    event_log_path: Optional[str] = None
) -> str:
    """Emit an automation event to the event log.

    Args:
        subsystem: Subsystem name (e.g., "SUB_DOC_ID", "PHASE_5")
        summary: Brief event summary
        subject: Subject of the event (e.g., file path, task ID)
        severity: Event severity (INFO, WARN, ERROR, etc.)
        step_id: Optional step identifier
        correlation_id: Optional correlation ID for tracking
        automation_chain_id: Optional automation chain ID
        sequence_id: Optional sequence number
        details: Optional additional details dict
        event_log_path: Optional path to event log (defaults to logs/events/events.jsonl)

    Returns:
        Generated event_id

    Example:
        >>> emit_automation_event(
        ...     subsystem="SUB_DOC_ID",
        ...     summary="Doc ID assigned",
        ...     subject="src/module.py",
        ...     severity=EventSeverity.INFO,
        ...     step_id="DOC_ID_ASSIGNED",
        ...     details={"doc_id": "DOC-CORE-MODULE-001"}
        ... )
        'evt-12345678'
    """
    # Generate event ID
    event_id = f"evt-{uuid.uuid4().hex[:8]}"

    # Get current timestamp in UTC
    timestamp_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    # Build event object
    event = {
        "event_id": event_id,
        "timestamp_utc": timestamp_utc,
        "subsystem": subsystem,
        "severity": severity,
        "step_id": step_id,
        "subject": subject,
        "summary": summary,
        "correlation_id": correlation_id or "",
        "details": details or {}
    }

    # Add optional fields if provided
    if automation_chain_id:
        event["automation_chain_id"] = automation_chain_id
    if sequence_id is not None:
        event["sequence_id"] = sequence_id

    # Determine event log path
    if not event_log_path:
        # Default to logs/events/events.jsonl
        event_log_path = Path("logs") / "events" / "events.jsonl"
    else:
        event_log_path = Path(event_log_path)

    # Ensure directory exists
    event_log_path.parent.mkdir(parents=True, exist_ok=True)

    # Write event to log (thread-safe)
    try:
        _write_event_to_log(event, event_log_path)
        logger.debug(f"Emitted event {event_id}: {summary}")
        return event_id
    except Exception as e:
        logger.error(f"Failed to emit event: {e}")
        return event_id  # Return ID even if write failed


def _write_event_to_log(event: Dict[str, Any], log_path: Path):
    """Write event to log file with file locking (thread-safe).

    Args:
        event: Event dictionary
        log_path: Path to event log file
    """
    with _write_lock:
        # Use append mode which is atomic for single writes
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                # Try to acquire exclusive lock (Unix only)
                if HAS_FCNTL:
                    try:
                        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                    except:
                        pass  # Lock failed, continue anyway

                # Write event as JSON line
                json.dump(event, f, ensure_ascii=False)
                f.write("\n")
                f.flush()

                # Release lock (Unix only)
                if HAS_FCNTL:
                    try:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                    except:
                        pass
        except Exception as e:
            logger.error(f"Failed to write event to {log_path}: {e}")
            raise


# Convenience functions for common event types

def emit_file_detected_event(
    subsystem: str,
    file_path: str,
    details: Optional[Dict[str, Any]] = None
) -> str:
    """Emit a file detected event.

    Args:
        subsystem: Subsystem name
        file_path: Path to detected file
        details: Optional additional details

    Returns:
        Event ID
    """
    return emit_automation_event(
        subsystem=subsystem,
        summary=f"File detected",
        subject=file_path,
        severity=EventSeverity.INFO,
        step_id="FILE_DETECTED",
        details=details
    )


def emit_task_started_event(
    subsystem: str,
    task_id: str,
    task_kind: str,
    tool_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> str:
    """Emit a task started event.

    Args:
        subsystem: Subsystem name
        task_id: Task identifier
        task_kind: Task type/kind
        tool_id: Optional tool identifier
        details: Optional additional details

    Returns:
        Event ID
    """
    detail_dict = details or {}
    if tool_id:
        detail_dict["tool_id"] = tool_id
    detail_dict["task_kind"] = task_kind

    return emit_automation_event(
        subsystem=subsystem,
        summary=f"Task started: {task_kind}",
        subject=task_id,
        severity=EventSeverity.INFO,
        step_id="TASK_START",
        details=detail_dict
    )


def emit_task_completed_event(
    subsystem: str,
    task_id: str,
    task_kind: str,
    exit_code: int = 0,
    duration_ms: Optional[float] = None,
    details: Optional[Dict[str, Any]] = None
) -> str:
    """Emit a task completed event.

    Args:
        subsystem: Subsystem name
        task_id: Task identifier
        task_kind: Task type/kind
        exit_code: Task exit code (0 = success)
        duration_ms: Optional task duration in milliseconds
        details: Optional additional details

    Returns:
        Event ID
    """
    detail_dict = details or {}
    detail_dict["task_kind"] = task_kind
    detail_dict["exit_code"] = exit_code
    if duration_ms is not None:
        detail_dict["duration_ms"] = duration_ms

    return emit_automation_event(
        subsystem=subsystem,
        summary=f"Task completed: {task_kind}",
        subject=task_id,
        severity=EventSeverity.INFO,
        step_id="TASK_COMPLETE",
        details=detail_dict
    )


def emit_task_failed_event(
    subsystem: str,
    task_id: str,
    task_kind: str,
    error: str,
    exit_code: int = 1,
    details: Optional[Dict[str, Any]] = None
) -> str:
    """Emit a task failed event.

    Args:
        subsystem: Subsystem name
        task_id: Task identifier
        task_kind: Task type/kind
        error: Error message
        exit_code: Task exit code
        details: Optional additional details

    Returns:
        Event ID
    """
    detail_dict = details or {}
    detail_dict["task_kind"] = task_kind
    detail_dict["error"] = error
    detail_dict["exit_code"] = exit_code

    return emit_automation_event(
        subsystem=subsystem,
        summary=f"Task failed: {task_kind}",
        subject=task_id,
        severity=EventSeverity.ERROR,
        step_id="TASK_FAILED",
        details=detail_dict
    )


def emit_validation_event(
    subsystem: str,
    subject: str,
    passed: bool,
    rule_name: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> str:
    """Emit a validation event.

    Args:
        subsystem: Subsystem name
        subject: Subject being validated
        passed: Whether validation passed
        rule_name: Optional validation rule name
        details: Optional additional details

    Returns:
        Event ID
    """
    detail_dict = details or {}
    detail_dict["passed"] = passed
    if rule_name:
        detail_dict["rule_name"] = rule_name

    return emit_automation_event(
        subsystem=subsystem,
        summary=f"Validation {'passed' if passed else 'failed'}: {subject}",
        subject=subject,
        severity=EventSeverity.INFO if passed else EventSeverity.WARN,
        step_id="VALIDATION_COMPLETE",
        details=detail_dict
    )


# Context manager for event chains
class EventChain:
    """Context manager for emitting related events with correlation ID.

    Example:
        >>> with EventChain("DOC_ID_ASSIGNMENT", "SUB_DOC_ID") as chain:
        ...     chain.emit("File detected", "src/module.py")
        ...     chain.emit("Doc ID assigned", "src/module.py", details={"doc_id": "DOC-001"})
    """

    def __init__(self, chain_name: str, subsystem: str):
        """Initialize event chain.

        Args:
            chain_name: Name of the automation chain
            subsystem: Subsystem emitting events
        """
        self.chain_id = f"chain-{uuid.uuid4().hex[:8]}"
        self.chain_name = chain_name
        self.subsystem = subsystem
        self.sequence = 0

    def __enter__(self):
        """Enter context."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        if exc_type:
            # Emit error event if exception occurred
            self.emit(
                f"Chain failed: {exc_val}",
                subject=self.chain_name,
                severity=EventSeverity.ERROR,
                step_id="CHAIN_ERROR"
            )
        return False  # Don't suppress exceptions

    def emit(
        self,
        summary: str,
        subject: str,
        severity: str = EventSeverity.INFO,
        step_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """Emit event in this chain.

        Args:
            summary: Event summary
            subject: Event subject
            severity: Event severity
            step_id: Optional step ID
            details: Optional details

        Returns:
            Event ID
        """
        self.sequence += 1
        return emit_automation_event(
            subsystem=self.subsystem,
            summary=summary,
            subject=subject,
            severity=severity,
            step_id=step_id,
            correlation_id=self.chain_id,
            automation_chain_id=self.chain_name,
            sequence_id=self.sequence,
            details=details
        )
