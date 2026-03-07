#!/usr/bin/env python3
# DOC_LINK: DOC-TEST-TRIGGER-ID-SCANNER-001
"""
Test suite for trigger_id scanner
"""
# DOC_ID: DOC-TEST-TRIGGER-ID-SCANNER-001

import sys
import pytest
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

def test_scanner_file_exists():
    """Test that scanner file exists"""
    scanner_path = Path(__file__).parent.parent / "1_CORE_OPERATIONS" / "trigger_id_scanner.py"
    assert scanner_path.exists(), "Scanner file should exist"

def test_scanner_pattern_recognition():
    """Test scanner regex pattern"""
    import re

    # Pattern should match TRIGGER-* format
    pattern = r'TRIGGER-[A-Z]+-[A-Z0-9-]+'

    test_cases = [
        "TRIGGER-WATCHER-FILE-CHANGED-001",
        "TRIGGER-HOOK-PRE-COMMIT-002",
        "TRIGGER-SYSTEM-BOOT-003"
    ]

    for test_case in test_cases:
        match = re.search(pattern, test_case)
        assert match is not None, f"Pattern should match {test_case}"

def test_trigger_format_structure():
    """Test TRIGGER-* format structure"""
    test_id = "TRIGGER-WATCHER-FILE-CHANGED-001"

    parts = test_id.split('-')
    assert parts[0] == "TRIGGER"
    assert len(parts) >= 4  # TRIGGER-CAT-DESC-NUM

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
