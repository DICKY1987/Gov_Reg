"""AIM+ Configuration Loader

Unified configuration loader for merged AIM+ config.

Supports:
- Loading merged aim_config.json
- Schema validation
- Environment variable expansion
- Backward compatibility with legacy configs

Contract Version: AIM_PLUS_V1
"""
# DOC_ID: DOC-PAT-AIM-REGISTRY-M01001C-CONFIG-LOADER-481

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False

from modules.aim_environment import ConfigurationError


class ConfigLoader:
    """Unified configuration loader for AIM+."""

    DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config" / "aim_config.json"
    SCHEMA_PATH = Path(__file__).parent.parent / "config" / "aim_config.schema.json"

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize config loader.

        Args:
            config_path: Path to config file. Defaults to aim/config/aim_config.json
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self._config = None
        self._schema = None

    def load(self, validate: bool = True) -> Dict[str, Any]:
        """Load configuration from file.

        Args:
            validate: Whether to validate against JSON schema

        Returns:
            Parsed and expanded configuration dict

        Raises:
            ConfigurationError: If config invalid or not found
        """
        if not self.config_path.exists():
            raise ConfigurationError(f"Config file not found: {self.config_path}")

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in config file: {e}")

        # Validate against schema if requested
        if validate and JSONSCHEMA_AVAILABLE:
            self._validate_schema(config)

        # Expand environment variables
        config = self._expand_env_vars(config)

        self._config = config
        return config

    def _validate_schema(self, config: Dict[str, Any]) -> None:
        """Validate config against JSON schema.

        Args:
            config: Configuration to validate

        Raises:
            ConfigurationError: If validation fails
        """
        if not self.SCHEMA_PATH.exists():
            # Schema not found, skip validation
            return

        try:
            with open(self.SCHEMA_PATH, "r", encoding="utf-8") as f:
                schema = json.load(f)

            jsonschema.validate(instance=config, schema=schema)
        except jsonschema.ValidationError as e:
            raise ConfigurationError(f"Config validation failed: {e.message}")
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in schema file: {e}")

    def _expand_env_vars(self, obj: Any) -> Any:
        """Recursively expand environment variables in config.

        Supports patterns:
        - %VAR_NAME% (Windows style)
        - $VAR_NAME or ${VAR_NAME} (Unix style)

        Args:
            obj: Object to expand (dict, list, str, or other)

        Returns:
            Object with expanded environment variables
        """
        if isinstance(obj, dict):
            return {k: self._expand_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._expand_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            return self._expand_string_env_vars(obj)
        else:
            return obj

    def _expand_string_env_vars(self, s: str) -> str:
        """Expand environment variables in a string.

        Args:
            s: String potentially containing env vars

        Returns:
            String with expanded variables
        """
        # Expand Windows-style %VAR%
        s = re.sub(
            r'%([A-Z_][A-Z0-9_]*)%',
            lambda m: os.environ.get(m.group(1), m.group(0)),
            s,
            flags=re.IGNORECASE
        )

        # Expand Unix-style $VAR or ${VAR}
        s = re.sub(
            r'\$\{([A-Z_][A-Z0-9_]*)\}',
            lambda m: os.environ.get(m.group(1), m.group(0)),
            s,
            flags=re.IGNORECASE
        )
        s = re.sub(
            r'\$([A-Z_][A-Z0-9_]*)',
            lambda m: os.environ.get(m.group(1), m.group(0)),
            s,
            flags=re.IGNORECASE
        )

        return s

    def get_registry(self) -> Dict[str, Any]:
        """Get registry section from config.

        Returns:
            Registry configuration
        """
        if self._config is None:
            self.load()
        return self._config.get("registry", {})

    def get_environment(self) -> Dict[str, Any]:
        """Get environment section from config.

        Returns:
            Environment configuration
        """
        if self._config is None:
            self.load()
        return self._config.get("environment", {})

    def get_audit(self) -> Dict[str, Any]:
        """Get audit section from config.

        Returns:
            Audit configuration
        """
        if self._config is None:
            self.load()
        return self._config.get("audit", {})

    def get_tool(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """Get specific tool configuration.

        Args:
            tool_id: Tool identifier

        Returns:
            Tool config or None if not found
        """
        registry = self.get_registry()
        return registry.get("tools", {}).get(tool_id)

    def get_capability(self, capability: str) -> Optional[Dict[str, Any]]:
        """Get capability routing configuration.

        Args:
            capability: Capability name

        Returns:
            Capability config or None if not found
        """
        registry = self.get_registry()
        return registry.get("capabilities", {}).get(capability)


# Singleton instance for convenience
_loader = None


def get_config_loader(config_path: Optional[Path] = None) -> ConfigLoader:
    """Get or create singleton config loader.

    Args:
        config_path: Optional custom config path

    Returns:
        ConfigLoader instance
    """
    global _loader
    if _loader is None or config_path is not None:
        _loader = ConfigLoader(config_path)
    return _loader


def load_config(validate: bool = True) -> Dict[str, Any]:
    """Load AIM+ configuration (convenience function).

    Args:
        validate: Whether to validate against schema

    Returns:
        Loaded configuration
    """
    loader = get_config_loader()
    return loader.load(validate=validate)
