#!/usr/bin/env python3
"""
Convert Phase Plan YAML files into executable Workstream JSON definitions.
Extracts execution steps and metadata for agent consumption.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

import yaml

REPO_ROOT = Path(__file__).parent
PLANS_DIR = REPO_ROOT / "plans" / "phases"
WORKSTREAMS_DIR = REPO_ROOT / "workstreams"


def load_phase_plan(yaml_path: Path) -> Dict[str, Any]:
    """Load and parse a phase plan YAML file."""
    with yaml_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def convert_to_workstream(phase_plan: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a phase plan to the workstream JSON format expected by agents."""

    phase_id = phase_plan["phase_identity"]

    workstream = {
        "id": phase_id["workstream_id"],
        "doc_id": phase_plan.get("doc_id", ""),
        "phase_id": phase_id["phase_id"],
        "title": phase_id["title"],
        "objective": phase_id["objective"],
        "status": phase_id["status"],
        "tool": phase_plan["environment_and_tools"]["ai_operators"]["primary_agent"],
        "gate": "acceptance_tests",
        "execution_profile": phase_plan["execution_profile"],
        "file_scope": phase_plan["scope_and_modules"]["file_scope"],
        "pre_flight_checks": phase_plan["pre_flight_checks"]["checks"],
        "execution_steps": phase_plan["execution_plan"]["steps"],
        "acceptance_tests": phase_plan["acceptance_tests"]["tests"],
        "expected_artifacts": phase_plan["expected_artifacts"],
        "completion_gate": phase_plan["completion_gate"],
        "tool_profiles_path": "config/tool_profiles.json",
        "circuit_breakers_path": "config/circuit_breakers.yaml",
        "prompt_template": phase_plan["execution_profile"]["prompt_template_id"],
    }

    return workstream


def main() -> None:
    """Convert all phase plans in plans/phases to workstream JSON files."""
    WORKSTREAMS_DIR.mkdir(exist_ok=True, parents=True)

    yaml_files: List[Path] = list(PLANS_DIR.glob("*.yml")) + list(PLANS_DIR.glob("*.yaml"))
    print(f"Found {len(yaml_files)} phase plan files")

    for yaml_path in yaml_files:
        print(f"Converting: {yaml_path.name}")

        phase_plan = load_phase_plan(yaml_path)
        workstream = convert_to_workstream(phase_plan)

        ws_id = workstream["id"]
        output_path = WORKSTREAMS_DIR / f"{ws_id}.json"

        with output_path.open("w", encoding="utf-8") as file:
            json.dump(workstream, file, indent=2)

        print(f"  -> {output_path}")

    print(f"\nConverted {len(yaml_files)} phase plans to workstreams")


if __name__ == "__main__":
    main()
