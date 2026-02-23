"""Tests for directory identity resolver.

FILE_ID: 01260213162246000072
PURPOSE: Test S10D-S12D pipeline, invalid .dir_id detection, zone classification
"""
import pytest
import tempfile
import json
from pathlib import Path

from govreg_core.P_01260207233100000070_dir_identity_resolver import (
    DirectoryIdentityResolver,
    IdentityResolutionResult
)
from govreg_core.P_01260207233100000069_dir_id_handler import DirIdManager
from govreg_core.P_01260207233100000068_zone_classifier import ZoneClassifier


class TestDirectoryIdentityResolver:
    """Test suite for DirectoryIdentityResolver."""
    
    @pytest.fixture
    def temp_project(self):
        """Create temporary project structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            
            # Create directory structure
            (project_root / "src").mkdir()
            (project_root / "src" / "module_a").mkdir()
            (project_root / ".git").mkdir()
            
            yield project_root
    
    @pytest.fixture
    def resolver(self, temp_project):
        """Create resolver for temp project."""
        return DirectoryIdentityResolver(
            project_root=temp_project,
            project_root_id="01260207201000000001"
        )
    
    def test_20_digit_id_allocation(self, resolver, temp_project):
        """Test that allocated IDs are exactly 20 digits."""
        test_dir = temp_project / "src" / "module_a"
        
        result = resolver.resolve_identity(test_dir, allocate_if_missing=True)
        
        assert result.status == "allocated"
        assert result.dir_id is not None
        assert len(result.dir_id) == 20, f"Expected 20 digits, got {len(result.dir_id)}"
        assert result.dir_id.isdigit(), "dir_id should be numeric only"
    
    def test_invalid_dir_id_raises_error(self, resolver, temp_project):
        """Test that invalid .dir_id JSON is detected (DIR-IDENTITY-005)."""
        test_dir = temp_project / "src" / "module_a"
        
        # Write invalid JSON
        dir_id_file = test_dir / ".dir_id"
        with open(dir_id_file, "w") as f:
            f.write("{ invalid json }}")
        
        result = resolver.resolve_identity(test_dir, allocate_if_missing=False)
        
        assert result.status == "error"
        assert "DIR-IDENTITY-005" in (result.error_message or "")
        assert "Invalid .dir_id format" in (result.error_message or "")
    
    def test_missing_dir_id_in_governed_zone(self, resolver, temp_project):
        """Test detection of missing .dir_id in governed zone."""
        test_dir = temp_project / "src" / "module_a"
        
        result = resolver.resolve_identity(test_dir, allocate_if_missing=False)
        
        assert result.status == "missing"
        assert result.zone == "governed"
        assert result.depth == 2
        assert result.needs_allocation is True
    
    def test_staging_zone_no_allocation(self, resolver, temp_project):
        """Test that staging zone (depth=0) doesn't allocate."""
        test_dir = temp_project / "src"
        
        result = resolver.resolve_identity(test_dir, allocate_if_missing=False)
        
        # src is depth=1, so it's governed
        assert result.zone == "governed"
        assert result.depth == 1
    
    def test_excluded_zone_skipped(self, resolver, temp_project):
        """Test that excluded zones (.git) are skipped."""
        test_dir = temp_project / ".git"
        
        result = resolver.resolve_identity(test_dir, allocate_if_missing=False)
        
        assert result.zone == "excluded"
        assert result.status == "skipped"
    
    def test_valid_dir_id_recognized(self, resolver, temp_project):
        """Test that valid .dir_id is recognized."""
        test_dir = temp_project / "src" / "module_a"
        
        # Allocate first
        result1 = resolver.resolve_identity(test_dir, allocate_if_missing=True)
        assert result1.status == "allocated"
        
        # Check it's recognized on second pass
        result2 = resolver.resolve_identity(test_dir, allocate_if_missing=False)
        assert result2.status == "exists"
        assert result2.dir_id == result1.dir_id
    
    def test_parent_dir_id_derivation(self, resolver, temp_project):
        """Test that parent_dir_id is derived by walking up tree."""
        parent_dir = temp_project / "src"
        child_dir = parent_dir / "module_a"
        
        # Allocate parent first
        parent_result = resolver.resolve_identity(parent_dir, allocate_if_missing=True)
        assert parent_result.status == "allocated"
        
        # Allocate child
        child_result = resolver.resolve_identity(child_dir, allocate_if_missing=True)
        assert child_result.status == "allocated"
        
        # Read child's .dir_id to check parent_dir_id
        manager = DirIdManager()
        anchor = manager.read_dir_id(child_dir)
        
        assert anchor.parent_dir_id == parent_result.dir_id


