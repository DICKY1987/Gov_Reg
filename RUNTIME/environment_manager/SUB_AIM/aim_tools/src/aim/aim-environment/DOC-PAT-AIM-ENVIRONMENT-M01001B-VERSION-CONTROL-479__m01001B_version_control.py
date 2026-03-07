"""
Version control for tracking and syncing tool versions.

Manages version drift detection and synchronization of installed tools
against pinned versions in configuration.
"""
# DOC_ID: DOC-PAT-AIM-ENVIRONMENT-M01001B-VERSION-CONTROL-479

import asyncio
from dataclasses import dataclass, field
from typing import Literal, Optional

from modules.aim_environment import VersionControlError
from modules.aim_environment import ToolInstaller


@dataclass
class VersionStatus:
    """Version status for a single tool."""

    tool: str
    manager: Literal["pipx", "npm", "winget"]
    expected_version: Optional[str]
    actual_version: Optional[str]
    status: Literal["ok", "drift", "missing", "unexpected"]

    @property
    def has_drift(self) -> bool:
        """Check if version has drifted."""
        return self.status in ("drift", "missing", "unexpected")

    @property
    def is_installed(self) -> bool:
        """Check if tool is installed."""
        return self.actual_version is not None


@dataclass
class VersionReport:
    """Complete version control report."""

    statuses: list[VersionStatus] = field(default_factory=list)

    @property
    def ok_count(self) -> int:
        """Count of tools with correct versions."""
        return sum(1 for s in self.statuses if s.status == "ok")

    @property
    def drift_count(self) -> int:
        """Count of tools with version drift."""
        return sum(1 for s in self.statuses if s.status == "drift")

    @property
    def missing_count(self) -> int:
        """Count of tools not installed."""
        return sum(1 for s in self.statuses if s.status == "missing")

    @property
    def unexpected_count(self) -> int:
        """Count of tools installed but not expected."""
        return sum(1 for s in self.statuses if s.status == "unexpected")

    @property
    def total_count(self) -> int:
        """Total count of tools."""
        return len(self.statuses)

    @property
    def has_drift(self) -> bool:
        """Check if any tool has drift."""
        return any(s.has_drift for s in self.statuses)


class VersionControl:
    """Track and sync tool versions."""

    def __init__(self, config: dict, installer: Optional[ToolInstaller] = None):
        """
        Initialize version control.

        Args:
            config: Configuration dict with version pins and tool lists
            installer: ToolInstaller instance (created if not provided)
        """
        self.config = config
        self.installer = installer or ToolInstaller(config)
        self.version_pins = config.get("environment", {}).get("versionPins", {})

    async def check_version(
        self,
        tool: str,
        manager: Literal["pipx", "npm"],
        expected: Optional[str] = None
    ) -> VersionStatus:
        """
        Check version status for a single tool.

        Args:
            tool: Tool name
            manager: Package manager
            expected: Expected version (None = any version ok)

        Returns:
            VersionStatus for the tool
        """
        # Get installed version
        actual = await self.installer._get_installed_version(manager, tool)

        # Determine status
        if actual is None:
            status = "missing"
        elif expected is None:
            # No specific version required - any install is ok
            status = "ok"
        elif actual == expected:
            status = "ok"
        else:
            status = "drift"

        return VersionStatus(
            tool=tool,
            manager=manager,
            expected_version=expected,
            actual_version=actual,
            status=status
        )

    async def check_all(
        self,
        manager: Optional[Literal["pipx", "npm"]] = None
    ) -> VersionReport:
        """
        Check all tools for version drift.

        Args:
            manager: Check only this manager (None = all managers)

        Returns:
            Complete version report
        """
        report = VersionReport()
        env_config = self.config.get("environment", {})

        managers = [manager] if manager else ["pipx", "npm"]

        for mgr in managers:
            # Get tool list
            if mgr == "pipx":
                tools = env_config.get("pipxApps", [])
            elif mgr == "npm":
                tools = env_config.get("npmGlobal", [])
            else:
                continue

            # Check each tool
            tasks = []
            for tool in tools:
                expected_version = self.version_pins.get(mgr, {}).get(tool)
                tasks.append(self.check_version(tool, mgr, expected_version))

            statuses = await asyncio.gather(*tasks)
            report.statuses.extend(statuses)

        return report

    async def sync(
        self,
        dry_run: bool = False,
        force: bool = False
    ) -> list[tuple[str, bool, str]]:
        """
        Sync all tools to pinned versions.

        Args:
            dry_run: Don't actually install, just report what would be done
            force: Force reinstall even if version matches

        Returns:
            List of (tool_name, success, message) tuples
        """
        results = []

        # Get current status
        report = await self.check_all()

        # Sync tools with drift or missing
        for status in report.statuses:
            if not status.has_drift and not force:
                results.append((status.tool, True, "Already synced"))
                continue

            if dry_run:
                action = "Would install" if status.status == "missing" else "Would update"
                version_str = status.expected_version or "latest"
                results.append((status.tool, True, f"{action} {version_str}"))
                continue

            # Actually sync
            try:
                if status.manager == "pipx":
                    result = await self.installer.install_pipx(
                        status.tool,
                        status.expected_version,
                        force=True
                    )
                elif status.manager == "npm":
                    result = await self.installer.install_npm(
                        status.tool,
                        status.expected_version,
                        force=True
                    )
                else:
                    results.append((status.tool, False, f"Unsupported manager: {status.manager}"))
                    continue

                if result.success:
                    results.append((status.tool, True, f"Synced to {result.version}"))
                else:
                    results.append((status.tool, False, result.message))

            except Exception as e:
                results.append((status.tool, False, str(e)))

        return results

    async def pin_current_versions(
        self,
        manager: Optional[Literal["pipx", "npm"]] = None
    ) -> dict:
        """
        Create version pins from currently installed versions.

        Args:
            manager: Pin only this manager (None = all managers)

        Returns:
            Dict of version pins suitable for config
        """
        pins = {"pipx": {}, "npm": {}}
        env_config = self.config.get("environment", {})

        managers = [manager] if manager else ["pipx", "npm"]

        for mgr in managers:
            # Get tool list
            if mgr == "pipx":
                tools = env_config.get("pipxApps", [])
            elif mgr == "npm":
                tools = env_config.get("npmGlobal", [])
            else:
                continue

            # Get current versions
            for tool in tools:
                version = await self.installer._get_installed_version(mgr, tool)
                if version:
                    pins[mgr][tool] = version

        return pins

    def update_config_pins(self, pins: dict) -> None:
        """
        Update config with new version pins.

        Args:
            pins: Dict of version pins by manager
        """
        if "environment" not in self.config:
            self.config["environment"] = {}

        if "versionPins" not in self.config["environment"]:
            self.config["environment"]["versionPins"] = {}

        for manager, tool_pins in pins.items():
            if manager not in self.config["environment"]["versionPins"]:
                self.config["environment"]["versionPins"][manager] = {}

            self.config["environment"]["versionPins"][manager].update(tool_pins)
