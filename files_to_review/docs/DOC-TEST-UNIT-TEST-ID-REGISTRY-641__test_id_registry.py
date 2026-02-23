#!/usr/bin/env python3
# DOC_LINK: DOC-TEST-UNIT-TEST-ID-REGISTRY-641
"""
Unit tests for ID Registry

Tests the ID allocation, validation, and management functionality.
"""
# DOC_ID: DOC-TEST-UNIT-TEST-ID-REGISTRY-641

import pytest
import json
import tempfile
from pathlib import Path
import sys

from _ssot_tool_loader import load_tool

try:
    _registry_module = load_tool(
        "DOC-CORE-SSOT-SYS-TOOLS-ID-REGISTRY-1105__id_registry.py"
    )
    IdRegistry = _registry_module.IdRegistry
    IdType = _registry_module.IdType
except Exception:
    pytest.skip("id_registry module not available", allow_module_level=True)


@pytest.fixture
def temp_registry():
    """Create temporary registry file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        initial_data = {
            "meta": {
                "version": "1.0.0",
                "last_updated": "2025-12-22T00:00:00Z"
            },
            "allocations": {},
            "indexes": {
                "by_type": {},
                "by_category": {},
                "by_artifact": {}
            }
        }
        json.dump(initial_data, f, indent=2)
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.mark.unit
class TestIdRegistry:
    """Test ID Registry functionality."""

    def test_allocate_artifact_id(self, temp_registry):
        """Test allocating a new artifact ID."""
        registry = IdRegistry(temp_registry)
        id_val = registry.allocate_id("A", "SSOT", "/path/to/artifact.py")

        assert id_val.startswith("A-SSOT-")
        assert len(id_val.split("-")) == 3
        assert id_val.split("-")[2].isdigit()

    def test_allocate_requirement_id(self, temp_registry):
        """Test allocating a new requirement ID."""
        registry = IdRegistry(temp_registry)
        id_val = registry.allocate_id("R", "DETERM", "/req/determinism.md")

        assert id_val.startswith("R-DETERM-")
        assert len(id_val.split("-")) == 3

    def test_allocate_section_id(self, temp_registry):
        """Test allocating a section ID."""
        registry = IdRegistry(temp_registry)
        id_val = registry.allocate_id("S", "ENFORCE", None)

        assert id_val.startswith("S-ENFORCE")

    def test_id_uniqueness(self, temp_registry):
        """Test that allocated IDs are unique."""
        registry = IdRegistry(temp_registry)

        id1 = registry.allocate_id("A", "TEST", "/path1.py")
        id2 = registry.allocate_id("A", "TEST", "/path2.py")

        assert id1 != id2

    def test_id_persistence(self, temp_registry):
        """Test that allocated IDs persist across instances."""
        # Allocate ID
        registry1 = IdRegistry(temp_registry)
        id1 = registry1.allocate_id("A", "PERSIST", "/path.py")

        # Load new instance and verify
        registry2 = IdRegistry(temp_registry)
        assert registry2.exists(id1)

    def test_lookup_by_artifact(self, temp_registry):
        """Test looking up ID by artifact path."""
        registry = IdRegistry(temp_registry)
        artifact_path = "/tools/validate.py"
        id_val = registry.allocate_id("A", "TOOL", artifact_path)

        found_id = registry.lookup_by_artifact(artifact_path)
        assert found_id == id_val

    def test_list_by_category(self, temp_registry):
        """Test listing IDs by category."""
        registry = IdRegistry(temp_registry)

        registry.allocate_id("A", "SCHEMA", "/schema1.json")
        registry.allocate_id("A", "SCHEMA", "/schema2.json")
        registry.allocate_id("A", "TOOL", "/tool.py")

        schema_ids = registry.list_by_category("SCHEMA")
        assert len(schema_ids) == 2
        assert all(id_val.startswith("A-SCHEMA-") for id_val in schema_ids)

    def test_validation_rejects_invalid_type(self, temp_registry):
        """Test that invalid ID types are rejected."""
        registry = IdRegistry(temp_registry)

        with pytest.raises(ValueError):
            registry.allocate_id("X", "INVALID", "/path.py")

    def test_validation_rejects_invalid_format(self, temp_registry):
        """Test validation rejects malformed IDs."""
        registry = IdRegistry(temp_registry)

        assert not registry.validate_id("INVALID-FORMAT")
        assert not registry.validate_id("A-")
        assert not registry.validate_id("A-CAT")

    def test_validation_accepts_valid_ids(self, temp_registry):
        """Test validation accepts well-formed IDs."""
        registry = IdRegistry(temp_registry)

        assert registry.validate_id("A-SSOT-001")
        assert registry.validate_id("R-DETERM-042")
        assert registry.validate_id("S-SECTION")
        assert registry.validate_id("T-0001")

    def test_export_statistics(self, temp_registry):
        """Test exporting registry statistics."""
        registry = IdRegistry(temp_registry)

        # Allocate some IDs
        registry.allocate_id("A", "TEST", "/a1.py")
        registry.allocate_id("A", "TEST", "/a2.py")
        registry.allocate_id("R", "REQ", "/r1.md")

        stats = registry.export_statistics()

        assert "total_allocations" in stats
        assert stats["total_allocations"] >= 3
        assert "by_type" in stats
        assert stats["by_type"]["A"] >= 2
        assert stats["by_type"]["R"] >= 1


@pytest.mark.integration
class TestIdRegistryIntegration:
    """Integration tests with real file system."""

    def test_concurrent_access(self, temp_registry):
        """Test concurrent registry access (simulated)."""
        # Simulate multiple processes accessing registry
        registry1 = IdRegistry(temp_registry)
        registry2 = IdRegistry(temp_registry)

        id1 = registry1.allocate_id("A", "CONCURRENT", "/path1.py")
        id2 = registry2.allocate_id("A", "CONCURRENT", "/path2.py")

        # Both should succeed and be different
        assert id1 != id2

        # Reload and verify both exist
        registry3 = IdRegistry(temp_registry)
        assert registry3.exists(id1)
        assert registry3.exists(id2)

