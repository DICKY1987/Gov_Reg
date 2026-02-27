#!/usr/bin/env python3
"""
Registry Integration Orchestrator - Main Pipeline Script
Coordinates all analyzers and writes results to registry.

This is the main entry point that orchestrates all 18 analyzer scripts.
"""
import datetime
import hashlib
import json
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional


# Analysis run metadata
class AnalysisRun:
    """Tracks analysis run context."""

    def __init__(self, file_id: str, file_path: Path, repo_root: Path):
        self.run_id = str(uuid.uuid4())
        self.file_id = file_id
        self.file_path = file_path
        self.repo_root = repo_root
        self.started_at = datetime.datetime.utcnow()
        self.results = {}
        self.errors = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "py_analysis_run_id": self.run_id,
            "file_id": self.file_id,
            "file_path": str(self.file_path),
            "repo_root": str(self.repo_root),
            "started_at": self.started_at.isoformat(),
            "py_analyzed_at_utc": self.started_at.isoformat() + "Z",
            "results": self.results,
            "errors": self.errors,
        }


def get_python_version() -> str:
    """Get Python version string."""
    v = sys.version_info
    return f"{v.major}.{v.minor}.{v.micro}"


def get_toolchain_id() -> str:
    """Generate toolchain ID from Python version and key dependencies."""
    version_str = get_python_version()
    # Include stdlib hash for determinism
    hash_input = f"python-{version_str}"
    return hashlib.sha256(hash_input.encode()).hexdigest()[:16]


def run_analyzer(
    script_name: str, args: List[str], timeout: int = 60
) -> Dict[str, Any]:
    """
    Run an analyzer script and return results.

    Returns dict with 'success', 'result', 'error'.
    """
    script_path = Path(__file__).parent / script_name

    if not script_path.exists():
        return {
            "success": False,
            "result": None,
            "error": f"Script not found: {script_name}",
        }

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if result.returncode == 0:
            # Try to parse JSON output
            try:
                output = json.loads(result.stdout)
                return {"success": True, "result": output, "error": None}
            except json.JSONDecodeError:
                # Return raw output
                return {
                    "success": True,
                    "result": {"stdout": result.stdout},
                    "error": None,
                }
        else:
            return {
                "success": False,
                "result": None,
                "error": result.stderr or result.stdout,
            }

    except subprocess.TimeoutExpired:
        return {"success": False, "result": None, "error": f"Timeout after {timeout}s"}
    except Exception as e:
        return {"success": False, "result": None, "error": str(e)}


def run_phase_a_core(run: AnalysisRun) -> bool:
    """
    Run Phase A core analyzers (required).

    Returns True if all succeed, False otherwise.
    """
    print(f"[Phase A] Running core analyzers...")

    # 1. Text normalizer
    result = run_analyzer("DOC-SCRIPT-1277__text_normalizer.py", [str(run.file_path)])
    if result["success"]:
        run.results.update(result["result"])
    else:
        run.errors.append(f"text_normalizer: {result['error']}")
        return False

    # 2. Component extractor
    result = run_analyzer(
        "DOC-SCRIPT-1278__component_extractor.py", [str(run.file_path)]
    )
    if result["success"]:
        run.results.update(result["result"])
    else:
        run.errors.append(f"component_extractor: {result['error']}")
        return False

    # 3. Component ID generator
    # Save components to temp file
    temp_components = Path(f"/tmp/components_{run.run_id}.json")
    temp_components.write_text(json.dumps(run.results.get("py_components_list", [])))

    result = run_analyzer(
        "DOC-SCRIPT-1279__component_id_generator.py",
        [run.file_id, str(temp_components)],
    )
    if result["success"]:
        run.results.update(result["result"])
    else:
        run.errors.append(f"component_id_generator: {result['error']}")

    temp_components.unlink(missing_ok=True)

    # 4. Dependency analyzer
    result = run_analyzer(
        "DOC-SCRIPT-1280__dependency_analyzer.py", [str(run.file_path)]
    )
    if result["success"]:
        run.results.update(result["result"])
    else:
        run.errors.append(f"dependency_analyzer: {result['error']}")
        return False

    # 5. I/O surface analyzer
    result = run_analyzer(
        "DOC-SCRIPT-1281__io_surface_analyzer.py", [str(run.file_path)]
    )
    if result["success"]:
        run.results.update(result["result"])
    else:
        run.errors.append(f"io_surface_analyzer: {result['error']}")
        return False

    # 6. Deliverable analyzer
    result = run_analyzer(
        "DOC-SCRIPT-1282__deliverable_analyzer.py", [str(run.file_path)]
    )
    if result["success"]:
        run.results.update(result["result"])
    else:
        run.errors.append(f"deliverable_analyzer: {result['error']}")

    return True


