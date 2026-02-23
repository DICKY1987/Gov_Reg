"""Tool result envelope helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .evidence import write_evidence


def build_envelope(
    *,
    tool: str,
    tool_version: str,
    status: str,
    exit_code: int,
    run_id: str,
    evidence_path: Path,
    summary: str,
    defects: List[Dict[str, Any]],
    artifacts_emitted: List[str],
    hashes: Dict[str, str],
    metrics: Optional[Dict[str, float]] = None,
    write_evidence_flag: bool = True,
    input_payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    envelope = {
        "tool": tool,
        "tool_version": tool_version,
        "status": status,
        "exit_code": exit_code,
        "run_id": run_id,
        "summary": summary,
        "evidence_paths": [str(evidence_path)],
        "artifacts_emitted": artifacts_emitted,
        "defects": defects,
        "hashes": hashes,
        "metrics": metrics or {},
    }

    if write_evidence_flag:
        payload = {
            "tool": tool,
            "tool_version": tool_version,
            "run_id": run_id,
            "status": status,
            "exit_code": exit_code,
            "summary": summary,
            "input": input_payload or {},
            "defects": defects,
            "hashes": hashes,
            "artifacts_emitted": artifacts_emitted,
            "timestamps": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
        }
        write_evidence(evidence_path, payload)

    return envelope
