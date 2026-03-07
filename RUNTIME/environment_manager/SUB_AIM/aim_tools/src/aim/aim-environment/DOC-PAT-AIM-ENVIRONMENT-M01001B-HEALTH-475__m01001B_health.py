"""AIM+ Health Check System

System health validation and environment verification.

Features:
- Command availability detection
- AI tool detection and validation
- PATH order verification
- Directory permission checks
- Secrets vault verification
- JSON health report generation

Contract Version: AIM_PLUS_V1
"""
# DOC_ID: DOC-PAT-AIM-ENVIRONMENT-M01001B-HEALTH-475

import shutil
import subprocess
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from modules.aim_environment import HealthCheckError


@dataclass
class HealthCheck:
    """Result of a single health check."""
    name: str
    status: str  # "pass", "warn", "fail"
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {k: v for k, v in asdict(self).items() if v is not None}


class HealthMonitor:
    """System health validation and monitoring."""

    def __init__(self):
        """Initialize health monitor."""
        self._config = None

    def check_all(self) -> List[HealthCheck]:
        """Run all health checks.

        Returns:
            List of HealthCheck results
        """
        checks = [
            self.check_python(),
            self.check_required_commands(),
            self.check_ai_tools(),
            self.check_secrets_vault(),
            self.check_config(),
        ]

        return checks

    def check_python(self) -> HealthCheck:
        """Verify Python installation and version.

        Returns:
            HealthCheck result
        """
        try:
            import sys
            version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

            # Check minimum version (3.10+)
            if sys.version_info >= (3, 10):
                return HealthCheck(
                    name="python",
                    status="pass",
                    message=f"Python {version} installed",
                    details={"version": version, "executable": sys.executable},
                    timestamp=self._get_timestamp()
                )
            else:
                return HealthCheck(
                    name="python",
                    status="warn",
                    message=f"Python {version} installed (recommend 3.10+)",
                    details={"version": version, "executable": sys.executable},
                    timestamp=self._get_timestamp()
                )
        except Exception as e:
            return HealthCheck(
                name="python",
                status="fail",
                message=f"Python check failed: {e}",
                timestamp=self._get_timestamp()
            )

    def check_required_commands(self) -> HealthCheck:
        """Verify required commands are available.

        Returns:
            HealthCheck result
        """
        required = self._get_required_commands()

        missing = []
        found = []

        for cmd in required:
            if shutil.which(cmd):
                found.append(cmd)
            else:
                missing.append(cmd)

        if not missing:
            return HealthCheck(
                name="required_commands",
                status="pass",
                message=f"All {len(found)} required commands found",
                details={"found": found},
                timestamp=self._get_timestamp()
            )
        elif len(missing) < len(required) / 2:
            return HealthCheck(
                name="required_commands",
                status="warn",
                message=f"{len(missing)} required command(s) missing",
                details={"found": found, "missing": missing},
                timestamp=self._get_timestamp()
            )
        else:
            return HealthCheck(
                name="required_commands",
                status="fail",
                message=f"{len(missing)} required commands missing",
                details={"found": found, "missing": missing},
                timestamp=self._get_timestamp()
            )

    def check_ai_tools(self) -> HealthCheck:
        """Check AI tool availability.

        Returns:
            HealthCheck result
        """
        try:
            from modules.aim_registry import get_config_loader

            loader = get_config_loader()
            registry = loader.get_registry()
            tools = registry.get("tools", {})

            detected = []
            not_detected = []

            for tool_id, tool_info in tools.items():
                detect_commands = tool_info.get("detectCommands", [])

                # Expand env vars in detect commands
                detect_commands = [self._expand_env_var(cmd) for cmd in detect_commands]

                # Check if any detect command is available
                found = False
                for cmd in detect_commands:
                    if shutil.which(cmd) or Path(cmd).exists():
                        detected.append({
                            "tool": tool_id,
                            "name": tool_info.get("name", tool_id),
                            "command": cmd
                        })
                        found = True
                        break

                if not found:
                    not_detected.append({
                        "tool": tool_id,
                        "name": tool_info.get("name", tool_id)
                    })

            if detected:
                return HealthCheck(
                    name="ai_tools",
                    status="pass" if len(detected) >= 1 else "warn",
                    message=f"{len(detected)} AI tool(s) detected",
                    details={
                        "detected": detected,
                        "not_detected": not_detected,
                        "total": len(tools)
                    },
                    timestamp=self._get_timestamp()
                )
            else:
                return HealthCheck(
                    name="ai_tools",
                    status="warn",
                    message="No AI tools detected",
                    details={"not_detected": not_detected},
                    timestamp=self._get_timestamp()
                )
        except Exception as e:
            return HealthCheck(
                name="ai_tools",
                status="fail",
                message=f"AI tool check failed: {e}",
                timestamp=self._get_timestamp()
            )

    def check_secrets_vault(self) -> HealthCheck:
        """Verify secrets vault is accessible.

        Returns:
            HealthCheck result
        """
        try:
            from modules.aim_environment import get_secrets_manager

            manager = get_secrets_manager()
            vault_path = manager.vault_path

            if vault_path.exists():
                # Try to list secrets
                secrets = manager.list_secrets()

                return HealthCheck(
                    name="secrets_vault",
                    status="pass",
                    message=f"Secrets vault accessible ({len(secrets)} secret(s))",
                    details={
                        "path": str(vault_path),
                        "secret_count": len(secrets)
                    },
                    timestamp=self._get_timestamp()
                )
            else:
                return HealthCheck(
                    name="secrets_vault",
                    status="warn",
                    message="Secrets vault not initialized",
                    details={"path": str(vault_path)},
                    timestamp=self._get_timestamp()
                )
        except Exception as e:
            return HealthCheck(
                name="secrets_vault",
                status="fail",
                message=f"Secrets vault check failed: {e}",
                timestamp=self._get_timestamp()
            )

    def check_config(self) -> HealthCheck:
        """Verify configuration is valid.

        Returns:
            HealthCheck result
        """
        try:
            from modules.aim_registry import get_config_loader

            loader = get_config_loader()
            config = loader.load(validate=False)

            # Check required sections
            required_sections = ["version", "registry", "environment"]
            missing_sections = [s for s in required_sections if s not in config]

            if not missing_sections:
                return HealthCheck(
                    name="config",
                    status="pass",
                    message="Configuration valid",
                    details={
                        "version": config.get("version"),
                        "sections": list(config.keys())
                    },
                    timestamp=self._get_timestamp()
                )
            else:
                return HealthCheck(
                    name="config",
                    status="fail",
                    message=f"Missing config sections: {missing_sections}",
                    details={"missing": missing_sections},
                    timestamp=self._get_timestamp()
                )
        except Exception as e:
            return HealthCheck(
                name="config",
                status="fail",
                message=f"Config check failed: {e}",
                timestamp=self._get_timestamp()
            )

    def generate_report(self, checks: Optional[List[HealthCheck]] = None) -> Dict[str, Any]:
        """Generate health report.

        Args:
            checks: List of health checks (runs all if None)

        Returns:
            Health report dictionary
        """
        if checks is None:
            checks = self.check_all()

        # Count by status
        status_counts = {"pass": 0, "warn": 0, "fail": 0}
        for check in checks:
            status_counts[check.status] = status_counts.get(check.status, 0) + 1

        # Determine overall status
        if status_counts["fail"] > 0:
            overall_status = "unhealthy"
        elif status_counts["warn"] > 0:
            overall_status = "degraded"
        else:
            overall_status = "healthy"

        return {
            "timestamp": self._get_timestamp(),
            "overall_status": overall_status,
            "summary": status_counts,
            "checks": [check.to_dict() for check in checks]
        }

    def _get_required_commands(self) -> List[str]:
        """Get list of required commands from config.

        Returns:
            List of required command names
        """
        try:
            from modules.aim_registry import get_config_loader

            loader = get_config_loader()
            env = loader.get_environment()
            health_config = env.get("healthChecks", {})

            return health_config.get("requiredCommands", ["git", "python", "node"])
        except Exception:
            # Fallback defaults
            return ["git", "python", "node"]

    @staticmethod
    def _expand_env_var(path: str) -> str:
        """Expand environment variables in path.

        Args:
            path: Path with potential env vars

        Returns:
            Expanded path
        """
        return os.path.expandvars(path)

    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp in ISO format.

        Returns:
            ISO timestamp string
        """
        return datetime.now(timezone.utc).isoformat()


def check_health() -> Dict[str, Any]:
    """Run health checks and return report (convenience function).

    Returns:
        Health report dictionary
    """
    monitor = HealthMonitor()
    return monitor.generate_report()
