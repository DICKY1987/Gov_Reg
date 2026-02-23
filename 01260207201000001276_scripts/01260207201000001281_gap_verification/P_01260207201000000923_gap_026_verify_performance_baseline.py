#!/usr/bin/env python3
"""
GAP #26 Verification: Performance Baseline & Monitoring
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

def verify_performance_baseline():
    root = Path(__file__).parent.parent.parent
    results = {
        "gap_id": "GAP-026",
        "gap_name": "Performance Baseline & Monitoring",
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "VERIFIED",
        "checks": []
    }
    
    all_passed = True
    
    # Check 1: Performance baselines file
    baselines_path = root / ".state" / "performance_baselines.json"
    check1 = {
        "check_id": "CHECK-026-001",
        "description": "Performance baselines defined",
        "status": "FAIL",
        "evidence": {"path": str(baselines_path), "exists": baselines_path.exists()}
    }
    if baselines_path.exists():
        check1["evidence"]["sha256"] = compute_sha256(baselines_path)
        with open(baselines_path, 'r') as f:
            baselines = json.load(f)
            if "system_metrics" in baselines and "quality_metrics" in baselines:
                check1["status"] = "PASS"
                check1["evidence"]["metrics_count"] = len(baselines.get("system_metrics", {}))
            else:
                all_passed = False
    else:
        all_passed = False
    results["checks"].append(check1)
    
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
    
    results, all_passed = verify_performance_baseline()
    
    evidence_file = evidence_dir / "gap_26_performance_baseline_monitoring.json"
    with open(evidence_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"GAP #26 Verification: {results['status']}")
    print(f"Evidence file: {evidence_file}")
    print(f"Checks passed: {sum(1 for c in results['checks'] if c['status'] == 'PASS')}/{len(results['checks'])}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
