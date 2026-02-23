import csv
import importlib.util
import json
from hashlib import sha256
from pathlib import Path
import sys


MODULE_PATH = Path(__file__).parent.parent / "scripts" / "P_01999000042260126011_registry_tui.py"
spec = importlib.util.spec_from_file_location("registry_tui", MODULE_PATH)
registry_tui = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = registry_tui
spec.loader.exec_module(registry_tui)

RegistrySnapshot = registry_tui.RegistrySnapshot
MetricEngine = registry_tui.MetricEngine
Issue = registry_tui.Issue
load_registry_snapshot = registry_tui.load_registry_snapshot
load_metrics_snapshot = registry_tui.load_metrics_snapshot
RegistryTuiApp = registry_tui.RegistryTuiApp


def make_snapshot(files):
    return RegistrySnapshot(
        files=files,
        metadata={},
        source_path=Path("registry.json"),
        registry_hash="hash",
        loaded_at="2026-02-08T00:00:00Z",
    )


def test_load_registry_snapshot_hash(tmp_path):
    data = {"files": [{"file_id": "01999000042260126011"}], "note": "sample"}
    path = tmp_path / "registry.json"
    raw = json.dumps(data).encode("utf-8")
    path.write_bytes(raw)

    snapshot = load_registry_snapshot(path)

    assert snapshot.files == data["files"]
    assert snapshot.metadata["note"] == "sample"
    assert snapshot.registry_hash == sha256(raw).hexdigest()


def test_load_registry_snapshot_missing_files(tmp_path):
    path = tmp_path / "registry.json"
    path.write_text(json.dumps({"note": "missing"}), encoding="utf-8")

    try:
        load_registry_snapshot(path)
        assert False, "Expected ValueError for missing files list"
    except ValueError as exc:
        assert "files" in str(exc)


def test_load_metrics_snapshot_shape(tmp_path):
    payload = {
        "generated_at": "2026-02-08T00:00:00Z",
        "source_registry_hash": "abc123",
        "metrics": {"total_files": {"value": 3}},
    }
    path = tmp_path / "metrics.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    result = load_metrics_snapshot(path)

    assert result["generated_at"] == payload["generated_at"]
    assert result["source_registry_hash"] == "abc123"
    assert result["metrics"]["total_files"]["value"] == 3


def test_metric_engine_basic_counts():
    files = [
        {
            "file_id": "01999000042260126011",
            "relative_path": "src/a.py",
            "extension": "py",
            "artifact_kind": "PYTHON_MODULE",
            "layer": "CORE",
            "canonicality": "CANONICAL",
            "status": None,
        },
        {
            "file_id": "bad",
            "relative_path": "docs/readme.md",
            "extension": ".md",
            "artifact_kind": None,
            "layer": None,
            "canonicality": None,
            "status": None,
        },
        {
            "file_id": None,
            "relative_path": "config/settings.yaml",
            "extension": "yaml",
            "artifact_kind": "YAML_DATA",
            "layer": "CONFIGURATION",
            "canonicality": "LEGACY",
            "status": None,
        },
    ]
    engine = MetricEngine(make_snapshot(files))

    assert engine.get_metric("total_files")["value"] == 3
    assert engine.get_metric("files_with_file_id")["value"] == 2
    assert engine.get_metric("files_missing_file_id")["value"] == 1
    assert engine.get_metric("invalid_file_id_format")["value"] == 1

    by_extension = engine.get_metric("by_extension")["value"]
    assert by_extension[".py"]["count"] == 1
    assert by_extension[".md"]["count"] == 1
    assert by_extension[".yaml"]["count"] == 1

    by_layer = engine.get_metric("by_layer")["value"]
    assert by_layer["CORE"]["count"] == 1
    assert by_layer["CONFIGURATION"]["count"] == 1
    assert by_layer["UNKNOWN"]["count"] == 1

    canon = engine.get_metric("canonical_vs_legacy")["value"]
    assert canon["CANONICAL"]["count"] == 1
    assert canon["LEGACY"]["count"] == 1
    assert canon["UNKNOWN"]["count"] == 1


def test_metric_engine_duplicate_ids():
    files = [
        {"file_id": "01999000042260126011", "relative_path": "a.py"},
        {"file_id": "01999000042260126011", "relative_path": "b.py"},
    ]
    engine = MetricEngine(make_snapshot(files))
    metric = engine.get_metric("duplicate_file_id", allow_heavy=True)

    assert metric["value"] == 2
    assert engine.duplicate_ids(allow_heavy=True) == ["01999000042260126011"]


def test_metric_engine_snapshot_overrides():
    files = [{"file_id": "01999000042260126011"}, {"file_id": None}]
    snapshot_metrics = {
        "generated_at": "2026-02-08T00:00:00Z",
        "metrics": {
            "total_files": {"value": 10},
            "files_with_file_id": {"value": 9},
            "files_missing_file_id": {"value": 1},
        },
    }
    engine = MetricEngine(make_snapshot(files), snapshot_metrics)

    assert engine.get_metric("total_files")["value"] == 10
    assert engine.get_metric("files_with_file_id")["value"] == 9
    assert engine.get_metric("files_missing_file_id")["value"] == 1
    assert engine.get_metric("invalid_file_id_format")["value"] == 0


def test_issue_list_severity_order():
    files = [
        {
            "file_id": "01999000042260126011",
            "relative_path": "a.py",
            "artifact_kind": "PYTHON_MODULE",
            "layer": "CORE",
            "canonicality": "CANONICAL",
            "status": None,
        },
        {
            "file_id": "01999000042260126011",
            "relative_path": "b.py",
            "artifact_kind": "PYTHON_MODULE",
            "layer": "CORE",
            "canonicality": "CANONICAL",
            "status": None,
        },
        {
            "file_id": "bad",
            "relative_path": "c.py",
            "artifact_kind": None,
            "layer": None,
            "canonicality": None,
            "status": None,
        },
        {
            "file_id": None,
            "relative_path": "d.py",
            "artifact_kind": None,
            "layer": None,
            "canonicality": None,
            "status": None,
        },
    ]
    engine = MetricEngine(make_snapshot(files))
    issues = engine.build_issue_list(allow_heavy=True)

    severity_rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    for left, right in zip(issues, issues[1:]):
        assert severity_rank[left.severity] <= severity_rank[right.severity]

    codes = {issue.code for issue in issues}
    assert "DUPLICATE_FILE_ID" in codes
    assert "INVALID_FILE_ID_FORMAT" in codes
    assert "MISSING_FILE_ID" in codes
    assert "MISSING_FIELDS" in codes


def test_export_helpers(tmp_path):
    issues = [
        Issue("HIGH", "INVALID_FILE_ID_FORMAT", "bad", "a.py", "file_id must be 20 digits"),
        Issue("CRITICAL", "MISSING_FILE_ID", "", "b.py", "file_id is missing"),
    ]
    json_path = tmp_path / "issues.json"
    csv_path = tmp_path / "issues.csv"

    RegistryTuiApp._export_issues_json(json_path, issues)
    RegistryTuiApp._export_issues_csv(csv_path, issues)

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data[0]["code"] == "INVALID_FILE_ID_FORMAT"

    with csv_path.open("r", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    assert rows[0] == ["severity", "code", "file_id", "relative_path", "detail"]
    assert rows[1][1] == "INVALID_FILE_ID_FORMAT"
