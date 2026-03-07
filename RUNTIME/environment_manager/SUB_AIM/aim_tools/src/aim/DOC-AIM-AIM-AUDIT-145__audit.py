# DOC_LINK: DOC-AIM-AIM-AUDIT-145
"""
Audit Logging Module for AIM+

Provides unified audit logging for all AIM+ operations:
- Tool installations/uninstalls
- Secret access
- Health check events
- Version changes
- Configuration updates
- Scan operations

Migrated from AI_MANGER/plugins/Audit
"""
# DOC_ID: DOC-AIM-AIM-AUDIT-145

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
import os


class EventType(Enum):
    """Types of audit events."""
    TOOL_INSTALL = "tool_install"
    TOOL_UNINSTALL = "tool_uninstall"
    TOOL_UPGRADE = "tool_upgrade"
    SECRET_SET = "secret_set"
    SECRET_GET = "secret_get"
    SECRET_DELETE = "secret_delete"
    HEALTH_CHECK = "health_check"
    VERSION_SYNC = "version_sync"
    CONFIG_UPDATE = "config_update"
    SCAN_EXECUTE = "scan_execute"
    ERROR = "error"


class EventSeverity(Enum):
    """Severity levels for audit events."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Represents a single audit event."""
    event_type: str
    timestamp: str
    severity: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    user: Optional[str] = None
    session_id: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    def to_jsonl(self) -> str:
        """Convert to JSON Lines format."""
        return json.dumps(self.to_dict())


