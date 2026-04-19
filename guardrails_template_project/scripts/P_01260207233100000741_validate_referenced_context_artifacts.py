#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

from validator_common import ALLOWED_AUTHORITY_LEVELS, artifact_records, base_evidence, default_main, fail, observe, repo_path


REQUIRED_POLICY = {
    "required_when_external_context_needed": True,
    "unbound_context_action": "fail_closed",
    "informational_artifacts_cannot_override_authoritative": True,
}
REQUIRED_VALIDATION_FLAGS = {
    "must_exist": True,
    "must_be_read_before_step_execution": True,
}


def context_artifact_id(artifact: dict[str, Any]) -> str | None:
    value = artifact.get("context_artifact_id") or artifact.get("artifact_id") or artifact.get("id")
    return str(value) if value else None


def referenced_context_ids(plan: dict[str, Any]) -> set[str]:
    refs: set[str] = set()
    for record in artifact_records(plan):
        dependencies = record.get("context_artifact_dependencies", [])
        if isinstance(dependencies, list):
            refs.update(str(item) for item in dependencies if item)

    step_contracts = plan.get("step_contracts", {})
    if isinstance(step_contracts, dict):
        for phase_steps in step_contracts.values():
            if not isinstance(phase_steps, dict):
                continue
            for step in phase_steps.values():
                if not isinstance(step, dict):
                    continue
                dependencies = step.get("context_artifact_dependencies", [])
                if isinstance(dependencies, list):
                    refs.update(str(item) for item in dependencies if item)
    return refs


def has_non_empty_scope(scope: Any) -> bool:
    if not isinstance(scope, dict):
        return False
    for value in scope.values():
        if isinstance(value, list) and value:
            return True
        if isinstance(value, str) and value.strip():
            return True
        if value not in (None, "", [], {}):
            return True
    return False


def validate(plan_path: Path, plan: dict[str, Any]) -> dict[str, Any]:
    evidence = base_evidence("GATE-CONTEXT-001", plan_path)
    section = plan.get("referenced_context_artifacts")
    if not isinstance(section, dict):
        fail(evidence, "Missing referenced_context_artifacts section")
        return evidence

    if section.get("enabled") is not True:
        fail(evidence, "referenced_context_artifacts.enabled must be true")

    policy = section.get("policy")
    if not isinstance(policy, dict):
        fail(evidence, "referenced_context_artifacts.policy must be an object")
        policy = {}
    for key, expected in REQUIRED_POLICY.items():
        if policy.get(key) != expected:
            fail(evidence, "Referenced context policy does not match fail-closed contract", field=key, expected=expected, observed=policy.get(key))

    artifacts = section.get("artifacts", [])
    if not isinstance(artifacts, list):
        fail(evidence, "referenced_context_artifacts.artifacts must be an array")
        return evidence

    allowed = set(policy.get("allowed_authority_levels", [])) or ALLOWED_AUTHORITY_LEVELS
    if not allowed.issubset(ALLOWED_AUTHORITY_LEVELS):
        fail(evidence, "Policy contains unsupported authority levels", observed=sorted(allowed))

    seen_ids: set[str] = set()
    seen_authoritative_scopes: set[str] = set()
    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            fail(evidence, "Context artifact record must be an object", index=index)
            continue
        artifact_id = context_artifact_id(artifact)
        authority = artifact.get("authority_level")
        if not artifact_id:
            fail(evidence, "Context artifact missing identifier", index=index)
        elif artifact_id in seen_ids:
            fail(evidence, "Duplicate context artifact identifier", artifact_id=artifact_id)
        else:
            seen_ids.add(artifact_id)
        if authority not in allowed:
            fail(evidence, "Context artifact has invalid authority_level", artifact_id=artifact_id, authority_level=authority)
        path_value = artifact.get("path") or artifact.get("relative_path")
        if not path_value:
            fail(evidence, "Context artifact missing path", artifact_id=artifact_id)
        elif not repo_path(path_value).exists():
            fail(evidence, "Context artifact path does not exist", artifact_id=artifact_id, path=path_value)
        if not artifact.get("artifact_type"):
            fail(evidence, "Context artifact missing artifact_type", artifact_id=artifact_id)
        if not isinstance(artifact.get("usage_purpose"), str) or not artifact.get("usage_purpose", "").strip():
            fail(evidence, "Context artifact missing usage_purpose", artifact_id=artifact_id)
        if not isinstance(artifact.get("required_for_correct_execution"), bool):
            fail(evidence, "Context artifact required_for_correct_execution must be boolean", artifact_id=artifact_id)
        scope = artifact.get("scope") or artifact.get("scope_mapping")
        if not has_non_empty_scope(scope):
            fail(evidence, "Context artifact missing non-ambiguous scope mapping", artifact_id=artifact_id)
        elif isinstance(scope, dict):
            scope_token = repr(sorted(scope.items()))
            if scope_token in seen_authoritative_scopes and authority == "AUTHORITATIVE":
                fail(evidence, "Duplicate authoritative scope mapping", artifact_id=artifact_id)
            if authority == "AUTHORITATIVE":
                seen_authoritative_scopes.add(scope_token)
        validation = artifact.get("validation")
        if not isinstance(validation, dict):
            fail(evidence, "Context artifact missing validation contract", artifact_id=artifact_id)
        else:
            for key, expected in REQUIRED_VALIDATION_FLAGS.items():
                if validation.get(key) != expected:
                    fail(evidence, "Context artifact validation flag does not match contract", artifact_id=artifact_id, field=key, expected=expected, observed=validation.get(key))

    unknown_refs = sorted(referenced_context_ids(plan) - seen_ids)
    for context_id in unknown_refs:
        fail(evidence, "Plan references an undeclared context artifact", context_artifact_id=context_id)

    observe(evidence, "Validated referenced context artifacts", artifact_count=len(artifacts))
    return evidence


if __name__ == "__main__":
    default_main("referenced_context_artifacts", validate)
