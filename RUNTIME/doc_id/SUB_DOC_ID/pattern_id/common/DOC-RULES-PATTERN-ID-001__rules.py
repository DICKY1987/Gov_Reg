# DOC_LINK: DOC-RULES-PATTERN-ID-001
# DOC_ID: DOC-RULES-PATTERN-ID-001
"""
doc_id: DOC-RULES-PATTERN-ID-001
Pattern ID validation rules and format specifications
"""

import re

# Format specification
PATTERN_ID_FORMAT = r'^PATTERN-([A-Z0-9]+)-([A-Z0-9-]+)-([0-9]{3,})$'
PATTERN_ID_PATTERN = re.compile(PATTERN_ID_FORMAT)

# Valid categories
VALID_CATEGORIES = ['EXEC', 'VALID', 'DOC', 'TEST']

# Validation functions

def validate_pattern_id_format(pattern_id: str) -> tuple[bool, str]:
    """
    Validate pattern_id format
    Returns: (is_valid, error_message)
    """
    if not pattern_id:
        return False, "pattern_id cannot be empty"

    match = PATTERN_ID_PATTERN.match(pattern_id)
    if not match:
        return False, f"Invalid format. Expected: PATTERN-{{CATEGORY}}-{{NAME}}-{{SEQ}}"

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

def extract_pattern_id_components(pattern_id: str) -> dict:
    """
    Extract components from a valid pattern_id
    Returns: dict with category, name, seq
    """
    match = PATTERN_ID_PATTERN.match(pattern_id)
    if not match:
        return None

    category, name, seq = match.groups()
    return {
        'category': category,
        'name': name,
        'sequence': seq,
        'sequence_int': int(seq)
    }

def format_pattern_id(category: str, name: str, sequence: int) -> str:
    """
    Format a pattern_id from components
    """
    seq_str = str(sequence).zfill(3)
    return f"PATTERN-{category.upper()}-{name.upper()}-{seq_str}"

# Export all
__all__ = [
    'PATTERN_ID_FORMAT',
    'PATTERN_ID_PATTERN',
    'VALID_CATEGORIES',
    'validate_pattern_id_format',
    'extract_pattern_id_components',
    'format_pattern_id'
]
