#!/usr/bin/env python
"""
splinter_sync_phase_to_github.py

Sync a SPLINTER Phase Plan to GitHub Issues and Projects v2.

Usage:
    python scripts/splinter_sync_phase_to_github.py \
        --phase-file phases/my_phase.yaml \
        --github-repo owner/repo \
        --github-token $GITHUB_TOKEN
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

import yaml

# Add patterns/executors to path
.parent.parent / "patterns" / "executors"))

from github_sync.phase_sync import (
    GitHubIntegrationConfig,
    GitHubIssueConfig,
    GitHubProjectConfig,
    PhaseIdentity,
    ensure_issue,
    ensure_project_item,
)


def load_phase_plan(phase_file: Path) -> dict:
    """Load and parse Phase Plan YAML."""
    with phase_file.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def extract_phase_identity(data: dict) -> PhaseIdentity:
    """Extract PhaseIdentity from phase plan data."""
    identity = data.get("phase_identity", {})
    execution = data.get("execution_profile", {})

    return PhaseIdentity(
        phase_id=identity.get("phase_id", "UNKNOWN"),
        workstream_id=identity.get("workstream_id", "UNKNOWN"),
        title=identity.get("title", "Untitled Phase"),
        status=identity.get("status", "planned"),
        risk_level=execution.get("risk_level"),
        target_date=None,  # TODO: Extract from completion_gate if present
    )


def build_config(
    data: dict, repo_owner: str, repo_name: str
) -> Optional[GitHubIntegrationConfig]:
    """Build GitHubIntegrationConfig from phase plan data."""
    gh = data.get("github_integration")
    if not gh:
        print("No github_integration block found in phase plan")
        return None

    if not gh.get("enabled", False):
        print("github_integration.enabled is false; skipping sync")
        return None

    repo_cfg = gh.get("repo", {})
    issue_cfg = gh.get("issue", {})
    project_cfg = gh.get("project", {})
    automation_cfg = gh.get("automation", {})

    return GitHubIntegrationConfig(
        enabled=True,
        repo_owner=repo_cfg.get("owner", repo_owner),
        repo_name=repo_cfg.get("name", repo_name),
        default_branch=repo_cfg.get("default_branch", "main"),
        issue=GitHubIssueConfig(
            mode=issue_cfg.get("mode", "one-per-phase"),
            number=issue_cfg.get("number"),
            title_template=issue_cfg.get("title_template", "[{phase_id}] {title}"),
            body_template_path=issue_cfg.get("body_template_path"),
            labels=issue_cfg.get("labels", []),
            assignees=issue_cfg.get("assignees", []),
        ),
        project=GitHubProjectConfig(
            url=project_cfg.get("url"),
            owner=project_cfg.get("owner", repo_owner),
            project_number=project_cfg.get("project_number"),
            item_id=project_cfg.get("item_id"),
            field_mappings=project_cfg.get("field_mappings", {}),
        ),
        automation=automation_cfg,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Sync SPLINTER Phase Plan to GitHub Issues and Projects v2"
    )
    parser.add_argument(
        "--phase-file",
        type=Path,
        required=True,
        help="Path to Phase Plan YAML file",
    )
    parser.add_argument(
        "--github-repo",
        required=True,
        help="GitHub repository in owner/repo format",
    )
    parser.add_argument(
        "--github-token",
        help="GitHub API token (or use GITHUB_TOKEN env var)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without making changes",
    )

    args = parser.parse_args()

    # Get token
    token = args.github_token or os.getenv("GITHUB_TOKEN")
    if not token:
        print("Error: GitHub token required (--github-token or GITHUB_TOKEN env var)")
        return 1

    # Parse repo
    try:
        repo_owner, repo_name = args.github_repo.split("/")
    except ValueError:
        print(
            f"Error: Invalid repo format '{args.github_repo}' (expected 'owner/repo')"
        )
        return 1

    # Load phase plan
    if not args.phase_file.exists():
        print(f"Error: Phase file not found: {args.phase_file}")
        return 1

    print(f"Loading phase plan: {args.phase_file}")
    data = load_phase_plan(args.phase_file)

    # Extract phase identity
    phase = extract_phase_identity(data)
    print(f"Phase: {phase.phase_id} - {phase.title}")
    print(f"  Workstream: {phase.workstream_id}")
    print(f"  Status: {phase.status}")
    print(f"  Risk: {phase.risk_level or 'unspecified'}")

    # Build config
    config = build_config(data, repo_owner, repo_name)
    if not config:
        return 0  # Not an error if disabled

    if args.dry_run:
        print("\n[DRY RUN] Would perform the following actions:")
        print(f"  1. Ensure issue exists for {phase.phase_id}")
        print(f"     Repository: {config.repo_owner}/{config.repo_name}")
        print(f"     Mode: {config.issue.mode}")
        if config.project.project_number:
            print(
                f"  2. Ensure project item in Project #{config.project.project_number}"
            )
            print(f"     Field mappings: {list(config.project.field_mappings.keys())}")
        return 0

    # 1. Ensure Issue
    print("\n1. Ensuring GitHub Issue...")
    try:
        issue_number = ensure_issue(
            config,
            phase,
            str(args.phase_file),
            token,
        )
        print(f"   ✓ Issue #{issue_number}")
    except Exception as e:
        print(f"   ✗ Failed to ensure issue: {e}")
        return 1

    # 2. Ensure Project Item (if configured)
    if config.project.project_number:
        print("\n2. Ensuring Project Item...")
        try:
            item_id = ensure_project_item(
                config,
                phase,
                issue_number,
                token,
            )
            print(f"   ✓ Project item: {item_id}")
        except Exception as e:
            print(f"   ✗ Failed to ensure project item: {e}")
            return 1
    else:
        print("\n2. Project sync: SKIPPED (no project_number configured)")

    print("\n✓ Sync complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
