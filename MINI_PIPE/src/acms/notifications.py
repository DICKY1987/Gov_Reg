"""ACMS Notification System

Handles sending notifications for ACMS pipeline events via multiple channels.
Supports email, Slack, and GitHub Issues integration.
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
import subprocess


class NotificationLevel(Enum):
    """Notification severity levels"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationChannel(Enum):
    """Available notification channels"""

    EMAIL = "email"
    SLACK = "slack"
    GITHUB_ISSUE = "github_issue"
    CONSOLE = "console"


@dataclass
class NotificationConfig:
    """Configuration for notification system"""

    enabled_channels: List[NotificationChannel]
    slack_webhook_url: Optional[str] = None
    email_recipients: Optional[List[str]] = None
    github_repo: Optional[str] = None
    min_level: NotificationLevel = NotificationLevel.INFO


@dataclass
class Notification:
    """A notification message"""

    title: str
    message: str
    level: NotificationLevel
    metadata: Dict[str, Any]
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class NotificationService:
    """Service for sending notifications through multiple channels"""

    def __init__(self, config: NotificationConfig):
        self.config = config
        self._validate_config()

    def _validate_config(self):
        """Validate notification configuration"""
        if NotificationChannel.SLACK in self.config.enabled_channels:
            if not self.config.slack_webhook_url:
                print("⚠️  Slack enabled but no webhook URL configured")

        if NotificationChannel.EMAIL in self.config.enabled_channels:
            if not self.config.email_recipients:
                print("⚠️  Email enabled but no recipients configured")

        if NotificationChannel.GITHUB_ISSUE in self.config.enabled_channels:
            if not self.config.github_repo:
                print("⚠️  GitHub Issues enabled but no repo configured")

    def send(self, notification: Notification) -> bool:
        """Send notification through all enabled channels"""
        if notification.level.value < self.config.min_level.value:
            return True

        success = True
        for channel in self.config.enabled_channels:
            try:
                if channel == NotificationChannel.CONSOLE:
                    self._send_console(notification)
                elif channel == NotificationChannel.SLACK:
                    self._send_slack(notification)
                elif channel == NotificationChannel.EMAIL:
                    self._send_email(notification)
                elif channel == NotificationChannel.GITHUB_ISSUE:
                    self._send_github_issue(notification)
            except Exception as e:
                print(f"❌ Failed to send notification via {channel.value}: {e}")
                success = False

        return success

    def _send_console(self, notification: Notification):
        """Send notification to console"""
        icons = {
            NotificationLevel.INFO: "ℹ️",
            NotificationLevel.WARNING: "⚠️",
            NotificationLevel.ERROR: "❌",
            NotificationLevel.CRITICAL: "🚨",
        }
        icon = icons.get(notification.level, "📢")

        print(f"\n{icon} {notification.title}")
        print(f"   {notification.message}")
        if notification.metadata:
            print(f"   Metadata: {json.dumps(notification.metadata, indent=2)}")

    def _send_slack(self, notification: Notification):
        """Send notification to Slack webhook"""
        if not self.config.slack_webhook_url:
            return

        colors = {
            NotificationLevel.INFO: "#36a64f",
            NotificationLevel.WARNING: "#ff9900",
            NotificationLevel.ERROR: "#ff0000",
            NotificationLevel.CRITICAL: "#8b0000",
        }

        payload = {
            "attachments": [
                {
                    "color": colors.get(notification.level, "#36a64f"),
                    "title": notification.title,
                    "text": notification.message,
                    "fields": [
                        {"title": k, "value": str(v), "short": True}
                        for k, v in notification.metadata.items()
                    ],
                    "footer": "ACMS Pipeline",
                    "ts": int(notification.timestamp.timestamp()),
                }
            ]
        }

        import urllib.request

        req = urllib.request.Request(
            self.config.slack_webhook_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req)

    def _send_email(self, notification: Notification):
        """Send notification via email (placeholder for SMTP integration)"""
        if not self.config.email_recipients:
            return

        # Placeholder - would integrate with SMTP server
        print(f"📧 Email would be sent to: {', '.join(self.config.email_recipients)}")
        print(f"   Subject: {notification.title}")
        print(f"   Body: {notification.message}")

    def _send_github_issue(self, notification: Notification):
        """Create GitHub issue for critical notifications"""
        if not self.config.github_repo or notification.level not in [
            NotificationLevel.ERROR,
            NotificationLevel.CRITICAL,
        ]:
            return

        # Only create issues for errors and critical
        title = f"[ACMS Alert] {notification.title}"
        body = f"""{notification.message}

**Level:** {notification.level.value}
**Timestamp:** {notification.timestamp.isoformat()}

**Metadata:**
`json
{json.dumps(notification.metadata, indent=2)}
`

---
*This issue was automatically created by ACMS Pipeline*
"""

        try:
            # Use gh CLI to create issue
            cmd = [
                "gh",
                "issue",
                "create",
                "--repo",
                self.config.github_repo,
                "--title",
                title,
                "--body",
                body,
                "--label",
                f"acms-{notification.level.value}",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print(f"✓ GitHub issue created: {result.stdout.strip()}")
        except Exception as e:
            print(f"Failed to create GitHub issue: {e}")


class ACMSNotifier:
    """Convenience wrapper for ACMS-specific notifications"""

    def __init__(self, config: NotificationConfig):
        self.service = NotificationService(config)

    def pipeline_started(self, run_id: str, mode: str):
        """Notify that pipeline has started"""
        self.service.send(
            Notification(
                title="ACMS Pipeline Started",
                message=f"Pipeline execution started in {mode} mode",
                level=NotificationLevel.INFO,
                metadata={"run_id": run_id, "mode": mode},
            )
        )

    def pipeline_completed(self, run_id: str, gaps_found: int, duration: float):
        """Notify that pipeline completed successfully"""
        self.service.send(
            Notification(
                title="ACMS Pipeline Completed",
                message=f"Found {gaps_found} gaps in {duration:.1f}s",
                level=NotificationLevel.INFO,
                metadata={
                    "run_id": run_id,
                    "gaps_found": gaps_found,
                    "duration_seconds": duration,
                },
            )
        )

    def pipeline_failed(self, run_id: str, error: str, phase: str):
        """Notify that pipeline failed"""
        self.service.send(
            Notification(
                title="ACMS Pipeline Failed",
                message=f"Pipeline failed in {phase}: {error}",
                level=NotificationLevel.ERROR,
                metadata={"run_id": run_id, "phase": phase, "error": error},
            )
        )

    def gap_discovered(self, gap_id: str, title: str, severity: str):
        """Notify about newly discovered gap"""
        level = NotificationLevel.WARNING
        if severity in ["critical", "high"]:
            level = NotificationLevel.ERROR

        self.service.send(
            Notification(
                title=f"New Gap: {title}",
                message=f"Gap {gap_id} discovered with {severity} severity",
                level=level,
                metadata={"gap_id": gap_id, "severity": severity},
            )
        )

    def execution_completed(self, run_id: str, tasks_completed: int, tasks_failed: int):
        """Notify about execution phase completion"""
        level = NotificationLevel.INFO
        if tasks_failed > 0:
            level = NotificationLevel.WARNING

        self.service.send(
            Notification(
                title="ACMS Execution Completed",
                message=f"Completed {tasks_completed} tasks, {tasks_failed} failed",
                level=level,
                metadata={
                    "run_id": run_id,
                    "tasks_completed": tasks_completed,
                    "tasks_failed": tasks_failed,
                },
            )
        )


def create_notifier_from_env() -> ACMSNotifier:
    """Create notifier from environment variables"""
    enabled_channels = []

    # Always enable console
    enabled_channels.append(NotificationChannel.CONSOLE)

    # Check for Slack
    slack_webhook = os.getenv("ACMS_SLACK_WEBHOOK")
    if slack_webhook:
        enabled_channels.append(NotificationChannel.SLACK)

    # Check for email
    email_recipients = os.getenv("ACMS_EMAIL_RECIPIENTS")
    email_list = email_recipients.split(",") if email_recipients else None
    if email_list:
        enabled_channels.append(NotificationChannel.EMAIL)

    # Check for GitHub
    github_repo = os.getenv("ACMS_GITHUB_REPO") or os.getenv("GITHUB_REPOSITORY")
    if github_repo:
        enabled_channels.append(NotificationChannel.GITHUB_ISSUE)

    config = NotificationConfig(
        enabled_channels=enabled_channels,
        slack_webhook_url=slack_webhook,
        email_recipients=email_list,
        github_repo=github_repo,
        min_level=NotificationLevel.INFO,
    )

    return ACMSNotifier(config)
