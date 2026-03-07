# DOC_LINK: DOC-TEST-PATTERNS-TEST-DOC-ID-COMPLIANCE-184
"""Tests for doc_id compliance (ID-SYSTEM-SPEC-V1)."""

import re
from pathlib import Path

import pytest
import yaml

DOC_ID_PATTERN = r"^[A-Z0-9]+(-[A-Z0-9]+)*$"


@pytest.mark.skip(reason="Legacy pattern registry path no longer exists")
def test_doc_id_format():
    """Test that all doc_id values match required format."""
    # DOC_ID: DOC-TEST-PATTERNS-TEST-DOC-ID-COMPLIANCE-184
    index_path = Path("patterns/registry/PATTERN_INDEX.yaml")
    with open(index_path) as f:
        data = yaml.safe_load(f)

    for pattern in data["patterns"]:
        doc_id = pattern.get("doc_id")
        assert doc_id, f"Pattern {pattern['pattern_id']} missing doc_id"
        assert re.match(DOC_ID_PATTERN, doc_id), f"Invalid doc_id format: {doc_id}"


@pytest.mark.skip(reason="Legacy pattern registry path no longer exists")
def test_doc_id_uniqueness():
    """Test that all doc_id values are unique."""
    index_path = Path("patterns/registry/PATTERN_INDEX.yaml")
    with open(index_path) as f:
        data = yaml.safe_load(f)

    doc_ids = [p["doc_id"] for p in data["patterns"] if "doc_id" in p]
    assert len(doc_ids) == len(set(doc_ids)), "Duplicate doc_id values found"
