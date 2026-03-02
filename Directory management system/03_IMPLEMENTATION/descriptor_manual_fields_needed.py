#!/usr/bin/env python3
"""
describe_automation.py
Static analyzer that extracts descriptor hints from Python scripts.
Outputs JSON descriptors with extracted fields + manual_fields_needed.
"""

from __future__ import annotations
import ast
import argparse
import json
import os
import re
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


FILE_ID_RE = re.compile(r"^(?P<id>\d{16})[_\-].+")


def safe_unparse(node: ast.AST) -> str:
    try:
        return ast.unparse(node)  # py3.9+
    except Exception:
        return node.__class__.__name__


def literal_str(node: ast.AST) -> Optional[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def dotted_name(node: ast.AST) -> Optional[str]:
    """Return dotted name for Name/Attribute chains."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = dotted_name(node.value)
        if base:
            return f"{base}.{node.attr}"
    return None


@dataclass
class Extracted:
    module_doc_first_line: Optional[str] = None
    imports: Set[str] = field(default_factory=set)
    has_ifmain: bool = False
    ifmain_calls: Set[str] = field(default_factory=set)

    # Inputs
    argparse_args: List[Dict[str, Any]] = field(default_factory=list)
    click_options: List[Dict[str, Any]] = field(default_factory=list)
    env_keys: Set[str] = field(default_factory=set)
    config_literals: Set[str] = field(default_factory=set)

    # Side effects / outputs
    file_reads: Set[str] = field(default_factory=set)
    file_writes: Set[str] = field(default_factory=set)
    deletes: Set[str] = field(default_factory=set)
    moves: Set[str] = field(default_factory=set)
    network_calls: Set[str] = field(default_factory=set)
    subprocess_calls: Set[str] = field(default_factory=set)
    db_calls: Set[str] = field(default_factory=set)

    # Observability
    uses_logging: bool = False

    # Trigger hints
    trigger_hints: Set[str] = field(default_factory=set)


class Analyzer(ast.NodeVisitor):
    def __init__(self) -> None:
        self.ex = Extracted()
        self._in_ifmain = False

    def visit_Import(self, node: ast.Import) -> Any:
        for alias in node.names:
            self.ex.imports.add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:
        mod = node.module or ""
        if node.level and mod:
            self.ex.imports.add("." * node.level + mod)
        elif node.level and not mod:
            self.ex.imports.add("." * node.level)
        else:
            self.ex.imports.add(mod)
        self.generic_visit(node)

    def visit_Expr(self, node: ast.Expr) -> Any:
        # module docstring is the first Expr Constant[str] in Module.body, handled outside
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> Any:
        # Detect if __name__ == "__main__"
        is_ifmain = False
        t = node.test
        if (
            isinstance(t, ast.Compare)
            and isinstance(t.left, ast.Name)
            and t.left.id == "__name__"
            and len(t.ops) == 1
            and isinstance(t.ops[0], ast.Eq)
            and len(t.comparators) == 1
            and isinstance(t.comparators[0], ast.Constant)
            and t.comparators[0].value == "__main__"
        ):
            is_ifmain = True

        if is_ifmain:
            self.ex.has_ifmain = True
            old = self._in_ifmain
            self._in_ifmain = True
            for stmt in node.body:
                self.visit(stmt)
            self._in_ifmain = old
            # still visit orelse normally
            for stmt in node.orelse:
                self.visit(stmt)
            return

        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> Any:
        fn = dotted_name(node.func) or safe_unparse(node.func)

        # Track calls in ifmain
        if self._in_ifmain:
            # only capture simple call names
            if isinstance(node.func, ast.Name):
                self.ex.ifmain_calls.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                name = dotted_name(node.func)
                if name:
                    self.ex.ifmain_calls.add(name)

        # Logging detection
        if fn.startswith("logging.") or fn in {"basicConfig", "getLogger"}:
            self.ex.uses_logging = True

        # Environment variable usage
        if fn in {"os.getenv", "os.environ.get"} and node.args:
            key = literal_str(node.args[0])
            if key:
                self.ex.env_keys.add(key)

        # Argparse extraction (heuristic)
        # parser.add_argument("--x", ...)
        if fn.endswith("add_argument") and node.args:
            flags = []
            for a in node.args:
                s = literal_str(a)
                if s:
                    flags.append(s)
            if flags:
                rec = {"flags": flags, "kwargs": {}}
                for kw in node.keywords:
                    if kw.arg:
                        rec["kwargs"][kw.arg] = literal_str(kw.value) or safe_unparse(kw.value)
                self.ex.argparse_args.append(rec)

        # Click options extraction (heuristic)
        # @click.option(...) is a decorator; but we can also see click.option(...) call nodes
        if fn in {"click.option", "click.argument"}:
            rec = {"fn": fn, "args": [], "kwargs": {}}
            for a in node.args:
                rec["args"].append(literal_str(a) or safe_unparse(a))
            for kw in node.keywords:
                if kw.arg:
                    rec["kwargs"][kw.arg] = literal_str(kw.value) or safe_unparse(kw.value)
            self.ex.click_options.append(rec)

        # Trigger hints
        if fn.startswith("watchdog.") or fn.startswith("apscheduler.") or fn.startswith("schedule."):
            self.ex.trigger_hints.add("event_or_scheduler_library")
        if fn in {"time.sleep"}:
            self.ex.trigger_hints.add("looping_daemon_possible")

        # File IO
        if fn in {"open"} and node.args:
            path = literal_str(node.args[0])
            mode = None
            if len(node.args) >= 2:
                mode = literal_str(node.args[1])
            for kw in node.keywords:
                if kw.arg == "mode":
                    mode = literal_str(kw.value)
            if path:
                if mode and ("w" in mode or "a" in mode or "+" in mode):
                    self.ex.file_writes.add(path)
                else:
                    self.ex.file_reads.add(path)

        # pathlib writes
        if fn.endswith(".write_text") or fn.endswith(".write_bytes"):
            self.ex.file_writes.add("pathlib:dynamic_or_unknown")

        # Deletes
        if fn in {"os.remove", "os.unlink", "Path.unlink", "shutil.rmtree"}:
            self.ex.deletes.add("dynamic_or_unknown")

        # Moves/copies/renames
        if fn in {"shutil.move", "shutil.copy", "shutil.copy2", "os.rename", "Path.rename", "Path.replace"}:
            self.ex.moves.add("dynamic_or_unknown")

        # Network
        if fn.startswith("requests.") or fn in {"urllib.request.urlopen"}:
            self.ex.network_calls.add(fn)

        # Subprocess
        if fn.startswith("subprocess.") or fn in {"os.system"}:
            self.ex.subprocess_calls.add(fn)

        # DB
        if fn in {"sqlite3.connect"}:
            self.ex.db_calls.add("sqlite3.connect")

        self.generic_visit(node)


def analyze_file(py_path: Path) -> Dict[str, Any]:
    text = py_path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(text, filename=str(py_path))
    except SyntaxError as e:
        return {
            "error": f"SyntaxError: {e}",
            "path": str(py_path),
        }

    an = Analyzer()

    # module docstring
    doc = ast.get_docstring(tree)
    if doc:
        first = doc.strip().splitlines()[0].strip() if doc.strip() else None
        an.ex.module_doc_first_line = first

    an.visit(tree)

    file_id = None
    m = FILE_ID_RE.match(py_path.name)
    if m:
        file_id = m.group("id")

    # Build a partial descriptor
    descriptor: Dict[str, Any] = {
        "schema_version": "1.0",
        "record_kind": "automation_file_descriptor",
        "identity": {
            "file_id": file_id or "",
            "basename": py_path.name,
            "relative_path": str(py_path.as_posix()),
            "language": "python",
            "entrypoint": "",
            "status": "active",
            "owner": "",
        },
        "purpose": {
            "one_line_summary": an.ex.module_doc_first_line or "",
            "scope_in": [],
            "scope_out": [],
            "primary_user_value": "",
        },
        "triggering": {
            "trigger_modes": [],
            "triggers": [],
        },
        "inputs": {
            "required_inputs": [],
            "optional_inputs": [],
            "config_files": sorted(list(an.ex.config_literals)),
            "secrets": sorted(list(an.ex.env_keys)),
        },
        "outputs": {
            "primary_outputs": [],
            "side_effects": [],
        },
        "state_and_ssot": {
            "ssot_reads": [],
            "ssot_writes": [],
            "derived_artifacts_written": [],
            "state_store": "",
            "state_keys": [],
        },
        "observability": {
            "logging": {
                "format": "",
                "log_paths": [],
                "log_fields_required": [],
            },
            "metrics": [],
            "evidence_artifacts": [],
            "notifications": {"channels": [], "escalation_rules": []},
        },
        "compatibility": {
            "supported_os": [],
            "runtime_requirements": [],
            "dependencies": {
                "internal": [],
                "external": sorted([i for i in an.ex.imports if i and not i.startswith(".")]),
            },
        },
        "execution": {
            "commands": {"run_examples": []},
            "exit_codes": {"success": [0], "known_errors": []},
        },
        "extracted_hints": {
            "has_ifmain": an.ex.has_ifmain,
            "ifmain_calls": sorted(list(an.ex.ifmain_calls)),
            "argparse_args": an.ex.argparse_args,
            "click_options": an.ex.click_options,
            "file_reads": sorted(list(an.ex.file_reads)),
            "file_writes": sorted(list(an.ex.file_writes)),
            "deletes": sorted(list(an.ex.deletes)),
            "moves": sorted(list(an.ex.moves)),
            "network_calls": sorted(list(an.ex.network_calls)),
            "subprocess_calls": sorted(list(an.ex.subprocess_calls)),
            "db_calls": sorted(list(an.ex.db_calls)),
            "uses_logging": an.ex.uses_logging,
            "trigger_hints": sorted(list(an.ex.trigger_hints)),
        },
    }

    # Best-effort entrypoint
    if an.ex.has_ifmain:
        descriptor["identity"]["entrypoint"] = "if __name__ == '__main__'"
    elif "typer" in an.ex.imports:
        descriptor["identity"]["entrypoint"] = "typer app (heuristic)"
    elif "click" in an.ex.imports:
        descriptor["identity"]["entrypoint"] = "click command (heuristic)"

    # Side effects summary
    se = descriptor["outputs"]["side_effects"]
    if an.ex.file_writes:
        se.append({"description": "writes files (some paths may be dynamic)", "reversible": False, "rollback_method": ""})
    if an.ex.deletes:
        se.append({"description": "deletes files/dirs (paths may be dynamic)", "reversible": False, "rollback_method": ""})
    if an.ex.moves:
        se.append({"description": "moves/renames files (paths may be dynamic)", "reversible": True, "rollback_method": ""})
    if an.ex.network_calls:
        se.append({"description": f"network calls: {sorted(list(an.ex.network_calls))}", "reversible": False, "rollback_method": ""})
    if an.ex.subprocess_calls:
        se.append({"description": f"subprocess calls: {sorted(list(an.ex.subprocess_calls))}", "reversible": False, "rollback_method": ""})
    if an.ex.db_calls:
        se.append({"description": "database usage detected", "reversible": False, "rollback_method": ""})

    manual_fields_needed = [
        "purpose.scope_in",
        "purpose.scope_out",
        "purpose.primary_user_value",
        "triggering.trigger_modes / triggers (confirm actual behavior)",
        "inputs.required_inputs (confirm which are mandatory at runtime)",
        "outputs.primary_outputs (define real artifacts + locations)",
        "state_and_ssot.ssot_reads / ssot_writes (must be explicit to be useful)",
        "error_handling (policy, retries, rollback, quarantine)",
        "execution.run_examples (exact CLI commands)",
        "testing.acceptance_tests (scenarios + evidence)",
        "security_and_safety (allowed paths, destructive ops safeguards)",
    ]

    return {
        "descriptor": descriptor,
        "manual_fields_needed": manual_fields_needed,
    }


def iter_py_files(path: Path) -> List[Path]:
    if path.is_file() and path.suffix.lower() == ".py":
        return [path]
    files: List[Path] = []
    for p in path.rglob("*.py"):
        # skip common virtualenv / cache dirs
        if any(part in {".venv", "venv", "__pycache__", ".git"} for part in p.parts):
            continue
        files.append(p)
    return files


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="Python file or directory to analyze")
    ap.add_argument("--out", default="", help="Output directory (default: stdout)")
    args = ap.parse_args()

    target = Path(args.path).resolve()
    py_files = iter_py_files(target)
    if not py_files:
        raise SystemExit(f"No .py files found under: {target}")

    out_dir = Path(args.out).resolve() if args.out else None
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for f in py_files:
        r = analyze_file(f)
        if out_dir:
            out_path = out_dir / (f.stem + ".automation_descriptor.json")
            out_path.write_text(json.dumps(r, indent=2), encoding="utf-8")
        else:
            results.append(r)

    if not out_dir:
        print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
