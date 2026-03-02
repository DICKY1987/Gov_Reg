#!/usr/bin/env python3
"""
automation_descriptor_extractor.py

Declared metadata (AUTOMATION_META) is authoritative.
AST inference fills missing fields and produces "manual_fields_needed".

Depends on your astroid-based PythonASTParser:
- PythonASTParser.parse_file(...) -> ParseResult(success, ast_tree, source, errors, parse_time_ms) :contentReference[oaicite:2]{index=2}
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import json

# Import your parser (shim or impl). Shim re-exports __all__ from impl. :contentReference[oaicite:3]{index=3}
from python_ast_parser import PythonASTParser  # type: ignore

try:
    import astroid
    from astroid import nodes as anodes
except Exception as e:
    raise RuntimeError("astroid is required (parser already depends on it).") from e


@dataclass
class DescriptorResult:
    success: bool
    descriptor: Dict[str, Any]
    manual_fields_needed: List[str]
    errors: List[str]
    extracted_hints: Dict[str, Any]


def _is_empty(v: Any) -> bool:
    return v is None or v == "" or v == [] or v == {}  # keep it strict


def _deep_merge_prefer_left(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
    """
    Overlay into base (overlay wins) recursively.
    """
    out = dict(base)
    for k, v in overlay.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge_prefer_left(out[k], v)
        else:
            out[k] = v
    return out


def _deep_fill_missing(target: Dict[str, Any], fill: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fill only missing/empty values in target using fill, recursively.
    """
    out = dict(target)
    for k, v in fill.items():
        if k not in out:
            out[k] = v
            continue
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_fill_missing(out[k], v)
            continue
        if _is_empty(out[k]) and not _is_empty(v):
            out[k] = v
    return out


def _default_descriptor_skeleton(file_path: Path) -> Dict[str, Any]:
    return {
        "schema_version": "1.0",
        "record_kind": "automation_file_descriptor",
        "identity": {
            "file_id": "",
            "basename": file_path.name,
            "relative_path": file_path.as_posix(),
            "language": "python",
            "entrypoint": "",
            "status": "active",
            "owner": "",
        },
        "purpose": {
            "one_line_summary": "",
            "scope_in": [],
            "scope_out": [],
            "primary_user_value": "",
        },
        "triggering": {"trigger_modes": [], "triggers": []},
        "inputs": {
            "required_inputs": [],
            "optional_inputs": [],
            "config_files": [],
            "secrets": [],
        },
        "outputs": {"primary_outputs": [], "side_effects": []},
        "state_and_ssot": {
            "ssot_reads": [],
            "ssot_writes": [],
            "derived_artifacts_written": [],
            "state_store": "",
            "state_keys": [],
        },
        "observability": {
            "logging": {"format": "", "log_paths": [], "log_fields_required": []},
            "metrics": [],
            "evidence_artifacts": [],
            "notifications": {"channels": [], "escalation_rules": []},
        },
        "security_and_safety": {
            "permissions_needed": [],
            "allowed_paths": [],
            "denied_paths": [],
            "destructive_ops": [],
            "data_handling": "",
        },
        "compatibility": {
            "supported_os": [],
            "runtime_requirements": [],
            "dependencies": {"internal": [], "external": []},
        },
        "execution": {
            "commands": {"run_examples": []},
            "exit_codes": {"success": [0], "known_errors": []},
        },
        "testing": {
            "acceptance_tests": [],
            "fixtures": [],
            "dry_run_supported": False,
            "deterministic_replay": "",
        },
    }


# -------------------------
# Safe literal evaluation of astroid nodes (for AUTOMATION_META)
# -------------------------

def _literal_from_astroid(node: anodes.NodeNG) -> Any:
    """
    Convert a subset of astroid nodes into Python literals safely.
    Accepts only: Const, Dict, List, Tuple, Set.
    """
    if isinstance(node, anodes.Const):
        return node.value

    if isinstance(node, anodes.List):
        return [_literal_from_astroid(elt) for elt in node.elts]

    if isinstance(node, anodes.Tuple):
        return tuple(_literal_from_astroid(elt) for elt in node.elts)

    if isinstance(node, anodes.Set):
        return {_literal_from_astroid(elt) for elt in node.elts}

    if isinstance(node, anodes.Dict):
        out = {}
        for k, v in zip(node.keys, node.values):
            if k is None:
                raise ValueError("Dict unpacking not supported in AUTOMATION_META")
            kk = _literal_from_astroid(k)
            vv = _literal_from_astroid(v)
            out[kk] = vv
        return out

    raise ValueError(f"Non-literal node in AUTOMATION_META: {type(node).__name__}")


