"""
Column Dictionary loader - canonical source for 147 header definitions.
"""

import json
from typing import Dict, Any
from pathlib import Path
from .registry_paths import COLUMN_DICTIONARY_PATH


def load() -> Dict[str, Any]:
    """
    Load Column Dictionary with 147 header definitions.

    Returns:
        dict: Complete Column Dictionary structure with:
            - headers: 147 header definitions (type, scope, presence, normalization, derivation)
            - header_count_expected: 147
            - dictionary_version: str
    """
    with open(COLUMN_DICTIONARY_PATH) as f:
        column_dict = json.load(f)
    
    # TASK-017: Gate to prevent reading wrong key
    if "columns" in column_dict and column_dict["columns"]:
        raise ValueError(
            "Column Dictionary has non-empty 'columns' key. "
            "This is deprecated. Use 'headers' key only."
        )
    
    if "headers" not in column_dict:
        raise ValueError("Column Dictionary missing required 'headers' key")

    # Validation
    header_count = len(column_dict.get("headers", {}))
    expected_count = column_dict.get("header_count_expected", 147)

    if header_count != expected_count:
        raise ValueError(
            f"Column Dictionary header count mismatch: "
            f"expected {expected_count}, found {header_count}"
        )

    return column_dict


def get_header_definition(header_name: str) -> Dict[str, Any]:
    """Get definition for a specific header."""
    column_dict = load()
    headers = column_dict.get("headers", {})

    if header_name not in headers:
        raise KeyError(f"Header '{header_name}' not found in Column Dictionary")

    return headers[header_name]


def get_all_headers() -> Dict[str, Dict[str, Any]]:
    """Get all 147 header definitions."""
    column_dict = load()
    return column_dict.get("headers", {})
