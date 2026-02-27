#!/usr/bin/env python3
"""Unified command line entry point for the v2 analysis pipeline.

This script replaces the individual phase scripts (dependency analyzer,
I/O surface analyzer, deliverable analyzer, complexity analyzer, semantic
signature extractor and file inventory builder) with a single
deterministic runner.  It walks the repository, builds a canonical
`FileContext` for each file, invokes all configured analyzers, assembles
the results into a version 2 inventory record, computes hashes and
writes the output as a JSONL stream.  A summary and sha256 checksum
are also persisted to the output directory to preserve evidence
behavior.

The resulting JSONL conforms to the schema defined in
``inventory_schema_v2.json`` in the same repository.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from analyzer_interface import (
    FileContext,
    DependencyAnalyzerAdapter,
    IOSurfaceAnalyzerAdapter,
    DeliverableAnalyzerAdapter,
    ComplexityAnalyzerAdapter,
    SemanticSignatureAnalyzerAdapter,
)


# Directories to exclude when walking the repository.  Mirrors the
# exclusions used by the original file inventory builder.
EXCLUDE_DIRS = {
    ".git",
    ".state",
    ".state_temp",
    ".worktrees",
    ".venv",
    "node_modules",
    ".pytest_cache",
}


def walk_repository(repo_root: Path) -> Iterable[Path]:
    """Yield all file paths underneath ``repo_root`` respecting exclusions."""
    for root, dirs, files in os.walk(repo_root):
        # In‑place modify dirs to skip excluded names
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for fname in files:
            # Skip intermediate regenerated files by convention
            if fname.endswith(".regenerated.json"):
                continue
            yield Path(root) / fname


def classify_file(rel_path: Path, ext: str, full_path: Path) -> str:
    """Classify the file in a similar manner to the original inventory builder.

    The classification helps downstream mapping stages.  See
    ``FileInventoryBuilder._classify_file`` for the original logic.
    """
    name = rel_path.name.lower()
    # Python files
    if ext == ".py":
        if name.startswith("test_") or name.endswith("_test.py"):
            return "python_test"
        if rel_path.parts and rel_path.parts[0].lower() == "scripts":
            return "python_entrypoint"
        try:
            text = full_path.read_text(encoding="utf-8")
            if "if __name__ == \"__main__\"" in text:
                return "python_entrypoint"
        except Exception:
            pass
        return "python_module"
    # JSON files
    if ext == ".json":
        try:
            data = json.loads(full_path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and ("$schema" in data or "$id" in data):
                return "schema_json"
        except Exception:
            pass
        if "template" in name or "spec" in name:
            return "template_json"
        return "data"
    # YAML/YML
    if ext in {".yml", ".yaml"}:
        return "config"
    # Markdown
    if ext == ".md":
        if any(token in name for token in ["spec", "instruction", "requirement"]):
            return "spec_doc"
        return "doc"
    # Unknown/Other
    return "unknown"


def build_record(ctx: FileContext, analyzers: List) -> Dict[str, Any]:
    """Assemble an inventory record from the context and analyzer outputs."""
    record: Dict[str, Any] = {
        "file_id": ctx.content_sha256,
        "path_rel": ctx.path_rel.as_posix(),
        "path_abs": str(ctx.file_path),
        "ext": ctx.ext,
        # classification will be set by caller
        "classification": None,
        "size_bytes": ctx.size_bytes,
        "mtime_utc": ctx.mtime_utc,
        "content_sha256": ctx.content_sha256,
        # parse section reserved for future parser metadata
        # e.g. AST syntax hash or line counts
        "parse": {},
        "facts": {},
        "provenance": {},
        "hashes": {},
    }
    # Run analyzers in deterministic order
    for analyzer in analyzers:
        res = analyzer.run(ctx)
        if not res.success or not res.output:
            continue
        # Each adapter returns a single top‑level key (e.g. "imports",
        # "io_surface") mapped to a nested structure.  Merge into
        # facts, overriding any existing key.
        for key, value in res.output.items():
            record["facts"][key] = value
    return record


def compute_hashes(record: Dict[str, Any]) -> None:
    """Compute the deterministic hashes for the provided record.

    This function mutates ``record`` in place.  It computes the
    ``facts_sha256`` over the canonical JSON of the ``facts`` object
    and the ``record_sha256`` over the entire record (excluding the
    ``record_sha256`` field itself).  Both hashes use SHA‑256 and
    hex‑encoded lowercase output.
    """
    # Compute facts hash
    canonical_facts = json.dumps(record["facts"], sort_keys=True, separators=(",", ":"))
    facts_hash = hashlib.sha256(canonical_facts.encode("utf-8")).hexdigest()
    record.setdefault("hashes", {})["facts_sha256"] = facts_hash
    # Compute record hash; exclude record_sha256 itself
    tmp_record = dict(record)
    # Deep copy the hashes object but omit record_sha256
    hashes_copy = dict(record.get("hashes", {}))
    hashes_copy.pop("record_sha256", None)
    tmp_record["hashes"] = hashes_copy
    canonical_record = json.dumps(tmp_record, sort_keys=True, separators=(",", ":"))
    record_hash = hashlib.sha256(canonical_record.encode("utf-8")).hexdigest()
    record["hashes"]["record_sha256"] = record_hash


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Run unified file analysis pipeline")
    parser.add_argument(
        "repo_root",
        type=str,
        help="Path to the root of the repository to analyze",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=".state/combined_output",
        help="Directory where inventory and summary will be written",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Instantiate analyzers once; order matters for determinism
    analyzers = [
        DependencyAnalyzerAdapter(),
        IOSurfaceAnalyzerAdapter(),
        DeliverableAnalyzerAdapter(),
        ComplexityAnalyzerAdapter(),
        SemanticSignatureAnalyzerAdapter(),
    ]

    run_id = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
    inventory_path = output_dir / "file_inventory_v2.jsonl"
    summary_path = output_dir / "inventory_summary.json"
    sha_path = output_dir / "inventory_sha256.json"

    record_count = 0
    with inventory_path.open("w", encoding="utf-8") as outf:
        for file_path in sorted(walk_repository(repo_root)):
            ctx = FileContext.from_path(file_path, repo_root)
            # Build base record and run analyzers
            record = build_record(ctx, analyzers)
            # Determine classification
            record["classification"] = classify_file(ctx.path_rel, ctx.ext, ctx.file_path)
            # Compute hashes
            compute_hashes(record)
            # Write as compact JSON
            outf.write(json.dumps(record, separators=(",", ":")) + "\n")
            record_count += 1

    # Compute overall file hash
    inventory_sha = hashlib.sha256(inventory_path.read_bytes()).hexdigest()
    summary = {
        "generated_at": datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat(),
        "file_count": record_count,
        "output_path": str(inventory_path),
        "output_sha256": inventory_sha,
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    sha_path.write_text(json.dumps({"sha256": inventory_sha}, indent=2, sort_keys=True), encoding="utf-8")

    print(f"Wrote {record_count} records to {inventory_path}")
    print(f"Inventory SHA256: {inventory_sha}")


if __name__ == "__main__":
    main()