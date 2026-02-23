#!/usr/bin/env python3
"""
Evidence Recorder - Metadata Script
Records analysis evidence for audit trail and reproducibility.

Saves all analyzer outputs, hashes, and metadata to evidence files.
"""
import datetime
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, Any


def compute_evidence_hash(evidence: Dict[str, Any]) -> str:
    """Compute SHA-256 hash of evidence."""
    canonical = json.dumps(evidence, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def create_evidence_record(
    run_id: str, file_id: str, file_path: Path, analysis_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create evidence record for an analysis run.

    Returns complete evidence structure.
    """
    evidence = {
        "evidence_version": "1.0",
        "evidence_type": "python_analysis",
        "created_at": datetime.datetime.utcnow().isoformat() + "Z",
        # Identity
        "run_id": run_id,
        "file_id": file_id,
        "file_path": str(file_path),
        # Source file hash
        "source_file_hash": hashlib.sha256(file_path.read_bytes()).hexdigest(),
        # Analysis results (all 37 columns + metadata)
        "analysis_results": analysis_results,
        # Toolchain information
        "toolchain": {
            "python_version": analysis_results.get("py_tool_versions", {}).get(
                "python"
            ),
            "toolchain_id": analysis_results.get("py_toolchain_id"),
            "mapp_py_version": analysis_results.get("py_tool_versions", {}).get(
                "mapp_py"
            ),
        },
        # Execution metadata
        "execution": {
            "success": analysis_results.get("py_analysis_success", False),
            "errors": analysis_results.get("errors", []),
            "analyzed_at_utc": analysis_results.get("py_analyzed_at_utc"),
        },
    }

    # Add evidence hash (hash of everything else)
    evidence["evidence_hash"] = compute_evidence_hash(evidence)

    return evidence


def save_evidence(
    evidence: Dict[str, Any], evidence_dir: Path, run_id: str, file_id: str
) -> Path:
    """
    Save evidence to file.

    File naming: evidence_{file_id}_{run_id}.json

    Returns path to saved evidence file.
    """
    evidence_dir.mkdir(parents=True, exist_ok=True)

    filename = f"evidence_{file_id}_{run_id}.json"
    evidence_path = evidence_dir / filename

    evidence_path.write_text(json.dumps(evidence, indent=2))

    return evidence_path


def record_evidence(
    run_id: str,
    file_id: str,
    file_path: Path,
    analysis_results: Dict[str, Any],
    evidence_dir: Path,
) -> dict:
    """
    Record analysis evidence.

    Returns dict with:
    - evidence_path: str
    - evidence_hash: str
    - success: bool
    - error: Optional[str]
    """
    try:
        # Create evidence record
        evidence = create_evidence_record(run_id, file_id, file_path, analysis_results)

        # Save to file
        evidence_path = save_evidence(evidence, evidence_dir, run_id, file_id)

        return {
            "evidence_path": str(evidence_path),
            "evidence_hash": evidence["evidence_hash"],
            "evidence_version": evidence["evidence_version"],
            "success": True,
            "error": None,
        }

    except Exception as e:
        return {
            "evidence_path": None,
            "evidence_hash": None,
            "evidence_version": None,
            "success": False,
            "error": f"Evidence recording failed: {e}",
        }


def verify_evidence(evidence_path: Path) -> dict:
    """
    Verify integrity of evidence file.

    Returns dict with:
    - valid: bool
    - stored_hash: str
    - computed_hash: str
    - match: bool
    """
    try:
        evidence = json.loads(evidence_path.read_text())

        stored_hash = evidence.pop("evidence_hash")
        computed_hash = compute_evidence_hash(evidence)

        return {
            "valid": True,
            "stored_hash": stored_hash,
            "computed_hash": computed_hash,
            "match": stored_hash == computed_hash,
        }

    except Exception as e:
        return {"valid": False, "error": str(e)}


def main():
    """CLI entry point."""
    if len(sys.argv) < 3:
        print("Usage: evidence_recorder.py <mode> <args...>", file=sys.stderr)
        print("", file=sys.stderr)
        print("Modes:", file=sys.stderr)
        print(
            "  record <run_id> <file_id> <file_path> <analysis_results.json> <evidence_dir>",
            file=sys.stderr,
        )
        print("  verify <evidence_path>", file=sys.stderr)
        sys.exit(1)

    mode = sys.argv[1]

    if mode == "record":
        if len(sys.argv) < 7:
            print(
                "Error: record mode requires: run_id, file_id, file_path, analysis_results.json, evidence_dir",
                file=sys.stderr,
            )
            sys.exit(1)

        run_id = sys.argv[2]
        file_id = sys.argv[3]
        file_path = Path(sys.argv[4])
        results_path = Path(sys.argv[5])
        evidence_dir = Path(sys.argv[6])

        if not file_path.exists():
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            sys.exit(1)

        if not results_path.exists():
            print(f"Error: Results file not found: {results_path}", file=sys.stderr)
            sys.exit(1)

        analysis_results = json.loads(results_path.read_text())

        result = record_evidence(
            run_id, file_id, file_path, analysis_results, evidence_dir
        )

        if result["success"]:
            print(f"Evidence saved: {result['evidence_path']}")
            print(f"Evidence hash: {result['evidence_hash']}")
        else:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)

    elif mode == "verify":
        if len(sys.argv) < 3:
            print("Error: verify mode requires: evidence_path", file=sys.stderr)
            sys.exit(1)

        evidence_path = Path(sys.argv[2])

        if not evidence_path.exists():
            print(f"Error: Evidence file not found: {evidence_path}", file=sys.stderr)
            sys.exit(1)

        result = verify_evidence(evidence_path)

        if result.get("valid"):
            print(f"Stored hash:   {result['stored_hash']}")
            print(f"Computed hash: {result['computed_hash']}")
            print(f"Match: {result['match']}")

            if not result["match"]:
                print("ERROR: Evidence integrity check failed!", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"Error: {result.get('error')}", file=sys.stderr)
            sys.exit(1)

    else:
        print(f"Error: Unknown mode: {mode}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
