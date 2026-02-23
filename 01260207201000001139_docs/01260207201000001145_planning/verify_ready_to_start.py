#!/usr/bin/env python3
"""
Pre-Implementation Verification Script
Validates all prerequisites before starting planning loop implementation
"""

import sys
import subprocess
from pathlib import Path
import re

def check(name: str, condition: bool, details: str = "") -> bool:
    """Print check result and return status"""
    status = "✓" if condition else "✗"
    print(f"[{status}] {name}")
    if details:
        print(f"    {details}")
    return condition

def main():
    print("=" * 70)
    print("Planning Loop Implementation - Pre-Start Verification")
    print("=" * 70)
    print()
    
    all_passed = True
    
    # 1. Template files exist
    print("[1/9] Template Source Files")
    template_v3 = Path("C:/Users/richg/Gov_Reg/newPhasePlanProcess/01260207201000000510_NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3.json")
    tech_spec_v3 = Path("C:/Users/richg/Gov_Reg/newPhasePlanProcess/01260207201000000180_NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3.json")
    
    all_passed &= check("Template V3 exists", template_v3.exists(), str(template_v3))
    all_passed &= check("Tech Spec V3 exists", tech_spec_v3.exists(), str(tech_spec_v3))
    print()
    
    # 2. Python version
    print("[2/9] Python Version")
    try:
        result = subprocess.run(["python", "--version"], capture_output=True, text=True)
        version_match = re.search(r'Python 3\.(10|11|12)', result.stdout)
        all_passed &= check("Python 3.10+", version_match is not None, result.stdout.strip())
    except Exception as e:
        all_passed &= check("Python 3.10+", False, str(e))
    print()
    
    # 3. Git version
    print("[3/9] Git Version")
    try:
        result = subprocess.run(["git", "--version"], capture_output=True, text=True)
        version_match = re.search(r'git version 2\.([4-9]\d|[5-9]\d)', result.stdout)
        all_passed &= check("Git 2.40+", version_match is not None, result.stdout.strip())
    except Exception as e:
        all_passed &= check("Git 2.40+", False, str(e))
    print()
    
    # 4. State directory isolation
    print("[4/9] State Directory Strategy")
    state_exists = Path(".state").exists()
    planning_state_exists = Path(".planning_loop_state").exists()
    
    check("Existing .state/ found", state_exists, "Governance tools use this (preserved)")
    check(".planning_loop_state/ not yet created", not planning_state_exists, "Planning loop will create this (isolated)")
    print()
    
    # 5. Plan document consistency
    print("[5/9] Plan Document Consistency")
    plan_file = Path("01260207201000001139_docs/01260207201000001145_planning/PLANNING_LOOP_IMPLEMENTATION_PLAN.md")
    
    if plan_file.exists():
        content = plan_file.read_text(encoding='utf-8')
        all_passed &= check("Version 2.0 declared", "Version 2.0" in content)
        all_passed &= check("GATE-009 present", "GATE-009" in content or "GATE-009:" in content)
        all_passed &= check("14 fields specified", "14 required fields" in content)
        all_passed &= check("State directory isolated", ".planning_loop_state/" in content)
    else:
        all_passed &= check("Plan file exists", False, str(plan_file))
    print()
    
    # 6. Required Python packages (check if available)
    print("[6/9] Python Packages (optional check)")
    packages = ["jsonschema", "jsonpatch", "click", "yaml", "rich"]
    for pkg in packages:
        try:
            __import__(pkg if pkg != "yaml" else "yaml")
            check(f"{pkg} installed", True)
        except ImportError:
            check(f"{pkg} installed", False, "Run: pip install -r requirements.txt")
    print()
    
    # 7. OpenAI API key (optional)
    print("[7/9] OpenAI API (optional for LLM mode)")
    import os
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        check("OpenAI API key found", True, "LLM mode available")
    else:
        check("OpenAI API key not found", True, "Deterministic mode only (OK)")
    print()
    
    # 8. Git repository status
    print("[8/9] Git Repository Status")
    try:
        result = subprocess.run(["git", "rev-parse", "--git-dir"], capture_output=True, text=True)
        in_git_repo = result.returncode == 0
        all_passed &= check("Git repository", in_git_repo)
        
        if in_git_repo:
            result = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True)
            current_branch = result.stdout.strip()
            check("Current branch", True, current_branch)
            
            if current_branch != "feature/planning-loop":
                print("    💡 Recommendation: git checkout -b feature/planning-loop")
    except Exception as e:
        all_passed &= check("Git repository", False, str(e))
    print()
    
    # 9. Disk space
    print("[9/9] Disk Space")
    try:
        import shutil
        stat = shutil.disk_usage(".")
        free_gb = stat.free / (1024**3)
        all_passed &= check("Disk space >= 10 GB", free_gb >= 10, f"{free_gb:.1f} GB free")
    except Exception as e:
        check("Disk space check", False, str(e))
    print()
    
    # Summary
    print("=" * 70)
    if all_passed:
        print("✅ ALL CHECKS PASSED - READY TO START IMPLEMENTATION")
        print()
        print("Next steps:")
        print("1. git checkout -b feature/planning-loop")
        print("2. mkdir -p schemas tests/schemas src/plan_refine_cli config prompts scripts")
        print("3. Start Week 1, Day 1: Create schemas/PLAN.schema.json")
        print()
        return 0
    else:
        print("❌ SOME CHECKS FAILED - FIX ISSUES BEFORE STARTING")
        print()
        print("Review output above for details.")
        print()
        return 1

if __name__ == "__main__":
    sys.exit(main())
