#!/usr/bin/env python3
"""
Codex CLI wrapper for Refiner - applies fixes to plans based on gate and critique reports.
ENHANCED: Uses ArtifactEnvelope v1 with LIV checks on inputs.
"""
import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path

# Import artifact envelope library
sys.path.insert(0, str(Path(__file__).parent))
from artifact_envelope import ArtifactEnvelope

REFINER_VERSION = "1.1.0"  # Updated for envelope integration

def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def run_cmd(cmd, stdout_path: Path, stderr_path: Path) -> int:
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.parent.mkdir(parents=True, exist_ok=True)
    
    with stdout_path.open("wb") as out, stderr_path.open("wb") as err:
        # Use shell=True on Windows to find .ps1/.cmd wrappers
        p = subprocess.run(cmd, stdout=out, stderr=err, env=os.environ.copy(), shell=True)
        return p.returncode

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True, type=Path)
    ap.add_argument("--plan-envelope", type=Path, help="Plan envelope for LIV")
    ap.add_argument("--critique", required=True, type=Path)
    ap.add_argument("--critique-envelope", type=Path, help="Critique envelope for LIV")
    ap.add_argument("--gate", required=True, type=Path)
    ap.add_argument("--gate-envelope", type=Path, help="Gate envelope for LIV")
    ap.add_argument("--schema", required=True, type=Path)
    ap.add_argument("--out-plan", required=True, type=Path)
    ap.add_argument("--out-envelope", type=Path, help="Output envelope path")
    ap.add_argument("--log-stdout", required=True, type=Path)
    ap.add_argument("--log-stderr", required=True, type=Path)
    ap.add_argument("--model", default="")
    ap.add_argument("--run-id", default="RUN_UNKNOWN", help="Run ID for provenance")
    ap.add_argument("--evidence-dir", type=Path, help="Directory for io_validation.json")
    args = ap.parse_args()
    
    # LIV: Verify inputs if envelopes provided
    input_artifacts = []
    
    if args.plan_envelope and args.plan_envelope.exists():
        envelope_data = json.loads(args.plan_envelope.read_text())
        plan_artifact = envelope_data.get("artifact", {})
        input_artifacts.append({
            "path": str(args.plan),
            "sha256": plan_artifact.get("sha256")
        })
    
    if args.gate_envelope and args.gate_envelope.exists():
        envelope_data = json.loads(args.gate_envelope.read_text())
        gate_artifact = envelope_data.get("artifact", {})
        input_artifacts.append({
            "path": str(args.gate),
            "sha256": gate_artifact.get("sha256")
        })
    
    if args.critique_envelope and args.critique_envelope.exists():
        envelope_data = json.loads(args.critique_envelope.read_text())
        critique_artifact = envelope_data.get("artifact", {})
        input_artifacts.append({
            "path": str(args.critique),
            "sha256": critique_artifact.get("sha256")
        })
    
    if input_artifacts:
        evidence_path = None
        if args.evidence_dir:
            evidence_path = args.evidence_dir / "refiner_io_validation.json"
        
        liv_success = ArtifactEnvelope.verify_lineage(input_artifacts, evidence_path)
        
        if not liv_success:
            print("ERROR: Lineage integrity verification FAILED for refiner inputs", file=sys.stderr)
            sys.exit(50)

    # Check auth
    if not os.getenv("CODEX_API_KEY"):
        print("ERROR: CODEX_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(50)

    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    critique = json.loads(args.critique.read_text(encoding="utf-8"))
    gate = json.loads(args.gate.read_text(encoding="utf-8"))

    prompt = (
        "You are the Refiner. Produce a revised plan as JSON ONLY.\n"
        "Hard rules:\n"
        "1) Output MUST validate against the provided JSON Schema.\n"
        "2) Apply every blocker/major defect from gate report and critic report.\n"
        "3) Keep plan_id the same unless schema requires otherwise.\n\n"
        f"Current plan JSON:\n{json.dumps(plan, indent=2)}\n\n"
        f"Gate report:\n{json.dumps(gate, indent=2)}\n\n"
        f"Critique report:\n{json.dumps(critique, indent=2)}\n"
    )

    cmd = ["codex", "exec", "--sandbox", "read-only", "--output-schema", str(args.schema), "-o", str(args.out_plan), prompt]
    if args.model:
        cmd[2:2] = ["--model", args.model]

    rc = run_cmd(cmd, args.log_stdout, args.log_stderr)
    if rc != 0:
        print(f"Refiner failed (codex exit={rc}). See {args.log_stderr}", file=sys.stderr)
        sys.exit(50)
    
    # Create envelope if requested
    if args.out_envelope:
        derived_from = []
        
        if args.plan_envelope and args.plan_envelope.exists():
            plan_sha256 = ArtifactEnvelope.compute_sha256(args.plan)
            derived_from.append({"path": str(args.plan), "sha256": plan_sha256})
        
        if args.gate_envelope and args.gate_envelope.exists():
            gate_sha256 = ArtifactEnvelope.compute_sha256(args.gate)
            derived_from.append({"path": str(args.gate), "sha256": gate_sha256})
        
        if args.critique_envelope and args.critique_envelope.exists():
            critique_sha256 = ArtifactEnvelope.compute_sha256(args.critique)
            derived_from.append({"path": str(args.critique), "sha256": critique_sha256})
        
        process_logic_hash = ArtifactEnvelope.compute_sha256(Path(__file__))
        
        ArtifactEnvelope.create_envelope(
            artifact_path=args.out_plan,
            run_id=args.run_id,
            produced_by_type="phase",
            produced_by_id="refiner",
            attempt=1,
            derived_from_artifacts=derived_from,
            transformation_rule="Codex CLI schema-enforced plan refinement from gate and critique feedback",
            process_semantic_version=REFINER_VERSION,
            process_logic_hash=process_logic_hash,
            output_path=args.out_envelope
        )
    
    sys.exit(0)

if __name__ == "__main__":
    main()
