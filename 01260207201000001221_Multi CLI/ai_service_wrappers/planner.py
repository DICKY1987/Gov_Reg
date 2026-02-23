#!/usr/bin/env python3
"""
Codex CLI wrapper for Planner - generates draft plans with schema enforcement.
ENHANCED: Uses ArtifactEnvelope v1 with lineage tracking.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

# Import artifact envelope library
sys.path.insert(0, str(Path(__file__).parent))
from artifact_envelope import ArtifactEnvelope

PLANNER_VERSION = "1.1.0"  # Updated for envelope integration

def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def run_cmd(cmd, stdout_path: Path, stderr_path: Path, env=None) -> int:
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.parent.mkdir(parents=True, exist_ok=True)
    
    with stdout_path.open("wb") as out, stderr_path.open("wb") as err:
        # Use shell=True on Windows to find .ps1/.cmd wrappers
        p = subprocess.run(cmd, stdout=out, stderr=err, env=env, shell=True)
        return p.returncode

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--request", required=True, type=Path)
    ap.add_argument("--schema", required=True, type=Path)
    ap.add_argument("--out-plan", required=True, type=Path)
    ap.add_argument("--out-envelope", required=True, type=Path)
    ap.add_argument("--log-stdout", required=True, type=Path)
    ap.add_argument("--log-stderr", required=True, type=Path)
    ap.add_argument("--model", default="", help="Optional: codex --model/-m override")
    ap.add_argument("--run-id", default="RUN_UNKNOWN", help="Run ID for provenance")
    args = ap.parse_args()

    # Check auth
    if not os.getenv("CODEX_API_KEY"):
        print("ERROR: CODEX_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(30)

    req = json.loads(args.request.read_text(encoding="utf-8"))

    prompt = (
        "You are the Planner. Produce a contract-first implementation plan as JSON ONLY.\n"
        "Hard rules:\n"
        "1) Output MUST validate against the provided JSON Schema.\n"
        "2) Include concrete acceptance criteria, explicit quality gates with evidence artifacts, and a risk register.\n"
        "3) Do not include markdown.\n\n"
        f"Planning request JSON:\n{json.dumps(req, indent=2)}\n"
    )

    cmd = ["codex", "exec", "--sandbox", "read-only", "--output-schema", str(args.schema), "-o", str(args.out_plan), prompt]
    if args.model:
        cmd[2:2] = ["--model", args.model]

    env = os.environ.copy()

    rc = run_cmd(cmd, args.log_stdout, args.log_stderr, env=env)
    if rc != 0:
        print(f"Planner failed (codex exit={rc}). See logs: {args.log_stderr}", file=sys.stderr)
        sys.exit(30)

    # Create ArtifactEnvelope v1 with provenance
    request_sha256 = ArtifactEnvelope.compute_sha256(args.request)
    process_logic_hash = ArtifactEnvelope.compute_sha256(Path(__file__))
    
    ArtifactEnvelope.create_envelope(
        artifact_path=args.out_plan,
        run_id=args.run_id,
        produced_by_type="phase",
        produced_by_id="planner",
        attempt=1,
        derived_from_artifacts=[
            {
                "path": str(args.request),
                "sha256": request_sha256
            }
        ],
        transformation_rule="Codex CLI schema-enforced plan generation from planning request",
        process_semantic_version=PLANNER_VERSION,
        process_logic_hash=process_logic_hash,
        output_path=args.out_envelope
    )
    
    sys.exit(0)

if __name__ == "__main__":
    main()
