# DOC_LINK: DOC-ERROR-UTILS-SECURITY-144
"""Security utilities for the error pipeline.

Provides input validation, secret redaction, and security checks to prevent
common vulnerabilities.
"""

# DOC_ID: DOC-ERROR-UTILS-SECURITY-144
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional


class SecurityError(Exception):
    """Raised when a security violation is detected."""

    pass


def validate_file_path(path: Path, allowed_root: Optional[Path] = None) -> None:
    """Validate file path to prevent directory traversal attacks.

    Args:
        path: File path to validate
        allowed_root: Optional root directory to restrict access to.
                     Defaults to current working directory.

    Raises:
        SecurityError: If path is outside allowed root or contains suspicious patterns
    """
    if allowed_root is None:
        allowed_root = Path.cwd()

    # Resolve to absolute path
    try:
        resolved = path.resolve()
    except (OSError, RuntimeError) as e:
        raise SecurityError(f"Cannot resolve path {path}: {e}")

    # Check if path is within allowed root
    try:
        resolved.relative_to(allowed_root)
    except ValueError:
        raise SecurityError(
            f"Path outside allowed directory: {path}\n"
            f"Resolved to: {resolved}\n"
            f"Allowed root: {allowed_root}"
        )

    # Check for suspicious patterns
    path_str = str(path)
    suspicious_patterns = [
        "..",  # Directory traversal
        "~",  # Home directory expansion
    ]

    for pattern in suspicious_patterns:
        if pattern in path_str:
            raise SecurityError(f"Suspicious pattern '{pattern}' in path: {path}")


def validate_file_size(path: Path, max_size_mb: int = 10) -> None:
    """Validate that file size is within acceptable limits.

    Args:
        path: File path to check
        max_size_mb: Maximum file size in megabytes

    Raises:
        SecurityError: If file is too large
    """
    if not path.exists():
        raise SecurityError(f"File does not exist: {path}")

    if not path.is_file():
        raise SecurityError(f"Not a regular file: {path}")

    file_size = path.stat().st_size
    max_size_bytes = max_size_mb * 1024 * 1024

    if file_size > max_size_bytes:
        size_mb = file_size / (1024 * 1024)
        raise SecurityError(
            f"File too large: {path}\n"
            f"Size: {size_mb:.2f} MB (max: {max_size_mb} MB)"
        )


def redact_secrets(text: str) -> str:
    """Redact potential secrets from text.

    Redacts common secret patterns:
    - API keys (OpenAI, Anthropic, etc.)
    - Tokens and passwords
    - Git commit-like hashes
    - Environment variable values containing 'key', 'token', 'secret'

    Args:
        text: Text potentially containing secrets

    Returns:
        Text with secrets replaced by [REDACTED]
    """
    if not text:
        return text

    # Define patterns for common secrets
    patterns = [
        # OpenAI keys (must come before generic sk- pattern)
        (r"sk-proj-[a-zA-Z0-9\-]{10,}", "[REDACTED_OPENAI_KEY]"),
        # Anthropic keys
        (r"sk-ant-[a-zA-Z0-9\-]{10,}", "[REDACTED_ANTHROPIC_KEY]"),
        # API keys (generic)
        (r"sk-[a-zA-Z0-9]{20,}", "[REDACTED_API_KEY]"),
        (r"key_[a-zA-Z0-9]{20,}", "[REDACTED_API_KEY]"),
        # Generic tokens
        (r"(token[\s:=]+['\"]?)([a-zA-Z0-9\-\.\_]+)(['\"]?)", r"\1[REDACTED_TOKEN]\3"),
        (r"(bearer[\s:=]+['\"]?)([a-zA-Z0-9\-\.\_]+)(['\"]?)", r"\1[REDACTED_TOKEN]\3"),
        # Passwords
        (r"(password[\s:=]+['\"]?)([^\s'\"]+)(['\"]?)", r"\1[REDACTED_PASSWORD]\3"),
        (r"(passwd[\s:=]+['\"]?)([^\s'\"]+)(['\"]?)", r"\1[REDACTED_PASSWORD]\3"),
        # Secret values
        (r"(secret[\s:=]+['\"]?)([^\s'\"]+)(['\"]?)", r"\1[REDACTED_SECRET]\3"),
        # Long hex strings (potential hashes/keys)
        (r"\b([a-f0-9]{40})\b", "[REDACTED_HASH]"),
        (r"\b([a-f0-9]{64})\b", "[REDACTED_HASH]"),
        # AWS keys
        (r"(AKIA[A-Z0-9]{16})", "[REDACTED_AWS_KEY]"),
        # Private keys
        (
            r"-----BEGIN (?:RSA )?PRIVATE KEY-----[^-]+-----END (?:RSA )?PRIVATE KEY-----",
            "[REDACTED_PRIVATE_KEY]",
        ),
    ]

    result = text
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    return result


def sanitize_path_for_log(path: Path) -> str:
    """Sanitize file path for logging.

    Removes sensitive parts like home directory, usernames, etc.

    Args:
        path: Path to sanitize

    Returns:
        Sanitized path string safe for logging
    """
    path_str = str(path)

    # Replace home directory with ~
    from pathlib import Path as PathLib

    home = str(PathLib.home())
    if path_str.startswith(home):
        path_str = "~" + path_str[len(home) :]

    # Remove username from Windows paths like C:\Users\username\
    path_str = re.sub(r"C:\\Users\\[^\\]+\\", r"C:\\Users\\[USER]\\", path_str)
    path_str = re.sub(r"/home/[^/]+/", r"/home/[USER]/", path_str)

    return path_str


def validate_command_safe(command: List[str]) -> None:
    """Validate that a command is safe to execute.

    Args:
        command: Command and arguments to validate

    Raises:
        SecurityError: If command contains suspicious elements
    """
    if not command:
        raise SecurityError("Empty command")

    # Check for shell injection patterns
    command_str = " ".join(command)

    suspicious_chars = [";", "&", "|", "`", "$", "(", ")", "<", ">"]
    for char in suspicious_chars:
        if char in command_str:
            raise SecurityError(
                f"Suspicious character '{char}' in command: {command_str}"
            )

    # Check for known dangerous commands
    dangerous_commands = ["rm", "del", "format", "dd", "mkfs"]
    if command[0] in dangerous_commands:
        raise SecurityError(f"Dangerous command not allowed: {command[0]}")


class ResourceLimits:
    """Resource limits for plugin execution."""

    def __init__(
        self,
        max_file_size_mb: int = 10,
        max_execution_time_seconds: int = 120,
        max_memory_mb: int = 512,
        allowed_root: Optional[Path] = None,
    ):
        self.max_file_size_mb = max_file_size_mb
        self.max_execution_time_seconds = max_execution_time_seconds
        self.max_memory_mb = max_memory_mb
        self.allowed_root = allowed_root

    def validate_file(self, path: Path) -> None:
        """Validate file against resource limits."""
        validate_file_path(path, allowed_root=self.allowed_root)
        validate_file_size(path, self.max_file_size_mb)

    def get_timeout(self) -> int:
        """Get execution timeout in seconds."""
        return self.max_execution_time_seconds
