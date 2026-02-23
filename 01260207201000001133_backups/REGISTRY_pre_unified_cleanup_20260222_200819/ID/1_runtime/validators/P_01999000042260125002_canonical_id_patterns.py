"""
Canonical ID Pattern Definitions

This is the ONLY module that may define ID-matching regex patterns.
All other modules MUST import from here.

Contract: docs/ID_IDENTITY_CONTRACT.md
"""

import re
from typing import Optional, Tuple

# ============================================================================
# Core Pattern Definitions (CANONICAL - DO NOT DUPLICATE ELSEWHERE)
# ============================================================================

# Raw ID patterns (no delimiters)
ID_20_DIGIT_RE = re.compile(r'^\d{20}$')
DOC_ID_RE = re.compile(r'^P_\d{20}$')
ENHANCED_ID_RE = re.compile(r'^\d{22}$')  # 17+5 structure

# Filename prefix patterns (with underscore boundary)
FILENAME_PREFIX_RE = re.compile(r'^(?P<doc_prefix>P_)?(?P<file_id>\d{20})(?P<sep>__|_)')
FILENAME_PREFIX_20_RE = re.compile(r'^\d{20}(?:__|_)')
FILENAME_PREFIX_DOC_RE = re.compile(r'^P_\d{20}(?:__|_)')

# ============================================================================
# Helper Functions
# ============================================================================

def extract_file_id_from_name(name: str) -> Tuple[bool, Optional[str], bool]:
    """
    Extract file_id from a filename.
    
    Args:
        name: Filename to parse
        
    Returns:
        (has_prefix, file_id, is_doc_prefixed)
        - has_prefix: True if valid ID prefix found
        - file_id: 20-digit numeric ID (no P_) or None
        - is_doc_prefixed: True if filename starts with P_
        
    Examples:
        >>> extract_file_id_from_name("P_01999000042260125002_patterns.py")
        (True, "01999000042260125002", True)
        
        >>> extract_file_id_from_name("01999000042260125002_patterns.py")
        (True, "01999000042260125002", False)
        
        >>> extract_file_id_from_name("patterns.py")
        (False, None, False)
    """
    match = FILENAME_PREFIX_RE.match(name)
    if not match:
        return (False, None, False)
    
    file_id = match.group('file_id')
    is_doc_prefixed = match.group('doc_prefix') is not None
    
    return (True, file_id, is_doc_prefixed)


def is_valid_file_id(file_id: str) -> bool:
    """
    Check if string is a valid 20-digit file_id.
    
    Args:
        file_id: String to validate
        
    Returns:
        True if valid 20-digit numeric ID
    """
    return ID_20_DIGIT_RE.match(file_id) is not None


def is_valid_doc_id(doc_id: str) -> bool:
    """
    Check if string is a valid doc_id (P_ prefix + 20 digits).
    
    Args:
        doc_id: String to validate
        
    Returns:
        True if valid doc_id format
    """
    return DOC_ID_RE.match(doc_id) is not None


def normalize_to_file_id(identifier: str) -> Optional[str]:
    """
    Convert doc_id or file_id to canonical 20-digit file_id.
    
    Args:
        identifier: Either "P_01999..." or "01999..."
        
    Returns:
        20-digit file_id or None if invalid
        
    Examples:
        >>> normalize_to_file_id("P_01999000042260125002")
        "01999000042260125002"
        
        >>> normalize_to_file_id("01999000042260125002")
        "01999000042260125002"
    """
    if is_valid_file_id(identifier):
        return identifier
    
    if is_valid_doc_id(identifier):
        return identifier[2:]  # Strip "P_"
    
    return None


def normalize_to_doc_id(file_id: str) -> Optional[str]:
    """
    Convert file_id to doc_id format.
    
    Args:
        file_id: 20-digit numeric ID
        
    Returns:
        "P_" + file_id or None if invalid
    """
    if not is_valid_file_id(file_id):
        return None
    
    return f"P_{file_id}"


def detect_id_type(identifier: str) -> Optional[str]:
    """
    Detect the type of an ID string.
    
    Args:
        identifier: String to classify
        
    Returns:
        "file_id", "doc_id", "enhanced_id", or None
    """
    if is_valid_file_id(identifier):
        return "file_id"
    
    if is_valid_doc_id(identifier):
        return "doc_id"
    
    if ENHANCED_ID_RE.match(identifier):
        return "enhanced_id"
    
    return None


# ============================================================================
# Validation Functions
# ============================================================================

def validate_filename_prefix(filename: str) -> dict:
    """
    Validate and extract all information from an ID-prefixed filename.
    
    Args:
        filename: Filename to validate
        
    Returns:
        Dictionary with validation results:
        {
            "valid": bool,
            "file_id": str or None,
            "is_doc_prefixed": bool,
            "prefix_kind": "DOC_PREFIXED" | "REGULAR" | None
        }
    """
    has_prefix, file_id, is_doc_prefixed = extract_file_id_from_name(filename)
    
    return {
        "valid": has_prefix,
        "file_id": file_id,
        "is_doc_prefixed": is_doc_prefixed,
        "prefix_kind": "DOC_PREFIXED" if is_doc_prefixed else "REGULAR" if has_prefix else None
    }
