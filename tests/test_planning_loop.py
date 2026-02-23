"""
Test Suite for Planning Loop CLI
Week 7: Unit and Integration Tests
"""
import pytest
import json
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from plan_refine_cli.hash_utils import compute_json_hash, compute_file_hash
from plan_refine_cli.run_directory import RunDirectoryManager
from plan_refine_cli.policy_manager import PolicyManager
from plan_refine_cli.patch_applicator import PatchApplicator


class TestHashUtils:
    """Test hash utility functions"""
    
    def test_compute_json_hash_deterministic(self):
        """JSON hash should be deterministic"""
        data1 = {"b": 2, "a": 1}
        data2 = {"a": 1, "b": 2}
        assert compute_json_hash(data1) == compute_json_hash(data2)
    
    def test_compute_json_hash_different(self):
        """Different data should produce different hashes"""
        data1 = {"a": 1}
        data2 = {"a": 2}
        assert compute_json_hash(data1) != compute_json_hash(data2)
    
    def test_hash_length(self):
        """Hash should be 64 hex characters"""
        data = {"test": "value"}
        hash_val = compute_json_hash(data)
        assert len(hash_val) == 64
        assert all(c in '0123456789abcdef' for c in hash_val)


class TestRunDirectoryManager:
    """Test run directory management"""
    
    def test_create_run_directory(self, tmp_path):
        """Should create run directory structure"""
        manager = RunDirectoryManager(tmp_path)
        run_id = manager.create_run_directory()
        
        assert run_id.startswith("planning_")
        run_dir = manager.get_run_directory(run_id)
        assert run_dir.exists()
        assert (run_dir / "iterations").exists()
        assert (run_dir / "patches").exists()
        assert (run_dir / "critic_reports").exists()
        assert (run_dir / "manifest.json").exists()
    
    def test_custom_run_id(self, tmp_path):
        """Should accept custom run ID"""
        manager = RunDirectoryManager(tmp_path)
        custom_id = "planning_20260218T120000Z_abc12345"
        run_id = manager.create_run_directory(custom_id)
        assert run_id == custom_id


class TestPatchApplicator:
    """Test patch application"""
    
    def test_apply_simple_patch(self):
        """Should apply simple replace operation"""
        applicator = PatchApplicator()
        
        plan = {"objective": "Old objective", "version": "2.0"}
        plan_hash = compute_json_hash(plan)
        
        patch = {
            "patch_id": "PATCH_TEST",
            "created_by": "TEST",
            "target_plan_hash": plan_hash,
            "justification": ["TEST"],
            "operations": [
                {"op": "replace", "path": "/objective", "value": "New objective"}
            ]
        }
        
        patched, success, error = applicator.apply_patch(plan, patch)
        
        assert success
        assert patched["objective"] == "New objective"
        assert patched["version"] == "2.0"
    
    def test_hash_mismatch(self):
        """Should reject patch with wrong target hash"""
        applicator = PatchApplicator()
        
        plan = {"objective": "Test"}
        patch = {
            "patch_id": "PATCH_TEST",
            "created_by": "TEST",
            "target_plan_hash": "0" * 64,
            "justification": ["TEST"],
            "operations": []
        }
        
        patched, success, error = applicator.apply_patch(plan, patch)
        
        assert not success
        assert "Hash mismatch" in error


class TestPolicyManager:
    """Test policy management"""
    
    def test_load_policy_schema(self, tmp_path):
        """Should load policy schema"""
        # Create minimal schema
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()
        
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["policy_id"]
        }
        
        with open(schema_dir / "planning_policy_snapshot.schema.json", 'w') as f:
            json.dump(schema, f)
        
        manager = PolicyManager(schema_dir)
        loaded = manager.load_policy_schema()
        
        assert loaded["type"] == "object"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
