# DOC_LINK: DOC-ERROR-ALERTING-001
"""Alerting for error automation failures and queue backlog

EXECUTION PATTERN: EXEC-003 (Tool Availability Guards)
- Validates Slack webhook before sending
- Graceful degradation if unavailable
- Logs alerts even if delivery fails

DOC_ID: DOC-ERROR-ALERTING-001
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


class AlertManager:
    """Sends alerts for error automation events"""

    def __init__(
        self,
        slack_webhook: Optional[str] = None,
        alert_log: Optional[Path] = None
    ):
        """Initialize alert manager.

        Pattern: EXEC-003 - Validate tool availability

        Args:
            slack_webhook: Slack webhook URL (or use SLACK_WEBHOOK_URL env var)
            alert_log: Path to alert log file
        """
        self.slack_webhook = slack_webhook or os.getenv('SLACK_WEBHOOK_URL')
        self.alert_log = alert_log or Path(".state/alerts.jsonl")
        self.alert_log.parent.mkdir(parents=True, exist_ok=True)

        # Check if requests is available for Slack
        try:
            import requests
            self.requests = requests
            self.slack_available = bool(self.slack_webhook)
        except ImportError:
            self.requests = None
            self.slack_available = False

    def alert_patch_failed(
        self,
        patch_path: str,
        error: str,
        confidence: Optional[Dict[str, float]] = None
    ) -> None:
        """Alert when patch validation fails.

        Args:
            patch_path: Path to patch file
            error: Error message
            confidence: Optional confidence scores
        """
        alert = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'type': 'patch_failed',
            'patch_path': patch_path,
            'error': error,
            'confidence': confidence or {}
        }

        # Log to file
        self._log_alert(alert)

        # Send to Slack
        if self.slack_available:
            self._send_slack({
                'text': f"❌ Patch validation failed: `{Path(patch_path).name}`",
                'attachments': [{
                    'color': 'danger',
                    'fields': [
                        {'title': 'Error', 'value': error, 'short': False},
                        {'title': 'Patch', 'value': patch_path, 'short': True},
                        {
                            'title': 'Confidence',
                            'value': f"{confidence.get('overall', 0):.1%}" if confidence else 'N/A',
                            'short': True
                        }
                    ]
                }]
            })

    def alert_queue_backlog(
        self,
        count: int,
        oldest_hours: float,
        threshold_count: int = 10,
        threshold_hours: float = 72
    ) -> None:
        """Alert when manual review queue grows too large.

        Args:
            count: Number of pending reviews
            oldest_hours: Age of oldest review in hours
            threshold_count: Alert if count exceeds this
            threshold_hours: Alert if age exceeds this
        """
        if count < threshold_count and oldest_hours < threshold_hours:
            return  # No alert needed

        alert = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'type': 'queue_backlog',
            'pending_count': count,
            'oldest_age_hours': oldest_hours
        }

        # Log to file
        self._log_alert(alert)

        # Determine severity
        color = 'danger' if count > threshold_count or oldest_hours > threshold_hours else 'warning'

        # Send to Slack
        if self.slack_available:
            self._send_slack({
                'text': "⚠️ Manual review queue backlog detected",
                'attachments': [{
                    'color': color,
                    'fields': [
                        {'title': 'Pending Reviews', 'value': str(count), 'short': True},
                        {'title': 'Oldest Age', 'value': f"{oldest_hours:.1f}h", 'short': True},
                        {
                            'title': 'Threshold',
                            'value': f"{threshold_count} items / {threshold_hours}h",
                            'short': False
                        }
                    ]
                }]
            })

    def alert_auto_merge_success(
        self,
        patch_path: str,
        confidence: Dict[str, float]
    ) -> None:
        """Alert when high-confidence patch auto-merges.

        Args:
            patch_path: Path to patch file
            confidence: Confidence scores
        """
        alert = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'type': 'auto_merge_success',
            'patch_path': patch_path,
            'confidence': confidence
        }

        # Log to file
        self._log_alert(alert)

        # Send to Slack (informational)
        if self.slack_available:
            self._send_slack({
                'text': f"✅ Auto-merged patch: `{Path(patch_path).name}`",
                'attachments': [{
                    'color': 'good',
                    'fields': [
                        {
                            'title': 'Confidence',
                            'value': f"{confidence['overall']:.1%}",
                            'short': True
                        },
                        {'title': 'Patch', 'value': patch_path, 'short': True}
                    ]
                }]
            })

    def _log_alert(self, alert: Dict[str, Any]) -> None:
        """Log alert to file.

        Args:
            alert: Alert dictionary
        """
        with open(self.alert_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(alert) + '\n')

    def _send_slack(self, payload: Dict[str, Any]) -> None:
        """Send Slack notification.

        Args:
            payload: Slack message payload

        Note:
            Non-fatal: Logs error but doesn't crash if Slack fails
        """
        if not self.slack_available or not self.requests:
            return

        try:
            response = self.requests.post(
                self.slack_webhook,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
        except Exception as e:
            # Non-fatal: Log error but don't crash
            print(f"Warning: Failed to send Slack alert: {e}")
