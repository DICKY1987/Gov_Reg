# DOC_LINK: DOC-CORE-CONVERTERS-CCIS-TO-PHASE-PLAN-388
"""
CCIS to Phase Plan Converter

Bridges pipeline CCIS to MASTER_SPLINTER Phase Plan format.
Implements Task 1.2 from Option 3 Implementation Plan.
"""
DOC_ID = "DOC-CORE-CONVERTERS-CCIS-TO-PHASE-PLAN-388"

from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import yaml

from src.schemas.ccis import CCIS


class CCISToPhaseplanConverter:
    """Convert CCIS to Phase Plan YAML format."""

    def __init__(
        self,
        default_tool: str = "github_copilot_cli",
        default_prompt_template: str = "EXECUTION_PROMPT_TEMPLATE_V2_DAG_MULTI_WORKSTREAM",
    ):
        self.default_tool = default_tool
        self.default_prompt_template = default_prompt_template

    def convert(self, ccis: CCIS) -> Dict[str, Any]:
        """
        Main conversion method.

        Args:
            ccis: Validated CCIS object

        Returns:
            Phase Plan dictionary ready for YAML serialization
        """
        phase_plan = {
            "file_id": f"PH-{ccis.ccis_id}",
            "template_version": "3",
            "phase_identity": self._build_phase_identity(ccis),
            "dag_and_dependencies": self._build_dag_info(ccis),
            "scope_and_modules": self._build_scope(ccis),
            "environment_and_tools": self._build_tools(ccis),
            "execution_profile": self._build_execution_profile(ccis),
            "pre_flight_checks": self._build_preflight_checks(ccis),
            "execution_plan": self._build_execution_plan(ccis),
            "fix_loop_and_circuit_breakers": self._build_circuit_breakers(ccis),
            "expected_artifacts": self._build_expected_artifacts(ccis),
            "acceptance_tests": self._build_acceptance_tests(ccis),
            "completion_gate": self._build_completion_gate(ccis),
            "observability_and_metrics": self._build_observability(ccis),
        }

        return phase_plan

    def _build_phase_identity(self, ccis: CCIS) -> Dict[str, Any]:
        """Build phase_identity section from CCIS."""
        # Extract numeric ID from CCIS ID (e.g., CCIS-2025-0001 -> 0001)
        ccis_num = ccis.ccis_id.split("-")[-1]

        return {
            "phase_id": f"PH-{ccis_num}",
            "workstream_id": f"WS-{ccis_num}",
            "title": ccis.summary.title,
            "summary": ccis.intent.problem_statement,
            "objective": ccis.summary.description,
            "phase_type": self._infer_phase_type(ccis.summary.change_kind),
            "status": "pending",
            "estimate_hours": None,  # Cannot infer from CCIS
            "gh_item_id": None,
            "tags": ccis.summary.change_kind,
            "priority": self._map_severity_to_priority(ccis.summary.severity),
            "rationale": ccis.intent.rationale,
        }

    def _build_dag_info(self, ccis: CCIS) -> Dict[str, Any]:
        """Build DAG and dependencies section."""
        return {
            "workstream_bundle_id": f"bundle-{ccis.ccis_id}",
            "depends_on": [],  # CCIS doesn't specify dependencies
            "may_run_parallel_with": [],
            "parallel_group": None,
            "is_critical_path": ccis.summary.blocking,
        }

    def _build_scope(self, ccis: CCIS) -> Dict[str, Any]:
        """Build scope_and_modules section."""
        modules = []
        for idx, mod_name in enumerate(ccis.scope.modules, 1):
            modules.append(
                {
                    "id": mod_name,
                    "description": f"Module generated from CCIS: {mod_name}",
                    "directory": mod_name,
                    "in_scope": True,
                }
            )

        # Categorize paths by intent (simple heuristic)
        modify_paths = []
        create_paths = []
        read_only_paths = []

        for path in ccis.scope.paths:
            # Simple categorization - can be enhanced
            if "test" in path.lower():
                create_paths.append(path)
            elif "*" in path:
                modify_paths.append(path)
            else:
                modify_paths.append(path)

        # Add context files as read-only
        if hasattr(ccis, "ai_guidance") and ccis.ai_guidance:
            read_only_paths.extend(getattr(ccis.ai_guidance, "context_files", []))

        return {
            "repo_root": ccis.scope.repo_root,
            "modules": modules,
            "file_scope": {
                "read_only": read_only_paths,
                "modify": modify_paths,
                "create": create_paths,
                "forbidden_paths": self._extract_forbidden_paths(ccis),
            },
            "worktree_strategy": "single",
        }

    def _build_tools(self, ccis: CCIS) -> Dict[str, Any]:
        """Build environment_and_tools section."""
        # Extract tool preferences from project_overrides if present
        primary_tool = self.default_tool
        secondary_tool = None

        if hasattr(ccis, "project_overrides") and ccis.project_overrides:
            tool_prefs = getattr(
                ccis.project_overrides, "execution_tool_preference", []
            )
            if tool_prefs:
                primary_tool = tool_prefs[0]
                if len(tool_prefs) > 1:
                    secondary_tool = tool_prefs[1]

        return {
            "target_os": "windows",
            "default_shell": "powershell",
            "primary_language": "python",
            "python": {
                "version": "3.12",
                "virtualenv": None,
            },
            "required_services": [],
            "config_files": [
                "orchestrator/config/ai_tool_profiles.json",
                "orchestrator/config/circuit_breaker_rules.yaml",
            ],
            "ai_operators": {
                "primary_agent": primary_tool,
                "secondary_agent": secondary_tool,
            },
            "tool_profiles": "orchestrator/config/ai_tool_profiles.json",
        }

    def _build_execution_profile(self, ccis: CCIS) -> Dict[str, Any]:
        """Build execution_profile section."""
        return {
            "prompt_template_id": f"prompts/{self.default_prompt_template}.md",
            "concurrency": 1,
            "retry_attempts": 2 if ccis.summary.severity in ["high", "critical"] else 1,
            "timeout_seconds": None,
            "no_stop_mode": True,
        }

    def _build_preflight_checks(self, ccis: CCIS) -> Dict[str, Any]:
        """Build pre_flight_checks section."""
        checks = [
            {
                "id": "verify-repo-root",
                "description": "Verify repository root exists",
                "command": f"Test-Path '{ccis.scope.repo_root}'",
                "success_pattern": "True",
                "on_fail": "abort",
            }
        ]

        # Add module checks
        for mod in ccis.scope.modules:
            checks.append(
                {
                    "id": f"verify-module-{mod}",
                    "description": f"Verify module {mod} exists",
                    "command": f"Test-Path '{ccis.scope.repo_root}/{mod}'",
                    "success_pattern": "True",
                    "on_fail": "warn",
                }
            )

        return {"checks": checks}

    def _build_execution_plan(self, ccis: CCIS) -> Dict[str, Any]:
        """Build execution_plan.steps from acceptance criteria."""
        steps = []

        for idx, criterion in enumerate(ccis.acceptance.definition_of_done, 1):
            step = {
                "id": f"step-{idx:02d}",
                "name": criterion[:60],  # Truncate for step name
                "operation_kind": self._infer_operation_kind(criterion),
                "description": criterion,
                "inputs": [],
                "outputs": [],
                "expected_artifacts": [],
                "requires_human_confirmation": False,
            }
            steps.append(step)

        return {"steps": steps}

    def _build_circuit_breakers(self, ccis: CCIS) -> Dict[str, Any]:
        """Build fix_loop_and_circuit_breakers section."""
        return {
            "circuit_breakers": [
                "cb-oscillation-detector",
                "cb-max-attempts",
                "cb-timeout",
                "cb-scope-violation",
            ],
            "defaults": {
                "max_attempts": 3,
                "oscillation_window": 3,
                "oscillation_threshold": 2,
            },
            "patterns": [],
        }

    def _build_expected_artifacts(self, ccis: CCIS) -> List[Dict[str, Any]]:
        """Build expected_artifacts list."""
        artifacts = []

        # Infer artifacts from acceptance criteria
        for idx, criterion in enumerate(ccis.acceptance.definition_of_done, 1):
            if "file" in criterion.lower() or "create" in criterion.lower():
                artifacts.append(
                    {
                        "id": f"artifact-{idx:02d}",
                        "description": criterion,
                        "path": None,  # Cannot infer specific path
                        "artifact_type": "code",
                    }
                )

        return artifacts

    def _build_acceptance_tests(self, ccis: CCIS) -> Dict[str, Any]:
        """Build acceptance_tests from suggested_tests."""
        tests = []

        for idx, test_desc in enumerate(ccis.acceptance.suggested_tests, 1):
            test = {
                "id": f"test-{idx:02d}",
                "description": test_desc,
                "test_type": "functional",
                "command": f"# TODO: Implement test for: {test_desc}",
                "expected_behavior": "Test passes",
            }
            tests.append(test)

        # Add non-functional requirements as tests
        for idx, nf_req in enumerate(ccis.acceptance.nonfunctional, 1):
            tests.append(
                {
                    "id": f"nfr-{idx:02d}",
                    "description": nf_req,
                    "test_type": "non_functional",
                    "command": f"# TODO: Validate: {nf_req}",
                    "expected_behavior": "Requirement met",
                }
            )

        return {"tests": tests}

    def _build_completion_gate(self, ccis: CCIS) -> Dict[str, Any]:
        """Build completion_gate section."""
        return {
            "rules": [
                "all_steps_completed",
                "all_acceptance_tests_pass",
                "no_circuit_breakers_tripped",
            ],
            "manual_override": {
                "allowed": False,
                "requires_approval_from": [],
            },
        }

    def _build_observability(self, ccis: CCIS) -> Dict[str, Any]:
        """Build observability_and_metrics section."""
        return {
            "logging": {
                "level": "INFO",
                "structured": True,
            },
            "metrics": {
                "track_duration": True,
                "track_resource_usage": False,
            },
            "reporting": {
                "generate_summary": True,
                "summary_format": "markdown",
            },
        }

    # Helper methods

    def _infer_phase_type(self, change_kinds: List[str]) -> str:
        """Infer phase type from change kinds."""
        if "new_feature" in change_kinds:
            return "implementation"
        elif "bug_fix" in change_kinds:
            return "bug_fix"
        elif "refactor" in change_kinds:
            return "refactor"
        else:
            return "implementation"

    def _map_severity_to_priority(self, severity: str) -> int:
        """Map CCIS severity to Phase Plan priority (1-10)."""
        mapping = {
            "critical": 1,
            "high": 3,
            "medium": 5,
            "low": 8,
        }
        return mapping.get(severity, 5)

    def _infer_operation_kind(self, criterion: str) -> str:
        """Infer operation kind from acceptance criterion text."""
        criterion_lower = criterion.lower()

        if "test" in criterion_lower:
            return "testing"
        elif "document" in criterion_lower:
            return "documentation"
        elif "implement" in criterion_lower or "create" in criterion_lower:
            return "implementation"
        elif "fix" in criterion_lower:
            return "bug_fix"
        elif "refactor" in criterion_lower:
            return "refactor"
        else:
            return "implementation"

    def _extract_forbidden_paths(self, ccis: CCIS) -> List[str]:
        """Extract forbidden paths from project overrides."""
        forbidden = [".git/*"]  # Always forbid .git

        if hasattr(ccis, "project_overrides") and ccis.project_overrides:
            forbidden_changes = getattr(ccis.project_overrides, "forbidden_changes", [])
            for item in forbidden_changes:
                # Extract path from text like "Do not modify files under docs/SSOT_MANUAL/"
                if "under" in item:
                    path = item.split("under")[-1].strip().rstrip(".")
                    forbidden.append(path)
                elif "/" in item or "\\" in item:
                    forbidden.append(item)

        return forbidden

    def save_to_yaml(self, phase_plan: Dict[str, Any], output_path: Path) -> None:
        """Save Phase Plan to YAML file."""
        with output_path.open("w", encoding="utf-8") as f:
            yaml.dump(
                phase_plan,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )


