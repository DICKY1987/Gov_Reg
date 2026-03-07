"""Circuit breakers, retries, and oscillation detection (PH-06).

Lightweight utilities to load breaker config, compute error/diff signatures,
and decide whether to continue FIX attempts.

Design goals:
- Pure Python stdlib implementation; optional YAML via PyYAML if available.
- Deterministic defaults when config missing.
- Easy to monkeypatch in tests.
"""

# DOC_ID: DOC-CORE-ENGINE-CIRCUIT-BREAKERS-144

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping

__all__ = [
    "load_config",
    "BreakerConfig",
    "FixLoopState",
    "compute_error_signature",
    "compute_diff_hash",
    "allow_fix_attempt",
    "detect_oscillation",
]


DEFAULTS: Dict[str, Any] = {
    "defaults": {
        "max_attempts_per_step": 3,
        "max_fix_attempts_per_step": 2,
        "max_attempts_per_error_signature": 3,
        "oscillation_window": 4,
        "oscillation_threshold": 2,
        "enable_fix_for_steps": ["static", "runtime"],
    },
    "per_step": {},
}


def _repo_root() -> Path:
    cur = Path.cwd().resolve()
    while cur != cur.parent:
        if (cur / ".git").exists():
            return cur
        cur = cur.parent
    return Path.cwd().resolve()


def load_config() -> Dict[str, Any]:
    """Load circuit breaker config from invoke.yaml, else return defaults.

    Migrated from config/circuit_breakers.yaml to invoke.yaml in Phase G.
    Falls back to legacy files for backward compatibility with deprecation warning.
    """
    # Try loading from invoke.yaml first (Phase G)
    try:
        from core.config_loader import get_circuit_breaker_config

        cfg = get_circuit_breaker_config()
        if cfg:
            # Map new structure to expected format
            result = {
                "defaults": {
                    "max_attempts_per_step": cfg.get("max_attempts_per_step", 3),
                    "max_fix_attempts_per_step": cfg.get(
                        "max_fix_attempts_per_step", 2
                    ),
                    "max_attempts_per_error_signature": cfg.get(
                        "max_attempts_per_error_signature", 3
                    ),
                    "oscillation_window": cfg.get("oscillation_window", 4),
                    "oscillation_threshold": cfg.get("oscillation_threshold", 2),
                    "enable_fix_for_steps": cfg.get(
                        "enable_fix_for_steps", ["static", "runtime"]
                    ),
                },
                "per_step": cfg.get("per_step", {}),
            }
            return result
    except Exception:
        pass

    # Fall back to legacy config files with deprecation warning
    root = _repo_root()
    ypath = root / "config" / "circuit_breakers.yaml"
    jpath = root / "config" / "circuit_breakers.json"

    if ypath.exists() or jpath.exists():
        import warnings

        warnings.warn(
            "Loading circuit breakers from config/ is deprecated. "
            "Configuration is now in invoke.yaml. "
            "Legacy files will be removed in Phase G+1.",
            DeprecationWarning,
            stacklevel=2,
        )

    if ypath.exists():
        try:
            import yaml  # type: ignore

            with ypath.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)  # type: ignore
            if isinstance(data, dict):
                return data  # type: ignore[return-value]
        except Exception:
            pass

    if jpath.exists():
        try:
            return json.loads(jpath.read_text(encoding="utf-8"))
        except Exception:
            pass

    return DEFAULTS.copy()


@dataclass
class BreakerConfig:
    defaults: Mapping[str, Any]
    per_step: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, cfg: Mapping[str, Any]) -> "BreakerConfig":
        return cls(
            defaults=cfg.get("defaults", {}),
            per_step=cfg.get("per_step", {}),
        )

    def for_step(self, step: str) -> Mapping[str, Any]:
        x = dict(self.defaults)
        x.update(self.per_step.get(step, {}))
        return x


@dataclass
class FixLoopState:
    step_attempts: int = 0
    fix_attempts: int = 0
    signature_counts: Dict[str, int] = field(default_factory=dict)
    recent_diff_hashes: List[str] = field(default_factory=list)


def compute_error_signature(error_code: str, message: str) -> str:
    norm = " ".join(message.split())[:2000]
    base = f"{error_code}|{norm}".encode("utf-8", errors="ignore")
    return hashlib.sha1(base).hexdigest()


def compute_diff_hash(payload: Mapping[str, Any]) -> str:
    # Hash stdout+stderr when available; else hash JSON of payload
    stdout = str(payload.get("stdout", ""))
    stderr = str(payload.get("stderr", ""))
    data = (stdout + "\n" + stderr).encode("utf-8", errors="ignore")
    if not data.strip():
        data = json.dumps(payload, sort_keys=True).encode("utf-8", errors="ignore")
    return hashlib.sha1(data).hexdigest()


def allow_fix_attempt(state: FixLoopState, step: str, cfg: BreakerConfig) -> bool:
    sc = cfg.for_step(step)
    max_total = int(sc.get("max_attempts_per_step", 3))
    max_fix = int(sc.get("max_fix_attempts_per_step", 2))
    # total attempts = 1 initial + state.fix_attempts so far, but we check prospective
    if state.step_attempts >= max_total:
        return False
    if state.fix_attempts >= max_fix:
        return False
    return True


def detect_oscillation(state: FixLoopState, cfg: BreakerConfig) -> bool:
    sc = cfg.for_step("static")  # same window/threshold for both by default
    window = int(sc.get("oscillation_window", 4))
    threshold = int(sc.get("oscillation_threshold", 2))
    recent = state.recent_diff_hashes[-window:]
    if not recent:
        return False
    # count most common value occurrences
    counts: Dict[str, int] = {}
    for h in recent:
        counts[h] = counts.get(h, 0) + 1
    return max(counts.values()) >= threshold
