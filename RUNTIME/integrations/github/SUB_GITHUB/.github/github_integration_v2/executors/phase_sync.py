"""
Pattern: GH_SYNC_PHASE_V1
Responsibility:
    - Ensure a GitHub Issue exists for a given SPLINTER phase.
    - Ensure a GitHub Project item exists and has correct field values.
    - Never guess: always derive from phase_identity + github_integration.
"""

import textwrap
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests

# =========
# MODELS
# =========


@dataclass
class PhaseIdentity:
    phase_id: str
    workstream_id: str
    title: str
    status: str
    risk_level: Optional[str] = None
    target_date: Optional[str] = None  # ISO date string, e.g. "2025-12-31"


@dataclass
class GitHubIssueConfig:
    mode: str  # "one-per-phase" | "none" | "reuse"
    number: Optional[int]
    title_template: str
    body_template_path: Optional[str]
    labels: list
    assignees: list


@dataclass
class GitHubProjectConfig:
    url: Optional[str]
    owner: str
    project_number: Optional[int]
    item_id: Optional[str]
    field_mappings: Dict[str, str]  # logical_name -> project field label


@dataclass
class GitHubIntegrationConfig:
    enabled: bool
    repo_owner: str
    repo_name: str
    default_branch: str
    issue: GitHubIssueConfig
    project: GitHubProjectConfig
    automation: Dict[str, Any]


# =========
# HELPERS
# =========


def _render_issue_title(phase: PhaseIdentity, cfg: GitHubIssueConfig) -> str:
    """
    PATTERN: RENDER_ISSUE_TITLE_V1
    Rule:
        - Only substitute known placeholders.
        - Do NOT silently drop unknown keys.
    """
    template = cfg.title_template or "[{phase_id}] {title}"
    return template.format(
        phase_id=phase.phase_id,
        title=phase.title,
        workstream_id=phase.workstream_id,
        status=phase.status,
        risk_level=phase.risk_level or "unknown",
    )


def _render_issue_body(phase: PhaseIdentity, phase_yaml_path: str) -> str:
    """
    PATTERN: RENDER_ISSUE_BODY_V1
    Minimal, but structured. You can later make this pluggable with a .md template.
    """
    return textwrap.dedent(
        f"""
        # Phase: {phase.phase_id} – {phase.title}

        - Workstream: `{phase.workstream_id}`
        - Status (SPLINTER): `{phase.status}`
        - Risk level: `{phase.risk_level or "unknown"}`
        - Target date: `{phase.target_date or "unset"}`

        Ground-truth phase spec: `{phase_yaml_path}`

        > This issue is synchronized from the SPLINTER Phase Plan.
        > Do not manually edit the phase contract here; change the YAML instead.
        """
    ).strip()


