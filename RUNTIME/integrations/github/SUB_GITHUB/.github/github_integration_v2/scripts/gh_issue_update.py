#!/usr/bin/env python3
"""Thin wrapper to post comments or set status on a GitHub issue.

Usage examples:
  python scripts/gh_issue_update.py --issue 123 --comment "Started run X"
  python scripts/gh_issue_update.py --issue 123 --state closed --add-label success
"""
# DOC_ID: DOC-SCRIPT-SCRIPTS-GH-ISSUE-UPDATE-213
# DOC_ID: DOC-SCRIPT-SCRIPTS-GH-ISSUE-UPDATE-150

from __future__ import annotations

import argparse
import sys
from typing import List

from pathlib import Path


def _repo_import():
    base = Path(__file__).resolve().parents[1]
    )
    from src.integrations import github_sync  # type: ignore

    return github_sync


def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--issue", required=True, help="Issue number")
    p.add_argument("--comment", help="Comment body")
    p.add_argument("--state", choices=["open", "closed"], help="Set issue state")
    p.add_argument("--add-label", dest="labels", action="append", help="Add a label (repeatable)")
    args = p.parse_args(argv)

    gh = _repo_import()
    ok = False
    if args.comment:
        ok = gh.comment(args.issue, args.comment)
    if args.state or args.labels:
        ok = gh.set_status(args.issue, state=args.state or "", add_labels=args.labels or []) or ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

