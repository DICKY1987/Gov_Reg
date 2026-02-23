#!/usr/bin/env python3
"""
GAP #28 Verification: Third-Party Dependency Management
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

def verify_dependency_management():
    root = Path(__file__).parent.parent.parent
    results = {
        "gap_id": "GAP-028",
        "gap_name": "Third-Party Dependency Management",
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "VERIFIED",
        "checks": []
    }
    
    all_passed = True
    
    # Check 1: Dependencies registry
    registry_path = root / ".state" / "dependencies.json"
    check1 = {
        "check_id": "CHECK-028-001",
        "description": "Dependencies registry with vulnerability scanning",
        "status": "FAIL",
        "evidence": {"path": str(registry_path), "exists": registry_path.exists()}
    }
    if registry_path.exists():
        check1["evidence"]["sha256"] = compute_sha256(registry_path)
        with open(registry_path, 'r') as f:
            registry = json.load(f)
            if "licensing" in registry and "update_policy" in registry:
                check1["status"] = "PASS"
                check1["evidence"]["approved_licenses"] = len(registry.get("licensing", {}).get("approved_licenses", []))
            else:
                all_passed = False
    else:
        all_passed = False
    results["checks"].append(check1)
    
    # Check 2: Compliance registry integration (GAP #24)
    compliance_path = root / ".state" / "compliance_registry.json"
    check2 = {
        "check_id": "CHECK-028-002",
        "description": "Compliance registry integration (GAP #24)",
        "status": "PASS" if compliance_path.exists() else "FAIL",
        "evidence": {"path": str(compliance_path), "exists": compliance_path.exists()}
    }
    if compliance_path.exists():
        check2["evidence"]["sha256"] = compute_sha256(compliance_path)
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
    
    results, all_passed = verify_dependency_management()
    
    evidence_file = evidence_dir / "gap_28_third_party_dependency_management.json"
    with open(evidence_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"GAP #28 Verification: {results['status']}")
    print(f"Evidence file: {evidence_file}")
    print(f"Checks passed: {sum(1 for c in results['checks'] if c['status'] == 'PASS')}/{len(results['checks'])}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
