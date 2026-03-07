# DOC_LINK: DOC-TEST-INTEGRATION-UNIFIED-001
# DOC_ID: DOC-TEST-INTEGRATION-UNIFIED-001
"""
Unified Integration Tests
doc_id: DOC-TEST-INTEGRATION-UNIFIED-001
Tests cross-ID-type interactions and unified systems
"""

import pytest
from pathlib import Path
import sys
import yaml
import json

sys.path.insert(0, str(Path(__file__).parent.parent / "common"))

class TestUnifiedSync:
    """Test unified sync across all ID types"""

    def test_sync_all_registries_runs(self):
        """Verify sync_all_registries.py executes without error"""
        from sync_all_registries import sync_all_registries

        results = sync_all_registries()
        assert results is not None
        assert 'doc_id' in results
        assert 'trigger_id' in results
        assert 'pattern_id' in results

    def test_registries_accessible(self):
        """Verify all registries can be loaded"""
        base_path = Path(__file__).parent.parent

        registries = {
            'doc_id': base_path / "5_REGISTRY_DATA" / "DOC_ID_REGISTRY.yaml",
            'trigger_id': base_path / "trigger_id" / "5_REGISTRY_DATA" / "TRIGGER_ID_REGISTRY.yaml",
            'pattern_id': base_path / "pattern_id" / "5_REGISTRY_DATA" / "PAT_ID_REGISTRY.yaml",
        }

        for id_type, registry_path in registries.items():
            assert registry_path.exists(), f"Registry missing: {id_type}"
            with open(registry_path) as f:
                data = yaml.safe_load(f)
                assert data is not None, f"Empty registry: {id_type}"

class TestUnifiedValidation:
    """Test unified validation layer"""

    def test_meta_registry_valid(self):
        """Verify ID_TYPE_REGISTRY.yaml is valid"""
        registry_path = Path(__file__).parent.parent / "ID_TYPE_REGISTRY.yaml"
        assert registry_path.exists()

        with open(registry_path) as f:
            data = yaml.safe_load(f)

        assert 'version' in data
        assert 'meta' in data
        assert 'id_types' in data
        assert len(data['id_types']) > 0

    def test_all_validators_importable(self):
        """Verify all validator modules can be imported"""
        base_path = Path(__file__).parent.parent

        validators = [
            base_path / "2_VALIDATION_FIXING" / "validate_doc_id_coverage.py",
            base_path / "2_VALIDATION_FIXING" / "validate_doc_id_uniqueness.py",
            base_path / "trigger_id" / "2_VALIDATION_FIXING" / "validate_trigger_id_sync.py",
            base_path / "pattern_id" / "2_VALIDATION_FIXING" / "validate_pattern_id_sync.py",
        ]

        for validator in validators:
            if validator.exists():
                # Check Python syntax by attempting to compile
                with open(validator, encoding='utf-8') as f:
                    code = f.read()
                try:
                    compile(code, str(validator), 'exec')
                except SyntaxError as e:
                    pytest.fail(f"Syntax error in {validator.name}: {e}")

class TestUnifiedPreCommit:
    """Test unified pre-commit hook"""

    def test_pre_commit_hook_exists(self):
        """Verify unified pre-commit hook exists"""
        hook_path = Path(__file__).parent.parent / "unified_pre_commit_hook.py"
        assert hook_path.exists()

    def test_pre_commit_hook_syntax(self):
        """Verify pre-commit hook has valid syntax"""
        hook_path = Path(__file__).parent.parent / "unified_pre_commit_hook.py"
        with open(hook_path, encoding='utf-8') as f:
            code = f.read()

        try:
            compile(code, str(hook_path), 'exec')
        except SyntaxError as e:
            pytest.fail(f"Syntax error in unified_pre_commit_hook.py: {e}")

class TestDashboard:
    """Test unified dashboard"""

    def test_dashboard_exists(self):
        """Verify unified dashboard HTML exists"""
        dashboard_path = Path(__file__).parent.parent / "unified_dashboard.html"
        assert dashboard_path.exists()

    def test_dashboard_has_content(self):
        """Verify dashboard is not empty"""
        dashboard_path = Path(__file__).parent.parent / "unified_dashboard.html"
        content = dashboard_path.read_text()
        assert len(content) > 1000
        assert "Stable ID" in content or "Dashboard" in content

class TestCrossIDTypeReferences:
    """Test references between different ID types"""

    def test_doc_ids_reference_patterns(self):
        """Check if doc_ids properly reference pattern_ids"""
        # This is a placeholder for actual cross-reference validation
        assert True  # TODO: Implement actual cross-reference checks

    def test_patterns_reference_triggers(self):
        """Check if patterns properly reference triggers"""
        assert True  # TODO: Implement actual cross-reference checks

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
