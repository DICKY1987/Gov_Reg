#!/usr/bin/env python3
"""
Copilot CLI wrapper for Critic - evaluates plans and returns critique.
ENHANCED: Uses ArtifactEnvelope v1 with LIV checks on inputs.
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path

# Import artifact envelope library
sys.path.insert(0, str(Path(__file__).parent))
from artifact_envelope import ArtifactEnvelope

CRITIC_VERSION = "1.1.0"  # Updated for envelope integration

def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def run_copilot(prompt: str, log_out: Path, log_err: Path) -> int:
    log_out.parent.mkdir(parents=True, exist_ok=True)
    log_err.parent.mkdir(parents=True, exist_ok=True)

    # Headless safety: deny write + deny all shell commands.
    cmd = [
        "copilot",
        "-s", "-p", prompt,
        "--no-color",
        "--deny-tool", "write",
        "--deny-tool", "shell"
    ]

    with log_out.open("wb") as out, log_err.open("wb") as err:
        p = subprocess.run(cmd, stdout=out, stderr=err, env=os.environ.copy())
        return p.returncode

def extract_json(text: str) -> dict:
    """Extract JSON object from text, handling markdown code blocks."""
    text = text.strip()
    
    # Remove markdown code blocks if present
    text = re.sub(r'^```json\s*', '', text)
    text = re.sub(r'^```\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    text = text.strip()
    
    if text.startswith("{") and text.endswith("}"):
        return json.loads(text)
    
    m = re.search(r'\{.*\}\s*$', text, re.DOTALL)
    if m:
        return json.loads(m.group(0))
    raise ValueError("No JSON object found")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True, type=Path)
    ap.add_argument("--plan-envelope", type=Path, help="Path to plan envelope for LIV")
    ap.add_argument("--schema", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--out-envelope", type=Path, help="Path to write critique envelope")
    ap.add_argument("--log-stdout", required=True, type=Path)
    ap.add_argument("--log-stderr", required=True, type=Path)
    ap.add_argument("--max-attempts", type=int, default=2)
    ap.add_argument("--run-id", default="RUN_UNKNOWN", help="Run ID for provenance")
    ap.add_argument("--evidence-dir", type=Path, help="Directory for io_validation.json")
    args = ap.parse_args()

    # LIV: Verify plan input if envelope provided
    if args.plan_envelope and args.plan_envelope.exists():
        envelope_data = json.loads(args.plan_envelope.read_text())
        plan_artifact = envelope_data.get("artifact", {})
        
        evidence_path = None
        if args.evidence_dir:
            evidence_path = args.evidence_dir / "critic_io_validation.json"
        
        liv_success = ArtifactEnvelope.verify_lineage(
            [{"path": str(args.plan), "sha256": plan_artifact.get("sha256")}],
            evidence_path
        )
        
        if not liv_success:
            print("ERROR: Lineage integrity verification FAILED for plan input", file=sys.stderr)
            sys.exit(40)

    # Check auth
    if not (os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")):
        print("ERROR: GH_TOKEN or GITHUB_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(40)

    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    plan_id = plan.get("plan_id", "")

    base_prompt = (
        "You are the Critic. Review the plan JSON and return ONLY a JSON object that matches this structure:\n"
        "{schema_version:'1.0', critique_id:<uuid>, plan_id:<uuid>, computed_at:<rfc3339>, verdict:'pass|needs_revision|fail', "
        "scorecard:{completeness:0-5, testability:0-5, risk_coverage:0-5, sequencing:0-5, gate_quality:0-5}, "
        "defects:[{code,severity,message,evidence,fix}]}\n"
        "Hard rules: output JSON only; no markdown; no extra keys.\n\n"
        f"plan_id: {plan_id}\n"
        f"Plan JSON:\n{json.dumps(plan, indent=2)}\n"
    )

    for attempt in range(1, args.max_attempts + 1):
        prompt = base_prompt if attempt == 1 else (base_prompt + "\nREMINDER: OUTPUT JSON ONLY. NO PROSE.\n")
        rc = run_copilot(prompt, args.log_stdout, args.log_stderr)
        if rc != 0:
            print(f"Critic failed (copilot exit={rc}). Check stderr log: {args.log_stderr}", file=sys.stderr)
            continue

        raw = args.log_stdout.read_text(encoding="utf-8", errors="replace")
        try:
            obj = extract_json(raw)
            # Enforce required top-level keys
            for k in ["schema_version", "critique_id", "plan_id", "computed_at", "verdict", "defects"]:
                if k not in obj:
                    raise ValueError(f"Missing key: {k}")
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(json.dumps(obj, indent=2), encoding="utf-8")
            
            # Create envelope if requested
            if args.out_envelope:
                plan_sha256 = ArtifactEnvelope.compute_sha256(args.plan)
                process_logic_hash = ArtifactEnvelope.compute_sha256(Path(__file__))
                
                ArtifactEnvelope.create_envelope(
                    artifact_path=args.out,
                    run_id=args.run_id,
                    produced_by_type="phase",
                    produced_by_id="critic",
                    attempt=attempt,
                    derived_from_artifacts=[
                        {
                            "path": str(args.plan),
                            "sha256": plan_sha256
                        }
                    ],
                    transformation_rule="Copilot CLI cross-model plan critique",
                    process_semantic_version=CRITIC_VERSION,
                    process_logic_hash=process_logic_hash,
                    output_path=args.out_envelope
                )
            
            sys.exit(0)
        except Exception as ex:
            if attempt == args.max_attempts:
                fallback = {
                    "schema_version": "1.0",
                    "critique_id": str(uuid.uuid4()),
                    "plan_id": plan_id,
                    "computed_at": utc_now(),
                    "verdict": "fail",
                    "defects": [{
                        "code": "CRITIC_JSON_INVALID",
                        "severity": "blocker",
                        "message": f"Copilot output not valid JSON: {type(ex).__name__}: {ex}",
                        "evidence": "critic.py wrapper",
                        "fix": "Re-run critic with stricter JSON-only prompt or migrate critic to ACP for NDJSON."
                    }]
                }
                args.out.parent.mkdir(parents=True, exist_ok=True)
                args.out.write_text(json.dumps(fallback, indent=2), encoding="utf-8")
                sys.exit(40)

    sys.exit(40)

if __name__ == "__main__":
    main()
