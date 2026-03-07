"""
ACMS / MINI_PIPE end-to-end test harness.

CLI:
  python acms_test_harness.py plan --repo-root <path>
  python acms_test_harness.py e2e  --repo-root <path> [--mode full] [--spec-path config/process_steps.json]
"""

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple


DEFAULT_SPEC_PATH = Path("config/process_steps.json")


@dataclass
class StepResult:
    step_id: str
    passed: bool
    detail: str


def _add_repo_to_sys_path(repo_root: Path) -> None:
    """Ensure repo_root and repo_root/src are on sys.path for imports."""
    for path in (repo_root, repo_root / "src"):
        path_str = str(path.resolve())
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


def load_process_spec(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_process_spec(spec: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    for key in ("version", "pipeline_id", "steps"):
        if key not in spec:
            errors.append(f"missing top-level key '{key}'")
    steps = spec.get("steps")
    if not isinstance(steps, list) or not steps:
        errors.append("steps must be a non-empty list")
        return errors

    required_step_fields = {
        "step_id",
        "phase",
        "owner_module",
        "description",
        "artifacts_in",
        "artifacts_out",
        "postconditions",
        "check_type",
    }
    allowed_conditions = {
        "dir_exists",
        "file_exists",
        "any_path_exists",
        "json_keys",
        "json_array_min_length",
        "state_has_fields",
        "state_field_equals",
    }

    seen_ids = set()
    for idx, step in enumerate(steps):
        if not isinstance(step, dict):
            errors.append(f"step at index {idx} is not an object")
            continue
        step_id = step.get("step_id")
        if not step_id:
            errors.append(f"step at index {idx} missing 'step_id'")
        elif step_id in seen_ids:
            errors.append(f"duplicate step_id '{step_id}'")
        else:
            seen_ids.add(step_id)

        for field in required_step_fields:
            if field not in step:
                errors.append(f"{step_id or idx}: missing '{field}'")

        postconditions = step.get("postconditions", [])
        if not isinstance(postconditions, list):
            errors.append(f"{step_id or idx}: postconditions must be a list")
            continue

        for cond in postconditions:
            if not isinstance(cond, dict):
                errors.append(f"{step_id}: postcondition is not an object")
                continue
            cond_type = cond.get("type")
            if cond_type not in allowed_conditions:
                errors.append(f"{step_id}: unsupported condition type '{cond_type}'")
                continue
            if cond_type in {
                "dir_exists",
                "file_exists",
                "json_keys",
                "json_array_min_length",
            }:
                if "path" not in cond:
                    errors.append(f"{step_id}: condition '{cond_type}' missing 'path'")
            if cond_type == "any_path_exists" and "paths" not in cond:
                errors.append(f"{step_id}: condition 'any_path_exists' missing 'paths'")
            if cond_type == "json_keys" and "keys" not in cond:
                errors.append(f"{step_id}: condition 'json_keys' missing 'keys'")
            if cond_type == "json_array_min_length":
                if "key" not in cond:
                    errors.append(
                        f"{step_id}: condition 'json_array_min_length' missing 'key'"
                    )
    return errors


def run_acms_pipeline(repo_root: Path, mode: str) -> Tuple[str, Path, Dict[str, Any]]:
    """Run the ACMS controller once and return (run_id, run_dir, state)."""
    _add_repo_to_sys_path(repo_root)
    from src.acms.controller import ACMSController  # type: ignore

    controller = ACMSController(repo_root=repo_root)
    state = controller.run_full_cycle(mode=mode)
    return controller.run_id, controller.run_dir, state


def _resolve_path(template: str, repo_root: Path, run_dir: Path, run_id: str) -> Path:
    replacements = {
        "<run_id>": run_id,
        "<run_dir>": str(run_dir),
        "<repo_root>": str(repo_root),
    }
    path_str = template
    for placeholder, value in replacements.items():
        path_str = path_str.replace(placeholder, value)
    path = Path(path_str)
    if not path.is_absolute():
        path = repo_root / path_str
    return path


def _load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_condition(
    condition: Dict[str, Any],
    repo_root: Path,
    run_dir: Path,
    run_id: str,
    state: Dict[str, Any],
) -> Tuple[bool, str]:
    cond_type = condition.get("type")
    optional = bool(condition.get("optional"))
    try:
        if cond_type == "dir_exists":
            path = _resolve_path(condition["path"], repo_root, run_dir, run_id)
            ok = path.is_dir()
            msg = f"dir_exists:{path}"
        elif cond_type == "file_exists":
            path = _resolve_path(condition["path"], repo_root, run_dir, run_id)
            ok = path.is_file()
            msg = f"file_exists:{path}"
        elif cond_type == "any_path_exists":
            paths = [
                _resolve_path(p, repo_root, run_dir, run_id)
                for p in condition.get("paths", [])
            ]
            ok = any(p.exists() for p in paths)
            msg = "any_path_exists:" + ",".join(str(p) for p in paths)
        elif cond_type == "json_keys":
            path = _resolve_path(condition["path"], repo_root, run_dir, run_id)
            data = _load_json(path)
            keys = condition.get("keys", [])
            ok = all(k in data for k in keys)
            msg = f"json_keys:{path} has {keys}"
        elif cond_type == "json_array_min_length":
            path = _resolve_path(condition["path"], repo_root, run_dir, run_id)
            data = _load_json(path)
            key = condition.get("key")
            arr = data.get(key, [])
            ok = isinstance(arr, list) and len(arr) >= int(condition.get("min", 0))
            msg = f"json_array_min_length:{path}.{key}>={condition.get('min', 0)}"
        elif cond_type == "state_has_fields":
            keys = condition.get("fields", [])
            ok = all(k in state for k in keys)
            msg = f"state_has_fields:{keys}"
        elif cond_type == "state_field_equals":
            field = condition.get("field")
            expected = condition.get("expected")
            ok = state.get(field) == expected
            msg = f"state_field_equals:{field}=={expected}"
        else:
            ok = False
            msg = f"unsupported condition type '{cond_type}'"
    except Exception as exc:  # pragma: no cover - defensive
        ok = False
        msg = f"{cond_type} error: {exc}"

    if not ok and optional:
        return True, f"optional:{msg}"
    return ok, msg


def evaluate_step(
    step: Dict[str, Any],
    repo_root: Path,
    run_dir: Path,
    run_id: str,
    state: Dict[str, Any],
) -> StepResult:
    failures: List[str] = []
    for condition in step.get("postconditions", []):
        passed, detail = check_condition(condition, repo_root, run_dir, run_id, state)
        if not passed:
            failures.append(detail)
    if failures:
        return StepResult(
            step_id=step.get("step_id", "?"), passed=False, detail="; ".join(failures)
        )
    return StepResult(step_id=step.get("step_id", "?"), passed=True, detail="ok")


def evaluate_spec(
    spec: Dict[str, Any],
    repo_root: Path,
    run_dir: Path,
    run_id: str,
    state: Dict[str, Any],
) -> List[StepResult]:
    results: List[StepResult] = []
    for step in spec.get("steps", []):
        results.append(evaluate_step(step, repo_root, run_dir, run_id, state))
    return results


def command_plan(args: argparse.Namespace) -> int:
    repo_root = (
        Path(args.repo_root).resolve() if args.repo_root else Path.cwd().resolve()
    )
    spec_path = Path(args.spec_path)
    if not spec_path.is_absolute():
        spec_path = repo_root / spec_path
    if not spec_path.exists():
        print(f"Spec not found: {spec_path}")
        return 1
    spec = load_process_spec(spec_path)
    errors = validate_process_spec(spec)
    if errors:
        print("Spec validation failed:")
        for err in errors:
            print(f"- {err}")
        return 1
    print(f"Spec OK ({len(spec.get('steps', []))} steps)")
    return 0


def command_e2e(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    spec_path = Path(args.spec_path)
    if not spec_path.is_absolute():
        spec_path = repo_root / spec_path
    if not spec_path.exists():
        print(f"Spec not found: {spec_path}")
        return 1
    spec = load_process_spec(spec_path)
    errors = validate_process_spec(spec)
    if errors:
        print("Spec validation failed:")
        for err in errors:
            print(f"- {err}")
        return 1

    run_id, run_dir, state = run_acms_pipeline(repo_root, args.mode)
    print(f"Run ID: {run_id}")
    print(f"Run dir: {run_dir}")
    print(f"Pipeline status: {state.get('final_status', 'unknown')}")

    results = evaluate_spec(spec, repo_root, run_dir, run_id, state)
    failures = [r for r in results if not r.passed]
    for res in results:
        prefix = "PASS" if res.passed else "FAIL"
        print(f"{prefix} {res.step_id}: {res.detail}")

    return 0 if not failures else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ACMS E2E test harness")
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan_parser = subparsers.add_parser("plan", help="Validate process-steps spec")
    plan_parser.add_argument(
        "--repo-root", type=Path, default=None, help="Repository root (defaults to CWD)"
    )
    plan_parser.add_argument(
        "--spec-path",
        type=Path,
        default=DEFAULT_SPEC_PATH,
        help="Path to process steps spec",
    )

    e2e_parser = subparsers.add_parser(
        "e2e", help="Run ACMS pipeline and check postconditions"
    )
    e2e_parser.add_argument(
        "--repo-root", type=Path, required=True, help="Repository root"
    )
    e2e_parser.add_argument(
        "--mode",
        choices=["full", "analyze_only", "plan_only", "execute_only"],
        default="full",
    )
    e2e_parser.add_argument(
        "--spec-path",
        type=Path,
        default=DEFAULT_SPEC_PATH,
        help="Path to process steps spec",
    )
    e2e_parser.add_argument(
        "--scenario", default="baseline", help="Scenario name (reserved)"
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "plan":
        sys.exit(command_plan(args))
    elif args.command == "e2e":
        sys.exit(command_e2e(args))


if __name__ == "__main__":
    main()
