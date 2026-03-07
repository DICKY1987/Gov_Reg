# DOC_LINK: DOC-TEST-TESTS-TEST-ORCHESTRATOR-LIFECYCLE-SYNC-092
# DOC_LINK: DOC-TEST-TESTS-TEST-ORCHESTRATOR-LIFECYCLE-SYNC-053
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[5]
PIPELINE_SRC = REPO_ROOT / "WORKFLOWS" / "planning" / "PHASE_1_PLANNING" / "pipeline" / "src"
ORCHESTRATOR_SRC = REPO_ROOT / "WORKFLOWS" / "planning" / "PHASE_1_PLANNING" / "orchestrator" / "src"

for path in (PIPELINE_SRC, ORCHESTRATOR_SRC, REPO_ROOT):
    if path.exists():
        sys.path.insert(0, str(path))

try:
    from core import orchestrator
    from modules.core_state import m010003_bundles as bundles
except Exception as exc:
    pytest.skip(f"Missing core orchestrator dependencies: {exc}", allow_module_level=True)


def test_lifecycle_comments_are_emitted(monkeypatch):
    # Enable sync and stub out the poster to capture events
    monkeypatch.setenv('ENABLE_GH_SYNC', 'true')

    events = []

    def fake_post(issue, ev):  # noqa: ARG001
        events.append((ev.step, ev.final_status))
        return True

    gh = importlib.import_module('src.integrations.github_sync')
    monkeypatch.setattr(gh, 'post_lifecycle_comment', fake_post)

    # Pick a known workstream id
    items = bundles.load_and_validate_bundles()
    ws_id = next(b.id for b in items if getattr(b, 'ccpm_issue', None) is not None)

    result = orchestrator.run_single_workstream_from_bundle(ws_id, context={"dry_run": True})
    assert result['final_status'] == 'done'
    # Expect start and end events
    assert ('workstream_start', None) in events
    assert ('workstream_end', 'done') in events