class TestDirIdHandler:
    """Test suite for DirIdManager."""
    
    def test_read_invalid_json_raises_valueerror(self):
        """Test that invalid JSON raises ValueError, not returns None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir)
            dir_id_file = test_dir / ".dir_id"
            
            # Write invalid JSON
            with open(dir_id_file, "w") as f:
                f.write("{ bad json: }")
            
            manager = DirIdManager()
            
            with pytest.raises(ValueError) as exc_info:
                manager.read_dir_id(test_dir)
            
            assert "Invalid .dir_id format" in str(exc_info.value)
    
    def test_read_missing_required_field_raises_error(self):
        """Test that missing required fields are caught."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir)
            dir_id_file = test_dir / ".dir_id"
            
            # Write JSON missing required field
            with open(dir_id_file, "w") as f:
                json.dump({"dir_id": "01260207201000000001"}, f)
            
            manager = DirIdManager()
            
            # Should raise due to missing fields
            with pytest.raises(ValueError):
                manager.read_dir_id(test_dir)
    
    def test_validate_rejects_non_20_digit_ids(self):
        """Test that validator rejects IDs that aren't exactly 20 digits."""
        from govreg_core.P_01260207233100000069_dir_id_handler import create_anchor
        
        manager = DirIdManager()
        
        # 19 digits
        anchor_19 = create_anchor(
            dir_id="0126020720100000001",  # 19 digits
            project_root_id="01260207201000000001",
            relative_path="test",
            depth=1,
            zone="governed"
        )
        is_valid, errors = manager.validate_dir_id(anchor_19)
        assert not is_valid
        assert any("exactly 20 digits" in e for e in errors)
        
        # 21 digits
        anchor_21 = create_anchor(
            dir_id="012602072010000000012",  # 21 digits
            project_root_id="01260207201000000001",
            relative_path="test",
            depth=1,
            zone="governed"
        )
        is_valid, errors = manager.validate_dir_id(anchor_21)
        assert not is_valid
        assert any("exactly 20 digits" in e for e in errors)
        
        # 20 digits - should pass
        anchor_20 = create_anchor(
            dir_id="01260207201000000001",  # 20 digits
            project_root_id="01260207201000000001",
            relative_path="test",
            depth=1,
            zone="governed"
        )
        is_valid, errors = manager.validate_dir_id(anchor_20)
        assert is_valid


class TestZoneClassifier:
    """Test suite for ZoneClassifier."""
    
    def test_depth_calculation(self):
        """Test directory depth calculation."""
        classifier = ZoneClassifier()
        
        assert classifier.compute_depth(".") == 0
        assert classifier.compute_depth("src") == 1
        assert classifier.compute_depth("src/module_a") == 2
        assert classifier.compute_depth("src/module_a/submodule_b") == 3
    
    def test_zone_classification(self):
        """Test zone classification (staging/governed/excluded)."""
        classifier = ZoneClassifier()
        
        # Staging: depth=0
        assert classifier.compute_zone(".") == "staging"
        
        # Governed: depth>=1, not excluded
        assert classifier.compute_zone("src") == "governed"
        assert classifier.compute_zone("src/module_a") == "governed"
        
        # Excluded: matches exclusion patterns
        assert classifier.compute_zone(".git") == "excluded"
        assert classifier.compute_zone(".venv") == "excluded"
        assert classifier.compute_zone("src/__pycache__") == "excluded"
        assert classifier.compute_zone("node_modules") == "excluded"
    
    def test_exclusion_pattern_matching(self):
        """Test that exclusion patterns work correctly."""
        classifier = ZoneClassifier()
        
        # Should be excluded
        assert classifier.should_skip(".git/hooks") is True
        assert classifier.should_skip(".venv/lib/python3.10") is True
        assert classifier.should_skip("build/output") is True
        
        # Should NOT be excluded
        assert classifier.should_skip("src/module") is False
        assert classifier.should_skip("tests") is False


class TestScannerService:
    """Test suite for ScannerService."""
    
    def test_scanner_detects_missing_dir_id(self):
        """Test that scanner detects missing .dir_id in governed zones."""
        from govreg_core.P_01260207233100000071_scanner_service import ScannerService
        
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            test_dir = project_root / "src" / "module_a"
            test_dir.mkdir(parents=True)
            
            scanner = ScannerService(
                project_root=project_root,
                project_root_id="01260207201000000001"
            )
            
            report = scanner.scan(repair=False)
            
            # Should detect violation
            assert report.violations_found > 0
            assert any(v.violation_code == "DIR-IDENTITY-004" for v in report.violations)
    
    def test_scanner_repairs_missing_dir_id(self):
        """Test that scanner --fix mode repairs missing .dir_id."""
        from govreg_core.P_01260207233100000071_scanner_service import ScannerService
        
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            test_dir = project_root / "src" / "module_a"
            test_dir.mkdir(parents=True)
            
            scanner = ScannerService(
                project_root=project_root,
                project_root_id="01260207201000000001"
            )
            
            # Scan with repair
            report = scanner.scan(repair=True)
            
            # Should repair violations
            assert report.repaired > 0
            
            # .dir_id should now exist
            assert (test_dir / ".dir_id").exists()
    
    def test_scanner_detects_invalid_dir_id(self):
        """Test that scanner detects DIR-IDENTITY-005 (invalid format)."""
        from govreg_core.P_01260207233100000071_scanner_service import ScannerService
        
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            test_dir = project_root / "src"
            test_dir.mkdir()
            
            # Write invalid .dir_id
            with open(test_dir / ".dir_id", "w") as f:
                f.write("{ corrupt }")
            
            scanner = ScannerService(
                project_root=project_root,
                project_root_id="01260207201000000001"
            )
            
            report = scanner.scan(repair=False)
            
            # Should detect DIR-IDENTITY-005
            assert any(v.violation_code == "DIR-IDENTITY-005" for v in report.violations)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
