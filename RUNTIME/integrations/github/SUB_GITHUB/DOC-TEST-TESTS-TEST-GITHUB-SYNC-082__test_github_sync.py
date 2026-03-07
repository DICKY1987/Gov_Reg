# DOC_LINK: DOC-TEST-TESTS-TEST-GITHUB-SYNC-082
# DOC_LINK: DOC-TEST-TESTS-TEST-GITHUB-SYNC-043
import os
import json
from pathlib import Path

import pytest


def import_mod():
    import importlib
    return importlib.import_module('src.integrations.github_sync')


def test_disabled_sync_is_noop(monkeypatch):
    monkeypatch.setenv('ENABLE_GH_SYNC', 'false')
    m = import_mod()
    assert m._enabled() is False
    # Should return False/no effect when disabled
    assert m.comment(123, 'hello') is False
    assert m.set_status(123, 'open', ['label']) is False


def test_ensure_epic_existing_via_search(monkeypatch):
    # Enable but fake gh via monkeypatched runner
    monkeypatch.setenv('ENABLE_GH_SYNC', 'true')
    m = import_mod()
    # Pretend gh is available
    monkeypatch.setattr(m, '_gh_available', lambda: True)

    calls = []

    def fake_run(args, timeout=30):
        calls.append(args)
        if args[0:3] == ['gh', 'issue', 'list']:
            out = json.dumps([{ 'number': 101, 'title': 'Epic: demo' }])
            return 0, out, ''
        return 1, '', 'unsupported'

    monkeypatch.setattr(m, '_run', fake_run)
    num = m.ensure_epic('Epic: demo')
    assert num == 101
    assert any(a[0:3] == ['gh','issue','list'] for a in calls)

