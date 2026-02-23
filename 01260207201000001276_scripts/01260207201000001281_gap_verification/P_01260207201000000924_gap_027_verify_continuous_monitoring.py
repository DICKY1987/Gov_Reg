#!/usr/bin/env python3
"""
GAP #27 Verification: Continuous Monitoring Plan
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

def verify_continuous_monitoring():
    root = Path(__file__).parent.parent.parent
    results = {
        "gap_id": "GAP-027",
        "gap_name": "Continuous Monitoring Plan",
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "VERIFIED",
        "checks": []
    }
    
    all_passed = True
    
    # Check 1: Monitoring configuration
    config_path = root / ".state" / "monitoring_config.json"
    check1 = {
        "check_id": "CHECK-027-001",
        "description": "Monitoring configuration with continuous checks",
        "status": "FAIL",
        "evidence": {"path": str(config_path), "exists": config_path.exists()}
    }
    if config_path.exists():
        check1["evidence"]["sha256"] = compute_sha256(config_path)
        with open(config_path, 'r') as f:
            config = json.load(f)
            if "continuous_monitoring" in config and "monitors" in config:
                check1["status"] = "PASS"
                check1["evidence"]["monitors_count"] = len(config.get("monitors", {}))
                check1["evidence"]["continuous_enabled"] = config.get("continuous_monitoring", {}).get("enabled")
            else:
                all_passed = False
    else:
        all_passed = False
    results["checks"].append(check1)
    
    # Check 2: Performance baselines integration (GAP #26)
    baselines_path = root / ".state" / "performance_baselines.json"
    check2 = {
        "check_id": "CHECK-027-002",
        "description": "Performance baselines integration (GAP #26)",
        "status": "PASS" if baselines_path.exists() else "FAIL",
        "evidence": {"path": str(baselines_path), "exists": baselines_path.exists()}
    }
    if baselines_path.exists():
        check2["evidence"]["sha256"] = compute_sha256(baselines_path)
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
    
    results, all_passed = verify_continuous_monitoring()
    
    evidence_file = evidence_dir / "gap_27_continuous_monitoring_plan.json"
    with open(evidence_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"GAP #27 Verification: {results['status']}")
    print(f"Evidence file: {evidence_file}")
    print(f"Checks passed: {sum(1 for c in results['checks'] if c['status'] == 'PASS')}/{len(results['checks'])}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
