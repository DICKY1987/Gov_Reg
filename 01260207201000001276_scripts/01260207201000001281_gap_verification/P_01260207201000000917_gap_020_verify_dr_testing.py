#!/usr/bin/env python3
"""
GAP #20 Verification: Disaster Recovery Testing
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

def verify_dr_testing():
    root = Path(__file__).parent.parent.parent
    results = {
        "gap_id": "GAP-020",
        "gap_name": "Disaster Recovery Testing",
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "VERIFIED",
        "checks": []
    }
    
    all_passed = True
    
    # Check 1: DR test results registry
    registry_path = root / ".state" / "dr_test_results.jsonl"
    check1 = {
        "check_id": "CHECK-020-001",
        "description": "DR test results registry initialized",
        "status": "PASS" if registry_path.exists() else "FAIL",
        "evidence": {"path": str(registry_path), "exists": registry_path.exists()}
    }
    if registry_path.exists():
        check1["evidence"]["sha256"] = compute_sha256(registry_path)
    else:
        all_passed = False
    results["checks"].append(check1)
    
    # Check 2: DR testing framework with RTO/RPO
    framework_path = root / "config" / "dr_testing_framework.json"
    check2 = {
        "check_id": "CHECK-020-002",
        "description": "DR testing framework with RTO/RPO targets",
        "status": "FAIL",
        "evidence": {"path": str(framework_path), "exists": framework_path.exists()}
    }
    if framework_path.exists():
        check2["evidence"]["sha256"] = compute_sha256(framework_path)
        with open(framework_path, 'r') as f:
            framework = json.load(f)
            dr_config = framework.get("dr_test_framework", {})
            if "rto_targets" in dr_config and "rpo_targets" in dr_config:
                check2["status"] = "PASS"
                check2["evidence"]["test_scenarios"] = len(dr_config.get("test_scenarios", []))
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
    
    results, all_passed = verify_dr_testing()
    
    evidence_file = evidence_dir / "gap_20_disaster_recovery_testing.json"
    with open(evidence_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"GAP #20 Verification: {results['status']}")
    print(f"Evidence file: {evidence_file}")
    print(f"Checks passed: {sum(1 for c in results['checks'] if c['status'] == 'PASS')}/{len(results['checks'])}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
