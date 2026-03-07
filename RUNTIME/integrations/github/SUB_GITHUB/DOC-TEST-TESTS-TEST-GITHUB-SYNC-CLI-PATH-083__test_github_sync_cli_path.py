# DOC_LINK: DOC-TEST-TESTS-TEST-GITHUB-SYNC-CLI-PATH-083
# DOC_LINK: DOC-TEST-TESTS-TEST-GITHUB-SYNC-CLI-PATH-044
import os
import stat
import sys
from pathlib import Path

import pytest


@pytest.mark.skipif(os.name == 'nt', reason='CLI stub resolution is POSIX-specific for this test')
def test_github_sync_uses_gh_cli_when_available(tmp_path, monkeypatch):
    # Create a stub gh that handles 'issue comment' and 'issue list'
    gh = tmp_path / 'gh'
    gh.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
if [[ "$1" == "issue" && "$2" == "comment" ]]; then
  # emulate success
  exit 0
fi
if [[ "$1" == "issue" && "$2" == "list" ]]; then
  echo '[{"number": 42, "title": "Epic: demo"}]'
  exit 0
fi
echo "unsupported" >&2
exit 1
""",
        encoding='utf-8',
    )
    gh.chmod(gh.stat().st_mode | stat.S_IEXEC)

    # Prepend stub to PATH and enable sync
    monkeypatch.setenv('PATH', f"{tmp_path}{os.pathsep}" + os.environ.get('PATH', ''))
    monkeypatch.setenv('ENABLE_GH_SYNC', 'true')

    import importlib

    mod = importlib.import_module('src.integrations.github_sync')
    assert mod._gh_available() is True

    # Comment should succeed
    assert mod.comment(123, 'hello') is True
    # ensure_epic should find our demo epic
    assert mod.ensure_epic('Epic: demo') == 42

