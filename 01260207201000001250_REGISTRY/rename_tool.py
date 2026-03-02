import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time
import shutil
from dataclasses import dataclass
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Missing dependency: pyyaml. pip install pyyaml", file=sys.stderr) # [cite: 7, 8]
    sys.exit(2)

TOOL_VERSION = "1.1" # 

@dataclass
class Op:
    old_path: Path
    new_path: Path
    old_rel: str
    new_rel: str
    file_id: str
    collision_resolved: bool = False
    collision_suffix: str = ""

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest() # [cite: 8]

def file_sha256(p: Path) -> str:
    # [cite: 62]
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def load_yaml(p: Path) -> dict:
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) # [cite: 8]

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True) # [cite: 8]

def now_utc_compact() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) # [cite: 8]

def write_manifest(path: Path, ops: list[Op], phase: str):
    # [cite: 62, 63]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["phase","path","size_bytes","mtime_epoch","sha256"])
        for o in sorted(ops, key=lambda x: str(x.old_path).lower()):
            p = o.old_path if phase == "before" else o.new_path
            st = p.stat()
            w.writerow([phase, str(p), st.st_size, int(st.st_mtime), file_sha256(p)])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()

    # Calculate script hash for auditability 
    script_path = Path(__file__).resolve()
    script_hash = file_sha256(script_path)

    cfg = load_yaml(Path(args.config)) # [cite: 10]
    run_cfg = cfg["run"]
    scan_cfg = cfg["scan"]
    ren_cfg = cfg["rename"]
    col_cfg = cfg["collisions"]
    gov_cfg = cfg.get("governance", {})

    run_id = run_cfg["run_id"]
    if run_id == "AUTO":
        run_id_prefix = run_cfg.get("run_id_prefix", "rename")
        run_id = f"{run_id_prefix}_{now_utc_compact()}" # [cite: 10]

    out_dir = Path(run_cfg["output_dir"]) / run_id
    ensure_dir(out_dir)

    # Config Echo 
    config_echo_path = out_dir / "CONFIG_ECHO.yml"
    shutil.copy2(args.config, config_echo_path)

    # Evidence / artifacts paths [cite: 10, 11]
    rename_map_path = out_dir / "RENAME_MAP.json"
    plan_report_path = out_dir / "PLAN_REPORT.md"
    exec_summary_path = out_dir / "EXECUTION_SUMMARY.md"
    run_manifest_path = out_dir / "RUN_MANIFEST.json"
    full_inventory_path = out_dir / "FULL_INVENTORY.csv"
    before_manifest_path = out_dir / "before_manifest.csv"
    after_manifest_path = out_dir / "after_manifest.csv"
    traversal_report_path = out_dir / "TRAVERSAL_REPORT.json"
    log_path = out_dir / "rename_log.jsonl"

    match_re = re.compile(ren_cfg["rule"]["match_regex"])
    repl = ren_cfg["rule"]["replace_with"]

    roots = [Path(r) for r in scan_cfg["roots"]]
    recursive = bool(scan_cfg.get("recursive", True))
    follow_symlinks = bool(scan_cfg.get("follow_symlinks", False))
    exclude_dirs = set(scan_cfg.get("exclude_dirs", []))
    exclude_contains = scan_cfg.get("exclude_path_contains", [])
    include_extensions = scan_cfg.get("include_extensions", [])
    include_exts = set()
    for ext in include_extensions:
        if not ext:
            continue
        norm = ext.lower()
        if not norm.startswith("."):
            norm = "." + norm
        include_exts.add(norm)
    emit_full_inventory = bool(scan_cfg.get("emit_full_inventory", False))
    hash_contents = bool(scan_cfg.get("hash_contents", True)) # [cite: 62]
    keep_prefix = ren_cfg.get("keep_prefix")

    dry_run = bool(run_cfg.get("dry_run", True)) # [cite: 12]
    no_overwrite = bool(gov_cfg.get("no_overwrite", True))

    t0 = time.time()

    dirs_visited = 0
    files_visited_total = 0
    matched = 0
    skipped_reasons = {}

    inventory_rows = []
    ops: list[Op] = []

    def skip(reason: str):
        skipped_reasons[reason] = skipped_reasons.get(reason, 0) + 1 # [cite: 12]

    # --- PHASE 1: Scan & Filter ---
    for root in roots:
        if not root.exists():
            skip("missing_root")
            continue # [cite: 47]

        if recursive:
            for dirpath, dirnames, filenames in os.walk(root, followlinks=follow_symlinks):
                # prune excluded dirs deterministically
                dirnames[:] = sorted([d for d in dirnames if d not in exclude_dirs]) # [cite: 48]
                dirs_visited += 1 # [cite: 47]
                filenames = sorted(filenames)

                for fn in filenames:
                    fp = Path(dirpath) / fn
                    files_visited_total += 1 # [cite: 48, 49]
                    
                    s = str(fp)
                    if any(tok in s for tok in exclude_contains):
                        skip("excluded_path_contains")
                        if emit_full_inventory:
                            inventory_rows.append((str(fp), "SKIP", "excluded_path_contains")) # [cite: 49, 50]
                        continue
                    if include_exts:
                        ext = fp.suffix.lower()
                        if ext not in include_exts:
                            skip("excluded_extension")
                            if emit_full_inventory:
                                inventory_rows.append((str(fp), "SKIP", "excluded_extension"))
                            continue

                    base = fp.name
                    m = match_re.match(base)
                    if not m:
                        skip("no_match")
                        if emit_full_inventory:
                            inventory_rows.append((str(fp), "SKIP", "no_match")) # [cite: 50, 51]
                        continue

                    prefix = m.group(1)
                    if keep_prefix and not prefix.startswith(keep_prefix):
                        skip("bad_prefix")
                        if emit_full_inventory:
                            inventory_rows.append((str(fp), "SKIP", "bad_prefix"))
                        continue
                    file_id = prefix.split("_", 1)[1] # [cite: 51, 52]
                    new_base = re.sub(match_re, repl, base)

                    if not new_base.startswith(prefix + "_"):
                        skip("invariant_prefix_changed")
                        if emit_full_inventory:
                            inventory_rows.append((str(fp), "SKIP", "invariant_prefix_changed")) # [cite: 52, 53]
                        continue
                    if fp.suffix != Path(new_base).suffix:
                        skip("invariant_ext_changed")
                        if emit_full_inventory:
                            inventory_rows.append((str(fp), "SKIP", "invariant_ext_changed")) # [cite: 53, 54]
                        continue

                    new_path = fp.with_name(new_base)
                    old_rel = str(fp.relative_to(root))
                    new_rel = str(new_path.relative_to(root)) # [cite: 54, 55]

                    ops.append(Op(fp, new_path, old_rel, new_rel, file_id))
                    matched += 1
                    if emit_full_inventory:
                        inventory_rows.append((str(fp), "MATCH", "")) # [cite: 55]
        else:
            dirs_visited += 1 # [cite: 56]
            for fp in sorted(root.iterdir()):
                if fp.is_dir():
                    continue
                files_visited_total += 1 # [cite: 56]

                s = str(fp)
                if any(tok in s for tok in exclude_contains):
                    skip("excluded_path_contains")
                    if emit_full_inventory:
                        inventory_rows.append((str(fp), "SKIP", "excluded_path_contains")) # [cite: 56, 57]
                    continue
                if include_exts:
                    ext = fp.suffix.lower()
                    if ext not in include_exts:
                        skip("excluded_extension")
                        if emit_full_inventory:
                            inventory_rows.append((str(fp), "SKIP", "excluded_extension"))
                        continue

                base = fp.name
                m = match_re.match(base)
                if not m:
                    skip("no_match")
                    if emit_full_inventory:
                        inventory_rows.append((str(fp), "SKIP", "no_match")) # [cite: 57, 58]
                    continue

                prefix = m.group(1)
                if keep_prefix and not prefix.startswith(keep_prefix):
                    skip("bad_prefix")
                    if emit_full_inventory:
                        inventory_rows.append((str(fp), "SKIP", "bad_prefix"))
                    continue
                file_id = prefix.split("_", 1)[1]
                new_base = re.sub(match_re, repl, base)

                if not new_base.startswith(prefix + "_"):
                    skip("invariant_prefix_changed")
                    if emit_full_inventory:
                        inventory_rows.append((str(fp), "SKIP", "invariant_prefix_changed"))
                    continue
                if fp.suffix != Path(new_base).suffix:
                    skip("invariant_ext_changed")
                    if emit_full_inventory:
                        inventory_rows.append((str(fp), "SKIP", "invariant_ext_changed"))
                    continue

                new_path = fp.with_name(new_base)

                old_rel = fp.name
                new_rel = new_path.name

                ops.append(Op(fp, new_path, old_rel, new_rel, file_id))
                matched += 1 # [cite: 58, 59]
                if emit_full_inventory:
                    inventory_rows.append((str(fp), "MATCH", ""))

    # --- PHASE 2: Collision Resolution ---
    def normalize_key(p: Path) -> tuple[str, str]:
        return (str(p.parent).lower(), p.name.lower()) # [cite: 59]

    planned_keys = set()
    
    def ensure_unique_dest(op: Op, planned_keys: set):
        attempt = 0
        while True:
            k = normalize_key(op.new_path)
            exists_fs = op.new_path.exists() and op.old_path.resolve() != op.new_path.resolve()
            exists_plan = k in planned_keys
            if (not exists_fs) and (not exists_plan):
                planned_keys.add(k)
                return # [cite: 60]
            attempt += 1
            h = sha256_hex(f"{op.old_rel}|{attempt}")[:int(col_cfg["hash_truncation"])]
            suffix = col_cfg["suffix_format"].format(hash8=h)
            op.collision_resolved = True
            op.collision_suffix = suffix # [cite: 60, 61]
            op.new_path = op.new_path.with_name(op.new_path.stem + suffix + op.new_path.suffix)

    # Initial sorting by destination to establish deterministic winners
    by_dest = {}
    for op in ops:
        key = (str(op.new_path.parent).lower(), op.new_path.name.lower())
        by_dest.setdefault(key, []).append(op)

    for key, group in by_dest.items():
        if len(group) == 1:
            continue
        group.sort(key=lambda o: o.old_rel)
        winner = group[0]
        for loser in group[1:]:
            h = sha256_hex(loser.old_rel)[:int(col_cfg["hash_truncation"])]
            suffix = col_cfg["suffix_format"].format(hash8=h)
            stem = loser.new_path.stem + suffix
            loser.new_path = loser.new_path.with_name(stem + loser.new_path.suffix)
            loser.collision_resolved = True
            loser.collision_suffix = suffix # [cite: 25, 26]

    # Guarantee absolute uniqueness globally
    planned_keys = set()
    for op in sorted(ops, key=lambda x: str(x.old_path).lower()):
        ensure_unique_dest(op, planned_keys) # [cite: 61]

    for op in ops:
        op.new_rel = str(Path(op.old_rel).with_name(op.new_path.name))

    collisions_resolved_count = sum(1 for o in ops if o.collision_resolved)

    # --- PHASE 3: Artifact Emission ---
    rename_map = {
        "run_id": run_id,
        "created_utc": now_utc_compact(),
        "operations": [
            {
                "file_id": o.file_id,
                "old_path": str(o.old_path),
                "new_path": str(o.new_path),
                "old_relative": o.old_rel,
                "new_relative": o.new_rel,
                "collision_resolved": o.collision_resolved,
                "collision_suffix": o.collision_suffix, # [cite: 29, 30]
            }
            for o in sorted(ops, key=lambda x: str(x.old_path).lower())
        ],
    }
    rename_map_path.write_text(json.dumps(rename_map, indent=2), encoding="utf-8")

    if emit_full_inventory:
        with full_inventory_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["path", "status", "reason"])
            w.writerows(inventory_rows) # [cite: 30, 31]

    # Write PLAN_REPORT.md [cite: 63, 64]
    with plan_report_path.open("w", encoding="utf-8") as f:
        f.write(f"# Plan Report for `{run_id}`\n\n")
        f.write(f"**Roots scanned:** {', '.join([str(r) for r in roots])}\n")
        f.write(f"**Recursive:** {recursive}\n\n")
        f.write("## Metrics\n")
        f.write(f"- Directories Visited: {dirs_visited}\n")
        f.write(f"- Files Visited Total: {files_visited_total}\n")
        f.write(f"- Files Matched: {matched}\n")
        f.write(f"- Collisions Resolved: {collisions_resolved_count}\n\n")
        f.write("## Skipped Reasons\n")
        for k, v in skipped_reasons.items():
            f.write(f"- {k}: {v}\n")
        f.write("\n## Candidate Preview (First 5)\n")
        for o in sorted(ops, key=lambda x: str(x.old_path).lower())[:5]:
            f.write(f"- {o.old_rel} -> {o.new_rel}\n")

    # Proceed gate
    gate_file = out_dir / run_cfg["proceed_gate_file"]
    if not gate_file.exists():
        gate_file.write_text("PROCEED_RENAME=NO\n", encoding="utf-8") # [cite: 31]

    gate_ok = False
    if gate_file.exists():
        txt = gate_file.read_text(encoding="utf-8", errors="replace")
        gate_ok = (run_cfg["proceed_gate_line"] in txt) # [cite: 31]

    if hash_contents and matched > 0:
        write_manifest(before_manifest_path, ops, "before") # [cite: 63]

    executed = 0
    failed = 0
    executed_ops: list[Op] = []

    # --- PHASE 4: Execution ---
    if (not dry_run) and gate_ok:
        with log_path.open("w", encoding="utf-8") as logf:
            for o in sorted(ops, key=lambda x: str(x.old_path).lower()): # [cite: 32]
                try:
                    if no_overwrite and o.new_path.exists():
                        raise RuntimeError("destination_exists_no_overwrite") # [cite: 32, 33]
                    
                    o.old_path.rename(o.new_path)
                    executed += 1
                    executed_ops.append(o)
                    logf.write(json.dumps({"event":"renamed","old":str(o.old_path),"new":str(o.new_path)})+"\n") # [cite: 33]
                except Exception as e:
                    failed += 1
                    logf.write(json.dumps({"event":"error","old":str(o.old_path),"new":str(o.new_path),"error":str(e)})+"\n") # [cite: 34]
                    break
        
        if hash_contents and executed_ops:
            write_manifest(after_manifest_path, executed_ops, "after") # [cite: 63]

    elapsed_ms = int((time.time() - t0) * 1000)

    metrics = {
        "dirs_visited": dirs_visited,
        "files_visited_total": files_visited_total, # [cite: 35, 36]
        "files_matched": matched,
        "collisions_resolved": collisions_resolved_count,
        "executed": executed,
        "failed": failed,
        "skipped_reasons": skipped_reasons,
        "files_skipped_reason_counts": skipped_reasons,
        "elapsed_ms": elapsed_ms # [cite: 36]
    }

    traversal_report = {
        "run_id": run_id,
        "created_utc": now_utc_compact(),
        "config_path": str(Path(args.config)),
        "config_echo_path": str(config_echo_path),
        "config": cfg,
        "metrics": metrics
    }
    traversal_report_path.write_text(json.dumps(traversal_report, indent=2), encoding="utf-8")

    # Write EXECUTION_SUMMARY.md [cite: 64]
    with exec_summary_path.open("w", encoding="utf-8") as f:
        f.write(f"# Execution Summary for `{run_id}`\n\n")
        f.write(f"- **Dry Run:** {dry_run}\n")
        f.write(f"- **Proceed Gate OK:** {gate_ok}\n")
        f.write(f"- **Total Executed:** {executed}\n")
        f.write(f"- **Total Failed:** {failed}\n")

    # RUN_MANIFEST [cite: 34, 35]
    manifest = {
        "run_id": run_id,
        "tool_version": TOOL_VERSION, # 
        "script_sha256": script_hash, # 
        "success": (failed == 0),
        "config_path": str(Path(args.config)),
        "roots": [str(r) for r in roots],
        "recursive": recursive,
        "dry_run": dry_run,
        "proceed_gate_ok": gate_ok,
        "metrics": metrics,
        "artifacts": {
            "rename_map": str(rename_map_path),
            "full_inventory": str(full_inventory_path) if emit_full_inventory else None,
            "before_manifest": str(before_manifest_path) if hash_contents else None,
            "after_manifest": str(after_manifest_path) if after_manifest_path.exists() else None,
            "rename_log": str(log_path) if log_path.exists() else None,
            "traversal_report": str(traversal_report_path),
            "plan_report": str(plan_report_path),
            "exec_summary": str(exec_summary_path),
            "config_echo": str(config_echo_path) # [cite: 36, 37, 65]
        }
    }
    run_manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8") # [cite: 37]

    print(json.dumps(metrics, indent=2)) # [cite: 37]

if __name__ == "__main__":
    main()
