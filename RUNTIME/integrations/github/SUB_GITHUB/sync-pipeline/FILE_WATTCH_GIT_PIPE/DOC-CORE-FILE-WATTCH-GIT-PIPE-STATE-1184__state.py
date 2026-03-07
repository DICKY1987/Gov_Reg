# DOC_LINK: DOC-CORE-FILE-WATTCH-GIT-PIPE-STATE-1184
from __future__ import annotations

import json
import DOC-ERROR-UTILS-TIME-145__time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict


@dataclass
class CircuitState:
    failures: int = 0
    last_failure_ts: float = 0.0
    disabled: bool = False


class StateStore:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.path = Path(base_dir) / "data" / "state.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data: Dict[str, CircuitState] = {}
        self._load()

    def _load(self):
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            for k, v in raw.get("circuits", {}).items():
                self.data[k] = CircuitState(**v)
        except Exception:
            # start fresh on corrupt state
            self.data = {}

    def _save(self):
        payload = {"circuits": {k: asdict(v) for k, v in self.data.items()}}
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def record_failure(self, plugin_key: str):
        st = self.data.get(plugin_key, CircuitState())
        st.failures += 1
        st.last_failure_ts = time.time()
        if st.failures >= 3:
            st.disabled = True
        self.data[plugin_key] = st
        self._save()

    def reset(self, plugin_key: str):
        self.data[plugin_key] = CircuitState()
        self._save()

    def is_disabled(self, plugin_key: str) -> bool:
        return self.data.get(plugin_key, CircuitState()).disabled

