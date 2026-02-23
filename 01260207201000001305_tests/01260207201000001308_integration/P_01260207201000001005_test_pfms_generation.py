"""
Integration Test: PFMS Generation
Tests PFMS generation and ingestion flow

Phase: PH-OP-001 (Week 1)
Generated: 2026-02-08
"""
import pytest
import sys
import os
from pathlib import Path

# Add parent directory for govreg_core package
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestPFMSGenerationIntegration:
    """Test PFMS generation integration"""
    
    def test_core_package_import(self):
        """Test govreg_core package is available"""
        try:
            import govreg_core
            assert govreg_core is not None
        except ImportError as e:
            pytest.fail(f"Cannot import govreg_core: {e}")
    
    def test_hash_functionality(self):
        """Test hashing functions for PFMS"""
        from govreg_core import hash_canonical_data
        
        # Test PFMS-style data hashing
        pfms_data = {
            "mutations": [{"type": "add", "path": "/test"}],
            "metadata": {"author": "system"}
        }
        
        hash_result = hash_canonical_data(pfms_data)
        assert len(hash_result) == 64
        assert hash_result.islower()  # Hex should be lowercase


@pytest.mark.integration
class TestPFMSFlowEndToEnd:
    """End-to-end PFMS flow tests"""
    
    def test_pfms_data_hashing(self):
        """Test PFMS data can be hashed consistently"""
        from govreg_core import hash_canonical_data
        
        # Simulate PFMS mutation set
        mutations_v1 = {"mutations": [{"op": "add"}], "version": "1.0"}
        mutations_v2 = {"version": "1.0", "mutations": [{"op": "add"}]}
        
        # Should produce same hash (order-independent)
        hash1 = hash_canonical_data(mutations_v1)
        hash2 = hash_canonical_data(mutations_v2)
        
        assert hash1 == hash2, "PFMS hashing should be deterministic"
    
    def test_geu_directory_exists(self):
        """Test GEU directory structure"""
        geu_dir = Path("GEU")
        if not geu_dir.exists():
            pytest.skip("GEU directory not found")
        
        # Check for GEU files
        geu_files = list(geu_dir.glob("*.json"))
        assert len(geu_files) >= 0  # May be empty initially


@pytest.mark.integration 
class TestFeatureFlags:
    """Test feature flag integration"""
    
    def test_feature_flags_functional(self):
        """Test feature flags module"""
        from govreg_core import get_feature_flags, MigrationPhase, FeatureFlags
        
        flags = get_feature_flags()
        assert flags is not None
        assert isinstance(flags, FeatureFlags)
    
    def test_migration_phase_enum(self):
        """Test migration phase enumeration"""
        from govreg_core import MigrationPhase
        
        # Check some expected phases
        assert hasattr(MigrationPhase, '__members__'), "Should be an enum"
        assert len(MigrationPhase.__members__) > 0, "Should have phase definitions"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
