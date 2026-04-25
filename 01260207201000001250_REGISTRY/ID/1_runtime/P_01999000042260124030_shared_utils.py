from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def atomic_json_read(path: Path | str, lock_timeout: float | None = None) -> Any:
    del lock_timeout
    with open(Path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def atomic_json_write(path: Path | str, payload: Any, lock_timeout: float | None = None) -> None:
    del lock_timeout

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    fd, temp_name = tempfile.mkstemp(
        prefix=f"{destination.name}.",
        suffix=".tmp",
        dir=str(destination.parent),
    )

    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")
        os.replace(temp_name, destination)
    finally:
        temp_path = Path(temp_name)
        if temp_path.exists():
            temp_path.unlink()
