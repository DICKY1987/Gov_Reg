#!/usr/bin/env python3
"""
GAP #19 Verification: Data Retention Policy Compliance
"""

import json
import hashlib
import sys
from pathlib import Path
from datetime import datetime, timezone

def compute_sha256(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest().upper()

def verify_data_retention_policy():
    root = Path(__file__).parent.parent.parent
    results = {
        "gap_id": "GAP-019",
        "gap_name": "Data Retention Policy Compliance",
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "VERIFIED",
        "checks": []
    }
    
    all_passed = True
    
    # Check 1: Retention registry exists
    registry_path = root / ".state" / "retention_registry.jsonl"
    check1 = {
        "check_id": "CHECK-019-001",
        "description": "Retention registry initialized",
        "status": "PASS" if registry_path.exists() else "FAIL",
        "evidence": {"path": str(registry_path), "exists": registry_path.exists()}
    }
    if registry_path.exists():
        check1["evidence"]["sha256"] = compute_sha256(registry_path)
    else:
        all_passed = False
    results["checks"].append(check1)
    
    # Check 2: Data retention policy with compliance requirements
    policy_path = root / "config" / "data_retention_policy.json"
    check2 = {
        "check_id": "CHECK-019-002",
        "description": "Data retention policy with SOX/GDPR compliance",
        "status": "FAIL",
        "evidence": {"path": str(policy_path), "exists": policy_path.exists()}
    }
    if policy_path.exists():
        check2["evidence"]["sha256"] = compute_sha256(policy_path)
        with open(policy_path, 'r') as f:
            policy = json.load(f)
            schedules = policy.get("retention_schedules", {})
            if "governance_artifacts" in schedules and "personal_data" in schedules:
                check2["status"] = "PASS"
                check2["evidence"]["retention_schedules"] = len(schedules)
            else:
                all_passed = False
    else:
        all_passed = False
    results["checks"].append(check2)
    
    # Final status
    results["status"] = "VERIFIED" if all_passed else "PARTIAL"
    
    # Cryptographic proof
    proof_data = json.dumps(results["checks"], sort_keys=True)
    results["cryptographic_proof"] = {
        "algorithm": "SHA256",
        "hash": hashlib.sha256(proof_data.encode()).hexdigest().upper(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    return results, all_passed

def main():
    evidence_dir = Path(__file__).parent.parent.parent / ".state" / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    
    results, all_passed = verify_data_retention_policy()
    
    evidence_file = evidence_dir / "gap_19_data_retention_policy.json"
    with open(evidence_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"GAP #19 Verification: {results['status']}")
    print(f"Evidence file: {evidence_file}")
    print(f"Checks passed: {sum(1 for c in results['checks'] if c['status'] == 'PASS')}/{len(results['checks'])}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
