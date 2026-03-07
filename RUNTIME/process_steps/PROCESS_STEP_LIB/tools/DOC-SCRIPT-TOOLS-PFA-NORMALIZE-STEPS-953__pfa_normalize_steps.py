#!/usr/bin/env python3
# DOC_LINK: DOC-SCRIPT-TOOLS-PFA-NORMALIZE-STEPS-953
"""
pfa_normalize_steps.py

Deterministic normalizer + stringifier for PFA process-step YAML files.

Outputs:
  1) <name>.normalized.yaml   (canonical-ish steps list)
  2) <name>.steps.txt         (one-line-per-step for diffing)

Supported input shapes:
  A) top-level "phases": {PHASE: {description:..., steps:[...]}, ...}
  B) top-level "steps": [ ... ]
  C) top-level "guardrail_checkpoints": { ... , SOME_GROUP:{..., steps:[...]}, ... }  (phase-like groups)

Usage:
  python pfa_normalize_steps.py path/to/file.yaml --outdir out

Diff workflow:
  python pfa_normalize_steps.py A.yaml --outdir out
  python pfa_normalize_steps.py B.yaml --outdir out
  git diff --no-index out/A.steps.txt out/B.steps.txt
"""
DOC_ID: DOC-SCRIPT-TOOLS-PFA-NORMALIZE-STEPS-953
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

import yaml


REQUIRED_STEP_KEYS = [
    "step_id",
    "phase",
    "name",
    "description",
    "responsible_component",
    "operation_kind",
    "inputs",
    "expected_outputs",
    "requires_human_confirmation",
]

# Superset (optional) keys observed across your five YAMLs.
OPTIONAL_STEP_KEYS = [
    "order",
    "lens",
    "automation_level",
    "pattern_ids",
    "artifact_registry_refs",
    "guardrail_checkpoint",
    "guardrail_checkpoint_id",
    "implementation_files",
    "artifacts_created",
    "artifacts_updated",
    "metrics_emitted",
    "preconditions",
    "postconditions",
    "error_handling",
    "state_transition",
    "anti_pattern_ids",
]

CANONICAL_STEP_KEYS = REQUIRED_STEP_KEYS + OPTIONAL_STEP_KEYS


def _safe_list(v: Any) -> List[Any]:
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]


def _as_bool(v: Any) -> bool:
    return bool(v) if v is not None else False


def _hash_step_payload(step: Dict[str, Any]) -> str:
    """Stable content hash for comparisons; ignores non-semantic ordering."""
    # Only hash canonical keys (so additional unknown fields don't break comparison).
    payload = {k: step.get(k) for k in CANONICAL_STEP_KEYS if k in step}
    # Normalize list ordering where it makes sense.
    for k in ["inputs", "expected_outputs", "pattern_ids", "artifact_registry_refs",
              "implementation_files", "artifacts_created", "artifacts_updated", "metrics_emitted",
              "anti_pattern_ids"]:
        if k in payload and isinstance(payload[k], list):
            payload[k] = list(payload[k])
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha1(raw).hexdigest()  # deterministic & short enough for diffing


