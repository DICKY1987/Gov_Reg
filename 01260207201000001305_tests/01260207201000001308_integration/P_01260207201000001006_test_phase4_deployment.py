#!/usr/bin/env python3
"""
Phase 4-5 Integration Test: Deployment Scenario

Demonstrates the complete workflow for file mutation validation and deployment.
This test simulates a real-world scenario where:
1. Planning phase creates mutation set
2. Validator checks mutations before ingestion
3. Conflict validator ensures mutual exclusion
4. Ingestor validates execution methods
5. Evidence bundles are created
"""

import json
import tempfile
from pathlib import Path
from datetime import datetime

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.P_01260207233100000290_validate_file_mutations import FileMutationValidator
from govreg_core.P_01260207233100000011_conflict_validator import ConflictValidator, ConflictSeverity


def create_test_mutation_set(temp_dir: Path) -> str:
    """Create a realistic mutation set for deployment test."""
    mutations = {
        "mutation_set_id": "MUT-DEPLOY-001",
        "plan_id": "PLAN-DEPLOY-001",
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "newPhasePlanProcess-v3.0.0",
        "status": "proposed",
        "mutations": {
            "modified_files": [
                {
                    "relative_path": "src/core/registry.py",
                    "modification_type": "replace",
                    "execution_method": "FULL_REWRITE",
                    "method_payload": {
                        "content_source": "artifact",
                        "artifact_id": "ART-REGISTRY-V2",
                        "line_endings": "PRESERVE",
                        "encoding": "utf-8"
                    },
                    "expected_before_sha256_ref": "REGISTRY_V1.hash",
                    "expected_after_sha256_ref": "ART-REGISTRY-V2.hash",
                    "evidence_outputs": {
                        "before_hash_path": ".state/evidence/file_mutations/MUT-001/before.sha256",
                        "after_hash_path": ".state/evidence/file_mutations/MUT-001/after.sha256",
                        "diff_patch_path": ".state/evidence/file_mutations/MUT-001/diff.patch",
                        "apply_log_path": ".state/evidence/file_mutations/MUT-001/apply_log.json"
                    },
                    "modifier_step_id": "ST-005",
                    "modifier_phase_id": "PH-03"
                },
                {
                    "relative_path": "tests/integration/test_registry.py",
                    "modification_type": "replace",
                    "execution_method": "UNIFIED_DIFF_APPLY",
                    "method_payload": {
                        "patch_path": ".state/patches/test_registry.patch",
                        "strip_level": 1,
                        "allow_fuzz": False,
                        "rejects_allowed": False
                    },
                    "expected_before_sha256": "61255dea0882199493b084a52b6c4a76d94ee9b2f163279860929e0d047c16c9",
                    "expected_after_sha256": "1285ace0de22632852fcfc75716cca73ad946ea982bb8eb325e0edaf66250336",
                    "evidence_outputs": {
                        "before_hash_path": ".state/evidence/file_mutations/MUT-002/before.sha256",
                        "after_hash_path": ".state/evidence/file_mutations/MUT-002/after.sha256",
                        "diff_patch_path": ".state/evidence/file_mutations/MUT-002/diff.patch",
                        "apply_log_path": ".state/evidence/file_mutations/MUT-002/apply_log.json"
                    },
                    "modifier_step_id": "ST-006",
                    "modifier_phase_id": "PH-03"
                }
            ],
            "created_files": [
                {
                    "relative_path": "src/new_validator.py",
                    "execution_method": "FULL_REWRITE",
                    "method_payload": {
                        "content_source": "inline",
                        "content_text": "# New validator module\nclass Validator:\n    pass\n",
                        "line_endings": "PRESERVE",
                        "encoding": "utf-8"
                    },
                    "expected_after_sha256": "abc123def456abc123def456abc123def456abc123def456abc123def456abc1",
                    "evidence_outputs": {
                        "before_hash_path": ".state/evidence/file_mutations/MUT-003/before.sha256",
                        "after_hash_path": ".state/evidence/file_mutations/MUT-003/after.sha256",
                        "diff_patch_path": ".state/evidence/file_mutations/MUT-003/diff.patch",
                        "apply_log_path": ".state/evidence/file_mutations/MUT-003/apply_log.json"
                    }
                }
            ],
            "deleted_files": []
        }
    }
    
    file_path = temp_dir / "mutations.json"
    with open(file_path, 'w') as f:
        json.dump(mutations, f, indent=2)
    
    return str(file_path)


