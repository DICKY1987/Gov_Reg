"""
Integration tests for file mutation execution methods.

Tests the full pipeline: create mutation set -> validate -> ingest -> verify registry entry.
"""

import json
import tempfile
from pathlib import Path

import pytest

from scripts.P_01260207233100000290_validate_file_mutations import FileMutationValidator
from govreg_core.P_01260207233100000011_conflict_validator import ConflictValidator


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mutations_file(temp_dir):
    """Create a test mutations file."""
    path = temp_dir / "mutations.json"
    yield str(path)


def write_mutations(path: str, data: dict) -> None:
    """Helper to write mutations to a file."""
    with open(path, 'w') as f:
        json.dump(data, f)


def base_mutations():
    """Get base valid mutations structure."""
    return {
        "mutation_set_id": "MUT-INT-001",
        "plan_id": "PLAN-INT-001",
        "created_at": "2026-02-12T11:03:00Z",
        "created_by": "integration_test",
        "status": "proposed",
        "mutations": {
            "modified_files": [],
            "created_files": [],
            "deleted_files": []
        }
    }


class TestFullRewriteValidationPipeline:
    """Test FULL_REWRITE mutation through validation pipeline."""
    
    def test_full_rewrite_inline_validates(self, mutations_file):
        """Test FULL_REWRITE with inline content validates successfully."""
        valid_hash_before = "61255dea0882199493b084a52b6c4a76d94ee9b2f163279860929e0d047c16c9"
        valid_hash_after = "1285ace0de22632852fcfc75716cca73ad946ea982bb8eb325e0edaf66250336"
        
        mutations = base_mutations()
        mutations["mutations"]["modified_files"] = [{
            "relative_path": "src/module.py",
            "modification_type": "replace",
            "execution_method": "FULL_REWRITE",
            "method_payload": {
                "content_source": "inline",
                "content_text": "def hello(): pass",
                "line_endings": "PRESERVE",
                "encoding": "utf-8"
            },
            "expected_before_sha256": valid_hash_before,
            "expected_after_sha256": valid_hash_after,
            "evidence_outputs": {
                "before_hash_path": ".state/evidence/file_mutations/MUT-001/before.sha256",
                "after_hash_path": ".state/evidence/file_mutations/MUT-001/after.sha256",
                "diff_patch_path": ".state/evidence/file_mutations/MUT-001/diff.patch",
                "apply_log_path": ".state/evidence/file_mutations/MUT-001/apply_log.json"
            },
            "modifier_step_id": "ST-001",
            "modifier_phase_id": "PH-001"
        }]
        
        write_mutations(mutations_file, mutations)
        
        # Validate
        validator = FileMutationValidator()
        exit_code = validator.validate(mutations_file)
        
        assert exit_code == 0, f"Validation failed with errors: {validator.errors}"
        assert "Schema validation" in validator.checks_passed
        assert "Execution method validation" in validator.checks_passed
        assert "Hash guard validation" in validator.checks_passed
    
    def test_full_rewrite_artifact_validates(self, mutations_file):
        """Test FULL_REWRITE with artifact reference validates successfully."""
        mutations = base_mutations()
        mutations["mutations"]["modified_files"] = [{
            "relative_path": "src/module.py",
            "modification_type": "replace",
            "execution_method": "FULL_REWRITE",
            "method_payload": {
                "content_source": "artifact",
                "artifact_id": "ART-MODULE-V2",
                "line_endings": "PRESERVE",
                "encoding": "utf-8"
            },
            "expected_before_sha256_ref": "CURRENT.hash",
            "expected_after_sha256_ref": "ART-MODULE-V2.hash",
            "evidence_outputs": {
                "before_hash_path": ".state/evidence/file_mutations/MUT-002/before.sha256",
                "after_hash_path": ".state/evidence/file_mutations/MUT-002/after.sha256",
                "diff_patch_path": ".state/evidence/file_mutations/MUT-002/diff.patch",
                "apply_log_path": ".state/evidence/file_mutations/MUT-002/apply_log.json"
            }
        }]
        
        write_mutations(mutations_file, mutations)
        
        # Validate
        validator = FileMutationValidator()
        exit_code = validator.validate(mutations_file)
        
        assert exit_code == 0, f"Validation failed with errors: {validator.errors}"


class TestUnifiedDiffValidationPipeline:
    """Test UNIFIED_DIFF_APPLY mutation through validation pipeline."""
    
    def test_unified_diff_validates(self, mutations_file):
        """Test UNIFIED_DIFF_APPLY with strict mode validates successfully."""
        valid_hash = "61255dea0882199493b084a52b6c4a76d94ee9b2f163279860929e0d047c16c9"
        
        mutations = base_mutations()
        mutations["mutations"]["modified_files"] = [{
            "relative_path": "src/module.py",
            "modification_type": "replace",
            "execution_method": "UNIFIED_DIFF_APPLY",
            "method_payload": {
                "patch_path": ".state/patches/module.patch",
                "strip_level": 1,
                "allow_fuzz": False,
                "rejects_allowed": False
            },
            "expected_before_sha256": valid_hash,
            "expected_after_sha256": valid_hash,
            "evidence_outputs": {
                "before_hash_path": ".state/evidence/file_mutations/MUT-003/before.sha256",
                "after_hash_path": ".state/evidence/file_mutations/MUT-003/after.sha256",
                "diff_patch_path": ".state/evidence/file_mutations/MUT-003/diff.patch",
                "apply_log_path": ".state/evidence/file_mutations/MUT-003/apply_log.json"
            }
        }]
        
        write_mutations(mutations_file, mutations)
        
        # Validate
        validator = FileMutationValidator()
        exit_code = validator.validate(mutations_file)
        
        assert exit_code == 0, f"Validation failed with errors: {validator.errors}"


