# DOC_LINK: DOC-CORE-FILE-WATTCH-GIT-PIPE-DISCOVERY-1179
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List


REQUIRED_FIELDS = {"name", "module", "class", "version"}


def discover_plugins(plugins_dir: str, logger) -> List[str]:
    specs: List[str] = []
    pdir = Path(plugins_dir)
    if not pdir.exists():
        return specs
    if str(pdir.resolve()) not in sys.path:
        ))
    for manifest in pdir.rglob("manifest.json"):
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            missing = REQUIRED_FIELDS - set(data.keys())
            if missing:
                logger.warning("Manifest %s missing fields: %s", manifest, ", ".join(sorted(missing)))
                continue
            module = data["module"]
            cls = data["class"]
            spec = f"{module}:{cls}"
            specs.append(spec)
            logger.info("Discovered plugin: %s (%s)", data.get("name"), spec)
        except Exception as e:
            logger.error("Failed to read manifest %s: %s", manifest, e)
    return specs

