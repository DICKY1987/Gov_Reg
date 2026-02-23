"""GEU governance evidence reporting.

FILE_ID: 0199900004226012491
DOC_ID: DOC-CORE-GEU-GOVERNANCE-REPORT-0199900004226012491
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .P_01999000042260124487_constants import EVIDENCE_JSON, EVIDENCE_MD
from .P_01999000042260124490_io_utils import write_json

JSON = Dict[str, Any]

def build_report(*, findings: List[Any], edge_schema_errors: List[str]) -> JSON:
    error_count = sum(1 for f in findings if getattr(f, "severity", None) == "ERROR")
    warn_count = sum(1 for f in findings if getattr(f, "severity", None) == "WARN")
    return {
        "generated": True,
        "passed": (error_count == 0 and len(edge_schema_errors) == 0),
        "counts": {"errors": error_count + len(edge_schema_errors), "warnings": warn_count},
        "findings": [f.__dict__ for f in findings],
        "edge_schema_errors": edge_schema_errors,
    }

def write_reports(report: JSON) -> None:
    write_json(EVIDENCE_JSON, report)

    lines: List[str] = []
    lines.append("# GEU Validation Report")
    lines.append("")
    lines.append(f"- Passed: {report['passed']}")
    lines.append(f"- Errors: {report['counts']['errors']}")
    lines.append(f"- Warnings: {report['counts']['warnings']}")
    lines.append("")

    if report["edge_schema_errors"]:
        lines.append("## Edge Schema Errors")
        lines.append("")
        for e in report["edge_schema_errors"]:
            lines.append(f"- {e}")
        lines.append("")

    lines.append("## Findings")
    lines.append("")
    if report["findings"]:
        for f in report["findings"]:
            lines.append(f"### {f['rule_id']} ({f['severity']})")
            lines.append(f"- Message: {f['message']}")
            if f.get("geu_id"):
                lines.append(f"- GEU: {f['geu_id']}")
            if f.get("file_id"):
                lines.append(f"- File: {f['file_id']}")
            if f.get("entry_path"):
                lines.append(f"- Entry: {f['entry_path']}")
            if f.get("remediation"):
                lines.append(f"- Remediation: {f['remediation']}")
            lines.append("")
    else:
        lines.append("No findings.")
        lines.append("")

    Path(EVIDENCE_MD).parent.mkdir(parents=True, exist_ok=True)
    Path(EVIDENCE_MD).write_text("\n".join(lines), encoding="utf-8")
