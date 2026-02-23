#!/usr/bin/env python3
"""
GAP #25 Verification: Change Control Board Records
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

def verify_ccb_records():
    root = Path(__file__).parent.parent.parent
    results = {
        "gap_id": "GAP-025",
        "gap_name": "Change Control Board Records",
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "VERIFIED",
        "checks": []
    }
    
    all_passed = True
    
    # Check 1: CCB meetings registry
    registry_path = root / ".state" / "ccb_meetings.jsonl"
    check1 = {
        "check_id": "CHECK-025-001",
        "description": "CCB meetings registry initialized",
        "status": "PASS" if registry_path.exists() else "FAIL",
        "evidence": {"path": str(registry_path), "exists": registry_path.exists()}
    }
    if registry_path.exists():
        check1["evidence"]["sha256"] = compute_sha256(registry_path)
    else:
        all_passed = False
    results["checks"].append(check1)
    
    # Check 2: Approval framework integration (GAP #15)
    approvals_path = root / ".state" / "approvals.jsonl"
    check2 = {
        "check_id": "CHECK-025-002",
        "description": "Approval framework integration (GAP #15)",
        "status": "PASS" if approvals_path.exists() else "FAIL",
        "evidence": {"path": str(approvals_path), "exists": approvals_path.exists()}
    }
    if approvals_path.exists():
        check2["evidence"]["sha256"] = compute_sha256(approvals_path)
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
    
    results, all_passed = verify_ccb_records()
    
    evidence_file = evidence_dir / "gap_25_change_control_board_records.json"
    with open(evidence_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"GAP #25 Verification: {results['status']}")
    print(f"Evidence file: {evidence_file}")
    print(f"Checks passed: {sum(1 for c in results['checks'] if c['status'] == 'PASS')}/{len(results['checks'])}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
