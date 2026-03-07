import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
import unittest
import json
from pathlib import Path
import shutil
from unittest.mock import patch, MagicMock


from acms_controller import ACMSController
from acms_ai_adapter import AIResponse


class TestPhaseGapDiscovery(unittest.TestCase):
    def setUp(self):
        self.test_repo_root = Path("./test_integration_repo").resolve()
        if self.test_repo_root.exists():
            shutil.rmtree(self.test_repo_root)
        self.test_repo_root.mkdir()

        # A mock AI response that the adapter will be patched to return
        self.mock_gap_report = {
            "version": "1.0",
            "gaps": [
                {
                    "gap_id": "GAP_INT_001",
                    "title": "Integration Test Gap",
                    "description": "A gap for integration testing.",
                    "category": "testing",
                    "severity": "high",
                    "file_paths": ["src/test.py"],
                }
            ],
        }

    def tearDown(self):
        if self.test_repo_root.exists():
            shutil.rmtree(self.test_repo_root)

    @patch("acms_controller.create_minipipe_adapter")
    @patch("acms_controller.create_ai_adapter")
    def test_gap_discovery_phase(
        self, mock_create_ai_adapter, mock_create_pipe_adapter
    ):
        """
        Tests the gap discovery phase (Steps 7-15) in an integrated way.
        - Mocks the AI adapter creation to return a pre-configured mock.
        - Runs the controller in 'analyze_only' mode.
        - Verifies that the raw report and normalized registry are created correctly.
        """
        # Configure the mock AI adapter that create_ai_adapter will return
        mock_ai_adapter_instance = MagicMock()
        mock_response = AIResponse(
            success=True, output=self.mock_gap_report, execution_time_seconds=1.0
        )
        mock_ai_adapter_instance.analyze_gaps.return_value = mock_response
        mock_create_ai_adapter.return_value = mock_ai_adapter_instance

        # Mock the minipipe adapter factory to avoid issues in later phases
        mock_create_pipe_adapter.return_value = MagicMock()

        # 2. Initialize and run the controller
        # The 'mock' adapter type will be used, and its 'analyze_gaps' method is what we patched.
        controller = ACMSController(
            repo_root=self.test_repo_root, ai_adapter_type="mock"
        )
        controller.run_full_cycle(mode="analyze_only")

        # 3. Assertions
        run_dir = controller.run_dir
        self.assertTrue(run_dir.exists())

        # Assert that the raw gap analysis report was written (Step 12)
        raw_report_path = run_dir / "gap_analysis_report.json"
        self.assertTrue(raw_report_path.exists())
        with open(raw_report_path, "r") as f:
            raw_data = json.load(f)
            self.assertEqual(len(raw_data["gaps"]), 1)
            self.assertEqual(raw_data["gaps"][0]["gap_id"], "GAP_INT_001")

        # Assert that the gap registry was created and contains the normalized gap (Steps 13-14)
        registry_path = run_dir / "gap_registry.json"
        self.assertTrue(registry_path.exists())
        with open(registry_path, "r") as f:
            registry_data = json.load(f)
            self.assertEqual(len(registry_data["gaps"]), 1)
            normalized_gap = registry_data["gaps"][0]
            self.assertEqual(normalized_gap["gap_id"], "GAP_INT_001")
            self.assertEqual(normalized_gap["status"], "discovered")
            self.assertEqual(normalized_gap["severity"], "high")

        # Verify the controller reached the DONE state
        self.assertEqual(controller.current_state.value, "done")


if __name__ == "__main__":
    unittest.main()
