"""Tool: plan.validate_ssot."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from ..utils import defects as defect_utils
from ..utils import hashing, paths
from ..utils.subprocess_runner import python_executable, run_command
from ..utils.tool_result import build_envelope


def handle(args: Dict[str, Any], tool_spec: Dict[str, Any], _config: Dict[str, Any]) -> Dict[str, Any]:
    context = args["context"]
    repo_root = context["repo_root"]
    run_id = context["run_id"]

    plan_path = args["plan_path"]
    evidence_path = _resolve_evidence_path(args, tool_spec, run_id)
    write_evidence_flag = args.get("write_evidence", True)
    timeout_s = args.get("timeout_s", 300)

    resolved_evidence, ok = paths.resolve_under_root(str(evidence_path), repo_root)
    if not ok:
        return _error_result(tool_spec, run_id, evidence_path, write_evidence_flag, "REPO_ROOT_VIOLATION", "evidence_path is outside repo_root", args)

    resolved_plan, ok = paths.resolve_under_root(plan_path, repo_root)
    if not ok:
        return _error_result(tool_spec, run_id, resolved_evidence, write_evidence_flag, "REPO_ROOT_VIOLATION", "plan_path is outside repo_root", args)
    if not resolved_plan.exists():
        return _error_result(tool_spec, run_id, resolved_evidence, write_evidence_flag, "INPUT_FILE_NOT_FOUND", f"plan_path not found: {resolved_plan}", args)

    script_path = Path(__file__).resolve().parents[2] / "scripts" / "P_01260207233100000260_validate_single_source_of_truth.py"
    if not script_path.exists():
        return _error_result(tool_spec, run_id, resolved_evidence, write_evidence_flag, "EXEC_BINDING_MISSING", "ssot validation script not found", args)

    evidence_dir = resolved_evidence.parent
    args_list = [
        python_executable(),
        str(script_path),
        "--plan-file",
        str(resolved_plan),
        "--evidence-dir",
        str(evidence_dir),
    ]

    try:
        exit_code, stdout, stderr = run_command(args_list, timeout_s)
    except Exception:
        return _error_result(tool_spec, run_id, resolved_evidence, write_evidence_flag, "TIMEOUT", "ssot validation timed out", args)

    script_evidence = evidence_dir / "ssot_validation.json"
    defects = []
    artifacts_emitted = []
    hashes = {}
    if script_evidence.exists():
        artifacts_emitted.append(str(script_evidence))
        hashes["ssot_evidence_sha256"] = hashing.sha256_file(script_evidence)
        try:
            evidence_data = json.loads(script_evidence.read_text(encoding="utf-8"))
            defects = defect_utils.from_ssot_evidence(evidence_data)
        except json.JSONDecodeError:
            defects.append(
                {
                    "severity": "high",
                    "code": "INVALID_JSON",
                    "location": str(script_evidence),
                    "message": "ssot evidence JSON is invalid",
                }
            )

    status = "pass" if exit_code == 0 else "fail"
    summary = stdout.strip() or stderr.strip() or "ssot validation complete"

    return build_envelope(
        tool=tool_spec["tool"],
        tool_version=tool_spec["tool_version"],
        status=status,
        exit_code=exit_code,
        run_id=run_id,
        evidence_path=resolved_evidence,
        summary=summary,
        defects=defects,
        artifacts_emitted=artifacts_emitted,
        hashes=hashes,
        write_evidence_flag=write_evidence_flag,
        input_payload=args,
    )


def _resolve_evidence_path(args: Dict[str, Any], tool_spec: Dict[str, Any], run_id: str) -> Path:
    template = tool_spec.get("default_evidence_path_template", "")
    raw = args.get("evidence_path") or template
    raw = raw.replace("{run_id}", run_id)
    return Path(raw)


def _error_result(
    tool_spec: Dict[str, Any],
    run_id: str,
    evidence_path: Path,
    write_evidence_flag: bool,
    code: str,
    message: str,
    input_payload: Dict[str, Any],
) -> Dict[str, Any]:
    defect = {
        "severity": "high",
        "code": code,
        "location": "mcp.plan.validate_ssot",
        "message": message,
    }
    return build_envelope(
        tool=tool_spec["tool"],
        tool_version=tool_spec["tool_version"],
        status="error",
        exit_code=1,
        run_id=run_id,
        evidence_path=evidence_path,
        summary=message,
        defects=[defect],
        artifacts_emitted=[],
        hashes={},
        write_evidence_flag=write_evidence_flag,
        input_payload=input_payload,
    )
