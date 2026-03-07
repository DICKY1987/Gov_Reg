# DOC_LINK: DOC-SCRIPT-TOOLS-PFA-COMMON-944
"""
PFA Common Utilities Library
Shared utilities for PROCESS_STEP_LIB tools
"""
# DOC_ID: DOC-SCRIPT-TOOLS-PFA-COMMON-944

import json
import yaml
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional


# =============================================================================
# File I/O Functions
# =============================================================================

def load_yaml(filepath: Path, encoding: str = 'utf-8') -> Dict[str, Any]:
    """Load YAML file and return parsed data."""
    with open(filepath, 'r', encoding=encoding) as f:
        return yaml.safe_load(f)


def save_yaml(data: Dict, filepath: Path, encoding: str = 'utf-8') -> None:
    """Save data to YAML file."""
    with open(filepath, 'w', encoding=encoding) as f:
        yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def load_json(filepath: Path, encoding: str = 'utf-8') -> Dict[str, Any]:
    """Load JSON file and return parsed data."""
    with open(filepath, 'r', encoding=encoding) as f:
        return json.load(f)


def save_json(data: Dict, filepath: Path, encoding: str = 'utf-8', indent: int = 2) -> None:
    """Save data to JSON file."""
    with open(filepath, 'w', encoding=encoding) as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


# =============================================================================
# Hashing & Validation Functions
# =============================================================================

def compute_content_hash(step_dict: Dict, exclude_fields: Optional[List[str]] = None) -> str:
    """
    Compute SHA-256 hash of step content.

    Args:
        step_dict: Step dictionary to hash
        exclude_fields: Fields to exclude from hash (e.g., ['step_id', 'phase'])

    Returns:
        Hexadecimal hash string
    """
    if exclude_fields is None:
        exclude_fields = []

    filtered = {k: v for k, v in step_dict.items() if k not in exclude_fields}
    content_str = json.dumps(filtered, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(content_str.encode('utf-8')).hexdigest()


def validate_required_fields(step: Dict, required: List[str]) -> List[str]:
    """
    Validate that step has all required fields.

    Args:
        step: Step dictionary to validate
        required: List of required field names

    Returns:
        List of missing field names (empty if all present)
    """
    return [field for field in required if field not in step or not step[field]]


# =============================================================================
# Logging Functions
# =============================================================================

def print_success(message: str) -> None:
    """Print success message with green checkmark."""
    print(f"✅ {message}")


def print_error(message: str) -> None:
    """Print error message with red X."""
    print(f"❌ {message}")


def print_warning(message: str) -> None:
    """Print warning message with yellow warning symbol."""
    print(f"⚠️  {message}")


def print_info(message: str) -> None:
    """Print informational message with blue info symbol."""
    print(f"ℹ️  {message}")


# =============================================================================
# Path Helper Functions
# =============================================================================

def get_project_root() -> Path:
    """
    Get the project root directory (ALL_AI).
    Assumes this file is in ALL_AI/PROCESS_STEP_LIB/
    """
    return Path(__file__).parent.parent


def resolve_schema_path(schema_name: str) -> Path:
    """
    Resolve schema file path relative to PROCESS_STEP_LIB.

    Args:
        schema_name: Name of schema file (with or without .yaml extension)

    Returns:
        Absolute path to schema file
    """
    if not schema_name.endswith('.yaml'):
        schema_name += '.yaml'

    schema_dir = Path(__file__).parent

    # Check common locations
    locations = [
        schema_dir / schema_name,
        schema_dir / 'schemas' / schema_name,
        schema_dir / 'schemas' / 'source' / schema_name,
        schema_dir / 'schemas' / 'expanded' / schema_name,
        schema_dir / 'schemas' / 'unified' / schema_name,
    ]

    for path in locations:
        if path.exists():
            return path

    raise FileNotFoundError(f"Schema not found: {schema_name}")


def resolve_config_path(config_name: str) -> Path:
    """
    Resolve config file path relative to PROCESS_STEP_LIB.

    Args:
        config_name: Name of config file (with or without .yaml extension)

    Returns:
        Absolute path to config file
    """
    if not config_name.endswith('.yaml'):
        config_name += '.yaml'

    base_dir = Path(__file__).parent

    # Check common locations
    locations = [
        base_dir / config_name,
        base_dir / 'config' / config_name,
    ]

    for path in locations:
        if path.exists():
            return path

    raise FileNotFoundError(f"Config not found: {config_name}")


def resolve_index_path(index_name: str) -> Path:
    """
    Resolve index file path relative to PROCESS_STEP_LIB.

    Args:
        index_name: Name of index file (with or without .json extension)

    Returns:
        Absolute path to index file
    """
    if not index_name.endswith('.json'):
        index_name += '.json'

    base_dir = Path(__file__).parent

    # Check common locations
    locations = [
        base_dir / index_name,
        base_dir / 'indices' / index_name,
    ]

    for path in locations:
        if path.exists():
            return path

    raise FileNotFoundError(f"Index not found: {index_name}")


# =============================================================================
# Utility Functions
# =============================================================================

def normalize_step_id(step_id: str) -> str:
    """
    Normalize step ID to consistent format.

    Args:
        step_id: Raw step ID

    Returns:
        Normalized step ID (uppercase, no extra spaces)
    """
    return step_id.strip().upper()


def get_step_source(step_id: str) -> str:
    """
    Determine source schema from step ID prefix.

    Args:
        step_id: Step ID (e.g., 'MS-001', 'PAT-042', 'SSOT-013')

    Returns:
        Source schema name ('master_splinter', 'patterns', 'glossary', 'ssot', 'process', 'unknown')
    """
    prefix = step_id.split('-')[0].upper()

    prefix_map = {
        'MS': 'master_splinter',
        'PAT': 'patterns',
        'GLOSS': 'glossary',
        'SSOT': 'ssot',
        'PROC': 'process',
    }

    return prefix_map.get(prefix, 'unknown')
