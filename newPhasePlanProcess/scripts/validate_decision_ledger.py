#!/usr/bin/env python3
"""Validate the decision ledger JSONL against SEC-014 rules."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REQUIRED_FIELDS = {"decision_id", "category", "timestamp", "options", "selected_option", "rationale", "owner"}
_ISO8601 = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
_DEC_ID = re.compile(r"^DEC-[A-Z0-9_]+-\d{3,}$")
MIN_DECISIONS = 5


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: validate_decision_ledger.py <ledger_path>", file=sys.stderr)
        return 1

    ledger_path = Path(sys.argv[1])
    if not ledger_path.exists():
        print(f"FAIL  ledger not found: {ledger_path}", file=sys.stderr)
        return 1

    decisions: list[tuple[int, dict]] = []
    errors: list[str] = []

    for lineno, raw in enumerate(ledger_path.read_text(encoding="utf-8").splitlines(), start=1):
        raw = raw.strip()
        if not raw:
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"line {lineno}: invalid JSON - {exc}")
            continue
        decisions.append((lineno, record))

    if len(decisions) < MIN_DECISIONS:
        errors.append(f"too few decisions: {len(decisions)} < {MIN_DECISIONS} required")

    seen_ids: dict[str, int] = {}
    for lineno, rec in decisions:
        did = rec.get("decision_id", "")

        missing = REQUIRED_FIELDS - rec.keys()
        if missing:
            errors.append(f"line {lineno} ({did}): missing fields {sorted(missing)}")

        if not _DEC_ID.match(str(did)):
            errors.append(f"line {lineno}: decision_id '{did}' does not match DEC-{{PROJECT}}-NNN pattern")

        if did in seen_ids:
            errors.append(f"line {lineno}: duplicate decision_id '{did}' (first seen at line {seen_ids[did]})")
        else:
            seen_ids[did] = lineno

        ts = rec.get("timestamp", "")
        if not _ISO8601.match(str(ts)):
            errors.append(f"line {lineno} ({did}): timestamp '{ts}' is not ISO 8601")

        opts = rec.get("options", [])
        if not isinstance(opts, list) or len(opts) < 2:
            errors.append(f"line {lineno} ({did}): 'options' must be a list with >=2 entries")

    if errors:
        for e in errors:
            print(f"FAIL  {e}")
        return 1

    print(f"PASS  {len(decisions)} decisions validated against SEC-014 rules")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
