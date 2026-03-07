#!/usr/bin/env python3
"""Phase 1 Quick Wins Validation Script

Validates that all Phase 1 components are properly installed and configured.
"""

import sys
from pathlib import Path
from typing import List, Tuple


def check_file_exists(path: Path, description: str) -> Tuple[bool, str]:
    """Check if a file exists"""
    if path.exists():
        return True, f"✓ {description}"
    return False, f"✗ {description} - NOT FOUND: {path}"


def check_import(module: str, description: str) -> Tuple[bool, str]:
    """Check if a Python module can be imported"""
    try:
        __import__(module)
        return True, f"✓ {description}"
    except ImportError as e:
        return False, f"✗ {description} - IMPORT ERROR: {e}"


def validate_phase1() -> List[Tuple[bool, str]]:
    """Run all Phase 1 validation checks"""
    results = []
    base_dir = Path(__file__).parent

    # Check GitHub Actions workflows
    results.append(
        check_file_exists(
            base_dir / ".github" / "workflows" / "acms-pipeline.yml",
            "ACMS Pipeline workflow",
        )
    )
    results.append(
        check_file_exists(base_dir / ".github" / "workflows" / "ci.yml", "CI workflow")
    )
    results.append(
        check_file_exists(
            base_dir / ".github" / "workflows" / "lint.yml", "Lint workflow"
        )
    )

    # Check notification system
    results.append(
        check_file_exists(
            base_dir / "src" / "acms" / "notifications.py", "Notification system module"
        )
    )
    results.append(check_import("src.acms.notifications", "Notification system import"))

    # Check monitoring system
    results.append(
        check_file_exists(
            base_dir / "src" / "acms" / "monitoring.py", "Monitoring system module"
        )
    )
    results.append(check_import("src.acms.monitoring", "Monitoring system import"))

    # Check pre-commit config
    results.append(
        check_file_exists(
            base_dir / ".pre-commit-config.yaml", "Pre-commit configuration"
        )
    )

    # Check requirements.txt
    results.append(
        check_file_exists(base_dir / "requirements.txt", "Requirements file")
    )

    # Check documentation
    results.append(
        check_file_exists(
            base_dir / "docs" / "PHASE1_QUICK_WINS_IMPLEMENTATION.md",
            "Phase 1 documentation",
        )
    )

    # Check controller integration
    try:
        with open(
            base_dir / "src" / "acms" / "controller.py",
            "r",
            encoding="utf-8",
            errors="ignore",
        ) as f:
            content = f.read()
            has_notif = "from src.acms.notifications import" in content
            has_monitor = "from src.acms.monitoring import" in content

            if has_notif and has_monitor:
                results.append((True, "✓ Controller monitoring integration"))
            else:
                results.append((False, "✗ Controller missing monitoring imports"))
    except Exception as e:
        results.append((False, f"✗ Controller integration check failed: {e}"))

    return results


def main():
    """Main validation entry point"""
    print("=" * 70)
    print("PHASE 1 QUICK WINS VALIDATION")
    print("=" * 70)
    print()

    results = validate_phase1()

    passed = sum(1 for success, _ in results if success)
    total = len(results)

    for success, message in results:
        print(message)

    print()
    print("=" * 70)
    print(f"RESULTS: {passed}/{total} checks passed")
    print("=" * 70)

    if passed == total:
        print()
        print("✅ All Phase 1 components validated successfully!")
        print()
        print("Next steps:")
        print("  1. Install pre-commit: pip install pre-commit && pre-commit install")
        print("  2. Run tests: pytest tests/")
        print("  3. Test workflows: gh workflow run acms-pipeline.yml")
        print("  4. Configure notifications (optional):")
        print('     export ACMS_SLACK_WEBHOOK="..."')
        print('     export ACMS_GITHUB_REPO="owner/repo"')
        print()
        return 0
    else:
        print()
        print("❌ Some Phase 1 components are missing or misconfigured.")
        print("Please review the errors above and fix any issues.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
