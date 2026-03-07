import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import shutil
import json
import time


from src.acms.minipipe_adapter import (
    create_minipipe_adapter,
    MiniPipeAdapter,
    MockMiniPipeAdapter,
    ExecutionRequest,
    ExecutionResult,
)


class TestAcmsMiniPipeAdapter(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("./test_adapter_temp").resolve()
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir()
        self.repo_root = self.test_dir
        self.plan_path = self.test_dir / "plan.json"

        # Create a dummy execution plan
        self.dummy_plan = {
            "plan_id": "test_plan",
            "name": "Test Plan",
            "tasks": [
                {"task_id": "T1", "task_kind": "analysis"},
                {"task_id": "T2", "task_kind": "implementation"},
            ],
        }
        with open(self.plan_path, "w") as f:
            json.dump(self.dummy_plan, f)

        self.request = ExecutionRequest(
            execution_plan_path=self.plan_path,
            repo_root=self.repo_root,
            run_id="test_run_123",
        )

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_adapter_factory(self):
        """Tests the create_minipipe_adapter factory function (Step 25)."""
        # Test mock adapter creation
        mock_adapter = create_minipipe_adapter("mock")
        self.assertIsInstance(mock_adapter, MockMiniPipeAdapter)

        # Test auto adapter creation
        auto_adapter = create_minipipe_adapter("auto")
        self.assertIsInstance(auto_adapter, MiniPipeAdapter)

        # Test invalid adapter type
        with self.assertRaises(ValueError):
            create_minipipe_adapter("invalid_type")

    def test_mock_adapter_execution(self):
        """Tests that the MockMiniPipeAdapter returns a successful mock result."""
        adapter = MockMiniPipeAdapter()
        result = adapter.execute_plan(self.request)

        self.assertTrue(result.success)
        self.assertEqual(result.tasks_completed, 2)
        self.assertEqual(result.tasks_failed, 0)
        self.assertIn("Mock execution", result.task_results[0].output)

    @patch("acms_minipipe_adapter.Path.exists")
    def test_auto_adapter_fallback_to_mock(self, mock_path_exists):
        """Tests that the 'auto' adapter falls back to mock execution if the CLI is not found."""
        # Force the adapter to think the orchestrator CLI doesn't exist
        mock_path_exists.return_value = False

        adapter = MiniPipeAdapter()
        result = adapter.execute_plan(self.request)

        self.assertTrue(result.success)
        self.assertEqual(result.tasks_completed, 2)
        self.assertEqual(result.tasks_failed, 0)
        self.assertIn("Mock execution", result.task_results[0].output)

    @patch("acms_minipipe_adapter.subprocess.run")
    @patch("acms_minipipe_adapter.Path.exists")
    def test_auto_adapter_cli_invocation(self, mock_path_exists, mock_subprocess_run):
        """Tests that the 'auto' adapter correctly calls the orchestrator CLI (Step 26-27)."""
        # Force the adapter to think the orchestrator CLI *does* exist
        mock_path_exists.return_value = True
        orchestrator_path = (
            Path(__file__).parent.parent.parent
            / "src"
            / "minipipe"
            / "orchestrator_cli.py"
        )

        # Mock the result of the subprocess call
        mock_subprocess_run.return_value = MagicMock(
            returncode=0, stdout="Task T1: completed\nTask T2: completed", stderr=""
        )

        adapter = MiniPipeAdapter(orchestrator_cli_path=orchestrator_path)
        result = adapter.execute_plan(self.request)

        self.assertTrue(result.success)
        mock_subprocess_run.assert_called_once()

        # Check that the command was constructed correctly
        args, kwargs = mock_subprocess_run.call_args
        command = args[0]
        self.assertIn(str(orchestrator_path), command)
        self.assertIn("--plan", command)
        self.assertIn(self.request.run_id, command)


if __name__ == "__main__":
    unittest.main()
