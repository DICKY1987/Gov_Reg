"""
Validate Everything - ACMS Artifact Validation Script

Validates all ACMS artifacts (gap registries, plans, configs, run statuses)
against their JSON schemas.

Usage:
    python validate_everything.py [--run-id RUN_ID] [--verbose]

Examples:
    # Validate latest run
    python validate_everything.py
    
    # Validate specific run
    python validate_everything.py --run-id 20251207001431_2E134BDB6F61
    
    # Verbose output
    python validate_everything.py --verbose
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from src.acms.schema_utils import SchemaValidator
from src.acms.guardrails import PatternGuardrails, validate_pattern_spec


class ArtifactValidator:
    """Validates ACMS artifacts"""

    def __init__(self, repo_root: Path, verbose: bool = False):
        self.repo_root = repo_root
        self.verbose = verbose
        self.validator = SchemaValidator()
        self.results = []

        # Load pattern guardrails if PATTERN_INDEX exists
        pattern_index = repo_root / "PATTERN_INDEX.yaml"
        self.pattern_guardrails = None
        if pattern_index.exists():
            try:
                self.pattern_guardrails = PatternGuardrails(pattern_index)
            except Exception as e:
                print(f"⚠️  Failed to load pattern guardrails: {e}")

    def validate_run(self, run_id: str) -> Dict[str, any]:
        """Validate all artifacts for a specific run"""
        run_dir = self.repo_root / ".acms_runs" / run_id

        if not run_dir.exists():
            return {
                "run_id": run_id,
                "success": False,
                "error": f"Run directory not found: {run_dir}",
            }

        results = {
            "run_id": run_id,
            "run_dir": str(run_dir),
            "artifacts": [],
            "success": True,
            "total": 0,
            "passed": 0,
            "failed": 0,
        }

        # Validate run_status.json
        self._validate_artifact(
            run_dir / "run_status.json", "run_status", "Run Status", results
        )

        # Validate gap_registry.json
        self._validate_artifact(
            run_dir / "gap_registry.json",
            "gap_record",  # Individual gaps
            "Gap Registry",
            results,
            validate_each_gap=True,
        )

        # Validate workstreams.json
        workstreams_path = run_dir / "workstreams.json"
        if workstreams_path.exists():
            self._validate_artifact(
                workstreams_path,
                "workstream_definition",
                "Workstreams",
                results,
                validate_each_item=True,
            )

        # Validate execution plan
        plan_path = run_dir / "mini_pipe_execution_plan.json"
        if plan_path.exists():
            self._validate_artifact(
                plan_path, "minipipe_execution_plan", "Execution Plan", results
            )

        # Validate PATTERN_INDEX.yaml if it exists
        pattern_index_path = run_dir.parent.parent / "PATTERN_INDEX.yaml"
        if pattern_index_path.exists():
            self._validate_artifact(
                pattern_index_path,
                None,  # No schema validation for now
                "Pattern Index",
                results,
                custom_validator=self._validate_pattern_index,
            )

        # Validate pattern specs
        patterns_dir = run_dir.parent.parent / "patterns"
        if patterns_dir.exists():
            self._validate_pattern_specs(patterns_dir, results)

        results["success"] = results["failed"] == 0
        return results

    def _validate_pattern_index(self, path: Path) -> Tuple[bool, Optional[str]]:
        """Custom validator for PATTERN_INDEX.yaml"""
        if not self.pattern_guardrails:
            return True, "Pattern guardrails not loaded"

        try:
            # Check that all referenced patterns have specs
            import yaml

            with open(path, "r", encoding="utf-8") as f:
                index = yaml.safe_load(f)

            patterns = index.get("patterns", {})
            missing_specs = []

            for pattern_id, pattern_def in patterns.items():
                spec_path = pattern_def.get("spec_path")
                if spec_path:
                    full_spec_path = path.parent / spec_path
                    if not full_spec_path.exists():
                        missing_specs.append(f"{pattern_id}: {spec_path}")

            if missing_specs:
                return False, f"Missing pattern specs: {', '.join(missing_specs)}"

            return True, None

        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def _validate_pattern_specs(self, patterns_dir: Path, results: Dict) -> None:
        """Validate all pattern spec files"""
        for spec_file in patterns_dir.glob("*.spec.yaml"):
            results["total"] += 1

            is_valid, error = validate_pattern_spec(spec_file)

            if is_valid:
                results["artifacts"].append(
                    {
                        "name": f"Pattern Spec: {spec_file.stem}",
                        "path": str(spec_file),
                        "status": "valid",
                    }
                )
                results["passed"] += 1
            else:
                results["artifacts"].append(
                    {
                        "name": f"Pattern Spec: {spec_file.stem}",
                        "path": str(spec_file),
                        "status": "invalid",
                        "error": error,
                    }
                )
                results["failed"] += 1
                results["success"] = False

    def _validate_artifact(
        self,
        path: Path,
        schema_name: str,
        artifact_name: str,
        results: Dict,
        validate_each_gap: bool = False,
        validate_each_item: bool = False,
        custom_validator=None,
    ) -> None:
        """Validate a single artifact"""
        results["total"] += 1

        if not path.exists():
            results["artifacts"].append(
                {
                    "name": artifact_name,
                    "path": str(path),
                    "status": "missing",
                    "error": "File not found",
                }
            )
            results["failed"] += 1
            results["success"] = False
            return

        try:
            # Use custom validator if provided
            if custom_validator:
                is_valid, error = custom_validator(path)
                if is_valid:
                    results["artifacts"].append(
                        {"name": artifact_name, "path": str(path), "status": "valid"}
                    )
                    results["passed"] += 1
                else:
                    results["artifacts"].append(
                        {
                            "name": artifact_name,
                            "path": str(path),
                            "status": "invalid",
                            "error": error,
                        }
                    )
                    results["failed"] += 1
                    results["success"] = False
                return

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Special handling for gap registry (validate each gap)
            if validate_each_gap and isinstance(data, dict) and "gaps" in data:
                gaps = data.get("gaps", {})
                total_gaps = len(gaps)
                failed_gaps = []

                for gap_id, gap_data in gaps.items():
                    is_valid, error = self.validator.validate(gap_data, schema_name)
                    if not is_valid:
                        failed_gaps.append(f"{gap_id}: {error}")

                if failed_gaps:
                    results["artifacts"].append(
                        {
                            "name": artifact_name,
                            "path": str(path),
                            "status": "invalid",
                            "error": f"{len(failed_gaps)}/{total_gaps} gaps invalid",
                            "details": failed_gaps[:5],  # First 5 errors
                        }
                    )
                    results["failed"] += 1
                    results["success"] = False
                else:
                    results["artifacts"].append(
                        {
                            "name": artifact_name,
                            "path": str(path),
                            "status": "valid",
                            "info": f"{total_gaps} gaps validated",
                        }
                    )
                    results["passed"] += 1
                return

            # Special handling for arrays of items
            if validate_each_item and isinstance(data, list):
                total_items = len(data)
                failed_items = []

                for i, item in enumerate(data):
                    is_valid, error = self.validator.validate(item, schema_name)
                    if not is_valid:
                        failed_items.append(f"Item {i}: {error}")

                if failed_items:
                    results["artifacts"].append(
                        {
                            "name": artifact_name,
                            "path": str(path),
                            "status": "invalid",
                            "error": f"{len(failed_items)}/{total_items} items invalid",
                            "details": failed_items[:5],
                        }
                    )
                    results["failed"] += 1
                    results["success"] = False
                else:
                    results["artifacts"].append(
                        {
                            "name": artifact_name,
                            "path": str(path),
                            "status": "valid",
                            "info": f"{total_items} items validated",
                        }
                    )
                    results["passed"] += 1
                return

            # Standard validation
            is_valid, error = self.validator.validate(data, schema_name)

            if is_valid:
                results["artifacts"].append(
                    {"name": artifact_name, "path": str(path), "status": "valid"}
                )
                results["passed"] += 1
            else:
                results["artifacts"].append(
                    {
                        "name": artifact_name,
                        "path": str(path),
                        "status": "invalid",
                        "error": error,
                    }
                )
                results["failed"] += 1
                results["success"] = False

        except Exception as e:
            results["artifacts"].append(
                {
                    "name": artifact_name,
                    "path": str(path),
                    "status": "error",
                    "error": str(e),
                }
            )
            results["failed"] += 1
            results["success"] = False

    def print_results(self, results: Dict) -> None:
        """Print validation results"""
        print(f"\n{'='*70}")
        print(f"VALIDATION RESULTS - Run {results['run_id']}")
        print(f"{'='*70}\n")

        for artifact in results["artifacts"]:
            status_icon = {
                "valid": "✓",
                "invalid": "✗",
                "missing": "⚠",
                "error": "✗",
            }.get(artifact["status"], "?")

            status_color = {
                "valid": "green",
                "invalid": "red",
                "missing": "yellow",
                "error": "red",
            }.get(artifact["status"], "white")

            print(f"  {status_icon} {artifact['name']}")

            if self.verbose or artifact["status"] != "valid":
                print(f"     Path: {artifact['path']}")

            if "error" in artifact:
                print(f"     Error: {artifact['error']}")

            if "info" in artifact:
                print(f"     Info: {artifact['info']}")

            if self.verbose and "details" in artifact:
                print(f"     Details:")
                for detail in artifact["details"]:
                    print(f"       - {detail}")

            print()

        print(f"{'='*70}")
        print(
            f"Total: {results['total']} | Passed: {results['passed']} | Failed: {results['failed']}"
        )
        print(
            f"Status: {'✓ ALL VALID' if results['success'] else '✗ VALIDATION FAILED'}"
        )
        print(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(description="Validate ACMS artifacts")
    parser.add_argument(
        "--run-id", help="Specific run ID to validate (default: latest)"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root (default: current directory)",
    )

    args = parser.parse_args()

    # Find run to validate
    runs_dir = args.repo_root / ".acms_runs"

    if not runs_dir.exists():
        print(f"✗ No runs found in {runs_dir}")
        sys.exit(1)

    if args.run_id:
        run_id = args.run_id
    else:
        # Get latest run
        runs = sorted(runs_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
        if not runs:
            print(f"✗ No runs found in {runs_dir}")
            sys.exit(1)
        run_id = runs[0].name
        print(f"Using latest run: {run_id}\n")

    # Validate
    validator = ArtifactValidator(args.repo_root, args.verbose)
    results = validator.validate_run(run_id)
    validator.print_results(results)

    # Exit with appropriate code
    sys.exit(0 if results["success"] else 1)


if __name__ == "__main__":
    main()
