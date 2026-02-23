#!/usr/bin/env python3
"""
GAP #16 Verification: Change Impact Assessment
Verifies the impact assessment framework infrastructure is operational.
"""

import json
import hashlib
import sys
from pathlib import Path
from datetime import datetime, timezone

def compute_sha256(file_path):
    """Compute SHA256 hash of file."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest().upper()

def verify_impact_assessment_framework():
    """Verify impact assessment framework components exist and are valid."""
    root = Path(__file__).parent.parent.parent
    results = {
        "gap_id": "GAP-016",
        "gap_name": "Change Impact Assessment",
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "VERIFIED",
        "checks": []
    }
    
    all_passed = True
    
    # Check 1: Impact assessment template exists with all 10 risk dimensions
    template_path = root / "templates" / "change_impact_assessment.json"
    check1 = {
        "check_id": "CHECK-016-001",
        "description": "Impact assessment template with 10 risk dimensions",
        "status": "FAIL",
        "evidence": {
            "path": str(template_path),
            "exists": template_path.exists()
        }
    }
    if template_path.exists():
        check1["evidence"]["sha256"] = compute_sha256(template_path)
        with open(template_path, 'r') as f:
            template = json.load(f)
            risk_dims = template.get("risk_dimensions", {})
            expected_dims = [
                "technical_risk", "operational_impact", "data_integrity",
                "performance_impact", "security_implications", "compliance_requirements",
                "rollback_complexity", "user_experience", "training_requirements",
                "third_party_dependencies"
            ]
            if all(dim in risk_dims for dim in expected_dims):
                check1["status"] = "PASS"
                check1["evidence"]["risk_dimensions_count"] = len(risk_dims)
            else:
                all_passed = False
    else:
        all_passed = False
    results["checks"].append(check1)
    
    # Check 2: Impact assessments registry exists
    registry_path = root / ".state" / "impact_assessments.jsonl"
    check2 = {
        "check_id": "CHECK-016-002",
        "description": "Impact assessments registry initialized",
        "status": "PASS" if registry_path.exists() else "FAIL",
        "evidence": {
            "path": str(registry_path),
            "exists": registry_path.exists()
        }
    }
    if registry_path.exists():
        check2["evidence"]["sha256"] = compute_sha256(registry_path)
    else:
        all_passed = False
    results["checks"].append(check2)
    
    # Check 3: Approval registry exists (dependency on GAP #15)
    approvals_path = root / ".state" / "approvals.jsonl"
    check3 = {
        "check_id": "CHECK-016-003",
        "description": "Approval registry exists (GAP #15 dependency)",
        "status": "PASS" if approvals_path.exists() else "FAIL",
        "evidence": {
            "path": str(approvals_path),
            "exists": approvals_path.exists()
        }
    }
    if approvals_path.exists():
        check3["evidence"]["sha256"] = compute_sha256(approvals_path)
    else:
        all_passed = False
    results["checks"].append(check3)
    
    # Final status
    if all_passed:
        results["status"] = "VERIFIED"
    else:
        results["status"] = "PARTIAL"
    
    # Cryptographic proof
    proof_data = json.dumps(results["checks"], sort_keys=True)
    results["cryptographic_proof"] = {
        "algorithm": "SHA256",
        "hash": hashlib.sha256(proof_data.encode()).hexdigest().upper(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    return results, all_passed

def main():
    """Main verification function."""
    # Create evidence directory
    evidence_dir = Path(__file__).parent.parent.parent / ".state" / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    
    # Run verification
    results, all_passed = verify_impact_assessment_framework()
    
    # Write evidence file
    evidence_file = evidence_dir / "gap_16_change_impact_assessment.json"
    with open(evidence_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print(f"GAP #16 Verification: {results['status']}")
    print(f"Evidence file: {evidence_file}")
    print(f"Checks passed: {sum(1 for c in results['checks'] if c['status'] == 'PASS')}/{len(results['checks'])}")
    
    # Exit code: 0 = VERIFIED, 1 = PARTIAL/FAILED
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
