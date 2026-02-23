#!/usr/bin/env python3
"""
Check Permissions
Validates filesystem write permissions and network access.
"""
import sys
import json
import tempfile
from pathlib import Path
import urllib.request


def check_permissions():
    """Check filesystem and network permissions"""
    results = {
        "checks": [],
        "all_passed": True
    }
    
    # Check filesystem write
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=True) as f:
            f.write("test")
        
        results["checks"].append({
            "permission": "Filesystem Write",
            "status": "OK",
            "error": None
        })
    except Exception as e:
        results["checks"].append({
            "permission": "Filesystem Write",
            "status": "FAILED",
            "error": str(e)
        })
        results["all_passed"] = False
    
    # Check network access (optional - for LLM mode)
    try:
        # Try to connect to a public DNS server
        urllib.request.urlopen("https://www.google.com", timeout=5)
        
        results["checks"].append({
            "permission": "Network Access",
            "status": "OK",
            "error": None
        })
    except Exception as e:
        # Network failure is not critical in deterministic mode
        results["checks"].append({
            "permission": "Network Access",
            "status": "LIMITED",
            "error": str(e),
            "note": "LLM mode will not be available"
        })
    
    return results


def main():
    results = check_permissions()
    
    print("=" * 70)
    print("Permission Check Report")
    print("=" * 70)
    print()
    
    for check in results["checks"]:
        status_icon = "✓" if check["status"] == "OK" else ("⚠" if check["status"] == "LIMITED" else "✗")
        print(f"  {status_icon} {check['permission']}: {check['status']}")
        if check.get("note"):
            print(f"    Note: {check['note']}")
    
    print()
    
    if results["all_passed"]:
        print("✅ All permission checks passed")
    else:
        print("⚠️ Some checks failed - review above")
    
    # Save evidence
    evidence_dir = Path(".planning_loop_state/evidence/PH-00")
    evidence_dir.mkdir(parents=True, exist_ok=True)
    
    with open(evidence_dir / "permissions_check.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    return 0 if results["all_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
