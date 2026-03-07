"""
ACMS Minimal Scenario Demo

Demonstrates the golden path with a small, controlled test repository.

This minimal scenario:
1. Uses test_repo/ (3 files, ~50 lines of code)
2. Single gap-analysis lens (minimal_gap_analysis_prompt.json)
3. Creates 1-2 workstreams
4. Executes safe, small changes
5. No triggers, no resilience, no patch ledger

Safety:
- All changes isolated to test_repo/
- No production code affected
- Easy to verify and rollback
"""

from pathlib import Path
import json
import sys

# Import ACMS controller
from src.acms.controller import ACMSController


def main():
    """Run minimal ACMS scenario"""

    print("=" * 70)
    print("ACMS MINIMAL SCENARIO - GOLDEN PATH DEMONSTRATION")
    print("=" * 70)
    print()

    # Configuration
    test_repo = Path(__file__).parent / "test_repo"

    if not test_repo.exists():
        print(f"❌ Test repository not found: {test_repo}")
        print("   Run this script from the MINI_PIPE directory")
        sys.exit(1)

    print(f"📁 Test Repository: {test_repo}")
    print(f"📊 Files:")
    for f in test_repo.rglob("*.py"):
        print(f"   - {f.relative_to(test_repo)}")
    print()

    # Show expected gaps
    print("📋 Expected Gaps to Discover:")
    print("   1. Missing docstrings (subtract, multiply, divide)")
    print("   2. Missing tests (multiply, divide)")
    print("   3. No error handling (divide by zero)")
    print("   4. No input validation")
    print()

    # Run ACMS with minimal configuration
    print("🚀 Starting ACMS Golden Path Execution...")
    print()

    # Create controller with minimal config
    controller = ACMSController(
        repo_root=test_repo,
        ai_adapter_type="mock",  # Use mock for now
        minipipe_adapter_type="mock",
        config={
            "triggers_enabled": False,
            "enable_resilience": False,
            "enable_patch_ledger": False,
            "max_concurrent_tasks": 2,
            "timeout_seconds": 300,
        },
    )

    # Run full cycle
    result = controller.run_full_cycle(mode="plan_only")  # Safe: just analyze and plan

    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print()

    # Show results
    print(f"✅ Run ID: {result['run_id']}")
    print(f"✅ Status: {result['final_status']}")
    print()

    # Show metrics
    metrics = result["metrics"]
    print("📊 Metrics:")
    print(f"   Gaps Discovered: {metrics['gaps_discovered']}")
    print(f"   Workstreams Created: {metrics['workstreams_created']}")
    print(
        f"   Tasks Planned: {metrics.get('tasks_executed', 0)}"
    )  # Will be 0 in plan_only mode
    print()

    # Show artifacts
    print("📄 Artifacts:")
    for name, path in result["artifacts"].items():
        if path:
            print(f"   {name}: {path}")
    print()

    # Show ledger summary
    print("📜 State Transitions:")
    for transition in result["state_transitions"]:
        print(f"   {transition['state']}")
    print()

    print("=" * 70)
    print("✅ Minimal scenario completed successfully!")
    print()
    print("Next steps:")
    print("  1. Review run_status.json in the run directory")
    print("  2. Check run.ledger.jsonl for detailed events")
    print("  3. Examine workstreams.json for planned changes")
    print("  4. Run with mode='full' to execute changes (mock adapter)")
    print("=" * 70)


if __name__ == "__main__":
    main()
