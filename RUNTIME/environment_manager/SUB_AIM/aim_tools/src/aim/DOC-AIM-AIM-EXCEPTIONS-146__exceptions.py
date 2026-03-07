# DOC_LINK: DOC-AIM-AIM-EXCEPTIONS-146
"""AIM+ Exception Classes

Custom exceptions for the AIM+ environment management system.

Contract Version: AIM_PLUS_V1
"""
# DOC_ID: DOC-AIM-AIM-EXCEPTIONS-146


class AIMPlusError(Exception):
    """Base exception for all AIM+ errors."""
    pass


class SecretsError(AIMPlusError):
    """Raised when secret operations fail."""
    pass


class HealthCheckError(AIMPlusError):
    """Raised when health checks fail critically."""
    pass


class InstallationError(AIMPlusError):
    """Raised when tool installation fails."""
    pass


class ConfigurationError(AIMPlusError):
    """Raised when configuration is invalid."""
    pass


class VersionControlError(AIMPlusError):
    """Raised when version control operations fail."""
    pass


class ScannerError(AIMPlusError):
    """Raised when scanner operations fail."""
    pass