class AuditLogger:
    """Unified audit logging system."""

    def __init__(self, log_path: Optional[Path] = None):
        """Initialize audit logger.

        Args:
            log_path: Path to audit log file. Defaults to AIM registry audit path.
        """
        if log_path is None:
            # Default to AIM registry audit path
            registry_path = os.getenv("AIM_REGISTRY_PATH") or Path.home() / ".AIM_ai-tools-registry"
            audit_dir = Path(registry_path) / "AIM_audit"
            audit_dir.mkdir(parents=True, exist_ok=True)
            self.log_path = audit_dir / "audit.jsonl"
        else:
            self.log_path = Path(log_path)
            self.log_path.parent.mkdir(parents=True, exist_ok=True)

        self.session_id = self._generate_session_id()
        self.user = os.getenv("USERNAME") or os.getenv("USER") or "unknown"

    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        import uuid
        return str(uuid.uuid4())[:8]

    def log_event(
        self,
        event_type: EventType,
        message: str,
        severity: EventSeverity = EventSeverity.INFO,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log an audit event.

        Args:
            event_type: Type of event
            message: Human-readable message
            severity: Event severity level
            details: Additional event details
        """
        event = AuditEvent(
            event_type=event_type.value,
            timestamp=datetime.now(timezone.utc).isoformat(),
            severity=severity.value,
            message=message,
            details=details or {},
            user=self.user,
            session_id=self.session_id
        )

        self._write_event(event)

    def _write_event(self, event: AuditEvent):
        """Write event to log file."""
        try:
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(event.to_jsonl() + '\n')
        except (IOError, OSError) as e:
            # Fail silently to not interrupt operations
            # Could optionally log to stderr
            pass

    def log_tool_install(self, tool: str, version: str, package_manager: str, success: bool):
        """Log a tool installation event."""
        self.log_event(
            event_type=EventType.TOOL_INSTALL,
            message=f"{'Installed' if success else 'Failed to install'} {tool} v{version}",
            severity=EventSeverity.INFO if success else EventSeverity.ERROR,
            details={
                "tool": tool,
                "version": version,
                "package_manager": package_manager,
                "success": success
            }
        )

    def log_tool_uninstall(self, tool: str, package_manager: str, success: bool):
        """Log a tool uninstall event."""
        self.log_event(
            event_type=EventType.TOOL_UNINSTALL,
            message=f"{'Uninstalled' if success else 'Failed to uninstall'} {tool}",
            severity=EventSeverity.INFO if success else EventSeverity.WARNING,
            details={
                "tool": tool,
                "package_manager": package_manager,
                "success": success
            }
        )

    def log_secret_access(self, action: str, key: str, success: bool):
        """Log secret access event.

        Args:
            action: "set", "get", or "delete"
            key: Secret key (value is NOT logged)
            success: Whether operation succeeded
        """
        event_type_map = {
            "set": EventType.SECRET_SET,
            "get": EventType.SECRET_GET,
            "delete": EventType.SECRET_DELETE
        }

        self.log_event(
            event_type=event_type_map.get(action, EventType.SECRET_SET),
            message=f"Secret {action}: {key}",
            severity=EventSeverity.INFO if success else EventSeverity.WARNING,
            details={
                "key": key,
                "action": action,
                "success": success
            }
        )

    def log_health_check(self, status: str, checks_passed: int, checks_failed: int):
        """Log health check event."""
        self.log_event(
            event_type=EventType.HEALTH_CHECK,
            message=f"Health check: {status}",
            severity=EventSeverity.INFO if status == "healthy" else EventSeverity.WARNING,
            details={
                "status": status,
                "passed": checks_passed,
                "failed": checks_failed
            }
        )

    def log_version_sync(self, tools_synced: int, tools_failed: int):
        """Log version sync event."""
        self.log_event(
            event_type=EventType.VERSION_SYNC,
            message=f"Version sync: {tools_synced} synced, {tools_failed} failed",
            severity=EventSeverity.INFO if tools_failed == 0 else EventSeverity.WARNING,
            details={
                "synced": tools_synced,
                "failed": tools_failed
            }
        )

    def log_scan(self, scan_type: str, duplicates: int, conflicts: int):
        """Log environment scan event."""
        self.log_event(
            event_type=EventType.SCAN_EXECUTE,
            message=f"Scan ({scan_type}): {duplicates} duplicates, {conflicts} conflicts",
            severity=EventSeverity.INFO,
            details={
                "scan_type": scan_type,
                "duplicates": duplicates,
                "conflicts": conflicts
            }
        )

    def log_error(self, operation: str, error_message: str, details: Optional[Dict] = None):
        """Log an error event."""
        self.log_event(
            event_type=EventType.ERROR,
            message=f"Error in {operation}: {error_message}",
            severity=EventSeverity.ERROR,
            details={
                "operation": operation,
                "error": error_message,
                **(details or {})
            }
        )

    def query_events(
        self,
        event_type: Optional[EventType] = None,
        severity: Optional[EventSeverity] = None,
        since: Optional[str] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """Query audit log for events.

        Args:
            event_type: Filter by event type
            severity: Filter by severity
            since: ISO timestamp to filter events after
            limit: Maximum number of events to return

        Returns:
            List of matching audit events
        """
        events = []

        if not self.log_path.exists():
            return events

        try:
            with open(self.log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        event_dict = json.loads(line)
                        event = AuditEvent(**event_dict)

                        # Apply filters
                        if event_type and event.event_type != event_type.value:
                            continue
                        if severity and event.severity != severity.value:
                            continue
                        if since and event.timestamp < since:
                            continue

                        events.append(event)

                        if len(events) >= limit:
                            break
                    except (json.JSONDecodeError, TypeError):
                        continue
        except (IOError, OSError):
            pass

        return events

    def get_recent_events(self, count: int = 50) -> List[AuditEvent]:
        """Get most recent audit events.

        Args:
            count: Number of recent events to return

        Returns:
            List of recent audit events
        """
        events = []

        if not self.log_path.exists():
            return events

        try:
            with open(self.log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Get last N lines
            for line in reversed(lines[-count:]):
                if not line.strip():
                    continue
                try:
                    event_dict = json.loads(line)
                    events.append(AuditEvent(**event_dict))
                except (json.JSONDecodeError, TypeError):
                    continue
        except (IOError, OSError):
            pass

        return events

    def get_stats(self) -> Dict[str, Any]:
        """Get audit log statistics.

        Returns:
            Dictionary with log statistics
        """
        stats = {
            "total_events": 0,
            "by_type": {},
            "by_severity": {},
            "log_size_bytes": 0,
            "oldest_event": None,
            "newest_event": None
        }

        if not self.log_path.exists():
            return stats

        try:
            stats["log_size_bytes"] = self.log_path.stat().st_size

            with open(self.log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        event_dict = json.loads(line)
                        stats["total_events"] += 1

                        # Count by type
                        event_type = event_dict.get("event_type", "unknown")
                        stats["by_type"][event_type] = stats["by_type"].get(event_type, 0) + 1

                        # Count by severity
                        severity = event_dict.get("severity", "unknown")
                        stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1

                        # Track timestamps
                        timestamp = event_dict.get("timestamp")
                        if timestamp:
                            if not stats["oldest_event"] or timestamp < stats["oldest_event"]:
                                stats["oldest_event"] = timestamp
                            if not stats["newest_event"] or timestamp > stats["newest_event"]:
                                stats["newest_event"] = timestamp
                    except (json.JSONDecodeError, TypeError):
                        continue
        except (IOError, OSError):
            pass

        return stats


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger(log_path: Optional[Path] = None) -> AuditLogger:
    """Get global audit logger instance.

    Note: If log_path is provided and differs from existing instance,
    creates a new instance (updates singleton).
    """
    global _audit_logger
    if _audit_logger is None or (log_path is not None and _audit_logger.log_path != Path(log_path)):
        _audit_logger = AuditLogger(log_path)
    return _audit_logger


def log_event(event_type: EventType, message: str, **kwargs):
    """Convenience function to log an event."""
    logger = get_audit_logger()
    logger.log_event(event_type, message, **kwargs)