def _extract_declared_meta(module: anodes.Module) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """
    Find module-level assignment: AUTOMATION_META = { ...literal... }
    Return (meta_dict or None, errors)
    """
    errors: List[str] = []
    for stmt in module.body:
        if isinstance(stmt, anodes.Assign):
            # targets can be multiple; handle Name targets
            for tgt in stmt.targets:
                if isinstance(tgt, anodes.AssignName) and tgt.name == "AUTOMATION_META":
                    try:
                        meta = _literal_from_astroid(stmt.value)
                        if not isinstance(meta, dict):
                            errors.append("AUTOMATION_META must be a dict literal")
                            return None, errors
                        return meta, errors
                    except Exception as e:
                        errors.append(f"Failed to evaluate AUTOMATION_META: {e}")
                        return None, errors
    return None, errors


# -------------------------
# Inference (fills gaps only)
# -------------------------

def _infer_imports(module: anodes.Module) -> List[str]:
    imports: List[str] = []
    for stmt in module.body:
        if isinstance(stmt, anodes.Import):
            for name, _alias in stmt.names:
                imports.append(name)
        elif isinstance(stmt, anodes.ImportFrom):
            mod = stmt.modname or ""
            if mod:
                imports.append(mod)
    # de-dupe, keep stable
    seen = set()
    out = []
    for x in imports:
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _infer_entrypoint(module: anodes.Module) -> str:
    # best-effort: detect if __name__ == "__main__" block exists
    for stmt in module.body:
        if isinstance(stmt, anodes.If):
            try:
                if stmt.test.as_string().replace('"', "'").strip() == "__name__ == '__main__'":
                    return "ifmain"
            except Exception:
                pass
    return ""


def _infer_env_keys(module: anodes.Module) -> List[str]:
    keys: List[str] = []
    for call in module.nodes_of_class(anodes.Call):
        try:
            fn = call.func.as_string()
        except Exception:
            continue

        if fn in ("os.getenv", "os.environ.get") and call.args:
            a0 = call.args[0]
            if isinstance(a0, anodes.Const) and isinstance(a0.value, str):
                keys.append(a0.value)

    seen = set()
    out = []
    for k in keys:
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out


def _infer_cli_args_argparse(module: anodes.Module) -> List[Dict[str, Any]]:
    """
    Heuristic: capture calls ending with '.add_argument(...)'
    """
    found: List[Dict[str, Any]] = []
    for call in module.nodes_of_class(anodes.Call):
        if not isinstance(call.func, anodes.Attribute):
            continue
        if call.func.attrname != "add_argument":
            continue

        flags: List[str] = []
        for a in call.args:
            if isinstance(a, anodes.Const) and isinstance(a.value, str):
                flags.append(a.value)

        if flags:
            found.append({"flags": flags})
    return found


def _infer_side_effects(module: anodes.Module) -> Dict[str, Any]:
    """
    Detect broad side effects: file writes/deletes/moves, subprocess, requests, sqlite.
    """
    hints = {
        "file_reads": [],
        "file_writes": [],
        "deletes": [],
        "moves": [],
        "network_calls": [],
        "subprocess_calls": [],
        "db_calls": [],
        "uses_logging": False,
    }

    for call in module.nodes_of_class(anodes.Call):
        try:
            fn = call.func.as_string()
        except Exception:
            continue

        # logging usage (rough)
        if fn.startswith("logging.") or fn.endswith(".info") or fn.endswith(".warning") or fn.endswith(".error"):
            hints["uses_logging"] = True

        # open(...)
        if fn == "open" and call.args:
            p0 = call.args[0]
            path_lit = p0.value if isinstance(p0, anodes.Const) and isinstance(p0.value, str) else None

            mode = None
            if len(call.args) >= 2 and isinstance(call.args[1], anodes.Const) and isinstance(call.args[1].value, str):
                mode = call.args[1].value
            for kw in call.keywords or []:
                if kw.arg == "mode" and isinstance(kw.value, anodes.Const) and isinstance(kw.value.value, str):
                    mode = kw.value.value

            if path_lit:
                if mode and any(x in mode for x in ("w", "a", "+")):
                    hints["file_writes"].append(path_lit)
                else:
                    hints["file_reads"].append(path_lit)

        # deletes
        if fn in ("os.remove", "os.unlink", "Path.unlink", "shutil.rmtree"):
            hints["deletes"].append("dynamic_or_unknown")

        # moves/renames
        if fn in ("shutil.move", "shutil.copy", "shutil.copy2", "os.rename", "Path.rename", "Path.replace"):
            hints["moves"].append("dynamic_or_unknown")

        # network
        if fn.startswith("requests.") or fn == "urllib.request.urlopen":
            hints["network_calls"].append(fn)

        # subprocess
        if fn.startswith("subprocess.") or fn == "os.system":
            hints["subprocess_calls"].append(fn)

        # db
        if fn == "sqlite3.connect":
            hints["db_calls"].append(fn)

    # de-dupe
    for k in ("file_reads", "file_writes", "deletes", "moves", "network_calls", "subprocess_calls", "db_calls"):
        seen = set()
        dedup = []
        for x in hints[k]:
            if x not in seen:
                seen.add(x)
                dedup.append(x)
        hints[k] = dedup

    return hints


