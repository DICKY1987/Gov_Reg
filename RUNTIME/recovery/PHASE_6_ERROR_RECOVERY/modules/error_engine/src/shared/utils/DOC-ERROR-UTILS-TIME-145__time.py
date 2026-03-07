# DOC_LINK: DOC-ERROR-UTILS-TIME-145
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

try:
    import ulid
except Exception:  # pragma: no cover - optional dependency
    ulid = None  # type: ignore


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def new_run_id() -> str:
    if ulid is not None:
        try:
            return str(ulid.new())
        except Exception:
            pass
    # Fallback sortable timestamp + suffix
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

