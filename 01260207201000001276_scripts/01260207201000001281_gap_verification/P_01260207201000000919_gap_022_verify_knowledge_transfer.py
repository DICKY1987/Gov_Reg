#!/usr/bin/env python3
"""
GAP #22 Verification: Knowledge Transfer Documentation
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

def verify_knowledge_transfer():
    root = Path(__file__).parent.parent.parent
    results = {
        "gap_id": "GAP-022",
        "gap_name": "Knowledge Transfer Documentation",
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "VERIFIED",
        "checks": []
    }
    
    all_passed = True
    
    # Check 1: Knowledge base directory structure
    kb_path = root / "docs" / "knowledge_base"
    check1 = {
        "check_id": "CHECK-022-001",
        "description": "Knowledge base directory structure exists",
        "status": "PASS" if kb_path.exists() else "FAIL",
        "evidence": {"path": str(kb_path), "exists": kb_path.exists()}
    }
    if kb_path.exists():
        subdirs = [d.name for d in kb_path.iterdir() if d.is_dir()]
        check1["evidence"]["subdirectories"] = subdirs
    else:
        all_passed = False
    results["checks"].append(check1)
    
    # Check 2: Knowledge base index
    index_path = root / ".state" / "knowledge_base_index.json"
    check2 = {
        "check_id": "CHECK-022-002",
        "description": "Knowledge base index exists",
        "status": "FAIL",
        "evidence": {"path": str(index_path), "exists": index_path.exists()}
    }
    if index_path.exists():
        check2["evidence"]["sha256"] = compute_sha256(index_path)
        with open(index_path, 'r') as f:
            index = json.load(f)
            categories = index.get("categories", {})
            if len(categories) > 0:
                check2["status"] = "PASS"
                check2["evidence"]["categories_count"] = len(categories)
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
    
    results, all_passed = verify_knowledge_transfer()
    
    evidence_file = evidence_dir / "gap_22_knowledge_transfer_documentation.json"
    with open(evidence_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"GAP #22 Verification: {results['status']}")
    print(f"Evidence file: {evidence_file}")
    print(f"Checks passed: {sum(1 for c in results['checks'] if c['status'] == 'PASS')}/{len(results['checks'])}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