def run_phase_b_similarity(run: AnalysisRun, candidate_files: List[Path]) -> bool:
    """
    Run Phase B similarity analyzers (optional).

    Returns True if successful.
    """
    if not candidate_files:
        print("[Phase B] No candidate files for similarity, skipping")
        return True

    print(
        f"[Phase B] Running similarity analyzers with {len(candidate_files)} candidates..."
    )

    # Structural similarity
    result = run_analyzer(
        "DOC-SCRIPT-1283__structural_similarity.py",
        [str(run.file_path)] + [str(f) for f in candidate_files],
    )
    if result["success"]:
        run.results.update(result["result"])
    else:
        run.errors.append(f"structural_similarity: {result['error']}")

    # Semantic similarity
    result = run_analyzer(
        "DOC-SCRIPT-1284__semantic_similarity.py",
        [str(run.file_path)] + [str(f) for f in candidate_files],
    )
    if result["success"]:
        run.results.update(result["result"])
    else:
        run.errors.append(f"semantic_similarity: {result['error']}")

    return True


def run_phase_c_quality(run: AnalysisRun) -> bool:
    """
    Run Phase C quality analyzers (optional).

    Returns True if successful.
    """
    print(f"[Phase C] Running quality analyzers...")

    # Test runner (only if test file)
    if run.results.get("py_deliverable_kind") == "TEST":
        result = run_analyzer(
            "DOC-SCRIPT-1286__test_runner.py", [str(run.file_path), str(run.repo_root)]
        )
        if result["success"]:
            run.results.update(result["result"])

    # Linter runner
    result = run_analyzer("DOC-SCRIPT-1287__linter_runner.py", [str(run.file_path)])
    if result["success"]:
        run.results.update(result["result"])

    # Complexity analyzer
    result = run_analyzer(
        "DOC-SCRIPT-1288__complexity_analyzer.py", [str(run.file_path)]
    )
    if result["success"]:
        run.results.update(result["result"])

    # Quality scorer (needs all metrics)
    temp_metrics = Path(f"/tmp/metrics_{run.run_id}.json")
    temp_metrics.write_text(json.dumps(run.results))

    result = run_analyzer("DOC-SCRIPT-1289__quality_scorer.py", [str(temp_metrics)])
    if result["success"]:
        run.results.update(result["result"])

    temp_metrics.unlink(missing_ok=True)

    return True


def analyze_file(
    file_id: str,
    file_path: Path,
    repo_root: Path,
    candidate_files: Optional[List[Path]] = None,
) -> dict:
    """
    Run complete analysis pipeline on a Python file.

    Args:
        file_id: 20-digit file identifier (string)
        file_path: Path to Python file
        repo_root: Repository root path
        candidate_files: Optional list of candidate files for similarity

    Returns analysis results dictionary.
    """
    run = AnalysisRun(file_id, file_path, repo_root)

    # Add metadata
    run.results["py_toolchain_id"] = get_toolchain_id()
    run.results["py_tool_versions"] = {
        "python": get_python_version(),
        "mapp_py": "1.0.0",
    }

    # Phase A: Core analysis (required)
    phase_a_success = run_phase_a_core(run)

    if not phase_a_success:
        run.results["py_analysis_success"] = False
        return run.to_dict()

    # Phase B: Similarity (optional)
    if candidate_files:
        run_phase_b_similarity(run, candidate_files)

    # Phase C: Quality (optional)
    run_phase_c_quality(run)

    # Mark analysis complete
    run.results["py_analysis_success"] = True

    return run.to_dict()


def main():
    """CLI entry point."""
    if len(sys.argv) < 4:
        print(
            "Usage: registry_integration_orchestrator.py <file_id> <file_path> <repo_root> [candidate_files...]",
            file=sys.stderr,
        )
        sys.exit(1)

    file_id = sys.argv[1]
    file_path = Path(sys.argv[2])
    repo_root = Path(sys.argv[3])
    candidate_files = [Path(f) for f in sys.argv[4:]] if len(sys.argv) > 4 else None

    # Validate file_id
    if not isinstance(file_id, str) or len(file_id) != 20 or not file_id.isdigit():
        print(
            f"Error: file_id must be 20-digit string, got: {file_id}", file=sys.stderr
        )
        sys.exit(1)

    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    # Run analysis
    result = analyze_file(file_id, file_path, repo_root, candidate_files)

    # Output results
    print(json.dumps(result, indent=2))

    # Exit with error if analysis failed
    if not result["results"].get("py_analysis_success"):
        sys.exit(1)


if __name__ == "__main__":
    main()
