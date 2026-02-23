#!/usr/bin/env python3
"""
GAP #24 Verification: Regulatory Compliance Documentation
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

def verify_compliance_documentation():
    root = Path(__file__).parent.parent.parent
    results = {
        "gap_id": "GAP-024",
        "gap_name": "Regulatory Compliance Documentation",
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "VERIFIED",
        "checks": []
    }
    
    all_passed = True
    
    # Check 1: Compliance registry exists
    registry_path = root / ".state" / "compliance_registry.json"
    check1 = {
        "check_id": "CHECK-024-001",
        "description": "Compliance registry with SOX/GDPR/ISO mappings",
        "status": "FAIL",
        "evidence": {"path": str(registry_path), "exists": registry_path.exists()}
    }
    if registry_path.exists():
        check1["evidence"]["sha256"] = compute_sha256(registry_path)
        with open(registry_path, 'r') as f:
            registry = json.load(f)
            frameworks = registry.get("frameworks", {})
            if "SOX" in frameworks and "GDPR" in frameworks and "ISO_27001" in frameworks:
                check1["status"] = "PASS"
                check1["evidence"]["frameworks_count"] = len(frameworks)
            else:
                all_passed = False
    else:
        all_passed = False
    results["checks"].append(check1)
    
    # Check 2: Evidence artifacts referenced
    check2 = {
        "check_id": "CHECK-024-002",
        "description": "Evidence artifacts mapped to compliance requirements",
        "status": "PASS",
        "evidence": {}
    }
    evidence_files = [
        root / ".state" / "approvals.jsonl",
        root / ".state" / "access_audit.jsonl",
        root / "config" / "data_retention_policy.json"
    ]
    missing = []
    for ef in evidence_files:
        if not ef.exists():
            missing.append(str(ef))
            all_passed = False
            check2["status"] = "FAIL"
    if missing:
        check2["evidence"]["missing_artifacts"] = missing
    else:
        check2["evidence"]["all_artifacts_present"] = True
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
    
    results, all_passed = verify_compliance_documentation()
    
    evidence_file = evidence_dir / "gap_24_regulatory_compliance_documentation.json"
    with open(evidence_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"GAP #24 Verification: {results['status']}")
    print(f"Evidence file: {evidence_file}")
    print(f"Checks passed: {sum(1 for c in results['checks'] if c['status'] == 'PASS')}/{len(results['checks'])}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
