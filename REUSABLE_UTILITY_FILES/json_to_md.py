#!/usr/bin/env python3
"""
Deterministic JSON -> Markdown converter (v2).

Determinism guarantees:
- Dict keys sorted lexicographically at every depth.
- Lists preserved in original order.
- Numbers parsed as Decimal; emitted canonically.
- Native floats are forbidden (hard-fail).
- Duplicate JSON keys forbidden (hard-fail).
- Stable table rendering (sorted columns) with missing-vs-null distinction.
- Stable newline normalization (\n).
- Optional embedded SHA-256 of canonical JSON.
- Optional contract mode embeds canonical JSON for round-trip.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import io
import os
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Tuple, Union

JsonT = Union[Dict[str, Any], List[Any], str, int, bool, None, Decimal]


# ----------------------------
# Canonicalization + hashing
# ----------------------------

def _decimal_to_canonical_str(d: Decimal) -> str:
    # Canonical: no exponent, trim trailing zeros, keep "0" for zero-ish.
    s = format(d, "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    if s == "-0":
        s = "0"
    return s


def _sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _canonicalize(obj: Any) -> Any:
    # Hard fail floats for cross-env determinism.
    if isinstance(obj, float):
        raise ValueError("Native float encountered (forbidden). Ensure parse_float=Decimal and no float injection.")
    if isinstance(obj, dict):
        return {k: _canonicalize(obj[k]) for k in sorted(obj.keys())}
    if isinstance(obj, list):
        return [_canonicalize(v) for v in obj]
    return obj


class _DecimalSafeEncoder(json.JSONEncoder):
    """Encode Decimals as JSON number literals, not strings."""

    def default(self, o: Any) -> Any:
        if isinstance(o, Decimal):
            # Return a sentinel that we replace post-serialization.
            # json.JSONEncoder.default can't emit raw numbers, so we
            # use iterencode override instead.
            raise TypeError  # fall through to iterencode
        return super().default(o)

    def iterencode(self, o: Any, _one_shot: bool = False) -> Any:
        return _decimal_iterencode(o, self.sort_keys)


def _decimal_iterencode(obj: Any, sort_keys: bool = True) -> str:
    """Serialize JSON with Decimals emitted as number literals."""
    buf = io.StringIO()
    _write_json(buf, obj, sort_keys)
    return iter([buf.getvalue()])


def _write_json(buf: io.StringIO, obj: Any, sort_keys: bool) -> None:
    if isinstance(obj, float):
        raise ValueError("Native float encountered during canonicalization (forbidden).")
    if obj is None:
        buf.write("null")
    elif isinstance(obj, bool):
        buf.write("true" if obj else "false")
    elif isinstance(obj, Decimal):
        buf.write(_decimal_to_canonical_str(obj))
    elif isinstance(obj, int):
        buf.write(str(obj))
    elif isinstance(obj, str):
        buf.write(json.dumps(obj, ensure_ascii=False))
    elif isinstance(obj, dict):
        buf.write("{")
        keys = sorted(obj.keys()) if sort_keys else list(obj.keys())
        for i, k in enumerate(keys):
            if i > 0:
                buf.write(",")
            buf.write(json.dumps(k, ensure_ascii=False))
            buf.write(":")
            _write_json(buf, obj[k], sort_keys)
        buf.write("}")
    elif isinstance(obj, list):
        buf.write("[")
        for i, v in enumerate(obj):
            if i > 0:
                buf.write(",")
            _write_json(buf, v, sort_keys)
        buf.write("]")
    else:
        raise TypeError(f"Unsupported type for JSON serialization: {type(obj)}")


def _canonical_json_string(obj: Any) -> str:
    canon = _canonicalize(obj)
    buf = io.StringIO()
    _write_json(buf, canon, sort_keys=True)
    return buf.getvalue()


def _pretty_json_with_decimals(obj: Any) -> str:
    """Pretty-print JSON preserving Decimals as number literals."""
    return _pretty_write(obj, indent=0, sort_keys=True)


def _pretty_write(obj: Any, indent: int, sort_keys: bool) -> str:
    sp = "  " * indent
    sp1 = "  " * (indent + 1)

    if isinstance(obj, float):
        raise ValueError("Native float encountered (forbidden).")
    if obj is None:
        return "null"
    if isinstance(obj, bool):
        return "true" if obj else "false"
    if isinstance(obj, Decimal):
        return _decimal_to_canonical_str(obj)
    if isinstance(obj, int):
        return str(obj)
    if isinstance(obj, str):
        return json.dumps(obj, ensure_ascii=False)
    if isinstance(obj, dict):
        if not obj:
            return "{}"
        keys = sorted(obj.keys()) if sort_keys else list(obj.keys())
        entries = []
        for k in keys:
            k_str = json.dumps(k, ensure_ascii=False)
            v_str = _pretty_write(obj[k], indent + 1, sort_keys)
            entries.append(f"{sp1}{k_str}: {v_str}")
        return "{\n" + ",\n".join(entries) + f"\n{sp}}}"
    if isinstance(obj, list):
        if not obj:
            return "[]"
        entries = [f"{sp1}{_pretty_write(v, indent + 1, sort_keys)}" for v in obj]
        return "[\n" + ",\n".join(entries) + f"\n{sp}]"
    raise TypeError(f"Unsupported type: {type(obj)}")


# ----------------------------
# JSON load with strictness
# ----------------------------

def _reject_duplicates_object_pairs(pairs: List[Tuple[str, Any]]) -> Dict[str, Any]:
    obj: Dict[str, Any] = {}
    seen = set()
    for k, v in pairs:
        if k in seen:
            raise ValueError(f"Duplicate JSON key detected: {k!r}")
        seen.add(k)
        obj[k] = v
    return obj


def _reject_non_json_constants(x: str) -> Any:
    # Reject NaN/Infinity if present (non-standard JSON).
    raise ValueError(f"Non-JSON constant encountered: {x!r}")


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(
            f,
            parse_float=Decimal,
            parse_int=int,
            object_pairs_hook=_reject_duplicates_object_pairs,
            parse_constant=_reject_non_json_constants,
        )


# ----------------------------
# Markdown emission
# ----------------------------

def _normalize_newlines(s: str) -> str:
    return s.replace("\r\n", "\n").replace("\r", "\n")


# Escape only high-risk inline chars; do NOT escape '.' and '-' globally.
# Keep '|' escaped because it breaks tables.
_MD_INLINE_SPECIAL = re.compile(r"([\\`*_{}\[\]()#+!|>])")


def _md_escape_inline(text: str) -> str:
    return _MD_INLINE_SPECIAL.sub(r"\\\1", text)


def _md_escape_table_cell(text: str) -> str:
    # Must escape pipes and normalize newlines.
    t = _normalize_newlines(text).replace("\n", "\\n")
    t = t.replace("|", r"\|")
    # Keep other inline escapes minimal.
    return _md_escape_inline(t)


def _is_primitive(x: Any) -> bool:
    if isinstance(x, float):
        raise ValueError("Native float encountered (forbidden).")
    return x is None or isinstance(x, (str, bool, int, Decimal))


def _value_to_inline_md(v: Any) -> str:
    if isinstance(v, float):
        raise ValueError("Native float encountered (forbidden).")
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, Decimal):
        return _decimal_to_canonical_str(v)
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        s = _normalize_newlines(v)
        if "\n" in s:
            return "(multiline)"
        return _md_escape_inline(s)
    return _md_escape_inline(str(v))


def _render_multiline_string(s: str, indent: str = "") -> List[str]:
    s = _normalize_newlines(s)
    lines = [f"{indent}```text"]
    lines.extend(f"{indent}{line}" for line in s.split("\n"))
    lines.append(f"{indent}```")
    return lines


def _list_of_objects_uniform(lst: List[Any]) -> Tuple[bool, List[str]]:
    if not lst or not all(isinstance(x, dict) for x in lst):
        return (False, [])
    keys = set()
    for row in lst:
        keys.update(row.keys())
    return (True, sorted(keys))


def _render_table(
    rows: List[Dict[str, Any]],
    cols: List[str],
    missing_sentinel: str,
) -> List[str]:
    def cell_for(row: Dict[str, Any], col: str) -> str:
        if col not in row:
            return _md_escape_table_cell(missing_sentinel)
        v = row.get(col)
        if isinstance(v, float):
            raise ValueError("Native float encountered in table cell (forbidden).")
        if v is None:
            return "null"
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, Decimal):
            return _decimal_to_canonical_str(v)
        if isinstance(v, int):
            return str(v)
        if isinstance(v, str):
            return _md_escape_table_cell(v)
        # Nested types: emit canonical JSON (still deterministic).
        return _md_escape_table_cell(_canonical_json_string(v))

    header = "| " + " | ".join(_md_escape_table_cell(c) for c in cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    out = [header, sep]
    for r in rows:
        out.append("| " + " | ".join(cell_for(r, c) for c in cols) + " |")
    return out


@dataclass(frozen=True)
class RenderOpts:
    max_depth: int = 15
    table_min_rows: int = 2
    missing_sentinel: str = "∅"
    max_heading_level: int = 6
    # Avoid tables when nested; indented tables often render as code blocks.
    allow_tables_only_at_root: bool = True


def _emit_heading_or_bullet(heading: str, level: int, indent: str, opts: RenderOpts) -> Tuple[List[str], str, int]:
    """
    If we are past max heading level, switch to bullet labels instead of deeper headings.
    Returns (lines_to_emit, new_indent, new_level).
    """
    h = _md_escape_inline(heading)
    if level <= opts.max_heading_level:
        return ([f"{indent}{'#' * level} {h}"], indent, level)
    # Past heading capacity: bullet label, then indent deeper.
    return ([f"{indent}- **{h}**:"], indent + "  ", level)


def _render_node(node: Any, heading: str | None, level: int, indent: str, opts: RenderOpts, depth: int = 0) -> List[str]:
    if depth > opts.max_depth:
        return [f"{indent}- **_error_**: max_depth exceeded"]

    out: List[str] = []
    if isinstance(node, float):
        raise ValueError("Native float encountered (forbidden).")

    if heading is not None:
        head_lines, indent, level = _emit_heading_or_bullet(heading, level, indent, opts)
        out.extend(head_lines)

    if isinstance(node, dict):
        for k in sorted(node.keys()):
            v = node[k]
            if _is_primitive(v):
                if isinstance(v, str) and "\n" in _normalize_newlines(v):
                    out.append(f"{indent}- **{_md_escape_inline(k)}**:")
                    out.extend(_render_multiline_string(v, indent=indent + "  "))
                else:
                    out.append(f"{indent}- **{_md_escape_inline(k)}**: {_value_to_inline_md(v)}")
            elif isinstance(v, dict):
                out.extend(_render_node(v, heading=k, level=level + 1, indent=indent, opts=opts, depth=depth + 1))
            elif isinstance(v, list):
                out.extend(_render_node(v, heading=k, level=level + 1, indent=indent, opts=opts, depth=depth + 1))
            else:
                out.append(f"{indent}- **{_md_escape_inline(k)}**: {_md_escape_inline(str(v))}")
        return out

    if isinstance(node, list):
        # Only render tables at root unless explicitly allowed
        uniform, cols = _list_of_objects_uniform(node)
        can_table = uniform and len(node) >= opts.table_min_rows
        if opts.allow_tables_only_at_root and indent != "":
            can_table = False

        if can_table:
            out.extend(_render_table(node, cols, missing_sentinel=opts.missing_sentinel))
            return out

        # List of primitives
        if all(_is_primitive(x) for x in node):
            for x in node:
                if isinstance(x, str) and "\n" in _normalize_newlines(x):
                    out.append(f"{indent}-")
                    out.extend(_render_multiline_string(x, indent=indent + "  "))
                else:
                    out.append(f"{indent}- {_value_to_inline_md(x)}")
            return out

        # Mixed/nested list
        for i, item in enumerate(node, start=1):
            if _is_primitive(item):
                out.append(f"{indent}{i}. {_value_to_inline_md(item)}")
            elif isinstance(item, str) and "\n" in _normalize_newlines(item):
                out.append(f"{indent}{i}.")
                out.extend(_render_multiline_string(item, indent=indent + "   "))
            else:
                out.append(f"{indent}{i}.")
                rendered = _render_node(item, heading=None, level=level, indent=indent + "   ", opts=opts, depth=depth + 1)
                out.extend(rendered)
        return out

    # Primitive root
    if isinstance(node, str) and "\n" in _normalize_newlines(node):
        out.extend(_render_multiline_string(node, indent=indent))
    else:
        out.append(f"{indent}{_value_to_inline_md(node)}")
    return out


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description="Deterministic JSON -> Markdown converter (v2)")
    ap.add_argument("input_json", help="Path to input JSON file")
    ap.add_argument("-o", "--output", help="Path to output Markdown file (default: <input>.md)")
    ap.add_argument("--title", help="Document title (default: filename)")
    ap.add_argument("--max-depth", type=int, default=15)
    ap.add_argument("--table-min-rows", type=int, default=2)
    ap.add_argument("--missing-sentinel", default="∅", help="Table sentinel for missing keys (default: ∅)")
    ap.add_argument("--mode", choices=["report", "contract"], default="report",
                    help="report=hash-only; contract=embed canonical JSON for round-trip")
    ap.add_argument("--verify", action="store_true", help="Fail if output would change existing output file")
    args = ap.parse_args()

    in_path = args.input_json
    out_path = args.output or os.path.splitext(in_path)[0] + ".md"
    title = args.title or os.path.basename(in_path)

    data = load_json(in_path)
    canon_str = _canonical_json_string(data)
    json_sha = _sha256_hex(canon_str)

    opts = RenderOpts(
        max_depth=args.max_depth,
        table_min_rows=args.table_min_rows,
        missing_sentinel=args.missing_sentinel,
    )

    lines: List[str] = []
    lines.append(f"# {_md_escape_inline(title)}")
    lines.append("")
    lines.append(f"- **source_file**: {_md_escape_inline(os.path.abspath(in_path))}")
    lines.append(f"- **canonical_sha256**: `{json_sha}`")
    lines.append(f"- **mode**: `{args.mode}`")
    lines.append("")
    lines.append("## content")
    lines.append("")
    lines.extend(_render_node(_canonicalize(data), heading=None, level=3, indent="", opts=opts))

    if args.mode == "contract":
        lines.append("")
        lines.append("## canonical_json")
        lines.append("")
        lines.append("```json")
        lines.append(_pretty_json_with_decimals(_canonicalize(data)))
        lines.append("```")

    md = "\n".join(lines).rstrip() + "\n"
    md = _normalize_newlines(md)
    md_sha = _sha256_hex(md)

    if args.verify and os.path.exists(out_path):
        # Fast path: hash compare first.
        existing = open(out_path, "r", encoding="utf-8").read()
        existing = _normalize_newlines(existing)
        existing_sha = _sha256_hex(existing)
        if existing_sha == md_sha:
            return 0
        if existing != md:
            raise SystemExit(f"VERIFY FAILED: {out_path} would change")

    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(md)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
