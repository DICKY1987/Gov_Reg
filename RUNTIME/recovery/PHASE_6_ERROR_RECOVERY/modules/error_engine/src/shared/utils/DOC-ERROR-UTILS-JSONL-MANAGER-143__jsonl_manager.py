# DOC_LINK: DOC-ERROR-UTILS-JSONL-MANAGER-143
from __future__ import annotations

import io
import json
import os
from pathlib import Path
from typing import Any, List


def append(path: Path, obj: Any, max_bytes: int = 75_000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(line)
    rotate_if_needed(path, max_bytes=max_bytes)


def read_all(path: Path) -> List[dict]:
    """Read all events from a JSONL file.

    Returns:
        List of parsed JSON objects, one per line
    """
    if not path.exists():
        return []

    events = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return events


def rotate_if_needed(path: Path, max_bytes: int = 75_000, max_lines: int = None) -> None:
    """Rotate JSONL file if it exceeds size or line limits.

    Args:
        path: Path to JSONL file
        max_bytes: Maximum file size in bytes
        max_lines: Maximum number of lines (optional, takes precedence if set)
    """
    try:
        size = path.stat().st_size
    except FileNotFoundError:
        return

    # If max_lines is specified, use line-based rotation
    if max_lines is not None:
        with path.open("r", encoding="utf-8") as f:
            lines = f.readlines()

        if len(lines) <= max_lines:
            return

        # Keep most recent max_lines
        kept_lines = lines[-max_lines:]
        tmp = path.with_suffix(path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            f.writelines(kept_lines)
        os.replace(tmp, path)
        return

    # Otherwise use byte-based rotation
    if size <= max_bytes:
        return

    # Keep newest lines up to max_bytes from end of file
    # Read in reverse chunks, then join and splitlines
    chunks: list[bytes] = []
    keep = max_bytes
    with path.open("rb") as f:
        f.seek(0, os.SEEK_END)
        pos = f.tell()
        while pos > 0 and keep > 0:
            step = int(min(8192, pos))
            pos -= step
            f.seek(pos)
            data = f.read(step)
            chunks.append(data)
            keep -= len(data)

    data = b"".join(reversed(chunks))
    # Keep last max_bytes worth of complete lines
    text = data.decode("utf-8", errors="ignore")
    lines = text.splitlines()
    # Ensure at least one line is kept
    tail = "\n".join(lines[-10_000:])  # cap lines to avoid extreme memory on huge logs
    tail_bytes = tail.encode("utf-8")
    if len(tail_bytes) > max_bytes:
        # Trim from the front to fit
        # Simple strategy: drop leading bytes until under limit at a newline boundary
        # Re-split to lines and iteratively keep from end
        lines2 = tail.splitlines()
        kept: list[str] = []
        total = 0
        for line in reversed(lines2):
            b = (line + "\n").encode("utf-8")
            if total + len(b) > max_bytes:
                break
            kept.append(line)
            total += len(b)
        kept_text = "\n".join(reversed(kept)) + ("\n" if kept else "")
    else:
        kept_text = tail + ("\n" if not tail.endswith("\n") else "")

    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        f.write(kept_text)
    os.replace(tmp, path)
