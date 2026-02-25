"""Ingest gate validator for reservation commitments.

FILE_ID: 01999000042260124034
DOC_ID: P_01999000042260124034
PHASE: 1.4 - Foundation (Validation Gate - Ingest)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).parent.parent / "govreg_core"))
from P_01999000042260124032_reservation_ledger import ReservationLedger


def validate_ingest_commitments(
    plan_id: str,
    registry_root: Path | str
) -> Dict:
    """Validate that all reservations are committed after ingest.
    
    Fail-closed: Uncommitted reservations block validation.
    
    Args:
        plan_id: Plan identifier
        registry_root: Root directory for REGISTRY
        
    Returns:
        Dict: Validation report
        
    Exit Codes:
        0: All commitments valid
        13: Uncommitted reservations remain
    """
    report = {
        "validator": "validate_ingest_commitments",
        "plan_id": plan_id,
        "status": "UNKNOWN",
        "passed": False,
        "errors": []
    }
    
    try:
        ledger = ReservationLedger(plan_id, registry_root)
        
        # Check ledger exists
        if not ledger.ledger_path.exists():
            report["status"] = "NO_LEDGER"
            report["details"] = "No reservation ledger found (no reservations expected)"
            report["passed"] = True
            return report
        
        # Validate all committed
        all_committed, uncommitted = ledger.validate_all_committed()
        
        if all_committed:
            report["status"] = "PASSED"
            report["passed"] = True
            report["details"] = "All reservations committed"
            
            audit = ledger.generate_audit_report()
            report["audit"] = audit
            
            return report
        else:
            report["status"] = "FAILED_UNCOMMITTED"
            report["passed"] = False
            report["errors"].append(
                f"{len(uncommitted)} reservation(s) not committed"
            )
            report["uncommitted_ids"] = uncommitted
            return report
        
    except Exception as e:
        report["status"] = "ERROR"
        report["passed"] = False
        report["errors"].append(f"Unexpected error: {str(e)}")
        return report


def exit_code_for_report(report: Dict) -> int:
    """Convert validation report to exit code.
    
    Exit Codes:
        0: All validations passed
        13: Uncommitted reservations or errors
    """
    return 0 if report.get("passed") else 13


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate ingest commitments")
    parser.add_argument("--plan-id", required=True, help="Plan identifier")
    parser.add_argument("--registry-root", default=".", help="Registry root directory")
    
    args = parser.parse_args()
    
    # Validate
    report = validate_ingest_commitments(args.plan_id, args.registry_root)
    
    # Output
    print(json.dumps(report, indent=2))
    sys.exit(exit_code_for_report(report))
