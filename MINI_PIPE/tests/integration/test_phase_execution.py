import unittest
import json
from pathlib import Path
import shutil
from unittest.mock import patch, MagicMock


from acms_controller import ACMSController
from acms_minipipe_adapter import ExecutionResult, TaskResult, ExecutionRequest


class TestPhaseExecution(unittest.TestCase):
    def setUp(self):
        self.test_repo_root = Path("./test_execution_repo").resolve()
        if self.test_repo_root.exists():
            shutil.rmtree(self.test_repo_root)
        self.test_repo_root.mkdir()

        self.run_id = "test_execution_run"
        self.run_dir = self.test_repo_root / ".acms_runs" / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)

        self.execution_plan_path = self.run_dir / "mini_pipe_execution_plan.json"
        self.dummy_plan = {
            "plan_id": "dummy_plan",
            "name": "Dummy Execution Plan",
            "version": "1.0",
            "tasks": [
                {
                    "task_id": "TASK_0001",
                    "task_kind": "analysis",
                    "description": "Analyze code",
                },
                {
                    "task_id": "TASK_0002",
                    "task_kind": "implementation",
                    "description": "Implement fix",
                },
                {
                    "task_id": "TASK_0003",
                    "task_kind": "test",
                    "description": "Run tests",
                },
            ],
        }
        with open(self.execution_plan_path, "w") as f:
            json.dump(self.dummy_plan, f)

    def tearDown(self):
        if self.test_repo_root.exists():
            shutil.rmtree(self.test_repo_root)

    @patch("acms_controller.create_ai_adapter")
    @patch("acms_controller.create_minipipe_adapter")
    @patch("acms_controller.ACMSController._phase_1_gap_discovery")
    @patch("acms_controller.ACMSController._phase_2_gap_consolidation")
    @patch("acms_controller.ACMSController._phase_3_plan_generation")
    def test_execution_phase_success(
        self,
        mock_phase_3_plan_generation,
        mock_phase_2_gap_consolidation,
        mock_phase_1_gap_discovery,
        mock_create_minipipe_adapter,
        mock_create_ai_adapter,
    ):
        """
        Tests the execution phase (Steps 25-42) with a successful MINI_PIPE run.
        - Mocks the MINI_PIPE adapter to return a successful execution result.
        - Runs the controller in 'execute_only' mode.
        - Verifies that the MINI_PIPE adapter was called and controller state is updated.
        """
        # Configure mocks
        mock_create_ai_adapter.return_value = MagicMock()
        mock_minipipe_adapter_instance = MagicMock()
        mock_create_minipipe_adapter.return_value = mock_minipipe_adapter_instance

        # Prepare a successful execution result from MINI_PIPE
        mock_execution_result = ExecutionResult(
            success=True,
            tasks_completed=3,
            tasks_failed=0,
            tasks_skipped=0,
            task_results=[
                TaskResult("TASK_0001", "completed", 0),
                TaskResult("TASK_0002", "completed", 0),
                TaskResult("TASK_0003", "completed", 0),
            ],
            execution_time_seconds=5.0,
        )
        mock_minipipe_adapter_instance.execute_plan.return_value = mock_execution_result

        # Initialize controller
        controller = ACMSController(
            repo_root=self.test_repo_root,
            run_id=self.run_id,
            ai_adapter_type="mock",  # Type does not matter as create_ai_adapter is mocked
        )

        # Manually set the execution plan path in controller state
        # This bypasses the planning phases for 'execute_only' mode
        controller.state["execution_plan_path"] = str(self.execution_plan_path)

        # Run the controller in 'execute_only' mode
        controller.run_full_cycle(mode="execute_only")

        # Assertions
        # 1. Verify MINI_PIPE adapter's execute_plan was called (Step 27)
        mock_minipipe_adapter_instance.execute_plan.assert_called_once()
        call_args, _ = mock_minipipe_adapter_instance.execute_plan.call_args
        actual_request = call_args[0]
        self.assertIsInstance(actual_request, ExecutionRequest)
        self.assertEqual(actual_request.execution_plan_path, self.execution_plan_path)
        self.assertEqual(actual_request.repo_root, self.test_repo_root)
        self.assertEqual(actual_request.run_id, self.run_id)

        # 2. Verify controller state reflects execution results (Steps 43-44)
        self.assertEqual(controller.state["tasks_completed"], 3)
        self.assertEqual(controller.state["tasks_failed"], 0)
        self.assertNotIn("execution_error", controller.state)

        # 3. Verify final status (Step 50)
        self.assertEqual(controller.current_state.value, "done")
        self.assertEqual(controller.state["final_status"], "success")

        # 4. Check run_status.json for metrics (Step 47-48)
        run_status_path = self.run_dir / "run_status.json"
        self.assertTrue(run_status_path.exists())
        with open(run_status_path, "r") as f:
            run_status = json.load(f)
            self.assertEqual(run_status["metrics"]["tasks_executed"], 3)
            self.assertEqual(run_status["metrics"]["tasks_failed"], 0)

    @patch("acms_controller.create_ai_adapter")
    @patch("acms_controller.create_minipipe_adapter")
    @patch("acms_controller.ACMSController._phase_1_gap_discovery")
    @patch("acms_controller.ACMSController._phase_2_gap_consolidation")
    @patch("acms_controller.ACMSController._phase_3_plan_generation")
    def test_execution_phase_failure(
        self,
        mock_phase_3_plan_generation,
        mock_phase_2_gap_consolidation,
        mock_phase_1_gap_discovery,
        mock_create_minipipe_adapter,
        mock_create_ai_adapter,
    ):
        """
        Tests the execution phase (Steps 25-42) with a failed MINI_PIPE run.
        - Mocks the MINI_PIPE adapter to return a failed execution result.
        - Runs the controller in 'execute_only' mode.
        - Verifies that the controller state reflects the failure.
        """
        # Configure mocks
        mock_create_ai_adapter.return_value = MagicMock()
        mock_minipipe_adapter_instance = MagicMock()
        mock_create_minipipe_adapter.return_value = mock_minipipe_adapter_instance

        # Prepare a failed execution result from MINI_PIPE
        mock_execution_result = ExecutionResult(
            success=False,
            tasks_completed=1,
            tasks_failed=2,
            tasks_skipped=0,
            task_results=[
                TaskResult("TASK_0001", "completed", 0),
                TaskResult("TASK_0002", "failed", 1, error="Task failed"),
                TaskResult("TASK_0003", "failed", 1, error="Task failed"),
            ],
            execution_time_seconds=5.0,
            error="MINI_PIPE execution failed",
        )
        mock_minipipe_adapter_instance.execute_plan.return_value = mock_execution_result

        # Initialize controller
        controller = ACMSController(
            repo_root=self.test_repo_root, run_id=self.run_id, ai_adapter_type="mock"
        )

        # Manually set the execution plan path in controller state
        controller.state["execution_plan_path"] = str(self.execution_plan_path)

        # Run the controller in 'execute_only' mode
        controller.run_full_cycle(mode="execute_only")

        # Assertions
        self.assertEqual(controller.state["tasks_completed"], 1)
        self.assertEqual(controller.state["tasks_failed"], 2)
        self.assertEqual(
            controller.state["execution_error"], "MINI_PIPE execution failed"
        )

        self.assertEqual(controller.current_state.value, "failed")
        self.assertEqual(controller.state["final_status"], "failed")

        run_status_path = self.run_dir / "run_status.json"
        self.assertTrue(run_status_path.exists())
        with open(run_status_path, "r") as f:
            run_status = json.load(f)
            self.assertEqual(
                run_status["metrics"]["tasks_executed"], 1
            )  # completed tasks
            self.assertEqual(run_status["metrics"]["tasks_failed"], 2)  # failed tasks


if __name__ == "__main__":
    unittest.main()
