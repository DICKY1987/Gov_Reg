import unittest
import json
from pathlib import Path
import shutil
from unittest.mock import patch, MagicMock
from datetime import UTC, datetime
import re


from acms_controller import ACMSController
from acms_ai_adapter import AIResponse
from acms_minipipe_adapter import ExecutionResult
from acms_golden_path import RunState
import jsonschema
import importlib
import acms_controller


class TestFailurePaths(unittest.TestCase):
    def setUp(self):
        self.test_repo_root = Path("./test_failure_repo").resolve()
        if self.test_repo_root.exists():
            shutil.rmtree(self.test_repo_root)
        self.test_repo_root.mkdir()

        (self.test_repo_root / "src").mkdir()
        with open(self.test_repo_root / "src" / "main.py", "w") as f:
            f.write("def foo():\n    pass\n")

        self.prompt_file_path = (
            Path(__file__).parent.parent.parent
            / "OVERLAP_AUTOMATION_AND_MASTER_GAP_ANALYSIS.merged.json"
        )
        with open(self.prompt_file_path, "w") as f:
            f.write("{}")

        self.run_status_schema = self._load_schema("run_status.schema.json")
        self.minipipe_plan_schema = self._load_schema(
            "minipipe_execution_plan.schema.json"
        )

        # Reload the acms_controller module to ensure latest changes are picked up
        importlib.reload(acms_controller)

    def tearDown(self):
        if self.test_repo_root.exists():
            shutil.rmtree(self.test_repo_root)
        if self.prompt_file_path.exists():
            self.prompt_file_path.unlink()

    def _load_schema(self, schema_name: str):
        schema_path = Path(__file__).parent.parent.parent / "schemas" / schema_name
        if not schema_path.exists():
            self.fail(f"Schema file not found: {schema_path}")
        with open(schema_path, "r") as f:
            return json.load(f)

    @patch("acms_controller.create_minipipe_adapter")
    @patch("acms_controller.create_ai_adapter")
    def test_ai_adapter_malformed_response(
        self, mock_create_ai_adapter, mock_create_minipipe_adapter
    ):
        """
        Tests failure scenario: AI adapter returns malformed JSON.
        Expected: Pipeline fails, controller state is FAILED, error logged.
        """
        mock_ai_adapter_instance = MagicMock()
        mock_ai_adapter_instance.analyze_gaps.return_value = AIResponse(
            success=True,
            output={"malformed_key": "not_a_gap_report"},
            execution_time_seconds=1.0,
        )
        mock_create_ai_adapter.return_value = mock_ai_adapter_instance

        mock_minipipe_adapter_instance = MagicMock()
        mock_minipipe_adapter_instance.execute_plan.return_value = ExecutionResult(
            success=True,
            tasks_completed=0,
            tasks_failed=0,
            tasks_skipped=0,
            execution_time_seconds=0.0,
        )
        mock_create_minipipe_adapter.return_value = mock_minipipe_adapter_instance

        controller = ACMSController(
            repo_root=self.test_repo_root,
            ai_adapter_type="mock",
            minipipe_adapter_type="mock",
        )

        controller.run_full_cycle(mode="full")

        self.assertEqual(controller.current_state.value, "failed")
        # Ensure run_status_data is loaded *after* run_full_cycle for assertion
        run_dir = controller.run_dir
        run_status_path = run_dir / "run_status.json"
        self.assertTrue(run_status_path.exists())
        with open(run_status_path, "r") as f:
            run_status_data = json.load(f)

        self.assertEqual(run_status_data["final_status"], "failed")
        self.assertIn("error", run_status_data)
        self.assertIn(
            "Gap report 'gaps' field must be a list.", run_status_data["error"]
        )

    @patch("acms_controller.create_minipipe_adapter")
    @patch("acms_controller.create_ai_adapter")
    def test_minipipe_execution_failure(
        self, mock_create_ai_adapter, mock_create_minipipe_adapter
    ):
        """
        Tests failure scenario: MINI_PIPE execution fails.
        Expected: Pipeline fails, controller state is FAILED, error logged.
        """
        # --- Mock AI Adapter (successful gap analysis) ---
        mock_ai_adapter_instance = MagicMock()
        mock_gap_report = {
            "version": "1.0",
            "gaps": [
                {
                    "gap_id": "E2E_FAILURE_001",
                    "title": "Failure Test Gap",
                    "description": "Gap for failure test.",
                    "category": "testing",
                    "severity": "high",
                    "file_paths": [str(self.test_repo_root / "src" / "main.py")],
                }
            ],
        }
        mock_ai_adapter_instance.analyze_gaps.return_value = AIResponse(
            success=True, output=mock_gap_report, execution_time_seconds=1.0
        )
        mock_create_ai_adapter.return_value = mock_ai_adapter_instance

        mock_create_minipipe_adapter.return_value = (
            MagicMock()
        )  # Still need to mock this for ACMSController init

        controller = ACMSController(
            repo_root=self.test_repo_root,
            ai_adapter_type="mock",
            minipipe_adapter_type="mock",
        )

        # Create a dummy mini_pipe_execution_plan.json for the controller to find
        run_dir = controller.run_dir
        run_dir.mkdir(parents=True, exist_ok=True)  # Ensure run_dir exists
        dummy_plan_path = run_dir / "mini_pipe_execution_plan.json"
        with open(dummy_plan_path, "w") as f:
            json.dump(
                {"plan_id": "dummy", "name": "dummy", "version": "1.0", "tasks": []}, f
            )

        # Patch the _phase_4_execution instance method directly
        with patch.object(
            controller,
            "_phase_4_execution",
            side_effect=RuntimeError("Simulated MINI_PIPE execution error"),
        ) as mock_phase_4_execution:
            controller.run_full_cycle(mode="full")
            mock_phase_4_execution.assert_called_once()  # Verify it was called

        self.assertEqual(controller.current_state.value, "failed")
        run_dir = controller.run_dir
        run_status_path = run_dir / "run_status.json"
        self.assertTrue(run_status_path.exists())
        with open(run_status_path, "r") as f:
            run_status_data = json.load(f)
            self.assertEqual(run_status_data["final_status"], "failed")
            self.assertIn(
                "Simulated MINI_PIPE execution error", run_status_data["error"]
            )


if __name__ == "__main__":
    unittest.main()