def main():
    """CLI entry point for conversion."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert CCIS to Phase Plan YAML format"
    )
    parser.add_argument("ccis_file", type=Path, help="Input CCIS YAML file")
    parser.add_argument(
        "--output",
        type=Path,
        help="Output Phase Plan YAML file (default: phase_plan_<ccis_id>.yml)",
    )
    parser.add_argument(
        "--tool", default="github_copilot_cli", help="Default execution tool"
    )

    args = parser.parse_args()

    # Load CCIS
    print(f"Loading CCIS from: {args.ccis_file}")
    with args.ccis_file.open("r") as f:
        ccis_data = yaml.safe_load(f)

    # Parse CCIS (handle both root-level and nested structure)
    if "ccis" in ccis_data:
        ccis = CCIS(**ccis_data["ccis"])
    else:
        ccis = CCIS(**ccis_data)

    print(f"✓ Loaded CCIS: {ccis.ccis_id}")

    # Convert
    converter = CCISToPhaseplanConverter(default_tool=args.tool)
    phase_plan = converter.convert(ccis)

    print(f"✓ Converted to Phase Plan: {phase_plan['file_id']}")

    # Save
    output_path = args.output or Path(f"phase_plan_{ccis.ccis_id}.yml")
    converter.save_to_yaml(phase_plan, output_path)

    print(f"✓ Saved Phase Plan to: {output_path}")
    print(f"\n✅ Conversion complete!")


if __name__ == "__main__":
    main()
