import unittest
import json
from pathlib import Path
import shutil
import subprocess
from unittest.mock import patch, MagicMock
from datetime import UTC, datetime


from acms_controller import ACMSController
from acms_ai_adapter import AIResponse
from acms_golden_path import RunState
import jsonschema


class TestFullRun(unittest.TestCase):
    def setUp(self):
        self.test_repo_root = Path("./test_e2e_repo").resolve()
        if self.test_repo_root.exists():
            shutil.rmtree(self.test_repo_root)
        self.test_repo_root.mkdir()

        # Create a dummy src/main.py for gap analysis context
        (self.test_repo_root / "src").mkdir()
        with open(self.test_repo_root / "src" / "main.py", "w") as f:
            f.write("def foo():\n    pass\n")

        # Create dummy OVERLAP_AUTOMATION_AND_MASTER_GAP_ANALYSIS.merged.json
        # This is needed by acms_controller._phase_1_gap_discovery
        with open(
            self.test_repo_root.parent
            / "OVERLAP_AUTOMATION_AND_MASTER_GAP_ANALYSIS.merged.json",
            "w",
        ) as f:
            f.write("{}")

        # Create a dummy MINI_PIPE_orchestrator_cli.py
        # This simulates the external MINI_PIPE executable
        self.minipipe_cli_path = (
            self.test_repo_root.parent / "MINI_PIPE_orchestrator_cli.py"
        )
        with open(self.minipipe_cli_path, "w") as f:
            f.write(
                """
import json
import sys
import argparse
from pathlib import Path

parser = argparse.ArgumentParser(description="MINI_PIPE Orchestrator CLI (Dummy)")
subparsers = parser.add_subparsers(dest="command", help="Available commands")

# Subparser for the 'run' command
run_parser = subparsers.add_parser("run", help="Run an execution plan")
run_parser.add_argument("--plan", type=Path, required=True, help="Path to the execution plan JSON")
run_parser.add_argument("--phase", type=str, required=True, help="Phase identifier")
run_parser.add_argument("--project", type=str, required=True, help="Project identifier")
run_parser.add_argument("--timeout", type=int, default=3600, help="Execution timeout in seconds")

args = parser.parse_args()

if args.command == "run":
    try:
        with open(args.plan, "r") as f:
            plan = json.load(f)
    except Exception as e:
        print(f"Error loading plan: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"MINI_PIPE_CLI: Executing plan {args.plan.name} for phase {args.phase}")

    tasks_completed = 0
    for workstream in plan.get("workstreams", []):
        for step in workstream.get("steps", []):
            task_id = step.get("id", "UNKNOWN_TASK")
            print(f"Task {task_id}: completed")
            tasks_completed += 1

    print(f"MINI_PIPE_CLI: All tasks completed. Total: {tasks_completed}")
    sys.exit(0)
else:
    print(f"Unknown command: {args.command}", file=sys.stderr)
    sys.exit(1)
"""
            )
        # Make the dummy CLI executable
        import stat

        self.minipipe_cli_path.chmod(
            self.minipipe_cli_path.stat().st_mode | stat.S_IXUSR
        )

        # Load schemas for validation
        self.run_status_schema = self._load_schema("run_status.schema.json")
        self.minipipe_plan_schema = self._load_schema(
            "minipipe_execution_plan.schema.json"
        )

    def tearDown(self):
        if self.test_repo_root.exists():
            shutil.rmtree(self.test_repo_root)
        if self.minipipe_cli_path.exists():
            self.minipipe_cli_path.unlink()
        if (
            self.test_repo_root.parent
            / "OVERLAP_AUTOMATION_AND_MASTER_GAP_ANALYSIS.merged.json"
        ).exists():
            (
                self.test_repo_root.parent
                / "OVERLAP_AUTOMATION_AND_MASTER_GAP_ANALYSIS.merged.json"
            ).unlink()

    def _load_schema(self, schema_name: str):
        schema_path = Path(__file__).parent.parent.parent / "schemas" / schema_name
        if not schema_path.exists():
            self.fail(f"Schema file not found: {schema_path}")
        with open(schema_path, "r") as f:
            return json.load(f)

    @patch("acms_minipipe_adapter.MiniPipeAdapter._find_orchestrator")
    @patch("acms_controller.create_ai_adapter")
    def test_full_successful_run(self, mock_create_ai_adapter, mock_find_orchestrator):
        """
        Tests a full end-to-end run of the ACMS controller (all 50 steps).
        - Uses a mocked AI adapter.
        - Uses a dummy MINI_PIPE orchestrator CLI.
        - Verifies all generated artifacts and state transitions.
        """
        # Configure mock AI adapter to return a predictable gap report
        mock_ai_adapter_instance = MagicMock()
        mock_gap_report = {
            "version": "1.0",
            "gaps": [
                {
                    "gap_id": "E2E_GAP_001",
                    "title": "E2E Missing Docstring",
                    "description": "Docstring for foo",
                    "category": "documentation",
                    "severity": "low",
                    "file_paths": [str(self.test_repo_root / "src" / "main.py")],
                },
                {
                    "gap_id": "E2E_GAP_002",
                    "title": "E2E Security Vulnerability",
                    "description": "SQL injection risk",
                    "category": "security",
                    "severity": "critical",
                    "file_paths": [str(self.test_repo_root / "src" / "main.py")],
                },
            ],
        }
        mock_ai_adapter_instance.analyze_gaps.return_value = AIResponse(
            success=True, output=mock_gap_report, execution_time_seconds=1.0
        )
        mock_create_ai_adapter.return_value = mock_ai_adapter_instance

        # Make _find_orchestrator return the path to our dummy CLI
        mock_find_orchestrator.return_value = self.minipipe_cli_path

        # Initialize controller
        controller = ACMSController(
            repo_root=self.test_repo_root, ai_adapter_type="mock"
        )

        # We don't need to patch controller.minipipe_adapter.execute_plan
        # or set controller.minipipe_adapter.orchestrator_cli_path explicitly
        # as _find_orchestrator is mocked and the real execute_plan will be called.

        # Run the full cycle
        result = controller.run_full_cycle(mode="full")

        # Assertions
        run_dir = controller.run_dir
        self.assertTrue(run_dir.exists())

        # 1. Verify ledger (run.ledger.jsonl)
        ledger_path = run_dir / "run.ledger.jsonl"
        self.assertTrue(ledger_path.exists())
        with open(ledger_path, "r") as f:
            ledger_entries = [json.loads(line) for line in f]
            # Check for state transitions
            expected_states = [
                RunState.INIT.value,
                RunState.GAP_ANALYSIS.value,
                RunState.PLANNING.value,
                RunState.EXECUTION.value,
                RunState.SUMMARY.value,
                RunState.DONE.value,
            ]
            actual_states = [
                e["state"] for e in ledger_entries if e["event"] == "enter_state"
            ]
            self.assertListEqual(actual_states, expected_states)

        # 2. Verify run_status.json
        run_status_path = run_dir / "run_status.json"
        self.assertTrue(run_status_path.exists())
        with open(run_status_path, "r") as f:
            run_status_data = json.load(f)
            jsonschema.validate(instance=run_status_data, schema=self.run_status_schema)
            self.assertEqual(run_status_data["final_status"], "success")
            self.assertEqual(run_status_data["metrics"]["gaps_discovered"], 2)
            self.assertGreaterEqual(
                run_status_data["metrics"]["workstreams_created"], 1
            )
            self.assertGreaterEqual(
                run_status_data["metrics"]["tasks_executed"], 2
            )  # At least two tasks from two workstreams

        # 3. Verify gap_analysis_report.json
        gap_report_path = run_dir / "gap_analysis_report.json"
        self.assertTrue(gap_report_path.exists())
        with open(gap_report_path, "r") as f:
            report_data = json.load(f)
            self.assertEqual(len(report_data["gaps"]), 2)
            self.assertEqual(report_data["gaps"][0]["gap_id"], "E2E_GAP_001")

        # 4. Verify gap_registry.json
        registry_path = run_dir / "gap_registry.json"
        self.assertTrue(registry_path.exists())
        with open(registry_path, "r") as f:
            registry_data = json.load(f)
            self.assertEqual(len(registry_data["gaps"]), 2)
            self.assertEqual(
                registry_data["gaps"][0]["status"], "discovered"
            )  # Status should be DISCOVERED after initial load

        # 5. Verify workstreams.json
        workstreams_path = run_dir / "workstreams.json"
        self.assertTrue(workstreams_path.exists())
        with open(workstreams_path, "r") as f:
            workstreams_data = json.load(f)
            self.assertGreaterEqual(len(workstreams_data["workstreams"]), 1)
            self.assertIn("E2E_GAP_001", workstreams_data["workstreams"][0]["gap_ids"])

        # 6. Verify mini_pipe_execution_plan.json
        execution_plan_path = run_dir / "mini_pipe_execution_plan.json"
        self.assertTrue(execution_plan_path.exists())
        with open(execution_plan_path, "r") as f:
            plan_data = json.load(f)
            jsonschema.validate(instance=plan_data, schema=self.minipipe_plan_schema)
            self.assertGreaterEqual(len(plan_data["tasks"]), 2)
            self.assertEqual(plan_data["version"], "1.0")


if __name__ == "__main__":
    unittest.main()
