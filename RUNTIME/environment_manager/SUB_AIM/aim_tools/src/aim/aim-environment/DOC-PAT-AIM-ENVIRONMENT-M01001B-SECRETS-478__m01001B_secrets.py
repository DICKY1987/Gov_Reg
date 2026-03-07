"""AIM+ Secrets Management

Secure secret storage using system keyring (DPAPI on Windows).

Features:
- Cross-platform secret storage using keyring library
- DPAPI encryption on Windows
- Metadata vault for non-sensitive information
- Auto-injection into environment variables

Contract Version: AIM_PLUS_V1
"""
# DOC_ID: DOC-PAT-AIM-ENVIRONMENT-M01001B-SECRETS-478

import json
import os
from pathlib import Path
from typing import Optional

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

from modules.aim_environment import SecretsError


class SecretsManager:
    """Secure secret storage using system keyring (DPAPI on Windows)."""

    SERVICE_NAME = "aim-plus"
    DEFAULT_VAULT_PATH = Path.home() / ".aim" / "secrets_metadata.json"

    def __init__(self, vault_path: Optional[Path] = None):
        """Initialize secrets manager.

        Args:
            vault_path: Path to metadata vault file (non-sensitive data only).
                       Defaults to ~/.aim/secrets_metadata.json
        """
        if not KEYRING_AVAILABLE:
            raise SecretsError(
                "keyring library not available. Install with: pip install keyring"
            )

        self.vault_path = vault_path or self.DEFAULT_VAULT_PATH
        self._ensure_vault_path()

    def _ensure_vault_path(self) -> None:
        """Ensure vault directory and file exist."""
        self.vault_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.vault_path.exists():
            self._save_metadata({})

    def _load_metadata(self) -> dict:
        """Load non-sensitive metadata from vault file."""
        try:
            with open(self.vault_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_metadata(self, metadata: dict) -> None:
        """Save non-sensitive metadata to vault file."""
        with open(self.vault_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

    def set_secret(self, key: str, value: str, description: str = "") -> None:
        """Store a secret securely.

        Args:
            key: Secret identifier (e.g., 'OPENAI_API_KEY')
            value: Secret value (encrypted via keyring)
            description: Optional description for the secret

        Raises:
            SecretsError: If secret storage fails
        """
        try:
            # Store secret value in system keyring (encrypted)
            keyring.set_password(self.SERVICE_NAME, key, value)

            # Store metadata (non-sensitive) in vault file
            metadata = self._load_metadata()
            metadata[key] = {
                "description": description,
                "created_at": self._get_timestamp()
            }
            self._save_metadata(metadata)

        except Exception as e:
            raise SecretsError(f"Failed to store secret '{key}': {e}")

    def get_secret(self, key: str) -> Optional[str]:
        """Retrieve a secret.

        Args:
            key: Secret identifier

        Returns:
            Secret value or None if not found
        """
        try:
            return keyring.get_password(self.SERVICE_NAME, key)
        except Exception as e:
            raise SecretsError(f"Failed to retrieve secret '{key}': {e}")

    def delete_secret(self, key: str) -> bool:
        """Delete a secret.

        Args:
            key: Secret identifier

        Returns:
            True if deleted, False if not found
        """
        try:
            # Delete from keyring
            keyring.delete_password(self.SERVICE_NAME, key)

            # Remove from metadata
            metadata = self._load_metadata()
            if key in metadata:
                del metadata[key]
                self._save_metadata(metadata)

            return True
        except keyring.errors.PasswordDeleteError:
            return False
        except Exception as e:
            raise SecretsError(f"Failed to delete secret '{key}': {e}")

    def list_secrets(self) -> list[dict]:
        """List all stored secret keys with metadata.

        Returns:
            List of dicts with 'key', 'description', 'created_at'
        """
        metadata = self._load_metadata()
        secrets = []

        for key, info in metadata.items():
            secrets.append({
                "key": key,
                "description": info.get("description", ""),
                "created_at": info.get("created_at", "unknown"),
                "exists": self.get_secret(key) is not None
            })

        return secrets

    def inject_into_env(self, keys: Optional[list[str]] = None) -> dict[str, str]:
        """Get secrets as environment variables.

        Args:
            keys: List of secret keys to retrieve. If None, retrieves all.

        Returns:
            Dict of {key: value} for all found secrets
        """
        if keys is None:
            # Get all keys from metadata
            metadata = self._load_metadata()
            keys = list(metadata.keys())

        env_vars = {}
        for key in keys:
            value = self.get_secret(key)
            if value is not None:
                env_vars[key] = value

        return env_vars

    def export_to_env(self, keys: Optional[list[str]] = None) -> None:
        """Export secrets to current process environment.

        Args:
            keys: List of secret keys to export. If None, exports all.
        """
        env_vars = self.inject_into_env(keys)
        for key, value in env_vars.items():
            os.environ[key] = value

    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()


def get_secrets_manager(vault_path: Optional[Path] = None) -> SecretsManager:
    """Factory function to get a SecretsManager instance.

    Args:
        vault_path: Optional custom vault path

    Returns:
        Configured SecretsManager instance
    """
    return SecretsManager(vault_path)
