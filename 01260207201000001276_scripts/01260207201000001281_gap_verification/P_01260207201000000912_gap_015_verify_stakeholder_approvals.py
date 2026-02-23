#!/usr/bin/env python3
"""
GAP #15 Verification: Stakeholder Approval Documentation
Verifies the approval framework infrastructure is operational.
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

def verify_approval_framework():
    """Verify approval framework components exist and are valid."""
    root = Path(__file__).parent.parent.parent
    results = {
        "gap_id": "GAP-015",
        "gap_name": "Stakeholder Approval Documentation",
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "VERIFIED",
        "checks": []
    }
    
    all_passed = True
    
    # Check 1: Approval schema exists
    schema_path = root / "schemas" / "approval_record.schema.json"
    check1 = {
        "check_id": "CHECK-015-001",
        "description": "Approval record schema exists",
        "status": "PASS" if schema_path.exists() else "FAIL",
        "evidence": {
            "path": str(schema_path),
            "exists": schema_path.exists()
        }
    }
    if schema_path.exists():
        check1["evidence"]["sha256"] = compute_sha256(schema_path)
    else:
        all_passed = False
    results["checks"].append(check1)
    
    # Check 2: Approval registry exists
    registry_path = root / ".state" / "approvals.jsonl"
    check2 = {
        "check_id": "CHECK-015-002",
        "description": "Approval registry initialized",
        "status": "PASS" if registry_path.exists() else "FAIL",
        "evidence": {
            "path": str(registry_path),
            "exists": registry_path.exists()
        }
    }
    if registry_path.exists():
        check2["evidence"]["sha256"] = compute_sha256(registry_path)
        # Verify genesis record
        with open(registry_path, 'r') as f:
            lines = f.readlines()
            if lines:
                genesis = json.loads(lines[0])
                check2["evidence"]["genesis_record"] = {
                    "approval_id": genesis.get("approval_id"),
                    "change_id": genesis.get("change_id"),
                    "decision": genesis.get("decision")
                }
    else:
        all_passed = False
    results["checks"].append(check2)
    
    # Check 3: Impact assessment template exists
    template_path = root / "templates" / "change_impact_assessment.json"
    check3 = {
        "check_id": "CHECK-015-003",
        "description": "Impact assessment template exists",
        "status": "PASS" if template_path.exists() else "FAIL",
        "evidence": {
            "path": str(template_path),
            "exists": template_path.exists()
        }
    }
    if template_path.exists():
        check3["evidence"]["sha256"] = compute_sha256(template_path)
    else:
        all_passed = False
    results["checks"].append(check3)
    
    # Check 4: Impact assessments registry exists
    assessments_path = root / ".state" / "impact_assessments.jsonl"
    check4 = {
        "check_id": "CHECK-015-004",
        "description": "Impact assessments registry initialized",
        "status": "PASS" if assessments_path.exists() else "FAIL",
        "evidence": {
            "path": str(assessments_path),
            "exists": assessments_path.exists()
        }
    }
    if assessments_path.exists():
        check4["evidence"]["sha256"] = compute_sha256(assessments_path)
    else:
        all_passed = False
    results["checks"].append(check4)
    
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
    results, all_passed = verify_approval_framework()
    
    # Write evidence file
    evidence_file = evidence_dir / "gap_15_stakeholder_approvals.json"
    with open(evidence_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print(f"GAP #15 Verification: {results['status']}")
    print(f"Evidence file: {evidence_file}")
    print(f"Checks passed: {sum(1 for c in results['checks'] if c['status'] == 'PASS')}/{len(results['checks'])}")
    
    # Exit code: 0 = VERIFIED, 1 = PARTIAL/FAILED
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
