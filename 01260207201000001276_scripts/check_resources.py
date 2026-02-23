#!/usr/bin/env python3
"""
Check Resources
Validates system has sufficient resources for planning loop.
"""
import sys
import json
import psutil
from pathlib import Path


def check_resources():
    """Check system resources"""
    results = {
        "checks": [],
        "all_passed": True
    }
    
    # Check RAM
    mem = psutil.virtual_memory()
    ram_gb = mem.total / (1024 ** 3)
    ram_available_gb = mem.available / (1024 ** 3)
    
    ram_check = {
        "resource": "RAM",
        "total_gb": round(ram_gb, 1),
        "available_gb": round(ram_available_gb, 1),
        "required_gb": 8,
        "passed": ram_gb >= 8
    }
    results["checks"].append(ram_check)
    
    if not ram_check["passed"]:
        results["all_passed"] = False
    
    # Check Disk Space
    disk = psutil.disk_usage('.')
    disk_free_gb = disk.free / (1024 ** 3)
    
    disk_check = {
        "resource": "Disk Space",
        "free_gb": round(disk_free_gb, 1),
        "required_gb": 10,
        "passed": disk_free_gb >= 10
    }
    results["checks"].append(disk_check)
    
    if not disk_check["passed"]:
        results["all_passed"] = False
    
    return results


def main():
    results = check_resources()
    
    print("=" * 70)
    print("Resource Check Report")
    print("=" * 70)
    print()
    
    for check in results["checks"]:
        status_icon = "✓" if check["passed"] else "✗"
        
        if check["resource"] == "RAM":
            print(f"  {status_icon} RAM: {check['total_gb']} GB total, {check['available_gb']} GB available (required: {check['required_gb']} GB)")
        elif check["resource"] == "Disk Space":
            print(f"  {status_icon} Disk: {check['free_gb']} GB free (required: {check['required_gb']} GB)")
    
    print()
    
    if results["all_passed"]:
        print("✅ All resource checks passed")
        
        # Save evidence
        evidence_dir = Path(".planning_loop_state/evidence/PH-00")
        evidence_dir.mkdir(parents=True, exist_ok=True)
        
        with open(evidence_dir / "resources_check.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        return 0
    else:
        print("❌ Insufficient resources")
        return 1


if __name__ == "__main__":
    sys.exit(main())
