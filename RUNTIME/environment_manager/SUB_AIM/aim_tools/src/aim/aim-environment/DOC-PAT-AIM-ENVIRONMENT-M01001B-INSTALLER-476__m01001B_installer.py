"""
Tool installer for AIM+ environment management.

Provides automated installation of tools via pipx, npm, and winget
with version pinning, parallel installation, and rollback support.
"""
# DOC_ID: DOC-PAT-AIM-ENVIRONMENT-M01001B-INSTALLER-476

import asyncio
import json
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional

from modules.aim_environment import InstallationError


@dataclass
class InstallResult:
    """Result of a tool installation attempt."""

    tool: str
    manager: Literal["pipx", "npm", "winget"]
    success: bool
    version: str
    message: str
    rollback_data: dict = field(default_factory=dict)


class ToolInstaller:
    """Automated tool installation and version management."""

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize the tool installer.

        Args:
            config: Optional configuration dict with version pins
        """
        self.config = config or {}
        self.version_pins = self.config.get("environment", {}).get("versionPins", {})

    async def _run_command(
        self,
        cmd: list[str],
        timeout: int = 300
    ) -> tuple[int, str, str]:
        """
        Run a command asynchronously.

        Args:
            cmd: Command and arguments to execute
            timeout: Timeout in seconds

        Returns:
            Tuple of (returncode, stdout, stderr)
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout
            )

            return (
                proc.returncode or 0,
                stdout.decode("utf-8", errors="replace"),
                stderr.decode("utf-8", errors="replace")
            )
        except asyncio.TimeoutError:
            return (-1, "", f"Command timed out after {timeout}s")
        except Exception as e:
            return (-1, "", str(e))

    async def _get_installed_version(
        self,
        manager: Literal["pipx", "npm"],
        package: str
    ) -> Optional[str]:
        """Get currently installed version of a package."""
        if manager == "pipx":
            returncode, stdout, _ = await self._run_command(
                ["pipx", "list", "--json"]
            )
            if returncode == 0:
                try:
                    data = json.loads(stdout)
                    for venv in data.get("venvs", {}).values():
                        if venv.get("metadata", {}).get("main_package", {}).get("package") == package:
                            return venv["metadata"]["main_package"]["package_version"]
                except (json.JSONDecodeError, KeyError):
                    pass

        elif manager == "npm":
            returncode, stdout, _ = await self._run_command(
                ["npm", "list", "-g", package, "--json"]
            )
            if returncode == 0:
                try:
                    data = json.loads(stdout)
                    deps = data.get("dependencies", {})
                    if package in deps:
                        return deps[package].get("version")
                except (json.JSONDecodeError, KeyError):
                    pass

        return None

    async def install_pipx(
        self,
        package: str,
        version: Optional[str] = None,
        force: bool = False
    ) -> InstallResult:
        """
        Install a Python package via pipx.

        Args:
            package: Package name to install
            version: Specific version to install (uses pinned version if not provided)
            force: Force reinstall even if already installed

        Returns:
            InstallResult with installation outcome
        """
        # Check for version pin
        if version is None:
            version = self.version_pins.get("pipx", {}).get(package)

        # Check if already installed
        existing_version = await self._get_installed_version("pipx", package)
        if existing_version and not force:
            if version is None or existing_version == version:
                return InstallResult(
                    tool=package,
                    manager="pipx",
                    success=True,
                    version=existing_version,
                    message=f"Already installed (v{existing_version})"
                )

        # Build install command
        cmd = ["pipx", "install"]
        if force:
            cmd.append("--force")

        package_spec = f"{package}=={version}" if version else package
        cmd.append(package_spec)

        # Execute installation
        returncode, stdout, stderr = await self._run_command(cmd)

        if returncode == 0:
            installed_version = await self._get_installed_version("pipx", package)
            return InstallResult(
                tool=package,
                manager="pipx",
                success=True,
                version=installed_version or version or "unknown",
                message="Installed successfully",
                rollback_data={"previous_version": existing_version}
            )
        else:
            return InstallResult(
                tool=package,
                manager="pipx",
                success=False,
                version="",
                message=f"Installation failed: {stderr}"
            )

    async def install_npm(
        self,
        package: str,
        version: Optional[str] = None,
        force: bool = False
    ) -> InstallResult:
        """
        Install a Node.js package globally via npm.

        Args:
            package: Package name to install
            version: Specific version to install (uses pinned version if not provided)
            force: Force reinstall even if already installed

        Returns:
            InstallResult with installation outcome
        """
        # Check for version pin
        if version is None:
            version = self.version_pins.get("npm", {}).get(package)

        # Check if already installed
        existing_version = await self._get_installed_version("npm", package)
        if existing_version and not force:
            if version is None or existing_version == version:
                return InstallResult(
                    tool=package,
                    manager="npm",
                    success=True,
                    version=existing_version,
                    message=f"Already installed (v{existing_version})"
                )

        # Build install command
        cmd = ["npm", "install", "-g"]
        if force:
            cmd.append("--force")

        package_spec = f"{package}@{version}" if version else package
        cmd.append(package_spec)

        # Execute installation
        returncode, stdout, stderr = await self._run_command(cmd)

        if returncode == 0:
            installed_version = await self._get_installed_version("npm", package)
            return InstallResult(
                tool=package,
                manager="npm",
                success=True,
                version=installed_version or version or "unknown",
                message="Installed successfully",
                rollback_data={"previous_version": existing_version}
            )
        else:
            return InstallResult(
                tool=package,
                manager="npm",
                success=False,
                version="",
                message=f"Installation failed: {stderr}"
            )

    async def install_winget(
        self,
        package: str,
        version: Optional[str] = None,
        force: bool = False
    ) -> InstallResult:
        """
        Install a package via winget.

        Args:
            package: Package ID to install
            version: Specific version to install
            force: Force reinstall even if already installed

        Returns:
            InstallResult with installation outcome
        """
        # Build install command
        cmd = ["winget", "install", "--id", package, "--exact", "--silent"]

        if version:
            cmd.extend(["--version", version])

        if force:
            cmd.append("--force")

        # Execute installation
        returncode, stdout, stderr = await self._run_command(cmd, timeout=600)

        if returncode == 0:
            return InstallResult(
                tool=package,
                manager="winget",
                success=True,
                version=version or "latest",
                message="Installed successfully"
            )
        else:
            return InstallResult(
                tool=package,
                manager="winget",
                success=False,
                version="",
                message=f"Installation failed: {stderr or stdout}"
            )

    async def uninstall_pipx(self, package: str) -> bool:
        """Uninstall a pipx package."""
        returncode, _, _ = await self._run_command(["pipx", "uninstall", package])
        return returncode == 0

    async def uninstall_npm(self, package: str) -> bool:
        """Uninstall a global npm package."""
        returncode, _, _ = await self._run_command(["npm", "uninstall", "-g", package])
        return returncode == 0

    async def rollback(self, result: InstallResult) -> bool:
        """
        Rollback a failed installation.

        Args:
            result: InstallResult to rollback

        Returns:
            True if rollback successful
        """
        if not result.rollback_data:
            return True

        previous_version = result.rollback_data.get("previous_version")

        # If there was no previous version, uninstall
        if previous_version is None:
            if result.manager == "pipx":
                return await self.uninstall_pipx(result.tool)
            elif result.manager == "npm":
                return await self.uninstall_npm(result.tool)
        else:
            # Reinstall previous version
            if result.manager == "pipx":
                rollback_result = await self.install_pipx(
                    result.tool,
                    version=previous_version,
                    force=True
                )
                return rollback_result.success
            elif result.manager == "npm":
                rollback_result = await self.install_npm(
                    result.tool,
                    version=previous_version,
                    force=True
                )
                return rollback_result.success

        return False

    async def install_all(
        self,
        tools: list[dict],
        rollback_on_failure: bool = True
    ) -> list[InstallResult]:
        """
        Install multiple tools in parallel.

        Args:
            tools: List of tool dicts with 'name', 'manager', optional 'version'
            rollback_on_failure: Whether to rollback all on any failure

        Returns:
            List of InstallResults
        """
        tasks = []
        for tool in tools:
            manager = tool["manager"]
            name = tool["name"]
            version = tool.get("version")

            if manager == "pipx":
                tasks.append(self.install_pipx(name, version))
            elif manager == "npm":
                tasks.append(self.install_npm(name, version))
            elif manager == "winget":
                tasks.append(self.install_winget(name, version))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to failed results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(InstallResult(
                    tool=tools[i]["name"],
                    manager=tools[i]["manager"],
                    success=False,
                    version="",
                    message=f"Exception during install: {str(result)}"
                ))
            else:
                final_results.append(result)

        # Handle rollback if requested
        if rollback_on_failure and any(not r.success for r in final_results):
            successful_installs = [r for r in final_results if r.success]
            for result in successful_installs:
                await self.rollback(result)

        return final_results

    async def install_from_config(
        self,
        manager: Literal["pipx", "npm"],
        rollback_on_failure: bool = True
    ) -> list[InstallResult]:
        """
        Install all tools from config for a specific package manager.

        Args:
            manager: Package manager to use ('pipx' or 'npm')
            rollback_on_failure: Whether to rollback all on any failure

        Returns:
            List of InstallResults
        """
        env_config = self.config.get("environment", {})

        if manager == "pipx":
            packages = env_config.get("pipxApps", [])
        elif manager == "npm":
            packages = env_config.get("npmGlobal", [])
        else:
            return []

        tools = [{"name": pkg, "manager": manager} for pkg in packages]
        return await self.install_all(tools, rollback_on_failure)
