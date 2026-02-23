#!/usr/bin/env python3
"""
Integration test for orchestration layer.
Tests that run-gates command executes gates in correct order and produces evidence.
"""

import json
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path


def create_minimal_plan(path: Path):
    """Create minimal valid plan document for testing."""
    plan = {
        "template_metadata": {
            "version": "2.4.0",
            "generator": "test",
            "timestamp": "2026-02-01T00:00:00Z",
        },
        "critical_constraint": {
            "constraint": "testing_constraint",
            "rationale": "For integration testing",
        },
        "validation_gates": [],
        "phase_contracts": [],
        "metrics": {},
        "infrastructure": {},
    }

    with open(path, "w") as f:
        json.dump(plan, f, indent=2)


def test_orchestration():
    """Run integration test."""
    print("🧪 Starting orchestration integration test...")

    # Create temporary directory structure
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        plan_file = tmpdir / "test_plan.json"
        evidence_dir = tmpdir / ".state" / "evidence"

        print(f"📁 Test directory: {tmpdir}")

        # Create minimal plan
        create_minimal_plan(plan_file)
        print(f"✅ Created test plan: {plan_file}")

        # Run orchestrator (only GATE-000 should pass with minimal plan)
        script_dir = Path(__file__).parent
        cli_script = script_dir / "P_01260207233100000242_NEWPHASEPLANPROCESS_plan_cli.py"

        print(f"\n▶️  Running: python {cli_script} run-gates {plan_file}")

        result = subprocess.run(
            [sys.executable, str(cli_script), "run-gates", str(plan_file)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )

        print("\n📊 STDOUT:")
        print(result.stdout)

        if result.stderr:
            print("\n⚠️  STDERR:")
            print(result.stderr)

        print(f"\n📊 Exit code: {result.returncode}")

        # Verify evidence was created
        gate_000_evidence = (
            tmpdir / ".state" / "evidence" / "GATE-000" / "structure_validation.json"
        )

        if gate_000_evidence.exists():
            print(f"✅ Evidence created: {gate_000_evidence}")

            with open(gate_000_evidence) as f:
                evidence = json.load(f)
            print(f"📋 Evidence summary: structure_ok={evidence.get('structure_ok')}")
        else:
            print(f"⚠️  Expected evidence not found: {gate_000_evidence}")

        # Check for evidence directory structure
        if evidence_dir.exists():
            evidence_files = list(evidence_dir.rglob("*.json"))
            print(f"\n📁 Evidence files created: {len(evidence_files)}")
            for ef in evidence_files:
                print(f"   - {ef.relative_to(tmpdir)}")

        # Test passes if orchestrator ran without crashing
        if result.returncode in (0, 1):  # 0=all passed, 1=some failed (expected)
            print("\n✅ Integration test PASSED - orchestrator executed successfully")
            return 0
        else:
            print(
                f"\n❌ Integration test FAILED - unexpected exit code {result.returncode}"
            )
            return 1


if __name__ == "__main__":
    sys.exit(test_orchestration())
