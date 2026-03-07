# DOC_LINK: DOC-ERROR-ENGINE-PIPELINE-ENGINE-118
"""Minimal deterministic pipeline engine implementation.

Coordinates hashing, plugin execution, temp-dir isolation, and reporting.
"""

# DOC_ID: DOC-ERROR-ENGINE-PIPELINE-ENGINE-118
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from phase6_error_recovery.modules.error_engine.src.shared.utils.jsonl_manager import (
    append as jsonl_append,
)
from phase6_error_recovery.modules.error_engine.src.shared.utils.time import (
    new_run_id,
    utc_now_iso,
)
from phase6_error_recovery.modules.error_engine.src.shared.utils.types import (
    PipelineReport,
    PipelineSummary,
    PluginIssue,
    PluginResult,
)


def _report_to_dict(rep: PipelineReport) -> Dict[str, object]:
    return {
        "run_id": rep.run_id,
        "file_in": rep.file_in,
        "file_out": rep.file_out,
        "timestamp_utc": rep.timestamp_utc,
        "toolchain": rep.toolchain,
        "summary": (
            {
                "plugins_run": rep.summary.plugins_run if rep.summary else 0,
                "total_errors": rep.summary.total_errors if rep.summary else 0,
                "total_warnings": rep.summary.total_warnings if rep.summary else 0,
                "auto_fixed": rep.summary.auto_fixed if rep.summary else 0,
            }
            if rep.summary
            else None
        ),
        "issues": [
            {
                "tool": i.tool,
                "path": i.path,
                "line": i.line,
                "column": i.column,
                "code": i.code,
                "category": i.category,
                "severity": i.severity,
                "message": i.message,
            }
            for i in rep.issues
        ],
        "status": rep.status,
    }


class PipelineEngine:
    """Co-ordinates validation work across the GUI and plugin system."""

    def __init__(
        self,
        plugin_manager,
        hash_cache,
    ) -> None:
        self._plugin_manager = plugin_manager
        self._hash_cache = hash_cache

    def process_files(self, file_paths: Iterable[Path]) -> List[PipelineReport]:
        """Process a batch of files through the validation pipeline."""
        reports: List[PipelineReport] = []
        for file_path in file_paths:
            reports.append(self.process_file(file_path))
        return reports

    def process_file(self, file_path: Path) -> PipelineReport:
        """Validate a single file using the registered plugins."""
        run_id = new_run_id()
        ts = utc_now_iso()

        # Incremental skip check
        changed = self._hash_cache.has_changed(file_path)
        if not changed:
            report = PipelineReport(
                run_id=run_id,
                file_in=str(file_path),
                file_out=None,
                timestamp_utc=ts,
                toolchain={},
                summary=PipelineSummary(
                    plugins_run=0, total_errors=0, total_warnings=0, auto_fixed=0
                ),
                issues=[],
                status="skipped",
            )
            # Append event to JSONL
            jsonl_append(
                Path("pipeline_errors.jsonl"),
                {
                    "event": "skipped",
                    "file": str(file_path),
                    "run_id": run_id,
                    "ts": ts,
                },
            )
            return report

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            tmp_file = tmpdir_path / file_path.name
            shutil.copy2(file_path, tmp_file)

            # Discover/apply plugins
            self._plugin_manager.discover()
            plugin_results = self._run_plugins(tmp_file)

            # Copy out with validated name
            out_name = f"{file_path.stem}_VALIDATED_{ts.replace(':','').replace('-','').replace('.','')}_{run_id}{file_path.suffix}"
            out_file = file_path.parent / out_name
            shutil.copy2(tmp_file, out_file)

        # Generate and persist report
        report = self._generate_report(file_path, plugin_results, run_id)
        report.file_out = str(out_file)
        # Write per-file JSON next to output
        report_json_path = out_file.with_suffix(out_file.suffix + ".json")
        report_json_path.write_text(
            json.dumps(_report_to_dict(report), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # Append aggregated JSONL
        jsonl_append(
            Path("pipeline_errors.jsonl"),
            {
                "event": "validated",
                "file": str(file_path),
                "out": str(out_file),
                "run_id": run_id,
                "ts": ts,
                "summary": {
                    "errors": report.summary.total_errors if report.summary else 0,
                    "warnings": report.summary.total_warnings if report.summary else 0,
                },
            },
        )

        # Update cache
        had_errors = (report.summary.total_errors > 0) if report.summary else False
        self._hash_cache.mark_validated(file_path, had_errors=had_errors)
        self._hash_cache.save()

        return report

    def _run_plugins(self, file_path: Path) -> List[PluginResult]:
        """Execute all applicable plugins for the given file."""
        plugins = self._plugin_manager.get_plugins_for_file(file_path)
        results = self._plugin_manager.run_plugins(plugins, file_path)
        return results

    def _generate_report(
        self,
        file_path: Path,
        plugin_results: List[PluginResult],
        run_id: Optional[str] = None,
    ) -> PipelineReport:
        """Generate pipeline report with enhanced metrics"""
        from phase6_error_recovery.modules.error_engine.src.shared.utils.layer_classifier import (
            classify_error_layer,
            is_auto_repairable,
        )

        if run_id is None:
            run_id = new_run_id()

        issues: List[PluginIssue] = []
        toolchain: Dict[str, str] = {}
        total_errors = 0
        total_warnings = 0
        auto_fixed_count = 0
        auto_repairable_count = 0
        requires_human_count = 0

        for result in plugin_results:
            toolchain[result.plugin_id] = "executed"

            for issue in result.issues:
                # Classify layer
                if issue.category:
                    issue.layer = classify_error_layer(issue.category)

                issues.append(issue)

                if issue.severity == "error":
                    total_errors += 1
                    # Check if auto-repairable
                    has_fix = result.metadata.get("has_fix_method", False)
                    if is_auto_repairable(issue.category or "", has_fix):
                        auto_repairable_count += 1
                    else:
                        requires_human_count += 1
                elif issue.severity == "warning":
                    total_warnings += 1

            # Count auto-fixes from metadata
            auto_fixed_count += result.metadata.get("auto_fixed", 0)

        summary = PipelineSummary(
            plugins_run=len(plugin_results),
            total_errors=total_errors,
            total_warnings=total_warnings,
            auto_fixed=auto_fixed_count,
            auto_repairable=auto_repairable_count,
            requires_human=requires_human_count,
        )

        return PipelineReport(
            run_id=run_id,
            file_in=str(file_path),
            file_out=None,
            timestamp_utc=utc_now_iso(),
            toolchain=toolchain,
            summary=summary,
            issues=issues,
            status="completed" if total_errors == 0 else "failed",
        )
