import unittest
import json
from pathlib import Path
import shutil
import subprocess
from unittest.mock import patch, MagicMock
from datetime import UTC, datetime
import re


from acms_controller import ACMSController
from acms_ai_adapter import AIResponse
from acms_golden_path import RunState
import jsonschema
from typing import Any, List
from acms_minipipe_adapter import ExecutionResult
import importlib
import acms_minipipe_adapter


class TestDeterminism(unittest.TestCase):
    def setUp(self):
        # Create a base temporary directory for all test repos
        self.base_temp_dir = Path("./test_determinism_base").resolve()
        if self.base_temp_dir.exists():
            shutil.rmtree(self.base_temp_dir)
        self.base_temp_dir.mkdir()

        # Create dummy OVERLAP_AUTOMATION_AND_MASTER_GAP_ANALYSIS.merged.json in the project root
        self.prompt_file_path = (
            Path(__file__).parent.parent.parent
            / "OVERLAP_AUTOMATION_AND_MASTER_GAP_ANALYSIS.merged.json"
        )
        with open(self.prompt_file_path, "w") as f:
            f.write("{}")

        # Reload the adapter module to ensure the latest changes (e.g., MockMiniPipeAdapter fix) are loaded
        importlib.reload(acms_minipipe_adapter)

    def tearDown(self):
        if self.base_temp_dir.exists():
            shutil.rmtree(self.base_temp_dir)
        if self.prompt_file_path.exists():
            self.prompt_file_path.unlink()

    def _setup_repo(self, repo_name: str) -> Path:
        """Helper to set up a fresh repository for a run."""
        repo_root = self.base_temp_dir / repo_name
        if repo_root.exists():
            shutil.rmtree(repo_root)
        repo_root.mkdir()

        # Create a dummy src/main.py for gap analysis context
        (repo_root / "src").mkdir()
        with open(repo_root / "src" / "main.py", "w") as f:
            f.write("def foo():\n    pass\n")

        return repo_root

    def _normalize_json(self, json_data: Any) -> str:
        """Removes volatile elements (timestamps, run_ids) from JSON for comparison."""

        # Helper to process a single dictionary
        def process_dict(data: dict) -> dict:
            processed_data = json.loads(json.dumps(data))  # Deep copy
            if "run_id" in processed_data:
                processed_data["run_id"] = "STATIC_RUN_ID"
            if "plan_id" in processed_data:
                processed_data["plan_id"] = "STATIC_PLAN_ID"
            if "metadata" in processed_data and "run_id" in processed_data["metadata"]:
                processed_data["metadata"]["run_id"] = "STATIC_RUN_ID"
            if (
                "metadata" in processed_data
                and "generated_at" in processed_data["metadata"]
            ):
                processed_data["metadata"]["generated_at"] = "STATIC_TIMESTAMP"
            if (
                "generated_at" in processed_data
            ):  # For top-level generated_at (e.g., in workstreams.json)
                processed_data["generated_at"] = "STATIC_TIMESTAMP"
            if "started_at" in processed_data:
                processed_data["started_at"] = "STATIC_TIMESTAMP"
            if "completed_at" in processed_data:
                processed_data["completed_at"] = "STATIC_TIMESTAMP"
            if "last_transition" in processed_data:
                processed_data["last_transition"] = "STATIC_TIMESTAMP"
            if "ts" in processed_data:
                processed_data["ts"] = "STATIC_TIMESTAMP"
            if (
                "timestamp" in processed_data
            ):  # Added for state_transitions in run_status.json
                processed_data["timestamp"] = "STATIC_TIMESTAMP"
            if "discovered_at" in processed_data:
                processed_data["discovered_at"] = "STATIC_TIMESTAMP"
            if "saved_at" in processed_data:  # Added for gap_registry.json
                processed_data["saved_at"] = "STATIC_TIMESTAMP"

            # Normalize path-like strings to remove specific repo_run_X and RUN_X_DETERMINISM
            def _normalize_path_string(path_str: str) -> str:
                # Replace repo_run_X with STATIC_REPO_ROOT
                normalized = re.sub(
                    r".*test_determinism_base[\\\\/](repo_run_\d+)",
                    "STATIC_REPO_ROOT",
                    path_str,
                )
                # Replace RUN_X_DETERMINISM with STATIC_RUN_ID
                normalized = re.sub(r"RUN_\d+_DETERMINISM", "STATIC_RUN_ID", normalized)
                return normalized

            # Normalize file paths and file scope
            if "file_paths" in processed_data and isinstance(
                processed_data["file_paths"], list
            ):
                processed_data["file_paths"] = [
                    _normalize_path_string(p) for p in processed_data["file_paths"]
                ]
            if "file_scope" in processed_data and isinstance(
                processed_data["file_scope"], list
            ):
                processed_data["file_scope"] = [
                    _normalize_path_string(p) for p in processed_data["file_scope"]
                ]

            # Normalize repo_root at top level, and in metadata, and any string that looks like a repo path
            if "repo_root" in processed_data:
                processed_data["repo_root"] = "STATIC_REPO_ROOT"
            if (
                "metadata" in processed_data
                and "repo_root" in processed_data["metadata"]
            ):
                processed_data["metadata"]["repo_root"] = "STATIC_REPO_ROOT"

            # Recursively normalize string values that are paths, including in nested dicts/lists
            for key, value in processed_data.items():
                if isinstance(value, str):
                    processed_data[key] = _normalize_path_string(value)
                elif isinstance(value, dict):
                    processed_data[key] = process_dict(value)
                elif isinstance(value, list):
                    processed_data[key] = [
                        process_dict(item)
                        if isinstance(item, dict)
                        else (
                            _normalize_path_string(item)
                            if isinstance(item, str)
                            else item
                        )
                        for item in value
                    ]
            return processed_data

        if isinstance(json_data, dict):
            normalized_data = process_dict(json_data)
        elif isinstance(json_data, list):
            # If it's a list (e.g., ledger entries), process each item
            normalized_data = [
                process_dict(item) if isinstance(item, dict) else item
                for item in json_data
            ]
        else:
            # For non-dict/list types, return as is (e.g., simple strings/numbers)
            return json.dumps(json_data, sort_keys=True, indent=2)

        return json.dumps(normalized_data, sort_keys=True, indent=2)

    @patch("acms_controller.create_minipipe_adapter")
    @patch("acms_controller.create_ai_adapter")
    def test_pipeline_determinism(
        self, mock_create_ai_adapter, mock_create_minipipe_adapter
    ):
        """
        Tests that running the ACMS pipeline twice with identical inputs produces
        identical output artifacts (excluding volatile elements like timestamps/run_ids).
        """
        # Configure mock AI adapter for a predictable gap report
        mock_ai_adapter_instance = MagicMock()

        def mock_analyze_gaps_side_effect(request):
            repo_root = request.repo_root
            mock_gap_report = {
                "version": "1.0",
                "gaps": [
                    {
                        "gap_id": "DETERMINISM_GAP_001",
                        "title": "Deterministic Test Gap",
                        "description": "Gap for determinism test.",
                        "category": "quality",
                        "severity": "medium",
                        "file_paths": [str(repo_root / "src" / "main.py")],
                    }
                ],
            }
            return AIResponse(
                success=True, output=mock_gap_report, execution_time_seconds=1.0
            )

        mock_ai_adapter_instance.analyze_gaps.side_effect = (
            mock_analyze_gaps_side_effect
        )
        mock_create_ai_adapter.return_value = mock_ai_adapter_instance

        # Configure mock MiniPipeAdapter to always return a successful result
        mock_minipipe_adapter_instance = MagicMock()
        mock_minipipe_adapter_instance.execute_plan.return_value = ExecutionResult(
            success=True,
            tasks_completed=3,
            tasks_failed=0,
            tasks_skipped=0,
            execution_time_seconds=2.0,
        )
        mock_create_minipipe_adapter.return_value = mock_minipipe_adapter_instance

        # --- Run 1 ---
        repo_root_1 = self._setup_repo("repo_run_1")
        run1_id = "RUN_1_DETERMINISM"
        controller1 = ACMSController(
            repo_root=repo_root_1,
            run_id=run1_id,
            ai_adapter_type="mock",
            minipipe_adapter_type="mock",
        )
        controller1.run_full_cycle(mode="full")
        run_dir1 = controller1.run_dir

        # --- Run 2 ---
        repo_root_2 = self._setup_repo("repo_run_2")
        run2_id = "RUN_2_DETERMINISM"
        controller2 = ACMSController(
            repo_root=repo_root_2,
            run_id=run2_id,
            ai_adapter_type="mock",
            minipipe_adapter_type="mock",
        )
        controller2.run_full_cycle(mode="full")
        run_dir2 = controller2.run_dir

        # --- Compare Artifacts ---
        artifacts_to_compare = [
            "run.ledger.jsonl",
            "gap_analysis_report.json",
            "gap_registry.json",
            "workstreams.json",
            "mini_pipe_execution_plan.json",
            "run_status.json",
        ]

        for artifact in artifacts_to_compare:
            path1 = run_dir1 / artifact
            path2 = run_dir2 / artifact

            self.assertTrue(path1.exists(), f"{artifact} not found in Run 1")
            self.assertTrue(path2.exists(), f"{artifact} not found in Run 2")

            with open(path1, "r") as f1, open(path2, "r") as f2:
                content1 = f1.read()
                content2 = f2.read()

                # Special handling for ledger as it's JSONL
                if artifact == "run.ledger.jsonl":
                    ledger1 = [
                        json.loads(line)
                        for line in content1.splitlines()
                        if line.strip()
                    ]
                    ledger2 = [
                        json.loads(line)
                        for line in content2.splitlines()
                        if line.strip()
                    ]
                    normalized_content1 = self._normalize_json(ledger1)
                    normalized_content2 = self._normalize_json(ledger2)
                else:
                    normalized_content1 = self._normalize_json(json.loads(content1))
                    normalized_content2 = self._normalize_json(json.loads(content2))

                self.assertEqual(
                    normalized_content1,
                    normalized_content2,
                    f"Artifact {artifact} differs between runs.",
                )


if __name__ == "__main__":
    unittest.main()
