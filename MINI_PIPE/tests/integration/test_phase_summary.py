import unittest
import json
from pathlib import Path
import shutil
from unittest.mock import patch, MagicMock
from datetime import UTC, datetime


from acms_controller import ACMSController
from acms_minipipe_adapter import ExecutionResult, TaskResult
from gap_registry import GapRegistry, GapRecord, GapStatus, GapSeverity
import jsonschema
from acms_golden_path import RunState


class TestPhaseSummary(unittest.TestCase):
    def setUp(self):
        self.test_repo_root = Path("./test_summary_repo").resolve()
        if self.test_repo_root.exists():
            shutil.rmtree(self.test_repo_root)
        self.test_repo_root.mkdir()

        self.run_id = "test_summary_run"
        self.run_dir = self.test_repo_root / ".acms_runs" / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)

        # Pre-create dummy gap_registry.json
        self.mock_registry = GapRegistry(self.run_dir / "gap_registry.json")
        self.mock_registry.add_gap(
            GapRecord(
                "G1", "T1", "D1", "auth", GapSeverity.CRITICAL, GapStatus.RESOLVED, "t"
            )
        )
        self.mock_registry.add_gap(
            GapRecord(
                "G2", "T2", "D2", "perf", GapSeverity.HIGH, GapStatus.DISCOVERED, "t"
            )
        )
        self.mock_registry.add_gap(
            GapRecord(
                "G3", "T3", "D3", "auth", GapSeverity.MEDIUM, GapStatus.IN_PROGRESS, "t"
            )
        )
        self.mock_registry.save()

        # Pre-create dummy mini_pipe_execution_plan.json
        self.execution_plan_path = self.run_dir / "mini_pipe_execution_plan.json"
        self.dummy_plan = {
            "plan_id": "dummy_plan",
            "name": "Dummy Execution Plan",
            "version": "1.0",
            "tasks": [
                {"task_id": "TASK_0001", "task_kind": "analysis"},
                {"task_id": "TASK_0002", "task_kind": "implementation"},
                {"task_id": "TASK_0003", "task_kind": "test"},
            ],
        }
        with open(self.execution_plan_path, "w") as f:
            json.dump(self.dummy_plan, f)

        # Load run_status schema for validation
        self.run_status_schema_path = (
            Path(__file__).parent.parent.parent / "schemas" / "run_status.schema.json"
        )
        if not self.run_status_schema_path.exists():
            self.fail(
                f"Run status schema file not found at {self.run_status_schema_path}"
            )
        with open(self.run_status_schema_path, "r") as f:
            self.run_status_schema = json.load(f)

    def tearDown(self):
        if self.test_repo_root.exists():
            shutil.rmtree(self.test_repo_root)

    @patch("acms_controller.create_ai_adapter")
    @patch("acms_controller.create_minipipe_adapter")
    @patch("acms_controller.GapRegistry")
    def test_summary_phase(
        self, MockGapRegistry, mock_create_minipipe_adapter, mock_create_ai_adapter
    ):
        """
        Tests the summary phase (Steps 43-50) in an integrated way.
        - Manually sets up controller state and gap registry as if preceding phases completed.
        - Verifies generation and content of run_status.json and summary_report.json.
        """
        # Mock implementations for the patched methods
        mock_create_ai_adapter.return_value = MagicMock()
        mock_create_minipipe_adapter.return_value = MagicMock()

        # Configure MockGapRegistry to return our pre-populated one
        MockGapRegistry.return_value = self.mock_registry

        # Initialize controller
        controller = ACMSController(
            repo_root=self.test_repo_root, run_id=self.run_id, ai_adapter_type="mock"
        )

        # Manually populate controller.state to simulate completed phases
        controller.state = {
            "run_id": self.run_id,
            "repo_root": str(self.test_repo_root),
            "started_at": datetime.now(UTC).isoformat(),
            "current_state": "execution",  # Simulates being in execution state
            "phases_completed": [
                "PHASE_0_RUN_CONFIG",
                "PHASE_1_GAP_DISCOVERY",
                "PHASE_2_GAP_CONSOLIDATION_AND_CLUSTERING",
                "PHASE_3_PLAN_GENERATION",
                "PHASE_4_PHASE_EXECUTION_MINI_PIPE",
            ],
            "ai_adapter_type": "mock",
            "minipipe_adapter_type": "auto",
            "config": {},
            "gap_count": len(self.mock_registry.gaps),  # Total gaps
            "workstream_count": 2,  # Example value
            "task_count": 3,  # Example value
            "tasks_completed": 2,  # Simulating MINI_PIPE results
            "tasks_failed": 1,  # Simulating MINI_PIPE results
            "execution_plan_path": str(self.execution_plan_path),
        }
        controller.current_state = RunState.EXECUTION  # Set the actual RunState enum

        # Directly call summary and finalize methods
        controller._phase_5_summary()
        controller._finalize_run("success")  # Should transition to DONE
        controller.current_state = (
            RunState.DONE
        )  # Explicitly set final state for assertion

        # Assertions
        # 1. Verify run_status.json was created (Step 48)
        run_status_path = self.run_dir / "run_status.json"
        self.assertTrue(run_status_path.exists())
        with open(run_status_path, "r") as f:
            run_status_data = json.load(f)

            # Validate against schema (Step 47)
            try:
                jsonschema.validate(
                    instance=run_status_data, schema=self.run_status_schema
                )
            except jsonschema.ValidationError as e:
                self.fail(f"Generated run_status.json failed schema validation: {e}")

            # Verify metrics (Step 47-48)
            self.assertEqual(
                run_status_data["metrics"]["gaps_discovered"],
                len(self.mock_registry.gaps),
            )
            self.assertEqual(
                run_status_data["metrics"]["gaps_resolved"], 1
            )  # G1 is resolved
            self.assertEqual(
                run_status_data["metrics"]["tasks_executed"], 2
            )  # From controller.state
            self.assertEqual(
                run_status_data["metrics"]["tasks_failed"], 1
            )  # From controller.state
            self.assertEqual(run_status_data["final_status"], "success")

        # 2. Verify summary_report.json was created (Step 48)
        summary_report_path = self.run_dir / "summary_report.json"
        self.assertTrue(summary_report_path.exists())
        with open(summary_report_path, "r") as f:
            summary_data = json.load(f)
            self.assertEqual(summary_data["run_id"], self.run_id)
            self.assertEqual(
                summary_data["gap_stats"]["total"], len(self.mock_registry.gaps)
            )
            self.assertEqual(summary_data["gap_stats"]["by_status"]["resolved"], 1)

        # 3. Verify the controller reached the DONE state (Step 50)
        self.assertEqual(controller.current_state.value, "done")
        self.assertEqual(controller.state["final_status"], "success")


if __name__ == "__main__":
    unittest.main()
