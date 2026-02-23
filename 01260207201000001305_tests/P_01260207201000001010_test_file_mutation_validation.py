"""
Unit tests for file mutation validation.
"""

import json
import tempfile
from pathlib import Path

import pytest

from scripts.P_01260207233100000290_validate_file_mutations import FileMutationValidator


@pytest.fixture
def validator():
    """Create a validator instance."""
    return FileMutationValidator()


@pytest.fixture
def temp_file():
    """Create a temporary file for test data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        yield f.name
    Path(f.name).unlink()


def write_mutations(path: str, data: dict) -> None:
    """Helper to write mutations to a file."""
    with open(path, 'w') as f:
        json.dump(data, f)


def base_mutations():
    """Get base valid mutations structure."""
    return {
        "mutation_set_id": "MUT-TEST-001",
        "plan_id": "PLAN-001",
        "created_at": "2026-02-12T11:03:00Z",
        "created_by": "test",
        "status": "proposed",
        "mutations": {
            "modified_files": [],
            "created_files": [],
            "deleted_files": []
        }
    }


class TestSchemaValidation:
    """Tests for basic schema validation."""
    
    def test_valid_schema(self, validator, temp_file):
        """Test validation of valid schema."""
        mutations = base_mutations()
        write_mutations(temp_file, mutations)
        
        result = validator._validate_schema(mutations)
        assert result is True
        assert "Schema validation" in validator.checks_passed
    
    def test_missing_mutations_field(self, validator):
        """Test error on missing mutations field."""
        mutations = {"mutation_set_id": "MUT-001"}
        result = validator._validate_schema(mutations)
        assert result is False
        assert any("Missing 'mutations'" in e for e in validator.errors)


class TestExecutionMethods:
    """Tests for execution method validation."""
    
    def test_valid_full_rewrite_inline(self, validator):
        """Test valid FULL_REWRITE with inline content."""
        mutations = base_mutations()
        mutations["mutations"]["modified_files"] = [{
            "relative_path": "src/test.py",
            "modification_type": "replace",
            "execution_method": "FULL_REWRITE",
            "method_payload": {
                "content_source": "inline",
                "content_text": "code here"
            }
        }]
        
        validator._validate_schema(mutations)
        result = validator._validate_execution_methods(mutations)
        assert result is True
    
    def test_valid_full_rewrite_artifact(self, validator):
        """Test valid FULL_REWRITE with artifact reference."""
        mutations = base_mutations()
        mutations["mutations"]["modified_files"] = [{
            "relative_path": "src/test.py",
            "modification_type": "replace",
            "execution_method": "FULL_REWRITE",
            "method_payload": {
                "content_source": "artifact",
                "artifact_id": "ART-001"
            }
        }]
        
        validator._validate_schema(mutations)
        result = validator._validate_execution_methods(mutations)
        assert result is True
    
    def test_valid_unified_diff_apply(self, validator):
        """Test valid UNIFIED_DIFF_APPLY method."""
        mutations = base_mutations()
        mutations["mutations"]["modified_files"] = [{
            "relative_path": "src/test.py",
            "modification_type": "replace",
            "execution_method": "UNIFIED_DIFF_APPLY",
            "method_payload": {
                "patch_path": ".state/patches/test.patch",
                "allow_fuzz": False,
                "rejects_allowed": False
            }
        }]
        
        validator._validate_schema(mutations)
        result = validator._validate_execution_methods(mutations)
        assert result is True
    
    def test_missing_execution_method(self, validator):
        """Test error on missing execution_method."""
        mutations = base_mutations()
        mutations["mutations"]["modified_files"] = [{
            "relative_path": "src/test.py",
            "modification_type": "replace"
        }]
        
        validator._validate_schema(mutations)
        result = validator._validate_execution_methods(mutations)
        assert result is False
        assert any("missing 'execution_method'" in e for e in validator.errors)
    
    def test_invalid_execution_method(self, validator):
        """Test error on invalid execution_method."""
        mutations = base_mutations()
        mutations["mutations"]["modified_files"] = [{
            "relative_path": "src/test.py",
            "modification_type": "replace",
            "execution_method": "INVALID_METHOD"
        }]
        
        validator._validate_schema(mutations)
        result = validator._validate_execution_methods(mutations)
        assert result is False
        assert any("invalid execution_method" in e for e in validator.errors)
    
    def test_unified_diff_with_allow_fuzz_true(self, validator):
        """Test error when UNIFIED_DIFF_APPLY has allow_fuzz=true."""
        mutations = base_mutations()
        mutations["mutations"]["modified_files"] = [{
            "relative_path": "src/test.py",
            "modification_type": "replace",
            "execution_method": "UNIFIED_DIFF_APPLY",
            "method_payload": {
                "patch_path": ".state/patches/test.patch",
                "allow_fuzz": True,
                "rejects_allowed": False
            }
        }]
        
        validator._validate_schema(mutations)
        result = validator._validate_execution_methods(mutations)
        assert result is False
        assert any("allow_fuzz" in e for e in validator.errors)
    
    def test_unified_diff_with_rejects_allowed_true(self, validator):
        """Test error when UNIFIED_DIFF_APPLY has rejects_allowed=true."""
        mutations = base_mutations()
        mutations["mutations"]["modified_files"] = [{
            "relative_path": "src/test.py",
            "modification_type": "replace",
            "execution_method": "UNIFIED_DIFF_APPLY",
            "method_payload": {
                "patch_path": ".state/patches/test.patch",
                "allow_fuzz": False,
                "rejects_allowed": True
            }
        }]
        
        validator._validate_schema(mutations)
        result = validator._validate_execution_methods(mutations)
        assert result is False
        assert any("rejects_allowed" in e for e in validator.errors)
    
    def test_full_rewrite_missing_content_text_inline(self, validator):
        """Test error on inline FULL_REWRITE without content_text."""
        mutations = base_mutations()
        mutations["mutations"]["modified_files"] = [{
            "relative_path": "src/test.py",
            "modification_type": "replace",
            "execution_method": "FULL_REWRITE",
            "method_payload": {
                "content_source": "inline"
            }
        }]
        
        validator._validate_schema(mutations)
        result = validator._validate_execution_methods(mutations)
        assert result is False
        assert any("content_text" in e for e in validator.errors)
    
    def test_full_rewrite_missing_artifact_id(self, validator):
        """Test error on artifact FULL_REWRITE without artifact_id."""
        mutations = base_mutations()
        mutations["mutations"]["modified_files"] = [{
            "relative_path": "src/test.py",
            "modification_type": "replace",
            "execution_method": "FULL_REWRITE",
            "method_payload": {
                "content_source": "artifact"
            }
        }]
        
        validator._validate_schema(mutations)
        result = validator._validate_execution_methods(mutations)
        assert result is False
        assert any("artifact_id" in e for e in validator.errors)


class TestHashGuards:
    """Tests for hash guard validation."""
    
    def test_valid_literal_hash(self, validator):
        """Test valid literal hash format."""
        valid_hash = "61255dea0882199493b084a52b6c4a76d94ee9b2f163279860929e0d047c16c9"
        mutations = base_mutations()
        mutations["mutations"]["modified_files"] = [{
            "relative_path": "src/test.py",
            "modification_type": "replace",
            "execution_method": "FULL_REWRITE",
            "method_payload": {"content_source": "inline", "content_text": "x"},
            "expected_before_sha256": valid_hash,
            "expected_after_sha256": valid_hash
        }]
        
        validator._validate_schema(mutations)
        result = validator._validate_hash_guards(mutations)
        assert result is True
    
    def test_both_literal_and_reference_hash(self, validator):
        """Test error when both literal and reference hashes specified."""
        mutations = base_mutations()
        mutations["mutations"]["modified_files"] = [{
            "relative_path": "src/test.py",
            "modification_type": "replace",
            "execution_method": "FULL_REWRITE",
            "method_payload": {"content_source": "inline", "content_text": "x"},
            "expected_after_sha256": "61255dea0882199493b084a52b6c4a76d94ee9b2f163279860929e0d047c16c9",
            "expected_after_sha256_ref": "ART-001.hash"
        }]
        
        validator._validate_schema(mutations)
        result = validator._validate_hash_guards(mutations)
        assert result is False
        assert any("Cannot specify both" in e for e in validator.errors)
    
    def test_invalid_hash_format(self, validator):
        """Test error on invalid hash format."""
        mutations = base_mutations()
        mutations["mutations"]["modified_files"] = [{
            "relative_path": "src/test.py",
            "modification_type": "replace",
            "execution_method": "FULL_REWRITE",
            "method_payload": {"content_source": "inline", "content_text": "x"},
            "expected_before_sha256": "not-a-valid-hash"
        }]
        
        validator._validate_schema(mutations)
        result = validator._validate_hash_guards(mutations)
        assert result is False
        assert any("invalid" in e and "expected_before_sha256" in e for e in validator.errors)
    
    def test_reference_hash_format(self, validator):
        """Test valid reference hash format."""
        mutations = base_mutations()
        mutations["mutations"]["modified_files"] = [{
            "relative_path": "src/test.py",
            "modification_type": "replace",
            "execution_method": "FULL_REWRITE",
            "method_payload": {"content_source": "artifact", "artifact_id": "ART-001"},
            "expected_before_sha256_ref": "CURRENT.hash",
            "expected_after_sha256_ref": "ART-001.hash"
        }]
        
        validator._validate_schema(mutations)
        result = validator._validate_hash_guards(mutations)
        assert result is True


class TestEvidenceOutputs:
    """Tests for evidence output path validation."""
    
    def test_valid_evidence_paths(self, validator):
        """Test valid evidence output paths."""
        mutations = base_mutations()
        mutations["mutations"]["modified_files"] = [{
            "relative_path": "src/test.py",
            "modification_type": "replace",
            "execution_method": "FULL_REWRITE",
            "method_payload": {"content_source": "inline", "content_text": "x"},
            "expected_after_sha256": "61255dea0882199493b084a52b6c4a76d94ee9b2f163279860929e0d047c16c9",
            "evidence_outputs": {
                "before_hash_path": ".state/evidence/file_mutations/MUT-001/before.sha256",
                "after_hash_path": ".state/evidence/file_mutations/MUT-001/after.sha256",
                "diff_patch_path": ".state/evidence/file_mutations/MUT-001/diff.patch",
                "apply_log_path": ".state/evidence/file_mutations/MUT-001/apply_log.json"
            }
        }]
        
        validator._validate_schema(mutations)
        result = validator._validate_evidence_outputs(mutations)
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
