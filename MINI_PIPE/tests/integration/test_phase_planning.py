import unittest
import json
from pathlib import Path
import shutil
from unittest.mock import patch, MagicMock


from acms_controller import ACMSController
from gap_registry import GapRegistry, GapRecord, GapStatus, GapSeverity
from phase_plan_compiler import MiniPipeExecutionPlan
import jsonschema


class TestPhasePlanning(unittest.TestCase):
    def setUp(self):
        self.test_repo_root = Path("./test_planning_repo").resolve()
        if self.test_repo_root.exists():
            shutil.rmtree(self.test_repo_root)
        self.test_repo_root.mkdir()

        # Create a mock GapRegistry with some gaps
        self.mock_registry = GapRegistry()
        self.mock_registry.add_gap(
            GapRecord(
                "G1",
                "T1",
                "D1",
                "auth",
                GapSeverity.CRITICAL,
                GapStatus.DISCOVERED,
                "t",
                file_paths=["src/auth.py"],
            )
        )
        self.mock_registry.add_gap(
            GapRecord(
                "G2",
                "T2",
                "D2",
                "perf",
                GapSeverity.HIGH,
                GapStatus.DISCOVERED,
                "t",
                file_paths=["src/perf.py"],
            )
        )
        self.mock_registry.add_gap(
            GapRecord(
                "G3",
                "T3",
                "D3",
                "auth",
                GapSeverity.MEDIUM,
                GapStatus.DISCOVERED,
                "t",
                file_paths=["src/auth_utils.py"],
            )
        )
        self.mock_registry.add_gap(
            GapRecord(
                "G4",
                "T4",
                "D4",
                "unknown",
                GapSeverity.LOW,
                GapStatus.DISCOVERED,
                "t",
                file_paths=["src/config.py"],
            )
        )

        # Load the schema for validation
        self.schema_path = (
            Path(__file__).parent.parent.parent
            / "schemas"
            / "minipipe_execution_plan.schema.json"
        )
        if not self.schema_path.exists():
            self.fail(f"Schema file not found at {self.schema_path}")
        with open(self.schema_path, "r") as f:
            self.execution_plan_schema = json.load(f)

    def tearDown(self):
        if self.test_repo_root.exists():
            shutil.rmtree(self.test_repo_root)

    @patch("acms_controller.GapRegistry")  # Patch the GapRegistry class itself
    @patch("acms_controller.create_ai_adapter")
    @patch("acms_controller.create_minipipe_adapter")
    @patch(
        "acms_controller.ACMSController._phase_1_gap_discovery"
    )  # Patch to prevent it from running
    def test_planning_phase(
        self,
        mock_phase_1_gap_discovery,
        mock_create_minipipe_adapter,
        mock_create_ai_adapter,
        MockGapRegistry,
    ):
        """
        Tests the planning phase (Steps 16-24) in an integrated way.
        - Uses a pre-populated GapRegistry.
        - Runs the controller in 'plan_only' mode.
        - Verifies that workstreams and execution plan JSONs are created and valid.
        """
        # Configure the mocked GapRegistry to return our pre-populated gaps
        MockGapRegistry.return_value = self.mock_registry

        # Mock adapter creations
        mock_create_ai_adapter.return_value = MagicMock()
        mock_create_minipipe_adapter.return_value = MagicMock()

        # 1. Initialize controller
        controller = ACMSController(
            repo_root=self.test_repo_root, ai_adapter_type="mock"
        )
        # controller.gap_registry = self.mock_registry # No longer needed due to patching GapRegistry class

        # 2. Run the controller in 'plan_only' mode
        controller.run_full_cycle(mode="plan_only")

        # 3. Assertions
        run_dir = controller.run_dir
        self.assertTrue(run_dir.exists())

        # Assert workstreams.json was created (Step 22)
        workstreams_path = run_dir / "workstreams.json"
        self.assertTrue(workstreams_path.exists())
        with open(workstreams_path, "r") as f:
            workstreams_data = json.load(f)
            self.assertIn("workstreams", workstreams_data)
            self.assertGreater(len(workstreams_data["workstreams"]), 0)

            # Expect 3 workstreams: 2 for auth gaps, 1 for perf gap, 1 for unknown gap
            # Assuming default clustering by category will group G1, G3 (auth) and G2 (perf) and G4 (unknown)
            # which will result in 3 workstreams: auth, perf, unknown.
            # (G1,G3) in auth, (G2) in perf, (G4) in unknown
            self.assertEqual(len(workstreams_data["workstreams"]), 3)

        # Assert mini_pipe_execution_plan.json was created (Step 24)
        execution_plan_path = run_dir / "mini_pipe_execution_plan.json"
        self.assertTrue(execution_plan_path.exists())
        with open(execution_plan_path, "r") as f:
            execution_plan_data = json.load(f)
            self.assertIn("tasks", execution_plan_data)
            self.assertGreater(len(execution_plan_data["tasks"]), 0)

            # Validate against schema (Step 23)
            try:
                jsonschema.validate(
                    instance=execution_plan_data, schema=self.execution_plan_schema
                )
            except jsonschema.ValidationError as e:
                self.fail(f"Generated execution plan failed schema validation: {e}")

        # Verify the controller reached the DONE state
        self.assertEqual(controller.current_state.value, "done")


if __name__ == "__main__":
    unittest.main()
