#!/usr/bin/env python3
"""
GAP #17 Verification: Access Control Audit Trail
Verifies the chain-hashed access audit log is operational.
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

def verify_access_audit_trail():
    """Verify access audit trail with chain hashing."""
    root = Path(__file__).parent.parent.parent
    results = {
        "gap_id": "GAP-017",
        "gap_name": "Access Control Audit Trail",
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "VERIFIED",
        "checks": []
    }
    
    all_passed = True
    
    # Check 1: Access audit log exists
    audit_path = root / ".state" / "access_audit.jsonl"
    check1 = {
        "check_id": "CHECK-017-001",
        "description": "Access audit log exists",
        "status": "PASS" if audit_path.exists() else "FAIL",
        "evidence": {
            "path": str(audit_path),
            "exists": audit_path.exists()
        }
    }
    if audit_path.exists():
        check1["evidence"]["sha256"] = compute_sha256(audit_path)
    else:
        all_passed = False
    results["checks"].append(check1)
    
    # Check 2: Genesis event with chain hash
    check2 = {
        "check_id": "CHECK-017-002",
        "description": "Genesis event with valid chain hash",
        "status": "FAIL",
        "evidence": {}
    }
    if audit_path.exists():
        with open(audit_path, 'r') as f:
            lines = f.readlines()
            if lines:
                genesis = json.loads(lines[0])
                check2["evidence"]["genesis_event_id"] = genesis.get("event_id")
                check2["evidence"]["genesis_hash"] = genesis.get("chain_hash")
                check2["evidence"]["previous_hash"] = genesis.get("previous_hash")
                
                # Verify chain hash integrity
                event_data = json.dumps({k: v for k, v in genesis.items() if k != 'chain_hash'}, sort_keys=True)
                computed_hash = hashlib.sha256(event_data.encode()).hexdigest().upper()
                
                if genesis.get("chain_hash") == computed_hash:
                    check2["status"] = "PASS"
                    check2["evidence"]["hash_verified"] = True
                else:
                    all_passed = False
                    check2["evidence"]["hash_verified"] = False
            else:
                all_passed = False
    else:
        all_passed = False
    results["checks"].append(check2)
    
    # Check 3: Approval registry integration (GAP #15 dependency)
    approvals_path = root / ".state" / "approvals.jsonl"
    check3 = {
        "check_id": "CHECK-017-003",
        "description": "Approval registry exists (GAP #15 integration)",
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
    evidence_dir = Path(__file__).parent.parent.parent / ".state" / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    
    results, all_passed = verify_access_audit_trail()
    
    evidence_file = evidence_dir / "gap_17_access_audit_trail.json"
    with open(evidence_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"GAP #17 Verification: {results['status']}")
    print(f"Evidence file: {evidence_file}")
    print(f"Checks passed: {sum(1 for c in results['checks'] if c['status'] == 'PASS')}/{len(results['checks'])}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
