"""
Canonical Normalizer for Registry records.

Applies Column Dictionary normalization transforms per-field:
- LOWERCASE: record_kind, entity_kind, extension
- NORMALIZE_SLASHES: relative_path, absolute_path
- STRIP dot from extension
- Timestamp normalization (ISO 8601 + Z suffix)
- Null coercion (empty strings -> None)
- Array dedup (preserve order, remove duplicates)
"""

import json
import re
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path


# Load normalization map from config
_NORMALIZATION_MAP = None


def _load_normalization_map() -> Dict[str, List[str]]:
    """Load normalization transform map from config."""
    global _NORMALIZATION_MAP
    if _NORMALIZATION_MAP is None:
        config_dir = Path(__file__).parent.parent.parent / "config"
        config_path = config_dir / "normalization_map.json"
        if not config_path.exists():
            config_path = config_dir / "01260207233100000449_normalization_map.json"
        with open(config_path) as f:
            _NORMALIZATION_MAP = json.load(f)
    return _NORMALIZATION_MAP


def normalize_path(path: Optional[str]) -> Optional[str]:
    """
    Normalize path: convert backslashes to forward slashes.

    Args:
        path: Path string with possible backslashes

    Returns:
        Path with forward slashes, or None if input is None
    """
    if path is None or path == "":
        return None
    return str(path).replace("\\", "/")


def normalize_timestamp(timestamp: Optional[str]) -> Optional[str]:
    """
    Normalize timestamp to ISO 8601 format with Z suffix.

    Args:
        timestamp: Timestamp string in various formats

    Returns:
        ISO 8601 formatted timestamp with Z suffix, or None if invalid
    """
    if timestamp is None or timestamp == "":
        return None

    # If already properly formatted, return as-is
    if re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$", timestamp):
        return timestamp

    # Try to parse and reformat
    try:
        # Handle various timestamp formats
        if "T" in timestamp:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        else:
            dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")

        # Return ISO format with Z suffix
        return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    except (ValueError, AttributeError):
        return None


def normalize_extension(ext: Optional[str]) -> Optional[str]:
    """
    Normalize extension: strip leading dot and lowercase.

    Args:
        ext: Extension string like '.py' or 'py'

    Returns:
        Extension without dot, lowercased, or None
    """
    if ext is None or ext == "":
        return None

    ext_str = str(ext)
    # Strip leading dot
    if ext_str.startswith("."):
        ext_str = ext_str[1:]

    # Lowercase
    return ext_str.lower()


def coerce_null(value: Any) -> Any:
    """
    Coerce empty strings to None.

    Args:
        value: Any value

    Returns:
        None if value is empty string, otherwise value unchanged
    """
    if value == "":
        return None
    return value


def dedup_array(arr: Optional[List[Any]]) -> Optional[List[Any]]:
    """
    Remove duplicates from array while preserving order.

    Args:
        arr: List with possible duplicates

    Returns:
        List with duplicates removed, order preserved, or None
    """
    if arr is None:
        return None
    if not isinstance(arr, list):
        return arr

    seen = set()
    result = []
    for item in arr:
        # Use JSON serialization for hashability of dicts/lists
        key = json.dumps(item, sort_keys=True) if isinstance(item, (dict, list)) else item
        if key not in seen:
            seen.add(key)
            result.append(item)

    return result


def apply_transforms(field_name: str, value: Any) -> Any:
    """
    Apply normalization transforms for a specific field.

    Args:
        field_name: Name of the field
        value: Current value

    Returns:
        Normalized value
    """
    if value is None:
        return None

    # Load transform rules
    norm_map = _load_normalization_map()
    transforms = norm_map.get(field_name, [])

    # Apply each transform in order
    for transform in transforms:
        if transform == "LOWERCASE":
            value = str(value).lower() if value is not None else None
        elif transform == "UPPERCASE":
            value = str(value).upper() if value is not None else None
        elif transform == "NORMALIZE_SLASHES":
            value = normalize_path(value)
        elif transform == "STRIP_LEADING_DOT":
            if value and str(value).startswith("."):
                value = str(value)[1:]

    # Special handling for extension (always strip dot and lowercase)
    if field_name == "extension":
        value = normalize_extension(value)

    return value


def normalize_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a complete registry record per Column Dictionary transforms.

    Applies:
    - Per-field transforms from normalization_map.json
    - Extension normalization (strip dot, lowercase)
    - Path normalization (forward slashes)
    - Timestamp normalization (ISO 8601 + Z)
    - Null coercion (empty strings -> None)
    - Array dedup

    Args:
        record: Registry record dict

    Returns:
        Normalized record dict
    """
    normalized = {}

    for field_name, value in record.items():
        # Apply null coercion first
        value = coerce_null(value)

        # Apply field-specific transforms
        value = apply_transforms(field_name, value)

        # Special handling for timestamps
        if field_name in ["generated", "last_modified", "created_at", "updated_at", "migrated_utc"]:
            value = normalize_timestamp(value)

        # Array deduplication
        if isinstance(value, list):
            value = dedup_array(value)

        normalized[field_name] = value

    return normalized


class Normalizer:
    """
    Canonical normalizer for registry records.
    Loads transform rules from config/normalization_map.json.
    """

    def __init__(self):
        """Initialize normalizer with config."""
        self.normalization_map = _load_normalization_map()

    def normalize_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a registry record."""
        return normalize_record(record)

    def normalize_path(self, path: Optional[str]) -> Optional[str]:
        """Normalize a path (convert backslashes to forward slashes)."""
        return normalize_path(path)

    def normalize_timestamp(self, timestamp: Optional[str]) -> Optional[str]:
        """Normalize a timestamp to ISO 8601 with Z suffix."""
        return normalize_timestamp(timestamp)