def _inferred_descriptor_fields(module: anodes.Module) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    imports = _infer_imports(module)
    entrypoint = _infer_entrypoint(module)
    env_keys = _infer_env_keys(module)
    argparse_args = _infer_cli_args_argparse(module)
    sidefx = _infer_side_effects(module)

    inferred = {
        "compatibility": {"dependencies": {"external": imports}},
        "identity": {"entrypoint": entrypoint},
        "inputs": {"secrets": env_keys},
        "extracted_hints": {  # keep these non-canonical
            "argparse_args": argparse_args,
            **sidefx,
        },
    }

    return inferred, inferred.get("extracted_hints", {})


def _manual_fields_needed(descriptor: Dict[str, Any]) -> List[str]:
    required_paths = [
        "purpose.one_line_summary",
        "purpose.primary_user_value",
        "triggering.trigger_modes",
        "state_and_ssot.ssot_reads",
        "state_and_ssot.ssot_writes",
        "security_and_safety.allowed_paths",
        "security_and_safety.destructive_ops",
        "execution.commands.run_examples",
        "testing.acceptance_tests",
    ]

    missing: List[str] = []

    def get_path(d: Dict[str, Any], path: str) -> Any:
        cur: Any = d
        for part in path.split("."):
            if not isinstance(cur, dict) or part not in cur:
                return None
            cur = cur[part]
        return cur

    for p in required_paths:
        v = get_path(descriptor, p)
        if _is_empty(v):
            missing.append(p)

    return missing


class AutomationDescriptorExtractor:
    def __init__(self, trace_id: Optional[str] = None, run_id: Optional[str] = None):
        self.parser = PythonASTParser(trace_id=trace_id, run_id=run_id)

    def extract_file(self, file_path: Path) -> DescriptorResult:
        pr = self.parser.parse_file(file_path)
        if not pr.success or pr.ast_tree is None:
            return DescriptorResult(
                success=False,
                descriptor={},
                manual_fields_needed=[],
                errors=list(pr.errors),
                extracted_hints={},
            )

        module: anodes.Module = pr.ast_tree

        base = _default_descriptor_skeleton(file_path)

        declared, decl_errors = _extract_declared_meta(module)
        declared = declared or {}

        inferred, hints = _inferred_descriptor_fields(module)

        # Merge strategy:
        # 1) base
        # 2) declared overrides base
        # 3) inferred fills blanks only (never overwrites declared)
        merged = _deep_merge_prefer_left(base, declared)
        merged = _deep_fill_missing(merged, inferred)

        missing = _manual_fields_needed(merged)

        # Attach parse-time evidence (non-canonical)
        merged.setdefault("extracted_hints", {})
        merged["extracted_hints"]["parse_time_ms"] = getattr(pr, "parse_time_ms", 0.0)

        all_errors = decl_errors

        return DescriptorResult(
            success=True,
            descriptor=merged,
            manual_fields_needed=missing,
            errors=all_errors,
            extracted_hints=hints,
        )

    @staticmethod
    def to_json(result: DescriptorResult) -> str:
        return json.dumps(
            {
                "success": result.success,
                "descriptor": result.descriptor,
                "manual_fields_needed": result.manual_fields_needed,
                "errors": result.errors,
                "extracted_hints": result.extracted_hints,
            },
            indent=2,
            sort_keys=False,
        )
