#!/usr/bin/env python3
"""
GAP #18 Verification: Sensitive Data Handling
Verifies sensitive data classification and handling infrastructure.
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

def verify_sensitive_data_handling():
    """Verify sensitive data handling infrastructure."""
    root = Path(__file__).parent.parent.parent
    results = {
        "gap_id": "GAP-018",
        "gap_name": "Sensitive Data Handling",
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "VERIFIED",
        "checks": []
    }
    
    all_passed = True
    
    # Check 1: Sensitive data registry exists
    registry_path = root / ".state" / "sensitive_data_registry.jsonl"
    check1 = {
        "check_id": "CHECK-018-001",
        "description": "Sensitive data registry exists",
        "status": "PASS" if registry_path.exists() else "FAIL",
        "evidence": {
            "path": str(registry_path),
            "exists": registry_path.exists()
        }
    }
    if registry_path.exists():
        check1["evidence"]["sha256"] = compute_sha256(registry_path)
    else:
        all_passed = False
    results["checks"].append(check1)
    
    # Check 2: Data classification policy with 5 levels
    policy_path = root / "config" / "data_classification_policy.json"
    check2 = {
        "check_id": "CHECK-018-002",
        "description": "Data classification policy with 5 levels",
        "status": "FAIL",
        "evidence": {
            "path": str(policy_path),
            "exists": policy_path.exists()
        }
    }
    if policy_path.exists():
        check2["evidence"]["sha256"] = compute_sha256(policy_path)
        with open(policy_path, 'r') as f:
            policy = json.load(f)
            levels = policy.get("classification_levels", {})
            expected_levels = ["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED", "TOP_SECRET"]
            if all(level in levels for level in expected_levels):
                check2["status"] = "PASS"
                check2["evidence"]["classification_levels"] = len(levels)
            else:
                all_passed = False
    else:
        all_passed = False
    results["checks"].append(check2)
    
    # Check 3: Access audit log integration (GAP #17 dependency)
    audit_path = root / ".state" / "access_audit.jsonl"
    check3 = {
        "check_id": "CHECK-018-003",
        "description": "Access audit log exists (GAP #17 integration)",
        "status": "PASS" if audit_path.exists() else "FAIL",
        "evidence": {
            "path": str(audit_path),
            "exists": audit_path.exists()
        }
    }
    if audit_path.exists():
        check3["evidence"]["sha256"] = compute_sha256(audit_path)
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
    evidence_dir = Path(__file__).parent.parent.parent / ".state" / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    
    results, all_passed = verify_sensitive_data_handling()
    
    evidence_file = evidence_dir / "gap_18_sensitive_data_handling.json"
    with open(evidence_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"GAP #18 Verification: {results['status']}")
    print(f"Evidence file: {evidence_file}")
    print(f"Checks passed: {sum(1 for c in results['checks'] if c['status'] == 'PASS')}/{len(results['checks'])}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
