import unittest
import json
from pathlib import Path
import shutil
from unittest.mock import MagicMock


from src.acms.execution_planner import Workstream
from src.acms.phase_plan_compiler import PhasePlanCompiler, MiniPipeExecutionPlan

# Mock jsonschema if not installed, as it's an optional dependency for this test
try:
    import jsonschema
except ImportError:
    jsonschema = None


class TestPhasePlanCompiler(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("./test_compiler_temp").resolve()
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir()
        self.repo_root = Path("/fake/repo")

        # Create sample workstreams
        self.ws1 = Workstream(
            workstream_id="WS_AUTH_01",
            name="auth_fixes",
            description="Fix authentication bugs",
            gap_ids=["G1", "G2"],
            priority_score=10.0,
            file_scope={"src/auth.py"},
            categories={"auth", "security"},
            estimated_effort="low",  # Explicitly set to avoid extra test task
        )
        self.ws2 = Workstream(
            workstream_id="WS_TEST_02",
            name="testing_enhancements",
            description="Add more tests",
            gap_ids=["G3"],
            priority_score=5.0,
            file_scope={"tests/test_auth.py"},
            categories={"testing"},
            dependencies=["WS_AUTH_01"],  # Depends on the first workstream
        )
        self.workstreams = [self.ws1, self.ws2]

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_initialization(self):
        """Tests that the PhasePlanCompiler can be initialized."""
        compiler = PhasePlanCompiler()
        self.assertEqual(compiler.task_counter, 0)

    def test_compile_from_workstreams(self):
        """Tests compiling a list of workstreams into a plan (Steps 21-22)."""
        compiler = PhasePlanCompiler()
        plan = compiler.compile_from_workstreams(self.workstreams, self.repo_root)

        self.assertIsInstance(plan, MiniPipeExecutionPlan)
        self.assertEqual(plan.metadata["workstream_count"], 2)

        # ws1 (auth) -> 2 tasks (analysis, implementation) because no 'test' category
        # ws2 (testing) -> 3 tasks (analysis, implementation, test)
        self.assertEqual(len(plan.tasks), 5)

        # Verify task kinds
        task_kinds = [t.task_kind for t in plan.tasks]
        self.assertEqual(task_kinds.count("analysis"), 2)
        self.assertEqual(task_kinds.count("implementation"), 2)
        self.assertEqual(task_kinds.count("test"), 1)

    def test_dependency_resolution(self):
        """Tests that dependencies between workstreams are correctly translated to task dependencies."""
        compiler = PhasePlanCompiler()
        plan = compiler.compile_from_workstreams(self.workstreams, self.repo_root)

        # Find the tasks related to ws2 (the dependent workstream)
        ws2_tasks = [
            t for t in plan.tasks if t.metadata["workstream_id"] == "WS_TEST_02"
        ]
        self.assertEqual(len(ws2_tasks), 3)

        # The first task of ws2 should depend on the last task of ws1
        first_ws2_task = ws2_tasks[0]

        ws1_tasks = [
            t for t in plan.tasks if t.metadata["workstream_id"] == "WS_AUTH_01"
        ]
        last_ws1_task_id = ws1_tasks[-1].task_id

        self.assertIn(last_ws1_task_id, first_ws2_task.depends_on)

    def test_save_plan(self):
        """Tests saving the compiled execution plan to a file."""
        output_path = self.test_dir / "execution_plan.json"
        compiler = PhasePlanCompiler()
        plan = compiler.compile_from_workstreams(self.workstreams, self.repo_root)
        compiler.save_plan(plan, output_path)

        self.assertTrue(output_path.exists())
        with open(output_path, "r") as f:
            data = json.load(f)
            self.assertEqual(data["plan_id"], plan.plan_id)
            self.assertEqual(len(data["tasks"]), 5)

    @unittest.skipIf(
        jsonschema is None,
        "jsonschema is not installed, skipping schema validation test.",
    )
    def test_plan_schema_validation(self):
        """Tests that the generated plan conforms to the JSON schema (Step 23)."""
        # Load the schema
        schema_path = (
            Path(__file__).parent.parent.parent
            / "schemas"
            / "execution"
            / "minipipe_execution_plan.schema.json"
        )
        if not schema_path.exists():
            self.skipTest(f"Schema file not found at {schema_path}")

        with open(schema_path, "r") as f:
            schema = json.load(f)

        # Generate the plan
        compiler = PhasePlanCompiler()
        plan = compiler.compile_from_workstreams(self.workstreams, self.repo_root)
        plan_dict = plan.to_dict()

        # Validate
        try:
            jsonschema.validate(instance=plan_dict, schema=schema)
        except jsonschema.ValidationError as e:
            self.fail(f"Generated plan failed schema validation: {e}")


if __name__ == "__main__":
    unittest.main()
