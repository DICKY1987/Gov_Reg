"""
Write Policy loader - canonical source for column update policies.
"""

import yaml
from typing import Dict, Any
from pathlib import Path
from .registry_paths import WRITE_POLICY_PATH


def load() -> Dict[str, Any]:
    """
    Load Write Policy YAML with all column policies.

    Returns:
        dict: Write Policy structure with:
            - columns: dict mapping column names to policies
                - update_policy: immutable | recompute_on_scan | manual_or_automated | manual_patch_only
                - null_policy: allow_null | forbid_null | conditional
                - actor_restrictions: list of allowed actors
    """
    with open(WRITE_POLICY_PATH) as f:
        write_policy = yaml.safe_load(f)

    return write_policy


def get_column_policy(column_name: str) -> Dict[str, Any]:
    """Get policy for a specific column."""
    write_policy = load()
    columns = write_policy.get("columns", {})

    if column_name not in columns:
        # Return default policy for undefined columns
        return {
            "update_policy": "manual_or_automated",
            "null_policy": "allow_null",
            "actor_restrictions": []
        }

    return columns[column_name]


def get_all_columns() -> Dict[str, Dict[str, Any]]:
    """Get all column policies."""
    write_policy = load()
    return write_policy.get("columns", {})
