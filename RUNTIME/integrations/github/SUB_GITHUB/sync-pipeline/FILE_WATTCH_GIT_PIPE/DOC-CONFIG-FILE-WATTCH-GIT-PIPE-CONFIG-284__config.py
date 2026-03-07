# DOC_LINK: DOC-CONFIG-FILE-WATTCH-GIT-PIPE-CONFIG-284
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional


DEFAULT_PLUGINS = [
    "fwgp.plugins.secrets_scanner:SecretsScanner",
    "fwgp.plugins.commit_msg:CommitMessage",
    "fwgp.plugins.lint_formatter:LintFormatter",
]


@dataclass
class Config:
    base_dir: str
    repo_path: str = ""
    remote: str = "origin"
    branch: str = "main"
    polling_interval_sec: float = 2.0
    enabled_plugins: List[str] = None

    def __post_init__(self):
        if self.enabled_plugins is None:
            self.enabled_plugins = list(DEFAULT_PLUGINS)


def _config_path(base_dir: str) -> Path:
    p = Path(base_dir) / "data" / "config.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load_config(base_dir: str) -> Config:
    p = _config_path(base_dir)
    if not p.exists():
        return Config(base_dir=base_dir)
    data = json.loads(p.read_text(encoding="utf-8"))
    return Config(base_dir=base_dir, **data)


def save_config(cfg: Config) -> None:
    p = _config_path(cfg.base_dir)
    p.write_text(json.dumps(asdict(cfg), indent=2), encoding="utf-8")

