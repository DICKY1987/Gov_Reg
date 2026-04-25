from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY = ROOT / "config" / "path_index.yaml"


def _strip_inline_comment(line: str) -> str:
    if "#" not in line:
        return line
    value, _comment = line.split("#", 1)
    return value.rstrip()


def load_registry(path: str | Path = DEFAULT_REGISTRY) -> dict[str, str]:
    registry_path = Path(path)
    if not registry_path.is_absolute():
        registry_path = ROOT / registry_path
    if not registry_path.exists():
        raise FileNotFoundError(f"Registry not found: {registry_path}")

    mappings: dict[str, str] = {}
    for raw_line in registry_path.read_text(encoding="utf-8").splitlines():
        line = _strip_inline_comment(raw_line).strip()
        if not line:
            continue
        if ":" not in line:
            raise ValueError(f"Invalid registry line: {raw_line}")
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if not key or not value:
            raise ValueError(f"Incomplete registry entry: {raw_line}")
        if key in mappings:
            raise ValueError(f"Duplicate registry key: {key}")
        mappings[key] = value
    return mappings


def resolve_key(key: str, path: str | Path = DEFAULT_REGISTRY) -> str:
    mappings = load_registry(path)
    if key not in mappings:
        raise KeyError(key)
    return mappings[key]

