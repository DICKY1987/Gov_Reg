import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import os
import shutil
import json


from src.acms.controller import ACMSController


class TestControllerInit(unittest.TestCase):
    def setUp(self):
        self.test_repo_root = Path("./test_repo_for_init").resolve()
        # Clean up before test
        if self.test_repo_root.exists():
            shutil.rmtree(self.test_repo_root)
        self.test_repo_root.mkdir()

    def tearDown(self):
        # Clean up after test
        if self.test_repo_root.exists():
            shutil.rmtree(self.test_repo_root)

    @patch("acms_controller.create_minipipe_adapter")
    @patch("acms_controller.create_ai_adapter")
    @patch("acms_controller.ACMSController._generate_ulid")
    def test_initialization(
        self, mock_generate_ulid, mock_create_ai_adapter, mock_create_pipe_adapter
    ):
        """
        Tests steps 1-5: Controller initialization, argument parsing, run_id generation,
        and run directory/ledger creation.
        """
        # Mock the ULID to be a predictable value
        mock_run_id = "20251206120000_TESTINIT"
        mock_generate_ulid.return_value = mock_run_id

        # 1. & 2. Simulate instantiation with arguments
        controller = ACMSController(
            repo_root=self.test_repo_root,
            ai_adapter_type="mock_ai",
            minipipe_adapter_type="mock_pipe",
        )

        # 3. Assert run_id was generated and set
        self.assertEqual(controller.run_id, mock_run_id)

        # 4. Assert run directory was created
        expected_run_dir = self.test_repo_root / ".acms_runs" / mock_run_id
        self.assertTrue(expected_run_dir.exists())
        self.assertTrue(expected_run_dir.is_dir())
        controller.run_dir = expected_run_dir  # for later assertions

        # Assert ledger file was created and contains the INIT event
        ledger_path = expected_run_dir / "run.ledger.jsonl"
        self.assertTrue(ledger_path.exists())

        with open(ledger_path, "r") as f:
            ledger_entry = json.loads(f.readline())
            self.assertEqual(ledger_entry["run_id"], mock_run_id)
            self.assertEqual(ledger_entry["state"], "init")
            self.assertEqual(ledger_entry["event"], "enter_state")

        # 5. Assert top-level run record was created in memory (state)
        self.assertEqual(controller.state["run_id"], mock_run_id)
        self.assertEqual(controller.state["repo_root"], str(self.test_repo_root))
        self.assertEqual(controller.state["current_state"], "init")
        self.assertEqual(controller.state["ai_adapter_type"], "mock_ai")
        self.assertEqual(controller.state["minipipe_adapter_type"], "mock_pipe")


if __name__ == "__main__":
    unittest.main()
