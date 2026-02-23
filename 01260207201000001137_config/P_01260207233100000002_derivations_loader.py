"""
Derivations loader - canonical source for computed field formulas.
"""

import yaml
from typing import Dict, Any
from pathlib import Path
from .registry_paths import DERIVATIONS_PATH


def load() -> Dict[str, Any]:
    """
    Load Derivations YAML with all computed field formulas.

    Returns:
        dict: Derivations structure with:
            - derived_columns: dict mapping column names to derivation specs
                - formula: DSL expression
                - dependencies: list of source fields
                - recompute_trigger: on_scan | on_write | manual
                - error_policy: fail | warn | use_null | use_default
    """
    with open(DERIVATIONS_PATH) as f:
        derivations = yaml.safe_load(f)

    return derivations


def get_derivation(column_name: str) -> Dict[str, Any]:
    """Get derivation formula for a specific column."""
    derivations = load()
    derived_columns = derivations.get("derived_columns", {})

    if column_name not in derived_columns:
        return None

    return derived_columns[column_name]


def get_all_derivations() -> Dict[str, Dict[str, Any]]:
    """Get all derivation formulas."""
    derivations = load()
    return derivations.get("derived_columns", {})
