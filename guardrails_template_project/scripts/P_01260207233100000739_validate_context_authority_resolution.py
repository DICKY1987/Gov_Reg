#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from validator_common import base_evidence, default_main, fail, observe


AUTHORITY_RANK = {"INFORMATIONAL": 1, "CONSTRAINING": 2, "AUTHORITATIVE": 3}
ALLOWED_CONFLICT_POLICIES = {
    "higher_authority_wins",
    "plan_wins_if_explicitly_declared",
    "manual_review",
}


def scope_token(scope: Any) -> str:
    if isinstance(scope, dict):
        return json.dumps(scope, sort_keys=True)
    return str(scope)


def validate(plan_path: Path, plan: dict[str, Any]) -> dict[str, Any]:
    evidence = base_evidence("GATE-CONTEXT-002", plan_path)
    section = plan.get("referenced_context_artifacts")
    if not isinstance(section, dict):
        fail(evidence, "Missing referenced_context_artifacts section")
        return evidence

    by_scope: dict[str, list[dict[str, Any]]] = {}
    artifacts = section.get("artifacts", [])
    if isinstance(artifacts, list):
        for artifact in artifacts:
            if isinstance(artifact, dict):
                conflict_policy = artifact.get("conflict_resolution_policy")
                if conflict_policy and conflict_policy not in ALLOWED_CONFLICT_POLICIES:
                    fail(
                        evidence,
                        "Context artifact has unsupported conflict_resolution_policy",
                        artifact_id=artifact.get("context_artifact_id") or artifact.get("artifact_id") or artifact.get("id"),
                        conflict_resolution_policy=conflict_policy,
                    )
                by_scope.setdefault(scope_token(artifact.get("scope") or artifact.get("scope_mapping")), []).append(artifact)

    for scope, scoped_artifacts in by_scope.items():
        authoritative = [item for item in scoped_artifacts if item.get("authority_level") == "AUTHORITATIVE"]
        if len(authoritative) > 1:
            hashes = [item.get("content_sha256") or item.get("hash") for item in authoritative]
            if any(not item for item in hashes):
                fail(evidence, "Multiple AUTHORITATIVE context artifacts for the same scope require content hashes", scope=scope)
            elif len(set(hashes)) > 1:
                fail(evidence, "Conflicting AUTHORITATIVE context artifacts for the same scope", scope=scope)
        ranked = sorted(scoped_artifacts, key=lambda item: AUTHORITY_RANK.get(str(item.get("authority_level")), 0))
        if ranked:
            selected = ranked[-1]
            observe(
                evidence,
                "Resolved context authority for scope",
                scope=scope,
                selected_artifact=selected.get("context_artifact_id") or selected.get("artifact_id") or selected.get("id"),
                authority_level=selected.get("authority_level"),
            )
    observe(evidence, "Validated context authority resolution", scope_count=len(by_scope))
    return evidence


if __name__ == "__main__":
    default_main("context_authority_resolution", validate)
