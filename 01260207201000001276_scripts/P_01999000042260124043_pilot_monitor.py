"""Pilot monitoring and validation utility.

FILE_ID: 01999000042260124043
DOC_ID: P_01999000042260124043

Monitors pilot execution and provides metrics for rollout decisions.
"""
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent / "govreg_core"))

from P_01999000042260124030_shared_utils import atomic_json_read
from P_01999000042260124032_reservation_ledger import ReservationLedger


def generate_pilot_report():
    """Generate comprehensive pilot metrics report using atomic reads."""
    reservations_dir = Path("REGISTRY/reservations")
    
    if not reservations_dir.exists():
        print("No reservations found - pilot has not started")
        return {
            "status": "NO_DATA",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Scan all ledgers
    ledgers = list(reservations_dir.glob("RES-*.json"))
    
    metrics = {
        "timestamp": datetime.utcnow().isoformat(),
        "total_plans": len(ledgers),
        "plans_passed": 0,
        "plans_failed": 0,
        "total_reservations": 0,
        "total_committed": 0,
        "total_uncommitted": 0,
        "failed_details": [],  # Capture failure reasons
        "plans": []
    }
    
    for ledger_path in sorted(ledgers):
        try:
            # Use atomic read to avoid partial reads
            ledger_data = atomic_json_read(ledger_path)
            
            plan_id = ledger_data.get("plan_id")
            entries = ledger_data.get("entries", {})
            
            committed_count = sum(1 for e in entries.values() if e.get("state") == "COMMITTED")
            uncommitted_count = len(entries) - committed_count
            all_committed = uncommitted_count == 0
            
            plan_status = "PASSED" if all_committed else "FAILED"
            
            plan_info = {
                "plan_id": plan_id,
                "total_files": len(entries),
                "committed": committed_count,
                "uncommitted": uncommitted_count,
                "status": plan_status,
                "created_at": ledger_data.get("created_at"),
                "updated_at": ledger_data.get("updated_at")
            }
            
            # Capture failure details
            if not all_committed:
                uncommitted_ids = [
                    fid for fid, e in entries.items()
                    if e.get("state") != "COMMITTED"
                ]
                plan_info["uncommitted_ids"] = uncommitted_ids
                metrics["failed_details"].append({
                    "plan_id": plan_id,
                    "reason": f"{len(uncommitted_ids)} uncommitted files",
                    "uncommitted_ids": uncommitted_ids
                })
            
            metrics["plans"].append(plan_info)
            
            metrics["total_reservations"] += len(entries)
            metrics["total_committed"] += committed_count
            metrics["total_uncommitted"] += uncommitted_count
            
            if all_committed:
                metrics["plans_passed"] += 1
            else:
                metrics["plans_failed"] += 1
        
        except Exception as e:
            metrics["failed_details"].append({
                "ledger_path": str(ledger_path),
                "error": f"Failed to read ledger: {str(e)}"
            })
            print(f"Warning: Could not read {ledger_path}: {e}")
    
    # Calculate pass rate
    if metrics["total_plans"] > 0:
        metrics["pass_rate"] = (metrics["plans_passed"] / metrics["total_plans"]) * 100
    else:
        metrics["pass_rate"] = 0
    
    return metrics


def generate_readiness_report():
    """Generate rollout readiness assessment."""
    report = generate_pilot_report()
    
    if report.get("status") == "NO_DATA":
        return {
            "status": "NOT_STARTED",
            "recommendation": "Pilot has not begun",
            "ready_for_production": False
        }
    
    total = report["total_plans"]
    passed = report["plans_passed"]
    pass_rate = report.get("pass_rate", 0)
    
    success_criteria = {
        "ten_plans_completed": total >= 10,
        "hundred_percent_pass": pass_rate == 100.0,
        "zero_uncommitted": report["total_uncommitted"] == 0,
        "all_validated": passed == total
    }
    
    all_met = all(success_criteria.values())
    
    readiness = {
        "timestamp": datetime.utcnow().isoformat(),
        "success_criteria_met": success_criteria,
        "all_criteria_met": all_met,
        "ready_for_production": all_met,
        "summary": {
            "plans_completed": total,
            "pass_rate": f"{pass_rate:.1f}%",
            "total_files_reserved": report["total_reservations"],
            "total_files_committed": report["total_committed"],
            "uncommitted_files": report["total_uncommitted"]
        },
        "recommendation": (
            "PROCEED TO PRODUCTION" if all_met
            else "CONTINUE PILOT" if total < 10
            else "INVESTIGATE FAILURES"
        )
    }
    
    return readiness


if __name__ == "__main__":
    print("=" * 70)
    print("PILOT MONITORING REPORT")
    print("=" * 70)
    
    metrics = generate_pilot_report()
    print("\nMetrics:")
    print(json.dumps(metrics, indent=2))
    
    print("\n" + "=" * 70)
    print("READINESS ASSESSMENT")
    print("=" * 70)
    
    readiness = generate_readiness_report()
    print(json.dumps(readiness, indent=2))
    
    if readiness["ready_for_production"]:
        print("\n✓ READY FOR PRODUCTION CUTOVER")
    else:
        print(f"\n→ ACTION: {readiness['recommendation']}")