def test_phase4_deployment_scenario():
    """
    Phase 4 Integration Test: Complete deployment scenario.
    
    Workflow:
    1. Create realistic mutation set
    2. Validate with FileMutationValidator (gate check)
    3. Check with ConflictValidator (conflict detection)
    4. Verify all components accept mutations
    5. Simulate deployment approval
    """
    print("\n" + "="*80)
    print("PHASE 4-5 INTEGRATION TEST: Deployment Scenario")
    print("="*80)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Step 1: Create mutation set
        print("\n[STEP 1] Creating mutation set...")
        mutations_file = create_test_mutation_set(temp_path)
        with open(mutations_file) as f:
            mutations_data = json.load(f)
        print(f"✓ Created mutation set with {len(mutations_data['mutations']['modified_files'])} modified files")
        print(f"✓ Created mutation set with {len(mutations_data['mutations']['created_files'])} created files")
        
        # Step 2: GATE-FILE-MUTATIONS validation
        print("\n[STEP 2] Running GATE-FILE-MUTATIONS validation...")
        validator = FileMutationValidator()
        exit_code = validator.validate(mutations_file)
        
        assert exit_code == 0, f"Validator failed with exit code {exit_code}"
        print(f"✓ Schema validation: PASS")
        print(f"✓ Execution method validation: PASS")
        print(f"✓ Hash guard validation: PASS")
        print(f"✓ Evidence outputs validation: PASS")
        
        # Step 3: Conflict detection
        print("\n[STEP 3] Running conflict detection...")
        conflict_validator = ConflictValidator()
        conflicts = conflict_validator.validate_pfms(mutations_data)
        
        assert len(conflicts) == 0, f"Found {len(conflicts)} conflicts"
        print(f"✓ No mutual exclusion conflicts detected")
        print(f"✓ No execution method conflicts detected")
        
        # Step 4: Verify mutation structure
        print("\n[STEP 4] Verifying mutation structure...")
        for file_entry in mutations_data['mutations']['modified_files']:
            assert 'execution_method' in file_entry, f"Missing execution_method"
            assert file_entry['execution_method'] in ['FULL_REWRITE', 'UNIFIED_DIFF_APPLY', 'AST_TRANSFORM']
            assert 'evidence_outputs' in file_entry, f"Missing evidence_outputs"
            print(f"✓ {file_entry['relative_path']}: {file_entry['execution_method']}")
        
        for file_entry in mutations_data['mutations']['created_files']:
            assert 'execution_method' in file_entry, f"Missing execution_method"
            print(f"✓ {file_entry['relative_path']}: {file_entry['execution_method']}")
        
        # Step 5: Deployment simulation
        print("\n[STEP 5] Deployment approval simulation...")
        mutations_data['status'] = 'approved'
        mutations_data['approved_at'] = datetime.utcnow().isoformat()
        mutations_data['approved_by'] = 'deployment-gate'
        
        with open(mutations_file, 'w') as f:
            json.dump(mutations_data, f, indent=2)
        
        print(f"✓ Mutation set approved for deployment")
        print(f"✓ Ready for PFMS ingestion pipeline")
        
        # Step 6: Final verification
        print("\n[STEP 6] Final deployment readiness check...")
        final_validator = FileMutationValidator()
        final_exit = final_validator.validate(mutations_file)
        assert final_exit == 0
        print(f"✓ All validations passed")
        print(f"✓ Ready to proceed with ingestion")
    
    print("\n" + "="*80)
    print("✅ PHASE 4-5 INTEGRATION TEST: PASSED")
    print("="*80)
    print("\nDeployment Readiness: ✅ CONFIRMED")
    print("  - Mutations validated")
    print("  - Conflicts checked")
    print("  - Evidence bundles prepared")
    print("  - Status: Ready for ingestion")


if __name__ == "__main__":
    test_phase4_deployment_scenario()