def _extract_steps(doc: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Return (steps, phase_order)."""
    # A) top-level steps
    if isinstance(doc.get("steps"), list):
        return [s for s in doc["steps"] if isinstance(s, dict)], _phase_order_from_steps(doc["steps"])

    # B) phases dict
    if isinstance(doc.get("phases"), dict):
        phase_order = list(doc["phases"].keys())
        steps: List[Dict[str, Any]] = []
        for ph_name, ph in doc["phases"].items():
            if isinstance(ph, dict) and isinstance(ph.get("steps"), list):
                for s in ph["steps"]:
                    if isinstance(s, dict):
                        steps.append(s)
        return steps, phase_order

    # C) guardrail_checkpoints has embedded phase groups with "steps"
    gc = doc.get("guardrail_checkpoints")
    if isinstance(gc, dict):
        phase_groups = [(k, v) for k, v in gc.items() if isinstance(v, dict) and isinstance(v.get("steps"), list)]
        # Preserve YAML order by iterating items() (PyYAML preserves mapping insertion order).
        phase_order = [k for k, _ in phase_groups]
        steps: List[Dict[str, Any]] = []
        for _, group in phase_groups:
            for s in group.get("steps", []):
                if isinstance(s, dict):
                    steps.append(s)
        return steps, phase_order

    raise ValueError("Unsupported schema: expected top-level 'steps', 'phases', or embedded 'steps' in 'guardrail_checkpoints'.")


def _phase_order_from_steps(steps: List[Any]) -> List[str]:
    seen = []
    for s in steps:
        if isinstance(s, dict):
            ph = s.get("phase")
            if isinstance(ph, str) and ph not in seen:
                seen.append(ph)
    return seen


def _coerce_step(step: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}

    # Required keys (with best-effort defaults)
    out["step_id"] = str(step.get("step_id", "")).strip()
    out["phase"] = str(step.get("phase", "")).strip()
    out["name"] = str(step.get("name", "")).strip()
    out["description"] = str(step.get("description", out["name"])).rstrip()
    out["responsible_component"] = str(step.get("responsible_component", "")).strip()
    out["operation_kind"] = str(step.get("operation_kind", "")).strip()
    out["inputs"] = _safe_list(step.get("inputs"))
    out["expected_outputs"] = _safe_list(step.get("expected_outputs"))
    out["requires_human_confirmation"] = _as_bool(step.get("requires_human_confirmation"))

    # Optional keys (only if present)
    for k in OPTIONAL_STEP_KEYS:
        if k in step:
            if k in ("pattern_ids", "artifact_registry_refs", "implementation_files",
                     "artifacts_created", "artifacts_updated", "metrics_emitted", "anti_pattern_ids",
                     "preconditions", "postconditions"):
                out[k] = _safe_list(step.get(k))
            elif k in ("guardrail_checkpoint",):
                out[k] = _as_bool(step.get(k))
            elif k in ("order",):
                try:
                    out[k] = int(step.get(k))
                except Exception:
                    out[k] = step.get(k)
            else:
                out[k] = step.get(k)

    out["_content_hash"] = _hash_step_payload(out)
    return out


def _sort_key(step: Dict[str, Any], phase_index: Dict[str, int]) -> Tuple[int, int, str]:
    ph = step.get("phase", "")
    pi = phase_index.get(ph, 10_000)

    # Prefer explicit "order" if present; else try to parse trailing digits from step_id.
    order = step.get("order")
    if isinstance(order, int):
        oi = order
    else:
        oi = _parse_trailing_int(step.get("step_id", "")) or 10_000
    return (pi, oi, step.get("step_id", ""))


def _parse_trailing_int(s: str) -> Optional[int]:
    # e.g. "P6-STEP-100" -> 100
    import re
    m = re.search(r"(\d+)\s*$", s)
    return int(m.group(1)) if m else None


def _one_line(step: Dict[str, Any], process_id: str) -> str:
    def join_list(v: Any) -> str:
        if not v:
            return ""
        if isinstance(v, list):
            return ",".join(str(x).strip() for x in v)
        return str(v).strip()

    cols = [
        process_id,
        step.get("phase", ""),
        str(step.get("order", "")),
        step.get("step_id", ""),
        step.get("operation_kind", ""),
        step.get("responsible_component", ""),
        step.get("lens", ""),
        step.get("automation_level", ""),
        str(step.get("requires_human_confirmation", False)).lower(),
        str(step.get("guardrail_checkpoint", False)).lower(),
        join_list(step.get("artifact_registry_refs")),
        join_list(step.get("implementation_files")),
        step.get("_content_hash", ""),
        step.get("name", ""),
    ]
    # Tab-separated: stable + easy to diff.
    return "\t".join(cols)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path, help="YAML file to normalize")
    ap.add_argument("--outdir", type=Path, default=Path("."), help="Output directory")
    ap.add_argument("--name", type=str, default="", help="Base name for outputs (default: input stem)")
    args = ap.parse_args()

    raw = yaml.safe_load(args.input.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise SystemExit("Top-level YAML must be a mapping/dict.")

    meta = raw.get("meta") if isinstance(raw.get("meta"), dict) else {}
    process_id = meta.get("process_id") or meta.get("doc_id") or args.input.stem

    steps_raw, phase_order = _extract_steps(raw)
    phase_index = {ph: i for i, ph in enumerate(phase_order)}

    steps = [_coerce_step(s) for s in steps_raw]
    # De-dupe by step_id (keep first occurrence deterministically)
    seen = set()
    deduped = []
    for s in steps:
        sid = s.get("step_id", "")
        if sid and sid not in seen:
            seen.add(sid)
            deduped.append(s)
    steps = sorted(deduped, key=lambda s: _sort_key(s, phase_index))

    outdir = args.outdir
    outdir.mkdir(parents=True, exist_ok=True)
    base = args.name.strip() or args.input.stem

    normalized_yaml = {
        "meta": {
            "process_id": process_id,
            "source_file": str(args.input),
            "normalized_by": "pfa_normalize_steps.py",
        },
        "steps": steps,
    }
    (outdir / f"{base}.normalized.yaml").write_text(
        yaml.safe_dump(normalized_yaml, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    header = "\t".join([
        "process_id",
        "phase",
        "order",
        "step_id",
        "operation_kind",
        "responsible_component",
        "lens",
        "automation_level",
        "requires_human_confirmation",
        "guardrail_checkpoint",
        "artifact_registry_refs",
        "implementation_files",
        "content_hash",
        "name",
    ])
    lines = [header] + [_one_line(s, process_id) for s in steps]
    (outdir / f"{base}.steps.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote: {outdir / f'{base}.normalized.yaml'}")
    print(f"Wrote: {outdir / f'{base}.steps.txt'}")
    print(f"Steps: {len(steps)}  |  Phases seen: {len(set(s.get('phase','') for s in steps))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
