"""
Integration Test: Planning Flow
Tests end-to-end planning module integration

Phase: PH-OP-001 (Week 1)
Generated: 2026-02-08
"""
import pytest
import sys
import os
from pathlib import Path

# Add parent directory to path for govreg_core package
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestPlanningFlowIntegration:
    """Test planning flow integration with core modules"""
    
    def test_core_package_import(self):
        """Verify core package can be imported"""
        try:
            import govreg_core
            assert hasattr(govreg_core, '__version__'), "Package should have version"
        except ImportError as e:
            pytest.fail(f"Failed to import govreg_core package: {e}")
    
    def test_canonical_hash_available(self):
        """Test canonical hash functions are available"""
        from govreg_core import hash_canonical_data, hash_file_content
        assert callable(hash_canonical_data), "hash_canonical_data should be callable"
        assert callable(hash_file_content), "hash_file_content should be callable"
        
        # Test basic functionality
        result = hash_canonical_data({"test": "data"})
        assert len(result) == 64, "Hash should be 64 characters (SHA256 hex)"
    
    def test_feature_flags_available(self):
        """Test feature flags are available"""
        from govreg_core import FeatureFlags, MigrationPhase, get_feature_flags
        assert FeatureFlags is not None
        assert MigrationPhase is not None
        assert callable(get_feature_flags)
    
    def test_core_modules_accessible(self):
        """Test core modules can be accessed"""
        import govreg_core
        # Package should be importable
        assert govreg_core.__version__ is not None


@pytest.mark.integration
class TestPlanningFlowEndToEnd:
    """End-to-end planning flow tests"""
    
    def test_planning_integration_points(self):
        """Verify all integration points are accessible"""
        integration_points_file = Path(".state/integration_points.json")
        assert integration_points_file.exists(), "Integration points file should exist"
        
        import json
        with open(integration_points_file) as f:
            data = json.load(f)
        
        assert data.get('count', 0) > 0, "Should have identified modules"
        assert 'modules' in data, "Should list modules"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
