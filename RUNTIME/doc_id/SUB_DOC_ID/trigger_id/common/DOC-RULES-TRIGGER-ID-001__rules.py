# DOC_LINK: DOC-RULES-TRIGGER-ID-001
# DOC_ID: DOC-RULES-TRIGGER-ID-001
"""
doc_id: DOC-RULES-TRIGGER-ID-001
Trigger ID validation rules and format specifications
"""

import re

# Format specification
TRIGGER_ID_FORMAT = r'^TRIGGER-([A-Z0-9]+)-([A-Z0-9-]+)-([0-9]{3,})$'
TRIGGER_ID_PATTERN = re.compile(TRIGGER_ID_FORMAT)

# Valid categories
VALID_CATEGORIES = ['HOOK', 'WATCHER', 'SCHED', 'RUNNER']

# Validation functions

def validate_trigger_id_format(trigger_id: str) -> tuple[bool, str]:
    """
    Validate trigger_id format
    Returns: (is_valid, error_message)
    """
    if not trigger_id:
        return False, "trigger_id cannot be empty"

    match = TRIGGER_ID_PATTERN.match(trigger_id)
    if not match:
        return False, f"Invalid format. Expected: TRIGGER-{{CATEGORY}}-{{NAME}}-{{SEQ}}"

    category, name, seq = match.groups()

    # Validate category
    if category not in VALID_CATEGORIES:
        return False, f"Invalid category '{category}'. Must be one of: {', '.join(VALID_CATEGORIES)}"

    # Validate name (alphanumeric and hyphens only)
    if not re.match(r'^[A-Z0-9-]+$', name):
        return False, f"Invalid name '{name}'. Must contain only uppercase letters, numbers, and hyphens"

    # Validate sequence (at least 3 digits)
    if len(seq) < 3:
        return False, f"Sequence number '{seq}' must be at least 3 digits"

    return True, ""

def extract_trigger_id_components(trigger_id: str) -> dict:
    """
    Extract components from a valid trigger_id
    Returns: dict with category, name, seq
    """
    match = TRIGGER_ID_PATTERN.match(trigger_id)
    if not match:
        return None

    category, name, seq = match.groups()
    return {
        'category': category,
        'name': name,
        'sequence': seq,
        'sequence_int': int(seq)
    }

def format_trigger_id(category: str, name: str, sequence: int) -> str:
    """
    Format a trigger_id from components
    """
    seq_str = str(sequence).zfill(3)
    return f"TRIGGER-{category.upper()}-{name.upper()}-{seq_str}"

# Export all
__all__ = [
    'TRIGGER_ID_FORMAT',
    'TRIGGER_ID_PATTERN',
    'VALID_CATEGORIES',
    'validate_trigger_id_format',
    'extract_trigger_id_components',
    'format_trigger_id'
]
