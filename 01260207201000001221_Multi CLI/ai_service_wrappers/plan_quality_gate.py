#!/usr/bin/env python3
"""
Deterministic plan quality gate - validates plan structure without AI.
ENHANCED: Uses ArtifactEnvelope v1 with LIV checks on inputs.
"""
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

# Import artifact envelope library
sys.path.insert(0, str(Path(__file__).parent))
from artifact_envelope import ArtifactEnvelope

QUALITY_GATE_VERSION = "1.1.0"  # Updated for envelope integration

try:
    from jsonschema import Draft202012Validator
except ImportError:
    print("ERROR: jsonschema not installed. Run: pip install jsonschema", file=sys.stderr)
    sys.exit(20)

DEFECTS = {
    "PLAN_SCHEMA_INVALID": ("blocker", "Plan JSON does not conform to schema"),
    "PLAN_MISSING_ACCEPTANCE": ("blocker", "One or more deliverables missing acceptance criteria"),
    "PLAN_WEAK_GATES": ("major", "One or more quality gates missing evidence artifacts or criteria"),
    "PLAN_NO_RISKS": ("major", "Risk register missing or empty"),
    "PLAN_NO_TIMELINE": ("major", "Timeline missing or empty")
}

def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def gate_checks(plan: dict):
    defects = []

    # Deterministic: acceptance criteria exist & non-empty
    missing_accept = []
    for d in plan.get("deliverables", []):
        ac = d.get("acceptance_criteria", [])
        if not isinstance(ac, list) or len(ac) == 0:
            missing_accept.append(d.get("id", "<unknown>"))
    if missing_accept:
        defects.append({
            "code": "PLAN_MISSING_ACCEPTANCE",
            "severity": DEFECTS["PLAN_MISSING_ACCEPTANCE"][0],
            "message": f"Deliverables missing acceptance_criteria: {missing_accept}",
            "location": "deliverables[*].acceptance_criteria",
            "remediation_template": "add_acceptance_criteria"
        })

    # Deterministic: gates have criteria + evidence_artifacts
    weak_gates = []
    for g in plan.get("quality_gates", []):
        crit = g.get("criteria", [])
        ev = g.get("evidence_artifacts", [])
        if not isinstance(crit, list) or len(crit) == 0 or not isinstance(ev, list) or len(ev) == 0:
            weak_gates.append(g.get("id", "<unknown>"))
    if weak_gates:
        defects.append({
            "code": "PLAN_WEAK_GATES",
            "severity": DEFECTS["PLAN_WEAK_GATES"][0],
            "message": f"Gates missing criteria/evidence_artifacts: {weak_gates}",
            "location": "quality_gates[*]",
            "remediation_template": "strengthen_gates"
        })

    # Deterministic: risks exist
    risks = plan.get("risks", [])
    if not isinstance(risks, list) or len(risks) == 0:
        defects.append({
            "code": "PLAN_NO_RISKS",
            "severity": DEFECTS["PLAN_NO_RISKS"][0],
            "message": "risks must be a non-empty array",
            "location": "risks",
            "remediation_template": "add_risks"
        })

    # Deterministic: timeline exists
    tl = plan.get("timeline", [])
    if not isinstance(tl, list) or len(tl) == 0:
        defects.append({
            "code": "PLAN_NO_TIMELINE",
            "severity": DEFECTS["PLAN_NO_TIMELINE"][0],
            "message": "timeline must be a non-empty array",
            "location": "timeline",
            "remediation_template": "heal_plan_schema"
        })

    return defects

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True, type=Path)
    ap.add_argument("--plan-envelope", type=Path, help="Plan envelope for LIV")
    ap.add_argument("--schema", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--out-envelope", type=Path, help="Output envelope path")
    ap.add_argument("--run-id", default="RUN_UNKNOWN", help="Run ID for provenance")
    ap.add_argument("--evidence-dir", type=Path, help="Directory for io_validation.json")
    args = ap.parse_args()
    
    # LIV: Verify plan input if envelope provided
    if args.plan_envelope and args.plan_envelope.exists():
        envelope_data = json.loads(args.plan_envelope.read_text())
        plan_artifact = envelope_data.get("artifact", {})
        
        evidence_path = None
        if args.evidence_dir:
            evidence_path = args.evidence_dir / "quality_gate_io_validation.json"
        
        liv_success = ArtifactEnvelope.verify_lineage(
            [{"path": str(args.plan), "sha256": plan_artifact.get("sha256")}],
            evidence_path
        )
        
        if not liv_success:
            print("ERROR: Lineage integrity verification FAILED for plan input", file=sys.stderr)
            sys.exit(10)

    report = {
        "schema_version": "1.0",
        "passed": False,
        "defects": [],
        "summary": "",
        "computed_at": utc_now()
    }

    try:
        plan = load_json(args.plan)
        schema = load_json(args.schema)
        v = Draft202012Validator(schema)

        schema_errors = sorted(v.iter_errors(plan), key=lambda e: e.path)
        if schema_errors:
            details = []
            for e in schema_errors[:10]:
                details.append(f"{list(e.path)}: {e.message}")
            report["defects"].append({
                "code": "PLAN_SCHEMA_INVALID",
                "severity": DEFECTS["PLAN_SCHEMA_INVALID"][0],
                "message": DEFECTS["PLAN_SCHEMA_INVALID"][1] + " | " + " ; ".join(details),
                "location": "schema",
                "remediation_template": "heal_plan_schema"
            })
        else:
            report["defects"].extend(gate_checks(plan))

        report["passed"] = (len([d for d in report["defects"] if d["severity"] == "blocker"]) == 0)
        report["summary"] = "PASS" if report["passed"] else f"FAIL ({len(report['defects'])} defects)"

        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        
        # Create envelope if requested
        if args.out_envelope:
            plan_sha256 = ArtifactEnvelope.compute_sha256(args.plan)
            process_logic_hash = ArtifactEnvelope.compute_sha256(Path(__file__))
            
            ArtifactEnvelope.create_envelope(
                artifact_path=args.out,
                run_id=args.run_id,
                produced_by_type="gate",
                produced_by_id="quality_gate",
                attempt=1,
                derived_from_artifacts=[
                    {
                        "path": str(args.plan),
                        "sha256": plan_sha256
                    }
                ],
                transformation_rule="Deterministic quality gate validation without AI",
                process_semantic_version=QUALITY_GATE_VERSION,
                process_logic_hash=process_logic_hash,
                output_path=args.out_envelope
            )

        sys.exit(0 if report["passed"] else 10)

    except Exception as ex:
        report["passed"] = False
        report["summary"] = f"ERROR: {type(ex).__name__}: {ex}"
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        sys.exit(20)

if __name__ == "__main__":
    main()
