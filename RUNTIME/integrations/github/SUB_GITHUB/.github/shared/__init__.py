"""
Shared GitHub API client for all GitHub integration scripts.

This module provides a unified GitHubProjectClient for interacting with
GitHub Projects v2 (GraphQL) and REST APIs.
"""

from .github_client import GitHubProjectClient

__all__ = ["GitHubProjectClient"]
