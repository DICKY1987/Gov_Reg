"""Defect normalization helpers."""

from __future__ import annotations

from typing import Any, Dict, List


def from_structure_evidence(evidence: Dict[str, Any]) -> List[Dict[str, Any]]:
    defects: List[Dict[str, Any]] = []
    result = evidence.get("validation_result", {})
    for item in result.get("errors", []):
        defects.append(
            {
                "severity": _map_severity(item.get("severity", "high")),
                "code": item.get("error_code", "LOAD_ERROR"),
                "location": item.get("location", "root"),
                "message": item.get("error_message", "Structure validation error"),
            }
        )
    for item in result.get("warnings", []):
        defects.append(
            {
                "severity": _map_severity(item.get("severity", "low")),
                "code": item.get("warning_code", "STRUCTURE_WARNING"),
                "location": item.get("location", "root"),
                "message": item.get("warning_message", "Structure validation warning"),
            }
        )
    return defects


def from_step_contracts_evidence(evidence: Dict[str, Any]) -> List[Dict[str, Any]]:
    defects: List[Dict[str, Any]] = []
    for item in evidence.get("defects", []):
        problem = item.get("problem", "")
        code = _map_step_contract_code(item.get("category", ""), problem)
        defects.append(
            {
                "severity": _map_severity(item.get("severity", "high")),
                "code": code,
                "location": item.get("location", "/"),
                "message": problem or "Step contract validation defect",
                "why_it_matters": item.get("why_it_matters", ""),
            }
        )
    return defects


def from_ssot_evidence(evidence: Dict[str, Any]) -> List[Dict[str, Any]]:
    defects: List[Dict[str, Any]] = []
    for item in evidence.get("defects", []):
        problem = item.get("problem", "")
        code = _map_ssot_code(item.get("category", ""), problem)
        defects.append(
            {
                "severity": _map_severity(item.get("severity", "high")),
                "code": code,
                "location": item.get("location", "/"),
                "message": problem or "SSOT validation defect",
                "why_it_matters": item.get("why_it_matters", ""),
            }
        )
    return defects


def _map_severity(value: str) -> str:
    value = value.lower()
    if value in {"info", "low", "medium", "high", "critical"}:
        return value
    if value == "error":
        return "high"
    if value == "warning":
        return "low"
    return "high"


def _map_step_contract_code(category: str, problem: str) -> str:
    text = f"{category} {problem}".lower()
    if "no phases" in text:
        return "NO_PHASES_DEFINED"
    if "has no steps" in text:
        return "PHASE_HAS_NO_STEPS"
    if "step_id" in text and "unique" in text:
        return "STEP_ID_NOT_UNIQUE"
    if "step_id" in text and "pattern" in text:
        return "STEP_ID_PATTERN_INVALID"
    if "artifact" in text:
        return "ARTIFACT_REF_INVALID"
    if "command" in text:
        return "COMMAND_INVALID"
    if "precondition" in text:
        return "PRECONDITIONS_MISSING"
    if "postcondition" in text:
        return "POSTCONDITIONS_MISSING"
    if "rollback" in text:
        return "ROLLBACK_INVALID"
    if "idempotency" in text:
        return "IDEMPOTENCY_INVALID"
    if "missing" in text:
        return "STEP_MISSING_REQUIRED_FIELD"
    return "STEP_MISSING_REQUIRED_FIELD"


def _map_ssot_code(category: str, problem: str) -> str:
    text = f"{category} {problem}".lower()
    if "no phases" in text or "missing" in text:
        return "SSOT_MISSING_PHASES"
    if "contradiction" in text:
        return "SSOT_CONTRADICTION"
    if "path '" in text:
        return "SSOT_DUPLICATE_PATH_FACT"
    if "version '" in text:
        return "SSOT_DUPLICATE_VERSION_FACT"
    if "config" in text:
        return "SSOT_DUPLICATE_CONFIG_FACT"
    return "SSOT_CONTRADICTION"
