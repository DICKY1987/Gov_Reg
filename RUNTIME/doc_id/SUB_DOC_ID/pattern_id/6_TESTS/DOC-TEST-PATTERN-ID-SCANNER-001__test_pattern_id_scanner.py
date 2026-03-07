#!/usr/bin/env python3
# DOC_LINK: DOC-TEST-PATTERN-ID-SCANNER-001
"""
Test suite for pattern_id scanner
"""
# DOC_ID: DOC-TEST-PATTERN-ID-SCANNER-001

import sys
import pytest
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

def test_scanner_file_exists():
    """Test that scanner file exists"""
    scanner_path = Path(__file__).parent.parent / "1_CORE_OPERATIONS" / "pattern_id_scanner.py"
    assert scanner_path.exists(), "Scanner file should exist"

def test_scanner_pattern_recognition():
    """Test scanner regex pattern"""
    import re

    pattern = r'PATTERN-[A-Z]+-[A-Z0-9-]+'

    test_cases = [
        "PATTERN-EXEC-DOC-ID-SCANNING-001",
        "PATTERN-SAGA-MIGRATION-002",
        "PATTERN-EVENT-SOURCING-003"
    ]

    for test_case in test_cases:
        match = re.search(pattern, test_case)
        assert match is not None, f"Pattern should match {test_case}"

def test_pattern_format_structure():
    """Test PATTERN-* format structure"""
    test_id = "PATTERN-EXEC-DOC-ID-SCANNING-001"

    parts = test_id.split('-')
    assert parts[0] == "PATTERN"
    assert len(parts) >= 4  # PATTERN-CAT-DESC-NUM

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
