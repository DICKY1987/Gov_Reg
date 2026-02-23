#!/usr/bin/env python3
"""
Registry TUI - read-only terminal UI for registry health.

FILE_ID: 01999000042260126011
DOC_ID: P_01999000042260126011
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

TEXTUAL_AVAILABLE = True
try:
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.screen import Screen
    from textual.widgets import DataTable, Footer, Header, Static
except ImportError:
    TEXTUAL_AVAILABLE = False
    App = object  # type: ignore[assignment]
    Screen = object  # type: ignore[assignment]
    ComposeResult = object  # type: ignore[assignment]
    DataTable = object  # type: ignore[assignment]
    Footer = object  # type: ignore[assignment]
    Header = object  # type: ignore[assignment]
    Static = object  # type: ignore[assignment]
    Binding = None  # type: ignore[assignment]


def _binding(*args: str) -> Optional["Binding"]:
    if not TEXTUAL_AVAILABLE:
        return None
    return Binding(*args)


ID_REGEX = re.compile(r"^[0-9]{20}$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass(frozen=True)
class RegistrySnapshot:
    files: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    source_path: Path
    registry_hash: str
    loaded_at: str


@dataclass(frozen=True)
class Issue:
    severity: str
    code: str
    file_id: str
    relative_path: str
    detail: str


def load_registry_snapshot(path: Path) -> RegistrySnapshot:
    raw = path.read_bytes()
    digest = sha256(raw).hexdigest()
    data = json.loads(raw.decode("utf-8"))
    files = data.get("files")
    if not isinstance(files, list):
        raise ValueError("Registry snapshot missing 'files' list")
    metadata = {k: v for k, v in data.items() if k != "files"}
    return RegistrySnapshot(
        files=files,
        metadata=metadata,
        source_path=path,
        registry_hash=digest,
        loaded_at=utc_now(),
    )


def load_metrics_snapshot(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    metrics = data.get("metrics", data)
    return {
        "generated_at": data.get("generated_at"),
        "source_registry_hash": data.get("source_registry_hash") or data.get("registry_hash"),
        "metrics": metrics if isinstance(metrics, dict) else {},
    }


class MetricEngine:
    def __init__(self, snapshot: RegistrySnapshot, metrics_snapshot: Optional[Dict[str, Any]] = None) -> None:
        self.snapshot = snapshot
        self.metrics_snapshot = metrics_snapshot or {}
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._duplicate_ids: Optional[List[str]] = None

    def _total_files(self) -> int:
        return len(self.snapshot.files)

    def _metric_from_snapshot(self, metric_id: str) -> Optional[Dict[str, Any]]:
        metrics = self.metrics_snapshot.get("metrics", {})
        raw = metrics.get(metric_id)
        if raw is None:
            return None
        result: Dict[str, Any] = {
            "metric_id": metric_id,
            "computed_at": self.metrics_snapshot.get("generated_at") or utc_now(),
        }
        if isinstance(raw, dict) and "value" in raw:
            result.update(raw)
            result.setdefault("metric_id", metric_id)
            result.setdefault("computed_at", self.metrics_snapshot.get("generated_at") or utc_now())
            return result
        result["value"] = raw
        result["percentage"] = None
        result["affected_records"] = None
        return result

    def get_metric(self, metric_id: str, allow_heavy: bool = False) -> Optional[Dict[str, Any]]:
        if metric_id in self._cache:
            return self._cache[metric_id]
        if metric_id == "duplicate_file_id" and not allow_heavy:
            return None

        snapshot_metric = None
        if metric_id != "duplicate_file_id":
            snapshot_metric = self._metric_from_snapshot(metric_id)
        if snapshot_metric is not None and metric_id in {"total_files", "files_with_file_id", "files_missing_file_id"}:
            self._cache[metric_id] = snapshot_metric
            return snapshot_metric

        compute_map = {
            "total_files": self._compute_total_files,
            "files_with_file_id": self._compute_files_with_file_id,
            "files_missing_file_id": self._compute_files_missing_file_id,
            "invalid_file_id_format": self._compute_invalid_file_id_format,
            "duplicate_file_id": self._compute_duplicate_file_id,
            "by_extension": self._compute_by_extension,
            "by_artifact_kind": self._compute_by_artifact_kind,
            "by_layer": self._compute_by_layer,
            "canonical_vs_legacy": self._compute_canonical_vs_legacy,
        }
        func = compute_map.get(metric_id)
        if func is None:
            return None
        result = func()
        self._cache[metric_id] = result
        return result

    def _compute_total_files(self) -> Dict[str, Any]:
        return {
            "metric_id": "total_files",
            "value": self._total_files(),
            "percentage": 100.0,
            "affected_records": None,
            "computed_at": utc_now(),
        }

    def _compute_files_with_file_id(self) -> Dict[str, Any]:
        count = sum(1 for f in self.snapshot.files if f.get("file_id"))
        total = self._total_files()
        return {
            "metric_id": "files_with_file_id",
            "value": count,
            "percentage": (count / total * 100.0) if total else 0.0,
            "affected_records": None,
            "computed_at": utc_now(),
        }

    def _compute_files_missing_file_id(self) -> Dict[str, Any]:
        count = sum(1 for f in self.snapshot.files if not f.get("file_id"))
        total = self._total_files()
        return {
            "metric_id": "files_missing_file_id",
            "value": count,
            "percentage": (count / total * 100.0) if total else 0.0,
            "affected_records": [f.get("relative_path") for f in self.snapshot.files if not f.get("file_id")],
            "computed_at": utc_now(),
        }

    def _compute_invalid_file_id_format(self) -> Dict[str, Any]:
        bad = [f for f in self.snapshot.files if f.get("file_id") and not ID_REGEX.match(str(f.get("file_id")))]
        total = self._total_files()
        return {
            "metric_id": "invalid_file_id_format",
            "value": len(bad),
            "percentage": (len(bad) / total * 100.0) if total else 0.0,
            "affected_records": [f.get("relative_path") for f in bad],
            "computed_at": utc_now(),
        }

    def _compute_duplicate_file_id(self) -> Dict[str, Any]:
        counts: Dict[str, int] = {}
        for f in self.snapshot.files:
            file_id = f.get("file_id")
            if not file_id:
                continue
            file_id = str(file_id)
            counts[file_id] = counts.get(file_id, 0) + 1
        duplicates = [fid for fid, count in counts.items() if count > 1]
        affected = []
        for f in self.snapshot.files:
            file_id = f.get("file_id")
            if file_id and str(file_id) in duplicates:
                affected.append(f.get("relative_path"))
        self._duplicate_ids = duplicates
        total = self._total_files()
        return {
            "metric_id": "duplicate_file_id",
            "value": len(affected),
            "percentage": (len(affected) / total * 100.0) if total else 0.0,
            "affected_records": affected,
            "duplicate_ids": duplicates,
            "computed_at": utc_now(),
        }

    def _group_by_field(self, field: str, fallback: str = "UNKNOWN") -> Dict[str, Dict[str, float]]:
        total = self._total_files()
        counts: Dict[str, int] = {}
        for f in self.snapshot.files:
            key = f.get(field) or fallback
            key = str(key)
            counts[key] = counts.get(key, 0) + 1
        return {
            key: {
                "count": count,
                "percentage": (count / total * 100.0) if total else 0.0,
            }
            for key, count in sorted(counts.items(), key=lambda item: item[0])
        }

    def _compute_by_extension(self) -> Dict[str, Any]:
        total = self._total_files()
        counts: Dict[str, int] = {}
        for f in self.snapshot.files:
            ext = f.get("extension")
            if not ext:
                rel = f.get("relative_path") or f.get("filename") or ""
                ext = Path(rel).suffix.lower()
            ext = ext.lower() if ext else "(none)"
            if ext and ext != "(none)" and not ext.startswith("."):
                ext = f".{ext}"
            counts[ext] = counts.get(ext, 0) + 1
        value = {
            ext: {"count": count, "percentage": (count / total * 100.0) if total else 0.0}
            for ext, count in sorted(counts.items(), key=lambda item: item[0])
        }
        return {
            "metric_id": "by_extension",
            "value": value,
            "percentage": None,
            "affected_records": None,
            "computed_at": utc_now(),
        }

    def _compute_by_artifact_kind(self) -> Dict[str, Any]:
        value = self._group_by_field("artifact_kind")
        return {
            "metric_id": "by_artifact_kind",
            "value": value,
            "percentage": None,
            "affected_records": None,
            "computed_at": utc_now(),
        }

    def _compute_by_layer(self) -> Dict[str, Any]:
        value = self._group_by_field("layer")
        return {
            "metric_id": "by_layer",
            "value": value,
            "percentage": None,
            "affected_records": None,
            "computed_at": utc_now(),
        }

    def _compute_canonical_vs_legacy(self) -> Dict[str, Any]:
        counts: Dict[str, int] = {}
        total = self._total_files()
        for f in self.snapshot.files:
            key = f.get("canonicality") or f.get("status") or "UNKNOWN"
            key = str(key)
            counts[key] = counts.get(key, 0) + 1
        value = {
            key: {"count": count, "percentage": (count / total * 100.0) if total else 0.0}
            for key, count in sorted(counts.items(), key=lambda item: item[0])
        }
        return {
            "metric_id": "canonical_vs_legacy",
            "value": value,
            "percentage": None,
            "affected_records": None,
            "computed_at": utc_now(),
        }

    def duplicate_ids(self, allow_heavy: bool = False) -> List[str]:
        if self._duplicate_ids is None and allow_heavy:
            self.get_metric("duplicate_file_id", allow_heavy=True)
        return self._duplicate_ids or []

    def build_issue_list(self, allow_heavy: bool = False) -> List[Issue]:
        duplicate_ids = set(self.duplicate_ids(allow_heavy=allow_heavy))
        issues: List[Issue] = []
        required_fields = ["artifact_kind", "layer", "canonicality", "status"]
        for rec in self.snapshot.files:
            file_id = str(rec.get("file_id") or "")
            rel = rec.get("relative_path") or rec.get("filename") or ""
            if not file_id:
                issues.append(Issue("CRITICAL", "MISSING_FILE_ID", "", rel, "file_id is missing"))
            elif not ID_REGEX.match(file_id):
                issues.append(Issue("HIGH", "INVALID_FILE_ID_FORMAT", file_id, rel, "file_id must be 20 digits"))
            if file_id and file_id in duplicate_ids:
                issues.append(Issue("CRITICAL", "DUPLICATE_FILE_ID", file_id, rel, "file_id appears multiple times"))
            missing_fields = [field for field in required_fields if not rec.get(field)]
            if missing_fields:
                issues.append(Issue("MEDIUM", "MISSING_FIELDS", file_id, rel, f"missing: {', '.join(missing_fields)}"))
            canonicality = (rec.get("canonicality") or rec.get("status") or "").upper()
            if canonicality and canonicality not in {"CANONICAL", "CURRENT"}:
                issues.append(Issue("LOW", "LEGACY_STATUS", file_id, rel, f"canonicality={canonicality}"))
        severity_rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        return sorted(issues, key=lambda issue: (severity_rank.get(issue.severity, 9), issue.relative_path))


class DashboardScreen(Screen):
    BINDINGS = [binding for binding in (_binding("h", "heavy_metrics", "Heavy metrics"),) if binding]

    def compose(self) -> ComposeResult:
        yield Header()
        self.summary = Static(id="summary")
        self.detail = Static(id="detail")
        self.status = Static(id="status")
        yield self.summary
        yield self.detail
        yield self.status
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_view()

    def action_heavy_metrics(self) -> None:
        self.app.compute_heavy_metrics()

    def refresh_view(self) -> None:
        app = self.app
        if app.snapshot is None or app.metrics is None:
            self.summary.update("No snapshot loaded.")
            return
        total = app.metric_value("total_files") or 0
        with_id = app.metric_value("files_with_file_id") or 0
        missing = app.metric_value("files_missing_file_id") or 0
        invalid = app.metric_value("invalid_file_id_format") or 0
        duplicate = app.metric_value("duplicate_file_id")
        coverage_pct = (with_id / total * 100.0) if total else 0.0
        violations = missing + invalid
        violations_text = f"{violations}" if duplicate is None else f"{violations + duplicate}"
        dup_text = "pending" if duplicate is None else str(duplicate)
        summary_lines = [
            f"Total files: {total}",
            f"ID coverage: {coverage_pct:.1f}%",
            f"Missing ID count: {missing}",
            f"Invalid ID format: {invalid}",
            f"Duplicate IDs: {dup_text}",
            f"Violations count: {violations_text}",
        ]
        self.summary.update("\n".join(summary_lines))

        canon = app.metric_dict("canonical_vs_legacy") or {}
        canon_lines = ["Canonicality split:"]
        for key, entry in canon.items():
            canon_lines.append(f"- {key}: {entry.get('count', 0)} ({entry.get('percentage', 0.0):.1f}%)")
        self.detail.update("\n".join(canon_lines))
        self.status.update(app.status_message)


class BreakdownScreen(Screen):
    BINDINGS = [
        binding
        for binding in (
            _binding("d", "cycle_dimension", "Dimension"),
            _binding("1", "dimension_extension", "Extension"),
            _binding("2", "dimension_artifact", "Artifact"),
            _binding("3", "dimension_layer", "Layer"),
        )
        if binding
    ]

    def __init__(self) -> None:
        super().__init__()
        self.dimension = "by_extension"

    def compose(self) -> ComposeResult:
        yield Header()
        self.title = Static(id="title")
        self.table = DataTable(id="breakdown")
        self.status = Static(id="status")
        yield self.title
        yield self.table
        yield self.status
        yield Footer()

    def on_mount(self) -> None:
        self.table.add_columns("Key", "Count", "Percent")
        self.refresh_view()

    def action_cycle_dimension(self) -> None:
        order = ["by_extension", "by_artifact_kind", "by_layer"]
        self.dimension = order[(order.index(self.dimension) + 1) % len(order)]
        self.refresh_view()

    def action_dimension_extension(self) -> None:
        self.dimension = "by_extension"
        self.refresh_view()

    def action_dimension_artifact(self) -> None:
        self.dimension = "by_artifact_kind"
        self.refresh_view()

    def action_dimension_layer(self) -> None:
        self.dimension = "by_layer"
        self.refresh_view()

    def refresh_view(self) -> None:
        label = {
            "by_extension": "Breakdown: Extension",
            "by_artifact_kind": "Breakdown: Artifact Kind",
            "by_layer": "Breakdown: Layer",
        }[self.dimension]
        self.title.update(label)
        self.table.clear()
        data = app.metric_dict(self.dimension)
        if not data:
            return
        for key, entry in data.items():
            self.table.add_row(key, str(entry.get("count", 0)), f"{entry.get('percentage', 0.0):.1f}%")
        self.status.update(app.status_message)


class CoverageScreen(Screen):
    BINDINGS = [binding for binding in (_binding("enter", "inspect", "Inspect"),) if binding]

    def __init__(self) -> None:
        super().__init__()
        self.issues: List[Issue] = []

    def compose(self) -> ComposeResult:
        yield Header()
        self.table = DataTable(id="coverage")
        self.status = Static(id="status")
        yield self.table
        yield self.status
        yield Footer()

    def on_mount(self) -> None:
        self.table.add_columns("Severity", "Issue", "File ID", "Relative Path", "Detail")
        self.refresh_view()

    def refresh_view(self) -> None:
        self.table.clear()
        self.issues = self.app.metric_issues()
        for issue in self.issues:
            self.table.add_row(
                issue.severity,
                issue.code,
                issue.file_id or "-",
                issue.relative_path,
                issue.detail,
            )
        self.status.update(app.status_message)

    def action_inspect(self) -> None:
        if not self.issues:
            return
        row = self.table.cursor_row
        if row is None or row >= len(self.issues):
            return
        issue = self.issues[row]
        self.app.open_inspector(issue)


class InspectorScreen(Screen):
    def __init__(self) -> None:
        super().__init__()
        self.issue: Optional[Issue] = None

    def compose(self) -> ComposeResult:
        yield Header()
        self.detail = Static(id="detail")
        self.status = Static(id="status")
        yield self.detail
        yield self.status
        yield Footer()

    def set_issue(self, issue: Optional[Issue]) -> None:
        self.issue = issue
        self.refresh_view()

    def refresh_view(self) -> None:
        if self.issue is None:
            self.detail.update("No selection.")
            return
        issue = self.issue
        detail_lines = [
            f"Severity: {issue.severity}",
            f"Issue: {issue.code}",
            f"File ID: {issue.file_id or '-'}",
            f"Relative Path: {issue.relative_path}",
            f"Detail: {issue.detail}",
        ]
        self.detail.update("\n".join(detail_lines))
        self.status.update(app.status_message)


class RegistryTuiApp(App):
    CSS = """
    Screen {
        padding: 1 2;
    }
    #summary, #detail, #status, #title {
        margin-bottom: 1;
    }
    #status {
        color: $text-muted;
    }
    """

    BINDINGS = [
        binding
        for binding in (
            _binding("tab", "next_screen", "Next"),
            _binding("shift+tab", "prev_screen", "Prev"),
            _binding("r", "refresh", "Refresh"),
            _binding("e", "export", "Export"),
            _binding("q", "quit", "Quit"),
            _binding("escape", "back", "Back"),
        )
        if binding
    ]

    def __init__(
        self,
        registry_path: Path,
        metrics_snapshot_path: Optional[Path] = None,
        refresh_interval: Optional[int] = None,
        read_only: bool = True,
    ) -> None:
        super().__init__()
        self.registry_path = registry_path
        self.metrics_snapshot_path = metrics_snapshot_path
        self.refresh_interval = refresh_interval
        self.read_only = read_only
        self.snapshot: Optional[RegistrySnapshot] = None
        self.metrics: Optional[MetricEngine] = None
        self.metrics_snapshot: Optional[Dict[str, Any]] = None
        self.status_message = ""
        self.screen_order = ["dashboard", "breakdown", "coverage"]
        self.current_screen_index = 0
        self.last_valid_snapshot: Optional[RegistrySnapshot] = None

    def on_mount(self) -> None:
        self.install_screen(DashboardScreen(), name="dashboard")
        self.install_screen(BreakdownScreen(), name="breakdown")
        self.install_screen(CoverageScreen(), name="coverage")
        self.install_screen(InspectorScreen(), name="inspector")
        self.refresh_data(force=True)
        self.show_screen("dashboard")
        if self.refresh_interval:
            self.set_interval(self.refresh_interval, self.refresh_data)

    def set_status(self, message: str) -> None:
        self.status_message = message
        screen = self.screen
        if isinstance(screen, (DashboardScreen, BreakdownScreen, CoverageScreen, InspectorScreen)):
            if hasattr(screen, "status"):
                screen.status.update(message)

    def show_screen(self, name: str) -> None:
        if hasattr(self, "switch_screen"):
            self.switch_screen(name)
        else:
            self.push_screen(name)

    def action_next_screen(self) -> None:
        self.current_screen_index = (self.current_screen_index + 1) % len(self.screen_order)
        self.show_screen(self.screen_order[self.current_screen_index])

    def action_prev_screen(self) -> None:
        self.current_screen_index = (self.current_screen_index - 1) % len(self.screen_order)
        self.show_screen(self.screen_order[self.current_screen_index])

    def action_back(self) -> None:
        if self.screen.name == "inspector":
            self.show_screen(self.screen_order[self.current_screen_index])

    def refresh_data(self, force: bool = False) -> None:
        try:
            snapshot = load_registry_snapshot(self.registry_path)
        except Exception as exc:
            if self.last_valid_snapshot is None:
                raise
            self.snapshot = self.last_valid_snapshot
            self.metrics = MetricEngine(self.snapshot, self.metrics_snapshot)
            self.set_status(f"Registry load error: {exc}. Using last valid snapshot.")
            return
        if not force and self.snapshot and snapshot.registry_hash == self.snapshot.registry_hash:
            self.set_status("Registry unchanged. Metrics reused.")
            return

        self.snapshot = snapshot
        self.last_valid_snapshot = snapshot
        self.metrics_snapshot = None
        warning = None
        if self.metrics_snapshot_path:
            try:
                self.metrics_snapshot = load_metrics_snapshot(self.metrics_snapshot_path)
                source_hash = self.metrics_snapshot.get("source_registry_hash")
                if source_hash and source_hash != snapshot.registry_hash:
                    warning = "Metrics snapshot hash mismatch. Live metrics only."
                    self.metrics_snapshot = None
            except Exception as exc:
                warning = f"Metrics snapshot error: {exc}. Live metrics only."
        self.metrics = MetricEngine(snapshot, self.metrics_snapshot)
        if warning:
            self.set_status(warning)
        else:
            self.set_status("Snapshot loaded.")
        self.refresh_views()

    def refresh_views(self) -> None:
        for name in ["dashboard", "breakdown"]:
            screen = self.get_screen(name)
            if hasattr(screen, "refresh_view"):
                screen.refresh_view()
        current_name = getattr(self.screen, "name", None)
        if current_name == "coverage":
            screen = self.get_screen("coverage")
            if hasattr(screen, "refresh_view"):
                screen.refresh_view()

    def metric_value(self, metric_id: str, allow_heavy: bool = False) -> Optional[int]:
        if self.metrics is None:
            return None
        metric = self.metrics.get_metric(metric_id, allow_heavy=allow_heavy)
        if metric is None:
            return None
        value = metric.get("value")
        return int(value) if isinstance(value, (int, float)) else None

    def metric_dict(self, metric_id: str) -> Dict[str, Dict[str, float]]:
        if self.metrics is None:
            return {}
        metric = self.metrics.get_metric(metric_id, allow_heavy=False)
        if metric is None:
            return {}
        value = metric.get("value")
        return value if isinstance(value, dict) else {}

    def metric_issues(self) -> List[Issue]:
        if self.metrics is None:
            return []
        return self.metrics.build_issue_list(allow_heavy=True)

    def compute_heavy_metrics(self) -> None:
        if self.metrics is None:
            return
        self.metrics.get_metric("duplicate_file_id", allow_heavy=True)
        self.refresh_views()

    def open_inspector(self, issue: Issue) -> None:
        screen = self.get_screen("inspector")
        if isinstance(screen, InspectorScreen):
            screen.set_issue(issue)
        self.show_screen("inspector")

    def action_export(self) -> None:
        if self.snapshot is None or self.metrics is None:
            self.set_status("Export failed: no snapshot loaded.")
            return
        reports_dir = Path("REPORTS")
        reports_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%MZ")
        if self.screen.name == "coverage":
            issues = self.metric_issues()
            json_path = reports_dir / f"registry_tui_issues_{timestamp}.json"
            csv_path = reports_dir / f"registry_tui_issues_{timestamp}.csv"
            self._export_issues_json(json_path, issues)
            self._export_issues_csv(csv_path, issues)
            self.set_status(f"Exported issues: {json_path} and {csv_path}")
        else:
            metrics = self._metrics_snapshot_export()
            json_path = reports_dir / f"registry_tui_snapshot_{timestamp}.json"
            json_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
            self.set_status(f"Exported metrics: {json_path}")

    def _metrics_snapshot_export(self) -> Dict[str, Any]:
        metrics_out = {}
        for metric_id in [
            "total_files",
            "files_with_file_id",
            "files_missing_file_id",
            "invalid_file_id_format",
            "duplicate_file_id",
            "by_extension",
            "by_artifact_kind",
            "by_layer",
            "canonical_vs_legacy",
        ]:
            metric = self.metrics.get_metric(metric_id, allow_heavy=(metric_id == "duplicate_file_id"))
            if metric is not None:
                metrics_out[metric_id] = {
                    "value": metric.get("value"),
                    "percentage": metric.get("percentage"),
                    "affected_records": metric.get("affected_records"),
                }
        return {
            "generated_at": utc_now(),
            "source_registry_hash": self.snapshot.registry_hash,
            "metrics": metrics_out,
        }

    @staticmethod
    def _export_issues_json(path: Path, issues: Iterable[Issue]) -> None:
        payload = [
            {
                "severity": issue.severity,
                "code": issue.code,
                "file_id": issue.file_id,
                "relative_path": issue.relative_path,
                "detail": issue.detail,
            }
            for issue in issues
        ]
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @staticmethod
    def _export_issues_csv(path: Path, issues: Iterable[Issue]) -> None:
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["severity", "code", "file_id", "relative_path", "detail"])
            for issue in issues:
                writer.writerow([issue.severity, issue.code, issue.file_id, issue.relative_path, issue.detail])


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Registry TUI (read-only).")
    parser.add_argument(
        "--registry-path",
        required=True,
        help="Path to registry JSON snapshot (example: REGISTRY\\01999000042260124503_REGISTRY_file.json)",
    )
    parser.add_argument("--metrics-snapshot", help="Path to precomputed metrics snapshot JSON.")
    parser.add_argument("--refresh-interval", type=int, help="Refresh interval in seconds.")
    parser.add_argument("--read-only", action="store_true", help="Read-only mode (default).")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    if not TEXTUAL_AVAILABLE:
        print("Textual is required. Install with: pip install textual", file=sys.stderr)
        return 1
    args = parse_args(argv)
    registry_path = Path(args.registry_path)
    metrics_snapshot = Path(args.metrics_snapshot) if args.metrics_snapshot else None
    app = RegistryTuiApp(
        registry_path=registry_path,
        metrics_snapshot_path=metrics_snapshot,
        refresh_interval=args.refresh_interval,
        read_only=True,
    )
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