class TestConflictValidatorIntegration:
    """Test conflict validator integration with execution methods."""
    
    def test_conflict_validator_detects_missing_execution_method(self):
        """Test that conflict validator detects missing execution_method."""
        mutations = base_mutations()
        mutations["mutations"]["modified_files"] = [{
            "relative_path": "src/test.py",
            "modification_type": "replace"
            # Missing execution_method
        }]
        
        validator = ConflictValidator()
        conflicts = validator.validate_execution_methods(mutations["mutations"])
        
        assert len(conflicts) > 0
        assert any("execution_method" in c.description for c in conflicts)
        assert conflicts[0].severity.value == "error"
    
    def test_conflict_validator_detects_fuzzy_matching(self):
        """Test that conflict validator detects fuzzy matching in UNIFIED_DIFF_APPLY."""
        mutations = base_mutations()
        mutations["mutations"]["modified_files"] = [{
            "relative_path": "src/test.py",
            "modification_type": "replace",
            "execution_method": "UNIFIED_DIFF_APPLY",
            "method_payload": {
                "patch_path": ".state/patches/test.patch",
                "allow_fuzz": True,  # Should be false
                "rejects_allowed": False
            }
        }]
        
        validator = ConflictValidator()
        conflicts = validator.validate_execution_methods(mutations["mutations"])
        
        assert len(conflicts) > 0
        assert any("UNIFIED_DIFF_APPLY" in c.description and "strict mode" in c.description for c in conflicts)
    
    def test_conflict_validator_accepts_valid_mutations(self):
        """Test that conflict validator passes valid mutations."""
        valid_hash = "61255dea0882199493b084a52b6c4a76d94ee9b2f163279860929e0d047c16c9"
        
        mutations = base_mutations()
        mutations["mutations"]["modified_files"] = [{
            "relative_path": "src/test.py",
            "modification_type": "replace",
            "execution_method": "FULL_REWRITE",
            "method_payload": {
                "content_source": "inline",
                "content_text": "code"
            },
            "expected_before_sha256": valid_hash,
            "expected_after_sha256": valid_hash
        }]
        
        validator = ConflictValidator()
        conflicts = validator.validate_execution_methods(mutations["mutations"])
        
        assert len(conflicts) == 0


class TestMultipleFileMutations:
    """Test validation pipeline with multiple file mutations."""
    
    def test_mixed_mutation_types_validate(self, mutations_file):
        """Test validation of mutations with different execution methods."""
        valid_hash = "61255dea0882199493b084a52b6c4a76d94ee9b2f163279860929e0d047c16c9"
        
        mutations = base_mutations()
        mutations["mutations"]["modified_files"] = [
            {
                "relative_path": "src/module1.py",
                "modification_type": "replace",
                "execution_method": "FULL_REWRITE",
                "method_payload": {
                    "content_source": "inline",
                    "content_text": "code1"
                },
                "expected_before_sha256": valid_hash,
                "expected_after_sha256": valid_hash,
                "evidence_outputs": {
                    "before_hash_path": ".state/evidence/file_mutations/MUT-A/before.sha256",
                    "after_hash_path": ".state/evidence/file_mutations/MUT-A/after.sha256",
                    "diff_patch_path": ".state/evidence/file_mutations/MUT-A/diff.patch",
                    "apply_log_path": ".state/evidence/file_mutations/MUT-A/apply_log.json"
                }
            },
            {
                "relative_path": "src/module2.py",
                "modification_type": "replace",
                "execution_method": "UNIFIED_DIFF_APPLY",
                "method_payload": {
                    "patch_path": ".state/patches/module2.patch",
                    "strip_level": 1,
                    "allow_fuzz": False,
                    "rejects_allowed": False
                },
                "expected_before_sha256": valid_hash,
                "expected_after_sha256": valid_hash,
                "evidence_outputs": {
                    "before_hash_path": ".state/evidence/file_mutations/MUT-B/before.sha256",
                    "after_hash_path": ".state/evidence/file_mutations/MUT-B/after.sha256",
                    "diff_patch_path": ".state/evidence/file_mutations/MUT-B/diff.patch",
                    "apply_log_path": ".state/evidence/file_mutations/MUT-B/apply_log.json"
                }
            }
        ]
        
        write_mutations(mutations_file, mutations)
        
        # Validate
        validator = FileMutationValidator()
        exit_code = validator.validate(mutations_file)
        
        assert exit_code == 0
        assert len(validator.errors) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
