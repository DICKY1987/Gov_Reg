"""Tool: planning.extract_file_mutation_set."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from ..utils import hashing, paths
from ..utils.subprocess_runner import python_executable, run_command
from ..utils.tool_result import build_envelope


def handle(args: Dict[str, Any], tool_spec: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    context = args["context"]
    repo_root = context["repo_root"]
    run_id = context["run_id"]

    plan_path = args["plan_path"]
    mutation_set_path = args["mutation_set_path"]
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
        return _error_result(tool_spec, run_id, resolved_evidence, write_evidence_flag, "PLAN_NOT_FOUND", f"plan_path not found: {resolved_plan}", args)

    resolved_mutation, ok = paths.resolve_under_root(mutation_set_path, repo_root)
    if not ok:
        return _error_result(tool_spec, run_id, resolved_evidence, write_evidence_flag, "REPO_ROOT_VIOLATION", "mutation_set_path is outside repo_root", args)

    command = _build_command(args, config)
    if not command:
        return _error_result(tool_spec, run_id, resolved_evidence, write_evidence_flag, "PFMS_EXTRACTOR_NOT_IMPLEMENTED", "no PFMS extractor binding configured", args)

    try:
        exit_code, stdout, stderr = run_command(command, timeout_s)
    except Exception:
        return _error_result(tool_spec, run_id, resolved_evidence, write_evidence_flag, "TIMEOUT", "pfms extraction timed out", args)

    artifacts_emitted: List[str] = []
    hashes: Dict[str, str] = {}
    if resolved_mutation.exists():
        artifacts_emitted.append(str(resolved_mutation))
        hashes["mutation_set_sha256"] = hashing.sha256_file(resolved_mutation)

    status = "pass" if exit_code == 0 else "fail"
    summary = stdout.strip() or stderr.strip() or "file mutation set extraction complete"

    return build_envelope(
        tool=tool_spec["tool"],
        tool_version=tool_spec["tool_version"],
        status=status,
        exit_code=exit_code,
        run_id=run_id,
        evidence_path=resolved_evidence,
        summary=summary,
        defects=[],
        artifacts_emitted=artifacts_emitted,
        hashes=hashes,
        write_evidence_flag=write_evidence_flag,
        input_payload=args,
    )


def _build_command(args: Dict[str, Any], config: Dict[str, Any]) -> List[str]:
    if "pfms_extract_command" in config:
        return _format_command(config["pfms_extract_command"], args)
    if "pfms_extract_script" in config:
        return [
            python_executable(),
            str(config["pfms_extract_script"]),
            "--plan-file",
            args["plan_path"],
            "--out",
            args["mutation_set_path"],
        ]
    return []


def _format_command(template: List[str], args: Dict[str, Any]) -> List[str]:
    mapping = {
        "plan_path": args["plan_path"],
        "mutation_set_path": args["mutation_set_path"],
    }
    return [part.format(**mapping) for part in template]


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
        "location": "mcp.planning.extract_file_mutation_set",
        "message": message,
    }
    return build_envelope(
        tool=tool_spec["tool"],
        tool_version=tool_spec["tool_version"],
        status="not_automatable" if code.endswith("NOT_IMPLEMENTED") else "error",
        exit_code=2,
        run_id=run_id,
        evidence_path=evidence_path,
        summary=message,
        defects=[defect],
        artifacts_emitted=[],
        hashes={},
        write_evidence_flag=write_evidence_flag,
        input_payload=input_payload,
    )
