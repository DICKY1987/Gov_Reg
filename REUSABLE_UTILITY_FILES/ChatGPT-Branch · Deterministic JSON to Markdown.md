# Branch · Deterministic JSON to Markdown

**User:** bill reed (richgwilks@gmail.com)  
**Created:** 2/21/2026 12:42:02  
**Updated:** 2/21/2026 14:59:30  
**Exported:** 2/22/2026 17:24:39  
**Link:** [https://chatgpt.com/g/g-p-698452aa43fc81918e9cd8c88e4e543d-newphaseplanprocess/c/6999fc77-cde0-8332-9be4-e3c529a305fc](https://chatgpt.com/g/g-p-698452aa43fc81918e9cd8c88e4e543d-newphaseplanprocess/c/6999fc77-cde0-8332-9be4-e3c529a305fc)  

## Response:
Thought for 36s

A deterministic JSON→Markdown converter is doable if you **standardize (1) JSON normalization** and **(2) Markdown emission rules**. If you don’t lock those down, Markdown will drift (key order, list rendering, table column order, string escaping, etc.).

Deterministic conversion contract
---------------------------------

### 1) JSON normalization (canonical form)

Rules:

*   **Object key order:** sort keys lexicographically (Unicode codepoint order).
*   **Arrays:** preserve array order exactly (arrays are already ordered in JSON).
*   **Numbers:** parse with `Decimal` and emit in a canonical string form (no scientific notation unless you choose it).
*   **Booleans/null:** emit `true/false/null`.
*   **Strings:** UTF-8, normalize newlines to `\n`.

Optional but recommended:

*   Compute **SHA-256 of canonical JSON** and embed it in the Markdown so you can verify the Markdown matches a specific JSON state.

### 2) Markdown emission rules (stable layout)

Choose one fixed structure and never deviate:

*   Document header:
    *   `# <title>` (title comes from CLI arg or filename)
    *   metadata bullets including `source_file`, `canonical_sha256`
*   Rendering primitives:
    *   `- **key**: value`
*   Rendering objects:
    *   `## key` then render its contents
*   Rendering arrays:
    *   If array of primitives → bullet list
    *   If array of objects with consistent keys → **table** with **sorted columns**
    *   Else → numbered list, each item rendered recursively
*   Multiline strings → fenced code block with ` ```text `

This gives you stable, diff-friendly output.

* * *

Reusable CLI (Python) — deterministic JSON→MD
---------------------------------------------

```
#!/usr/bin/env python3
"""
Deterministic JSON -> Markdown converter.

Determinism guarantees:
- Dict keys sorted lexicographically at every depth.
- Lists preserved in original order.
- Numbers parsed as Decimal; emitted canonically.
- Stable table rendering (sorted columns).
- Stable newline normalization (\n).
- Optional embedded SHA-256 of canonical JSON.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Tuple, Union

JsonT = Union[Dict[str, Any], List[Any], str, int, float, bool, None, Decimal]

def _decimal_to_canonical_str(d: Decimal) -> str:
    # Canonical: no exponent, trim trailing zeros, keep "0" for zero-ish.
    # quantize is risky without context; use normalized string logic.
    s = format(d, "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    if s == "-0":
        s = "0"
    return s

def _canonicalize(obj: JsonT) -> JsonT:
    if isinstance(obj, dict):
        return {k: _canonicalize(obj[k]) for k in sorted(obj.keys())}
    if isinstance(obj, list):
        return [_canonicalize(v) for v in obj]
    if isinstance(obj, Decimal):
        return obj
    if isinstance(obj, float):
        # Avoid float nondeterminism by converting through repr (still imperfect).
        # Prefer Decimal parsing at load time; this is fallback.
        return Decimal(repr(obj))
    return obj

def _canonical_json_string(obj: JsonT) -> str:
    # Convert Decimals to canonical strings for hashing/serialization.
    def conv(x: Any) -> Any:
        if isinstance(x, dict):
            return {k: conv(v) for k, v in x.items()}
        if isinstance(x, list):
            return [conv(v) for v in x]
        if isinstance(x, Decimal):
            return _decimal_to_canonical_str(x)
        return x

    canon = conv(_canonicalize(obj))
    # separators remove spaces for stable hashing; ensure_ascii=False preserves UTF-8 content.
    return json.dumps(canon, ensure_ascii=False, separators=(",", ":"), sort_keys=True)

def _sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

_MD_SPECIAL = re.compile(r"([\\`*_{}\[\]()#+\-.!|>])")

def _md_escape_inline(text: str) -> str:
    # Escape Markdown punctuation including pipe (for tables).
    return _MD_SPECIAL.sub(r"\\\1", text)

def _normalize_newlines(s: str) -> str:
    return s.replace("\r\n", "\n").replace("\r", "\n")

def _is_primitive(x: Any) -> bool:
    return x is None or isinstance(x, (str, bool, int, Decimal))

def _value_to_inline_md(v: Any) -> str:
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
            # Caller should render multiline separately.
            return "(multiline)"
        return _md_escape_inline(s)
    # Fallback
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
    # Uniform keys = union keys; table will have sorted columns.
    keys = set()
    for row in lst:
        keys.update(row.keys())
    cols = sorted(keys)
    return (True, cols)

def _render_table(rows: List[Dict[str, Any]], cols: List[str], indent: str = "") -> List[str]:
    # Render a Markdown table deterministically.
    def cell(v: Any) -> str:
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
                s = s.replace("\n", "\\n")
            return _md_escape_inline(s)
        # For nested types, emit compact JSON marker deterministically.
        return _md_escape_inline(_canonical_json_string(_canonicalize(v)))

    header = indent + "| " + " | ".join(_md_escape_inline(c) for c in cols) + " |"
    sep = indent + "| " + " | ".join("---" for _ in cols) + " |"
    out = [header, sep]
    for r in rows:
        out.append(indent + "| " + " | ".join(cell(r.get(c)) for c in cols) + " |")
    return out

@dataclass(frozen=True)
class RenderOpts:
    max_depth: int = 50
    table_min_rows: int = 2

def _render_node(node: Any, heading: str | None, level: int, opts: RenderOpts, depth: int = 0) -> List[str]:
    if depth > opts.max_depth:
        return ["- **_error_**: max_depth exceeded"]

    out: List[str] = []

    if heading is not None:
        out.append(f"{'#' * level} {_md_escape_inline(heading)}")

    if isinstance(node, dict):
        for k in sorted(node.keys()):
            v = node[k]
            if _is_primitive(v):
                if isinstance(v, str) and "\n" in _normalize_newlines(v):
                    out.append(f"- **{_md_escape_inline(k)}**:")
                    out.extend(_render_multiline_string(v, indent="  "))
                else:
                    out.append(f"- **{_md_escape_inline(k)}**: {_value_to_inline_md(v)}")
            elif isinstance(v, dict):
                out.extend(_render_node(v, heading=k, level=level + 1, opts=opts, depth=depth + 1))
            elif isinstance(v, list):
                out.extend(_render_node(v, heading=k, level=level + 1, opts=opts, depth=depth + 1))
            else:
                out.append(f"- **{_md_escape_inline(k)}**: {_md_escape_inline(str(v))}")
        return out

    if isinstance(node, list):
        # Table if uniform object list and enough rows
        uniform, cols = _list_of_objects_uniform(node)
        if uniform and len(node) >= opts.table_min_rows:
            out.extend(_render_table(node, cols))
            return out

        # List of primitives
        if all(_is_primitive(x) or (isinstance(x, str) and "\n" not in _normalize_newlines(x)) for x in node):
            for x in node:
                if isinstance(x, str) and "\n" in _normalize_newlines(x):
                    out.append("-")
                    out.extend(_render_multiline_string(x, indent="  "))
                else:
                    out.append(f"- {_value_to_inline_md(x)}")
            return out

        # Mixed/nested list
        for i, item in enumerate(node, start=1):
            if _is_primitive(item):
                out.append(f"{i}. {_value_to_inline_md(item)}")
            elif isinstance(item, str) and "\n" in _normalize_newlines(item):
                out.append(f"{i}.")
                out.extend(_render_multiline_string(item, indent="   "))
            else:
                out.append(f"{i}.")
                out.extend("   " + line for line in _render_node(item, heading=None, level=level, opts=opts, depth=depth + 1))
        return out

    # Primitive root
    if isinstance(node, str) and "\n" in _normalize_newlines(node):
        out.extend(_render_multiline_string(node))
    else:
        out.append(_value_to_inline_md(node))
    return out

def load_json(path: str) -> JsonT:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f, parse_float=Decimal, parse_int=int)

def main() -> int:
    ap = argparse.ArgumentParser(description="Deterministic JSON -> Markdown converter")
    ap.add_argument("input_json", help="Path to input JSON file")
    ap.add_argument("-o", "--output", help="Path to output Markdown file (default: <input>.md)")
    ap.add_argument("--title", help="Document title (default: filename)")
    ap.add_argument("--max-depth", type=int, default=50)
    ap.add_argument("--table-min-rows", type=int, default=2)
    ap.add_argument("--verify", action="store_true", help="Fail if output would change existing output file")
    args = ap.parse_args()

    in_path = args.input_json
    out_path = args.output or os.path.splitext(in_path)[0] + ".md"
    title = args.title or os.path.basename(in_path)

    data = load_json(in_path)
    canon_str = _canonical_json_string(data)
    sha = _sha256_hex(canon_str)

    opts = RenderOpts(max_depth=args.max_depth, table_min_rows=args.table_min_rows)

    lines: List[str] = []
    lines.append(f"# {_md_escape_inline(title)}")
    lines.append("")
    lines.append(f"- **source_file**: {_md_escape_inline(os.path.abspath(in_path))}")
    lines.append(f"- **canonical_sha256**: `{sha}`")
    lines.append("")
    lines.append("## content")
    lines.append("")
    lines.extend(_render_node(_canonicalize(data), heading=None, level=2, opts=opts))

    md = "\n".join(lines).rstrip() + "\n"
    md = _normalize_newlines(md)

    if args.verify and os.path.exists(out_path):
        with open(out_path, "r", encoding="utf-8") as f:
            existing = _normalize_newlines(f.read())
        if existing != md:
            raise SystemExit(f"VERIFY FAILED: {out_path} would change")

    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(md)

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

### Usage

```
python json_to_md.py path/to/file.json
python json_to_md.py path/to/file.json -o path/to/file.md --title "Phase Contract"
python json_to_md.py path/to/file.json --verify
```

* * *

If you need “deterministic but schema-aware”
--------------------------------------------

The generic renderer above is deterministic but “dumb.” For your phase/workstream contracts, you’ll usually want:

*   a **profile** file that maps JSON Pointers to fixed section headings/order
*   a whitelist/blacklist of fields
*   field render modes (table vs bullets vs code block)

If you want, I can give you a second version that reads a `render_profile.json` like:

*   ordered `sections[]` with `{heading, pointer, mode}`
*   per-field `mode_overrides`
*   fixed ordering even when keys differ

That’s how you get “deterministic” _and_ “nice, contract-like Markdown” for your SSOT docs.

## Response:
Stopped thinking

## Response:
Thought for 1m 2s

Your feedback is correct. The fixes you called out (float hard-fail + duplicate-key detection) are mandatory if you actually mean “same input + same state → same output” (total, single-valued transition function).

Determinism is

Below is a tightened v2 script that implements those fixes plus the table “missing vs null” distinction and less noisy escaping.

What this version fixes (directly mapping to your points)
---------------------------------------------------------

*   **Hard-fail on native floats** anywhere in the loaded structure (no silent conversion).
*   **Reject duplicate JSON keys** at parse time (`object_pairs_hook`), instead of last-wins.
*   **Missing vs null in tables**: missing key renders as a sentinel (default `∅`), explicit `null` stays `null`.
*   **`--verify` optimized**: compares SHA-256 of normalized Markdown first; only falls back to full compare if needed.
*   **Escape policy tightened**: stops escaping `.` and `-` everywhere; still escapes table-breaking `|` and other high-risk chars.
*   **Depth defaults**: `max_depth` default lowered to 15; heading overflow handled by switching to indented bullets instead of going past `######`.
*   **Optional true round-trip**: `--mode contract` embeds canonical JSON in a fenced block so a trivial `md_to_json` can reconstruct exactly. Default `report` stays “hash-only”.

* * *

```
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
import os
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Tuple, Union, Callable

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

def _canonical_json_string(obj: Any) -> str:
    # Convert Decimals to canonical strings for hashing/serialization.
    def conv(x: Any) -> Any:
        if isinstance(x, float):
            raise ValueError("Native float encountered during canonicalization (forbidden).")
        if isinstance(x, dict):
            return {k: conv(v) for k, v in x.items()}
        if isinstance(x, list):
            return [conv(v) for v in x]
        if isinstance(x, Decimal):
            return _decimal_to_canonical_str(x)
        return x

    canon = conv(_canonicalize(obj))
    return json.dumps(canon, ensure_ascii=False, separators=(",", ":"), sort_keys=True)

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
        if all(_is_primitive(x) or (isinstance(x, str) and "\n" not in _normalize_newlines(x)) for x in node):
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
        # Round-trip anchor: canonical JSON embedded verbatim (sorted keys, stable separators).
        # If you want pretty-printing, do it deterministically, but compact is safest.
        lines.append("")
        lines.append("## canonical_json")
        lines.append("")
        lines.append("```json")
        # Emit a stable, readable canonical JSON. Pretty-print with sorted keys.
        canon_obj = json.loads(canon_str)  # safe: already canonical
        lines.append(json.dumps(canon_obj, ensure_ascii=False, indent=2, sort_keys=True))
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
```

Usage
-----

```
python json_to_md_v2.py path/to/file.json
python json_to_md_v2.py path/to/file.json --verify
python json_to_md_v2.py path/to/file.json --mode contract
python json_to_md_v2.py path/to/file.json --missing-sentinel "<missing>"
```

If you want schema-driven determinism (next step)
-------------------------------------------------

If you have JSON Schema, stop using heuristics for “table vs list” and drive rendering from schema:

*   `type: array` + `items: object` → always table
*   column order from `properties` order (or explicit `x-md-order`)
*   required vs optional controls missing sentinel explicitly

If you want, I’ll add `--schema schema.json` and a tiny `render_profile.json` so your phase/workstream contracts always render in a fixed section order (no runtime inference).



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)