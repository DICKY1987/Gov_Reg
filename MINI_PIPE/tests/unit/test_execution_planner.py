import unittest
from pathlib import Path
import shutil
import json


from src.acms.gap_registry import GapRegistry, GapRecord, GapStatus, GapSeverity
from src.acms.execution_planner import ExecutionPlanner, Workstream


class TestExecutionPlanner(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("./test_planner_temp").resolve()
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir()

        # Initialize a GapRegistry with some gaps
        self.registry = GapRegistry()
        self.gaps = [
            GapRecord(
                "G1",
                "T1",
                "D1",
                "auth",
                GapSeverity.CRITICAL,
                GapStatus.DISCOVERED,
                "t",
                file_paths=["f1.py", "f2.py"],
            ),
            GapRecord(
                "G2",
                "T2",
                "D2",
                "auth",
                GapSeverity.HIGH,
                GapStatus.DISCOVERED,
                "t",
                file_paths=["f1.py"],
            ),
            GapRecord(
                "G3",
                "T3",
                "D3",
                "perf",
                GapSeverity.MEDIUM,
                GapStatus.DISCOVERED,
                "t",
                file_paths=["f3.py"],
            ),
            GapRecord(
                "G4",
                "T4",
                "D4",
                "perf",
                GapSeverity.LOW,
                GapStatus.RESOLVED,
                "t",
                file_paths=["f4.py"],
            ),  # Should be ignored
            GapRecord(
                "G5",
                "T5",
                "D5",
                "auth",
                GapSeverity.LOW,
                GapStatus.DISCOVERED,
                "t",
                file_paths=["f5.py"],
                dependencies=["G3"],
            ),
        ]
        for gap in self.gaps:
            self.registry.add_gap(gap)

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_initialization(self):
        """Tests that the ExecutionPlanner can be initialized."""
        planner = ExecutionPlanner(self.registry)
        self.assertIsNotNone(planner.gap_registry)
        self.assertEqual(len(planner.workstreams), 0)

    def test_cluster_by_category(self):
        """Tests clustering gaps by category (Steps 17-18)."""
        planner = ExecutionPlanner(self.registry)
        workstreams = planner.cluster_gaps(category_based=True)

        self.assertEqual(len(workstreams), 2)  # 'auth' and 'perf'

        ws_auth = next((ws for ws in workstreams if ws.name == "auth"), None)
        ws_perf = next((ws for ws in workstreams if ws.name == "perf"), None)

        self.assertIsNotNone(ws_auth)
        self.assertIsNotNone(ws_perf)

        # 'auth' workstream should have 3 gaps (G1, G2, G5)
        self.assertEqual(len(ws_auth.gap_ids), 3)
        self.assertIn("G1", ws_auth.gap_ids)
        self.assertIn("G2", ws_auth.gap_ids)
        self.assertIn("G5", ws_auth.gap_ids)
        self.assertEqual(ws_auth.file_scope, {"f1.py", "f2.py", "f5.py"})

        # 'perf' workstream should have 1 gap (G3)
        self.assertEqual(len(ws_perf.gap_ids), 1)
        self.assertIn("G3", ws_perf.gap_ids)
        self.assertEqual(ws_perf.file_scope, {"f3.py"})

        # Check priority calculation (auth should be higher)
        self.assertGreater(ws_auth.priority_score, ws_perf.priority_score)

    def test_dependency_extraction(self):
        """Tests that dependencies between workstreams are identified (Step 19)."""
        planner = ExecutionPlanner(self.registry)
        workstreams = planner.cluster_gaps(category_based=True)

        # Manually assign workstream_id to the dependency gap for testing
        self.registry.get_gap("G3").workstream_id = "WS_PERF_0002"

        # Re-run a single workstream creation to test dependency logic
        ws_auth = planner._create_workstream(
            "WS_AUTH_0001", "auth", [self.gaps[0], self.gaps[1], self.gaps[4]], 0
        )

        # G5 depends on G3, and G3 is in the 'perf' workstream
        self.assertIn("WS_PERF_0002", ws_auth.dependencies)

    def test_get_prioritized_workstreams(self):
        """Tests that workstreams are sorted by priority."""
        planner = ExecutionPlanner(self.registry)
        planner.cluster_gaps(category_based=True)

        prioritized = planner.get_prioritized_workstreams()

        self.assertEqual(len(prioritized), 2)
        # First workstream should be 'auth' due to higher priority score
        self.assertEqual(prioritized[0].name, "auth")
        self.assertEqual(prioritized[1].name, "perf")
        self.assertGreater(prioritized[0].priority_score, prioritized[1].priority_score)

    def test_save_workstreams(self):
        """Tests saving the generated workstreams to a file."""
        output_path = self.test_dir / "workstreams.json"
        planner = ExecutionPlanner(self.registry)
        planner.cluster_gaps()
        planner.save_workstreams(output_path)

        self.assertTrue(output_path.exists())
        with open(output_path, "r") as f:
            data = json.load(f)
            self.assertEqual(len(data["workstreams"]), 2)
            self.assertIn("version", data)
            self.assertIn("generated_at", data)


if __name__ == "__main__":
    unittest.main()
