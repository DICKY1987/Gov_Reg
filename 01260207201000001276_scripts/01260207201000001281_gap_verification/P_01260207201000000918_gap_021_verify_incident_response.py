#!/usr/bin/env python3
"""
GAP #21 Verification: Incident Response Procedures
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

def verify_incident_response():
    root = Path(__file__).parent.parent.parent
    results = {
        "gap_id": "GAP-021",
        "gap_name": "Incident Response Procedures",
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "VERIFIED",
        "checks": []
    }
    
    all_passed = True
    
    # Check 1: Incidents registry
    registry_path = root / ".state" / "incidents.jsonl"
    check1 = {
        "check_id": "CHECK-021-001",
        "description": "Incidents registry initialized",
        "status": "PASS" if registry_path.exists() else "FAIL",
        "evidence": {"path": str(registry_path), "exists": registry_path.exists()}
    }
    if registry_path.exists():
        check1["evidence"]["sha256"] = compute_sha256(registry_path)
    else:
        all_passed = False
    results["checks"].append(check1)
    
    # Check 2: Incident response template
    template_path = root / "templates" / "incident_response_record.json"
    check2 = {
        "check_id": "CHECK-021-002",
        "description": "Incident response template exists",
        "status": "PASS" if template_path.exists() else "FAIL",
        "evidence": {"path": str(template_path), "exists": template_path.exists()}
    }
    if template_path.exists():
        check2["evidence"]["sha256"] = compute_sha256(template_path)
    else:
        all_passed = False
    results["checks"].append(check2)
    
    # Check 3: Incident runbooks directory
    runbooks_path = root / "docs" / "runbooks" / "incidents"
    check3 = {
        "check_id": "CHECK-021-003",
        "description": "Incident runbooks directory exists",
        "status": "PASS" if runbooks_path.exists() else "FAIL",
        "evidence": {"path": str(runbooks_path), "exists": runbooks_path.exists()}
    }
    if not runbooks_path.exists():
        all_passed = False
    results["checks"].append(check3)
    
    # Check 4: Access audit log integration (GAP #17)
    audit_path = root / ".state" / "access_audit.jsonl"
    check4 = {
        "check_id": "CHECK-021-004",
        "description": "Access audit log integration (GAP #17)",
        "status": "PASS" if audit_path.exists() else "FAIL",
        "evidence": {"path": str(audit_path), "exists": audit_path.exists()}
    }
    if audit_path.exists():
        check4["evidence"]["sha256"] = compute_sha256(audit_path)
    else:
        all_passed = False
    results["checks"].append(check4)
    
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
    
    results, all_passed = verify_incident_response()
    
    evidence_file = evidence_dir / "gap_21_incident_response_procedures.json"
    with open(evidence_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"GAP #21 Verification: {results['status']}")
    print(f"Evidence file: {evidence_file}")
    print(f"Checks passed: {sum(1 for c in results['checks'] if c['status'] == 'PASS')}/{len(results['checks'])}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
