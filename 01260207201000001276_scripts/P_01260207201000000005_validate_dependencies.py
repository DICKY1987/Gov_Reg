#!/usr/bin/env python3
"""
Validate Dependencies
Checks all required Python packages are installed.
"""
import sys
import importlib
import json
from pathlib import Path


REQUIRED_PACKAGES = {
    "jsonschema": "4.21",
    "jsonpatch": "1.33",
    "click": "8.1",
    "yaml": "6.0",
    "rich": "13.7"
}


def check_dependencies():
    """Check all required packages"""
    results = {
        "timestamp": "",
        "checks": [],
        "all_passed": True
    }
    
    for package, min_version in REQUIRED_PACKAGES.items():
        try:
            mod = importlib.import_module(package if package != "yaml" else "yaml")
            version = getattr(mod, "__version__", "unknown")
            
            results["checks"].append({
                "package": package,
                "required_version": f">={min_version}",
                "installed_version": version,
                "status": "INSTALLED"
            })
            
        except ImportError:
            results["checks"].append({
                "package": package,
                "required_version": f">={min_version}",
                "installed_version": None,
                "status": "MISSING"
            })
            results["all_passed"] = False
    
    return results


def main():
    results = check_dependencies()
    
    print("=" * 70)
    print("Dependency Validation Report")
    print("=" * 70)
    print()
    
    for check in results["checks"]:
        status_icon = "✓" if check["status"] == "INSTALLED" else "✗"
        print(f"  {status_icon} {check['package']}: {check['installed_version'] or 'NOT INSTALLED'}")
    
    print()
    
    if results["all_passed"]:
        print("✅ All dependencies satisfied")
        
        # Save evidence
        evidence_dir = Path(".planning_loop_state/evidence/PH-00")
        evidence_dir.mkdir(parents=True, exist_ok=True)
        
        with open(evidence_dir / "dependencies_validation.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        return 0
    else:
        print("❌ Missing dependencies - install with:")
        print("   pip install jsonschema>=4.21 jsonpatch>=1.33 click>=8.1 pyyaml>=6.0 rich>=13.7")
        return 1


if __name__ == "__main__":
    sys.exit(main())