def _github_request(
    method: str,
    url: str,
    token: str,
    *,
    json: Optional[dict] = None,
) -> dict:
    """
    PATTERN: GITHUB_REQUEST_V1
    - Centralize auth, headers, error handling.
    - Raise on non-2xx so orchestrator can decide.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    resp = requests.request(method, url, headers=headers, json=json)
    if not resp.ok:
        raise RuntimeError(
            f"GitHub API error {resp.status_code} for {url}: {resp.text[:500]}"
        )
    return resp.json()


# =========
# CORE: ENSURE ISSUE
# =========


def ensure_issue(
    gh_cfg: GitHubIntegrationConfig,
    phase: PhaseIdentity,
    phase_yaml_path: str,
    token: str,
) -> int:
    """
    PATTERN: GH_SYNC_PHASE_ISSUE_V1

    Behavior:
        - If github_integration.enabled is false or mode == "none": do nothing.
        - If issue.number is set: update title/body/labels.
        - Else: create a new issue and return its number.
    """
    if not gh_cfg.enabled:
        raise RuntimeError("GitHub integration disabled; aborting ensure_issue().")

    issue_cfg = gh_cfg.issue
    if issue_cfg.mode == "none":
        raise RuntimeError(
            "Issue mode is 'none'; ensure_issue() should not be invoked."
        )

    owner = gh_cfg.repo_owner
    repo = gh_cfg.repo_name

    title = _render_issue_title(phase, issue_cfg)
    body = _render_issue_body(phase, phase_yaml_path)

    labels = [
        *[lbl for lbl in issue_cfg.labels if lbl is not None],
        f"workstream:{phase.workstream_id}",
        f"phase:{phase.phase_id}",
    ]

    if issue_cfg.number:
        # UPDATE EXISTING ISSUE
        url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_cfg.number}"
        payload = {
            "title": title,
            "body": body,
            "labels": labels,
        }
        _github_request("PATCH", url, token, json=payload)
        return issue_cfg.number

    # CREATE NEW ISSUE
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    payload = {
        "title": title,
        "body": body,
        "labels": labels,
    }
    if issue_cfg.assignees:
        payload["assignees"] = [a for a in issue_cfg.assignees if a]

    result = _github_request("POST", url, token, json=payload)
    issue_number = result["number"]

    # NOTE:
    # You can optionally write back issue_number into the YAML in a later step.
    return issue_number


# =========
# CORE: ENSURE PROJECT ITEM
# =========


def ensure_project_item(
    gh_cfg: GitHubIntegrationConfig,
    phase: PhaseIdentity,
    issue_number: int,
    token: str,
) -> str:
    """
    PATTERN: GH_SYNC_PHASE_PROJECT_V1

    Behavior:
        - Resolve project id from owner + project_number or URL.
        - Find or create a Project item linked to the issue.
        - Upsert field values (Phase ID, Status, Risk, Target date, doc_id, etc.).
    """
    project_cfg = gh_cfg.project

    if not project_cfg.url and not project_cfg.project_number:
        raise RuntimeError("Project config incomplete: need url or project_number.")

    # 1) Resolve ProjectV2 node id
    project_node_id = _resolve_project_node_id(project_cfg, token)

    # 2) Get issue node ID
    issue_node_id = _get_issue_node_id(
        gh_cfg.repo_owner, gh_cfg.repo_name, issue_number, token
    )

    # 3) Ensure item exists for this issue
    item_id = project_cfg.item_id or _find_project_item_for_issue(
        project_node_id, issue_node_id, token
    )

    if item_id is None:
        item_id = _create_project_item_for_issue(project_node_id, issue_node_id, token)

    # 4) Upsert field values
    _update_project_item_fields(
        project_node_id,
        item_id,
        project_cfg.field_mappings,
        phase,
        token,
    )

    return item_id


# =========
# GRAPHQL HELPERS
# =========


def _graphql_request(token: str, query: str, variables: Dict[str, Any]) -> dict:
    """
    PATTERN: GITHUB_GRAPHQL_REQUEST_V1
    - Single entrypoint for GraphQL calls.
    - No business logic.
    """
    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    resp = requests.post(
        url, headers=headers, json={"query": query, "variables": variables}
    )
    if not resp.ok:
        raise RuntimeError(f"GraphQL error {resp.status_code}: {resp.text[:500]}")
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(f"GraphQL errors: {data['errors']}")
    return data["data"]


def _resolve_project_node_id(project_cfg: GitHubProjectConfig, token: str) -> str:
    """
    PATTERN: GH_PROJECT_RESOLVE_NODE_ID_V1
    Resolve ProjectV2 node ID from owner + project_number.
    """
    if not project_cfg.project_number:
        raise RuntimeError("project_number is required to resolve project node ID")

    query = """
    query($owner: String!, $number: Int!) {
      user(login: $owner) {
        projectV2(number: $number) {
          id
        }
      }
      organization(login: $owner) {
        projectV2(number: $number) {
          id
        }
      }
    }
    """
    variables = {
        "owner": project_cfg.owner,
        "number": project_cfg.project_number,
    }

    data = _graphql_request(token, query, variables)

    # Try user first, then organization
    if data.get("user") and data["user"].get("projectV2"):
        return data["user"]["projectV2"]["id"]
    elif data.get("organization") and data["organization"].get("projectV2"):
        return data["organization"]["projectV2"]["id"]
    else:
        raise RuntimeError(
            f"Could not find project {project_cfg.project_number} for owner {project_cfg.owner}"
        )


def _get_issue_node_id(owner: str, repo: str, issue_number: int, token: str) -> str:
    """
    Get the global node ID for an issue.
    """
    query = """
    query($owner: String!, $repo: String!, $number: Int!) {
      repository(owner: $owner, name: $repo) {
        issue(number: $number) {
          id
        }
      }
    }
    """
    variables = {
        "owner": owner,
        "repo": repo,
        "number": issue_number,
    }

    data = _graphql_request(token, query, variables)
    return data["repository"]["issue"]["id"]


def _find_project_item_for_issue(
    project_node_id: str,
    issue_node_id: str,
    token: str,
) -> Optional[str]:
    """
    PATTERN: GH_PROJECT_FIND_ITEM_FOR_ISSUE_V1
    Find existing project item for an issue.
    """
    query = """
    query($projectId: ID!, $after: String) {
      node(id: $projectId) {
        ... on ProjectV2 {
          items(first: 100, after: $after) {
            pageInfo {
              hasNextPage
              endCursor
            }
            nodes {
              id
              content {
                ... on Issue {
                  id
                }
              }
            }
          }
        }
      }
    }
    """

    after = None
    while True:
        variables = {"projectId": project_node_id, "after": after}
        data = _graphql_request(token, query, variables)

        items = data["node"]["items"]
        for item in items["nodes"]:
            if item.get("content") and item["content"].get("id") == issue_node_id:
                return item["id"]

        if not items["pageInfo"]["hasNextPage"]:
            break
        after = items["pageInfo"]["endCursor"]

    return None


def _create_project_item_for_issue(
    project_node_id: str,
    issue_node_id: str,
    token: str,
) -> str:
    """
    PATTERN: GH_PROJECT_CREATE_ITEM_FOR_ISSUE_V1
    Create a new project item linked to an issue.
    """
    mutation = """
    mutation($projectId: ID!, $contentId: ID!) {
      addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
        item {
          id
        }
      }
    }
    """
    variables = {
        "projectId": project_node_id,
        "contentId": issue_node_id,
    }

    data = _graphql_request(token, mutation, variables)
    return data["addProjectV2ItemById"]["item"]["id"]


def _update_project_item_fields(
    project_node_id: str,
    item_id: str,
    field_mappings: Dict[str, str],
    phase: PhaseIdentity,
    token: str,
) -> None:
    """
    PATTERN: GH_PROJECT_UPDATE_FIELDS_V1
    Update custom field values for a project item.
    """
    # 1) Get project fields and build name -> field metadata map
    fields_map = _get_project_fields(project_node_id, token)

    # 2) Build value map from phase identity
    value_map = {
        "phase_id_field": phase.phase_id,
        "workstream_field": phase.workstream_id,
        "status_field": phase.status,
        "risk_field": phase.risk_level,
        "target_date_field": phase.target_date,
    }

    # 3) Update each mapped field
    for logical_key, field_name in field_mappings.items():
        if field_name is None:
            continue

        value = value_map.get(logical_key)
        if value is None:
            continue

        field_meta = fields_map.get(field_name)
        if field_meta is None:
            print(f"Warning: Field '{field_name}' not found in project")
            continue

        _update_single_field(
            project_node_id,
            item_id,
            field_meta["id"],
            field_meta["dataType"],
            value,
            field_meta.get("options", []),
            token,
        )


def _get_project_fields(project_node_id: str, token: str) -> Dict[str, Dict[str, Any]]:
    """
    Get all custom fields for a project.
    Returns dict mapping field name -> {id, dataType, options}
    """
    query = """
    query($projectId: ID!) {
      node(id: $projectId) {
        ... on ProjectV2 {
          fields(first: 100) {
            nodes {
              ... on ProjectV2Field {
                id
                name
                dataType
              }
              ... on ProjectV2SingleSelectField {
                id
                name
                dataType
                options {
                  id
                  name
                }
              }
            }
          }
        }
      }
    }
    """
    variables = {"projectId": project_node_id}
    data = _graphql_request(token, query, variables)

    fields_map = {}
    for field in data["node"]["fields"]["nodes"]:
        fields_map[field["name"]] = {
            "id": field["id"],
            "dataType": field["dataType"],
            "options": field.get("options", []),
        }

    return fields_map


def _update_single_field(
    project_node_id: str,
    item_id: str,
    field_id: str,
    data_type: str,
    value: Any,
    options: list,
    token: str,
) -> None:
    """
    Update a single field value on a project item.
    """
    mutation = """
    mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $value: ProjectV2FieldValue!) {
      updateProjectV2ItemFieldValue(
        input: {projectId: $projectId, itemId: $itemId, fieldId: $fieldId, value: $value}
      ) {
        projectV2Item {
          id
        }
      }
    }
    """

    # Convert value based on field type
    if data_type == "TEXT":
        field_value = {"text": str(value)}
    elif data_type == "DATE":
        field_value = {"date": value}  # ISO 8601 format
    elif data_type == "NUMBER":
        field_value = {"number": float(value)}
    elif data_type == "SINGLE_SELECT":
        # Find option ID by name
        option_id = None
        for option in options:
            if option["name"].lower() == str(value).lower():
                option_id = option["id"]
                break
        if option_id is None:
            print(f"Warning: Option '{value}' not found for single-select field")
            return
        field_value = {"singleSelectOptionId": option_id}
    else:
        print(f"Warning: Unsupported field type '{data_type}'")
        return

    variables = {
        "projectId": project_node_id,
        "itemId": item_id,
        "fieldId": field_id,
        "value": field_value,
    }

    _graphql_request(token, mutation, variables)
