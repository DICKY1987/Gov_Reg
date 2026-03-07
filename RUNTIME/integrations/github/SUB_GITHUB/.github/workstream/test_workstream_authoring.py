# DOC_LINK: DOC-TEST-PIPELINE-TEST-WORKSTREAM-AUTHORING-139
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

# Adjust sys.path to allow importing bundles
project_root = Path(__file__).resolve().parents[2]
)

from core.state import bundles as m010003_bundles

# Define paths relative to the project root
WORKSTREAM_SCHEMA_PATH = project_root / "schema" / "workstream.schema.json"
WORKSTREAM_TEMPLATE_PATH = project_root / "templates" / "workstream_template.json"
VALIDATOR_SCRIPT_PATH = project_root / "scripts" / "validate_workstreams_authoring.py"

# Prepare environment for subprocess calls
_env = os.environ.copy()
_env["PYTHONPATH"] = str(project_root / "src") + os.pathsep + _env.get("PYTHONPATH", "")


@pytest.fixture(scope="module")
def workstream_schema():
    """Loads the workstream JSON schema."""
    with open(WORKSTREAM_SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def workstream_template_raw():
    """Loads the raw workstream template JSON."""
    with open(WORKSTREAM_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        # The template should now be clean of comments, but this line is kept for robustness
        content = "".join(line for line in f if not line.strip().startswith("//"))
        return json.loads(content)


@pytest.fixture
def temp_workstream_dir(tmp_path):
    """Creates a temporary directory for workstream bundles."""
    temp_dir = tmp_path / "workstreams"
    temp_dir.mkdir()
    return temp_dir


def create_bundle_file(directory: Path, filename: str, content: dict):
    """Helper to create a workstream bundle JSON file."""
    with open(directory / filename, "w", encoding="utf-8") as f:
        json.dump(content, f, indent=2)


# --- Test Cases ---


def test_template_validity(workstream_template_raw, workstream_schema):
    """
    Test that the workstream template is valid against the schema after filling placeholders.
    """
    # Create a valid bundle from the template by replacing placeholders
    valid_bundle_data = workstream_template_raw.copy()
    valid_bundle_data["id"] = "ws-test-template"
    valid_bundle_data["openspec_change"] = "OS-TEST-001"
    valid_bundle_data["ccpm_issue"] = 123
    valid_bundle_data["gate"] = 1
    valid_bundle_data["files_scope"] = ["src/test_file.py"]
    valid_bundle_data["tasks"] = ["Test task for template."]
    valid_bundle_data["tool"] = "aider"

    # Remove comment fields if they exist in the template for validation
    if "comment" in valid_bundle_data:
        del valid_bundle_data["comment"]

    # Ensure optional fields that are lists are empty if not specified
    if "files_create" not in valid_bundle_data:
        valid_bundle_data["files_create"] = []
    if "acceptance_tests" not in valid_bundle_data:
        valid_bundle_data["acceptance_tests"] = []
    if "depends_on" not in valid_bundle_data:
        valid_bundle_data["depends_on"] = []

    # Use bundles.validate_bundle_data for validation
    try:
        bundles.validate_bundle_data(valid_bundle_data, schema=workstream_schema)
    except bundles.BundleValidationError as e:
        pytest.fail(f"Workstream template is not valid against schema: {e}")


def test_validator_success(temp_workstream_dir):
    """
    Test validate_workstreams_authoring.py with valid bundles.
    """
    bundle1 = {
        "id": "ws-valid-bundle-1",
        "openspec_change": "OS-001",
        "ccpm_issue": 1,
        "gate": 1,
        "files_scope": ["src/unique_file_for_ws1.py"],
        "tasks": ["Task 1"],
        "tool": "aider",
    }
    bundle2 = {
        "id": "ws-valid-bundle-2",
        "openspec_change": "OS-002",
        "ccpm_issue": 2,
        "gate": 1,
        "files_scope": ["src/unique_file_for_ws2.py"],
        "tasks": ["Task 2"],
        "depends_on": ["ws-valid-bundle-1"],
        "tool": "aider",
    }
    create_bundle_file(temp_workstream_dir, "bundle1.json", bundle1)
    create_bundle_file(temp_workstream_dir, "bundle2.json", bundle2)

    result = subprocess.run(
        [sys.executable, str(VALIDATOR_SCRIPT_PATH), "--dir", str(temp_workstream_dir)],
        capture_output=True,
        text=True,
        check=False,
        env=_env,
    )
    assert (
        result.returncode == 0
    ), f"Validator failed with exit code {result.returncode}. Stderr: {result.stderr}"
    assert "2 workstream bundles validated successfully." in result.stdout


def test_validator_schema_failure(temp_workstream_dir):
    """
    Test validate_workstreams_authoring.py with an invalid bundle (missing required field).
    """
    invalid_bundle = {
        "id": "ws-invalid-bundle",
        "openspec_change": "OS-003",
        # "ccpm_issue": 3, # Missing required field
        "gate": 1,
        "files_scope": ["src/file3.py"],
        "tasks": ["Task 3"],
        "tool": "aider",
    }
    create_bundle_file(temp_workstream_dir, "invalid_bundle.json", invalid_bundle)

    result = subprocess.run(
        [sys.executable, str(VALIDATOR_SCRIPT_PATH), "--dir", str(temp_workstream_dir)],
        capture_output=True,
        text=True,
        check=False,
        env=_env,
    )
    assert result.returncode != 0
    assert "Validation failed" in result.stderr
    assert "ccpm_issue" in result.stderr


def test_validator_overlap_failure(temp_workstream_dir):
    """
    Test validate_workstreams_authoring.py with bundles having overlapping files_scope.
    """
    bundle_a = {
        "id": "ws-overlap-a",
        "openspec_change": "OS-004",
        "ccpm_issue": 4,
        "gate": 1,
        "files_scope": ["src/shared_file.py", "src/file_a.py"],
        "tasks": ["Task A"],
        "tool": "aider",
    }
    bundle_b = {
        "id": "ws-overlap-b",
        "openspec_change": "OS-005",
        "ccpm_issue": 5,
        "gate": 1,
        "files_scope": ["src/shared_file.py", "src/file_b.py"],
        "tasks": ["Task B"],
        "tool": "aider",
    }
    create_bundle_file(temp_workstream_dir, "bundle_a.json", bundle_a)
    create_bundle_file(temp_workstream_dir, "bundle_b.json", bundle_b)

    result = subprocess.run(
        [sys.executable, str(VALIDATOR_SCRIPT_PATH), "--dir", str(temp_workstream_dir)],
        capture_output=True,
        text=True,
        check=False,
        env=_env,
    )
    assert result.returncode != 0
    assert "Validation failed" in result.stderr
    assert "File scope overlaps detected" in result.stderr
    assert "src/shared_file.py" in result.stderr


def test_validator_json_mode(temp_workstream_dir):
    """
    Test validate_workstreams_authoring.py with --json flag on a failing set.
    """
    invalid_bundle = {
        "id": "ws-json-invalid",
        "openspec_change": "OS-006",
        # "ccpm_issue": 6, # Missing required field
        "gate": 1,
        "files_scope": ["src/json_file.py"],
        "tasks": ["Task JSON"],
        "tool": "aider",
    }
    create_bundle_file(temp_workstream_dir, "json_invalid.json", invalid_bundle)

    result = subprocess.run(
        [
            sys.executable,
            str(VALIDATOR_SCRIPT_PATH),
            "--dir",
            str(temp_workstream_dir),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
        env=_env,
    )
    assert result.returncode != 0

    try:
        output_json = json.loads(result.stdout)  # Changed to stdout
    except json.JSONDecodeError:
        pytest.fail(
            f"Validator --json output is not valid JSON. Stdout: {result.stdout}. Stderr: {result.stderr}"
        )

    assert output_json["ok"] is False
    assert output_json["bundles_checked"] == 1  # Expect 1 bundle checked
    assert len(output_json["errors"]) > 0
    assert output_json["errors"][0]["type"] == "schema"
    assert "ccpm_issue" in output_json["errors"][0]["details"]


def test_validator_json_mode_success(temp_workstream_dir):
    """
    Test validate_workstreams_authoring.py with --json flag on a successful set.
    """
    bundle1 = {
        "id": "ws-json-valid-1",
        "openspec_change": "OS-007",
        "ccpm_issue": 7,
        "gate": 1,
        "files_scope": ["src/json_valid_file1.py"],
        "tasks": ["Task JSON Valid 1"],
        "tool": "aider",
    }
    create_bundle_file(temp_workstream_dir, "json_valid1.json", bundle1)

    result = subprocess.run(
        [
            sys.executable,
            str(VALIDATOR_SCRIPT_PATH),
            "--dir",
            str(temp_workstream_dir),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
        env=_env,
    )
    assert result.returncode == 0

    try:
        output_json = json.loads(result.stdout)
    except json.JSONDecodeError:
        pytest.fail(
            f"Validator --json output is not valid JSON. Stdout: {result.stdout}. Stderr: {result.stderr}"
        )

    assert output_json["ok"] is True
    assert output_json["bundles_checked"] == 1
    assert len(output_json["errors"]) == 0


def test_validator_dependency_failure(temp_workstream_dir):
    """
    Test validate_workstreams_authoring.py with a missing dependency.
    """
    bundle_dep_missing = {
        "id": "ws-dep-missing",
        "openspec_change": "OS-008",
        "ccpm_issue": 8,
        "gate": 1,
        "files_scope": ["src/dep_file.py"],
        "tasks": ["Task Dep Missing"],
        "depends_on": ["ws-non-existent-bundle"],  # Missing dependency
        "tool": "aider",
    }
    create_bundle_file(temp_workstream_dir, "dep_missing.json", bundle_dep_missing)

    result = subprocess.run(
        [sys.executable, str(VALIDATOR_SCRIPT_PATH), "--dir", str(temp_workstream_dir)],
        capture_output=True,
        text=True,
        check=False,
        env=_env,
    )
    assert result.returncode != 0
    assert "Validation failed" in result.stderr
    assert "Missing dependency references" in result.stderr
    assert "ws-non-existent-bundle" in result.stderr


def test_validator_cycle_failure(temp_workstream_dir):
    """
    Test validate_workstreams_authoring.py with a dependency cycle.
    """
    bundle_cycle_a = {
        "id": "ws-cycle-a",
        "openspec_change": "OS-009",
        "ccpm_issue": 9,
        "gate": 1,
        "files_scope": ["src/cycle_a.py"],
        "tasks": ["Task Cycle A"],
        "depends_on": ["ws-cycle-b"],
        "tool": "aider",
    }
    bundle_cycle_b = {
        "id": "ws-cycle-b",
        "openspec_change": "OS-010",
        "ccpm_issue": 10,
        "gate": 1,
        "files_scope": ["src/cycle_b.py"],
        "tasks": ["Task Cycle B"],
        "depends_on": ["ws-cycle-a"],
        "tool": "aider",
    }
    create_bundle_file(temp_workstream_dir, "cycle_a.json", bundle_cycle_a)
    create_bundle_file(temp_workstream_dir, "cycle_b.json", bundle_cycle_b)

    result = subprocess.run(
        [sys.executable, str(VALIDATOR_SCRIPT_PATH), "--dir", str(temp_workstream_dir)],
        capture_output=True,
        text=True,
        check=False,
        env=_env,
    )
    assert result.returncode != 0
    assert "Validation failed" in result.stderr
    assert "Dependency cycle(s) detected" in result.stderr
    # Check for both IDs in the cycle message, as the order might vary
    assert "ws-cycle-a" in result.stderr and "ws-cycle-b" in result.stderr
