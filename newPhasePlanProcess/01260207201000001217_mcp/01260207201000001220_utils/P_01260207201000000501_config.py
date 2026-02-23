"""Configuration loader for MCP server bindings."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict


def load_config() -> Dict[str, Any]:
    env_path = os.environ.get("NPP_MCP_CONFIG", "").strip()
    if env_path:
        config_path = Path(env_path)
    else:
        config_path = Path(__file__).resolve().parents[1] / "mcp_config.json"

    if not config_path.exists():
        return {}

    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
