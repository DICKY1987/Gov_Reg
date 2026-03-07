# DOC_LINK: DOC-TEST-REGISTRY-INTEGRITY-001
# DOC_ID: DOC-TEST-REGISTRY-INTEGRITY-001
"""
Registry Integrity Tests
doc_id: DOC-TEST-REGISTRY-INTEGRITY-001
Validates structure and integrity of all registries
"""

import pytest
from pathlib import Path
import yaml
import json

class TestDocIDRegistry:
    """Test DOC_ID_REGISTRY.yaml integrity"""

    @pytest.fixture
    def registry_path(self):
        return Path(__file__).parent.parent / "5_REGISTRY_DATA" / "DOC_ID_REGISTRY.yaml"

    @pytest.fixture
    def registry_data(self, registry_path):
        with open(registry_path) as f:
            return yaml.safe_load(f)

    def test_registry_exists(self, registry_path):
        """Registry file must exist"""
        assert registry_path.exists()

    def test_registry_loadable(self, registry_data):
        """Registry must be valid YAML"""
        assert registry_data is not None

    def test_registry_structure(self, registry_data):
        """Registry must have expected structure"""
        # Should be a list of doc_id entries
        assert isinstance(registry_data, list)

        if len(registry_data) > 0:
            first_entry = registry_data[0]
            assert 'doc_id' in first_entry
            assert 'category' in first_entry

    def test_doc_ids_unique(self, registry_data):
        """All doc_ids must be unique"""
        doc_ids = [entry.get('doc_id') for entry in registry_data if 'doc_id' in entry]
        assert len(doc_ids) == len(set(doc_ids)), "Duplicate doc_ids found"

    def test_doc_ids_format(self, registry_data):
        """Doc IDs must follow correct format"""
        for entry in registry_data[:10]:  # Sample first 10
            doc_id = entry.get('doc_id', '')
            assert doc_id.startswith('DOC-'), f"Invalid doc_id format: {doc_id}"

class TestTriggerIDRegistry:
    """Test TRIGGER_ID_REGISTRY.yaml integrity"""

    @pytest.fixture
    def registry_path(self):
        return Path(__file__).parent.parent / "trigger_id" / "5_REGISTRY_DATA" / "TRIGGER_ID_REGISTRY.yaml"

    @pytest.fixture
    def registry_data(self, registry_path):
        if not registry_path.exists():
            pytest.skip("Trigger ID registry not found")
        with open(registry_path) as f:
            return yaml.safe_load(f)

    def test_registry_exists(self, registry_path):
        """Registry file must exist"""
        assert registry_path.exists()

    def test_registry_structure(self, registry_data):
        """Registry must have expected structure"""
        assert 'triggers' in registry_data or isinstance(registry_data, list)

    def test_trigger_ids_format(self, registry_data):
        """Trigger IDs must follow correct format"""
        triggers = registry_data.get('triggers', []) if isinstance(registry_data, dict) else registry_data

        for trigger in triggers[:10]:  # Sample first 10
            trigger_id = trigger.get('trigger_id', trigger.get('id', ''))
            assert 'TRIGGER-' in trigger_id or 'TRG-' in trigger_id, f"Invalid trigger_id format: {trigger_id}"

class TestPatternIDRegistry:
    """Test PAT_ID_REGISTRY.yaml integrity"""

    @pytest.fixture
    def registry_path(self):
        return Path(__file__).parent.parent / "pattern_id" / "5_REGISTRY_DATA" / "PAT_ID_REGISTRY.yaml"

    @pytest.fixture
    def registry_data(self, registry_path):
        if not registry_path.exists():
            pytest.skip("Pattern ID registry not found")
        with open(registry_path) as f:
            return yaml.safe_load(f)

    def test_registry_exists(self, registry_path):
        """Registry file must exist"""
        assert registry_path.exists()

    def test_registry_structure(self, registry_data):
        """Registry must have expected structure"""
        assert 'patterns' in registry_data or isinstance(registry_data, list)

    def test_pattern_ids_format(self, registry_data):
        """Pattern IDs must follow correct format"""
        patterns = registry_data.get('patterns', []) if isinstance(registry_data, dict) else registry_data

        for pattern in patterns[:10]:  # Sample first 10
            pattern_id = pattern.get('pattern_id', pattern.get('id', ''))
            assert 'PATTERN-' in pattern_id or 'PAT-' in pattern_id, f"Invalid pattern_id format: {pattern_id}"

class TestMetaRegistry:
    """Test ID_TYPE_REGISTRY.yaml (meta-registry) integrity"""

    @pytest.fixture
    def registry_path(self):
        return Path(__file__).parent.parent / "ID_TYPE_REGISTRY.yaml"

    @pytest.fixture
    def registry_data(self, registry_path):
        with open(registry_path) as f:
            return yaml.safe_load(f)

    def test_meta_registry_exists(self, registry_path):
        """Meta registry must exist"""
        assert registry_path.exists()

    def test_meta_registry_structure(self, registry_data):
        """Meta registry must have required sections"""
        assert 'version' in registry_data
        assert 'meta' in registry_data
        assert 'id_types' in registry_data

    def test_meta_counts_reasonable(self, registry_data):
        """Meta counts should match actual id_types list"""
        meta = registry_data['meta']
        id_types_list = registry_data['id_types']

        total_types = meta.get('total_types', 0)
        actual_count = len(id_types_list)

        # Allow some tolerance for derived types
        assert abs(total_types - actual_count) <= 10, \
            f"Meta count mismatch: declared {total_types}, found {actual_count}"

    def test_all_id_types_have_required_fields(self, registry_data):
        """Each ID type must have required fields"""
        required_fields = ['type_id', 'tier', 'format', 'status']

        for id_type in registry_data['id_types']:
            for field in required_fields:
                assert field in id_type, f"Missing field '{field}' in {id_type.get('type_id', 'unknown')}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
