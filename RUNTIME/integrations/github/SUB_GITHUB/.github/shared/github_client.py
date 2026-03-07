import json
import os
import DOC-ERROR-UTILS-TIME-145__time
from typing import Any, Dict, Iterable, Optional, Tuple

import requests


class GitHubProjectClient:
    """Thin helper for GitHub Projects v2 GraphQL + REST calls with basic retries."""

    def __init__(
        self,
        token: Optional[str] = None,
        base_rest_url: str = "https://api.github.com",
        graphql_url: str = "https://api.github.com/graphql",
        max_attempts: int = 3,
        backoff_seconds: float = 1.5,
    ) -> None:
        self.token = token or os.getenv("PROJECT_TOKEN") or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise RuntimeError("Missing GitHub token in PROJECT_TOKEN or GITHUB_TOKEN")
        self.base_rest_url = base_rest_url.rstrip("/")
        self.graphql_url = graphql_url
        self.max_attempts = max_attempts
        self.backoff_seconds = backoff_seconds

    def _rest(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
    ) -> Any:
        url = f"{self.base_rest_url}/{path.lstrip('/')}"
        for attempt in range(1, self.max_attempts + 1):
            resp = requests.request(
                method,
                url,
                params=params,
                json=json_body,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Accept": "application/vnd.github+json",
                },
                timeout=30,
            )
            if resp.status_code < 500 and resp.status_code != 429:
                resp.raise_for_status()
                if resp.text:
                    return resp.json()
                return None
            self._sleep(attempt, resp.status_code)
        resp.raise_for_status()

    def _graphql(self, query: str, variables: Dict[str, Any]) -> Any:
        for attempt in range(1, self.max_attempts + 1):
            resp = requests.post(
                self.graphql_url,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Accept": "application/vnd.github+json",
                },
                json={"query": query, "variables": variables},
                timeout=30,
            )
            if resp.status_code == 200:
                payload = resp.json()
                if payload.get("errors"):
                    # GraphQL errors are surfaced; only retry on transient messages.
                    if (
                        attempt < self.max_attempts
                        and self._is_retryable_graphql_error(payload["errors"])
                    ):
                        self._sleep(attempt, 200)
                        continue
                    raise RuntimeError(f"GraphQL errors: {payload['errors']}")
                return payload.get("data")
            if resp.status_code in (429, 502, 503):
                self._sleep(attempt, resp.status_code)
                continue
            resp.raise_for_status()
        raise RuntimeError("Exhausted retries for GraphQL request")

    def _sleep(self, attempt: int, status_code: int) -> None:
        time.sleep(self.backoff_seconds * attempt)

    @staticmethod
    def _is_retryable_graphql_error(errors: Iterable[Dict[str, Any]]) -> bool:
        for err in errors:
            msg = (err.get("message") or "").lower()
            if "rate limit" in msg or "temporarily unavailable" in msg:
                return True
        return False

    # Project helpers

    def resolve_project_and_fields(
        self, org: str, project_number: int
    ) -> Tuple[str, Dict[str, Any]]:
        query = """
        query GetProjectFields($org: String!, $projectNumber: Int!) {
          organization(login: $org) {
            projectV2(number: $projectNumber) {
              id
              title
              fields(first: 100) {
                nodes {
                  __typename
                  ... on ProjectV2FieldCommon {
                    id
                    name
                  }
                  ... on ProjectV2SingleSelectField {
                    id
                    name
                    options { id name }
                  }
                }
              }
            }
          }
        }
        """
        data = self._graphql(query, {"org": org, "projectNumber": project_number})
        project = (data or {}).get("organization", {}).get("projectV2")
        if not project:
            raise RuntimeError("Project not found; verify org and project number")
        return project["id"], project["fields"]["nodes"]

    def find_project_item_id(self, content_id: str, project_id: str) -> Optional[str]:
        query = """
        query ($contentId: ID!, $projectId: ID!) {
          node(id: $contentId) {
            ... on Issue {
              projectItems(first: 20) { nodes { id project { id } } }
            }
            ... on PullRequest {
              projectItems(first: 20) { nodes { id project { id } } }
            }
          }
        }
        """
        data = self._graphql(query, {"contentId": content_id, "projectId": project_id})
        project_items = (
            (data or {}).get("node", {}).get("projectItems", {}).get("nodes", [])
        )
        for item in project_items:
            if item.get("project", {}).get("id") == project_id:
                return item.get("id")
        return None

    def add_content_to_project(self, project_id: str, content_id: str) -> str:
        mutation = """
        mutation AddItemToProject($projectId: ID!, $contentId: ID!) {
          addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
            item { id }
          }
        }
        """
        data = self._graphql(
            mutation, {"projectId": project_id, "contentId": content_id}
        )
        item = (data or {}).get("addProjectV2ItemById", {}).get("item")
        if not item:
            raise RuntimeError("Failed to add content item to project")
        return item["id"]

    def add_draft_item(self, project_id: str, title: str) -> str:
        mutation = """
        mutation AddDraftItem($projectId: ID!, $title: String!) {
          addProjectV2DraftIssue(input: {projectId: $projectId, title: $title}) {
            projectItem { id }
          }
        }
        """
        data = self._graphql(mutation, {"projectId": project_id, "title": title})
        item = (data or {}).get("addProjectV2DraftIssue", {}).get("projectItem")
        if not item:
            raise RuntimeError("Failed to add draft item to project")
        return item["id"]

    def find_draft_item_by_title(self, project_id: str, title: str) -> Optional[str]:
        query = """
        query ($projectId: ID!, $title: String!) {
          node(id: $projectId) {
            ... on ProjectV2 {
              items(first: 50, query: $title) {
                nodes {
                  id
                  type
                  content {
                    ... on DraftIssue { title }
                  }
                }
              }
            }
          }
        }
        """
        data = self._graphql(query, {"projectId": project_id, "title": title})
        nodes = (data or {}).get("node", {}).get("items", {}).get("nodes", [])
        for node in nodes:
            content = node.get("content") or {}
            if content.get("title") == title:
                return node.get("id")
        return None

    def update_single_select(
        self, project_id: str, item_id: str, field_id: str, option_id: str
    ) -> None:
        mutation = """
        mutation UpdateSingleSelectField($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
          updateProjectV2ItemFieldValue(
            input: { projectId: $projectId, itemId: $itemId, fieldId: $fieldId, value: { singleSelectOptionId: $optionId } }
          ) { projectV2Item { id } }
        }
        """
        self._graphql(
            mutation,
            {
                "projectId": project_id,
                "itemId": item_id,
                "fieldId": field_id,
                "optionId": option_id,
            },
        )

    def update_number_field(
        self, project_id: str, item_id: str, field_id: str, number_value: float
    ) -> None:
        mutation = """
        mutation UpdateNumberField($projectId: ID!, $itemId: ID!, $fieldId: ID!, $numberValue: Float!) {
          updateProjectV2ItemFieldValue(
            input: { projectId: $projectId, itemId: $itemId, fieldId: $fieldId, value: { number: $numberValue } }
          ) { projectV2Item { id } }
        }
        """
        self._graphql(
            mutation,
            {
                "projectId": project_id,
                "itemId": item_id,
                "fieldId": field_id,
                "numberValue": number_value,
            },
        )

    # REST helpers

    def list_milestone_items(
        self, owner: str, repo: str, milestone_number: int
    ) -> Iterable[Dict[str, Any]]:
        page = 1
        while True:
            issues = self._rest(
                "GET",
                f"repos/{owner}/{repo}/issues",
                params={
                    "milestone": milestone_number,
                    "state": "all",
                    "per_page": 100,
                    "page": page,
                },
            )
            if not issues:
                break
            for issue in issues:
                yield issue
            if len(issues) < 100:
                break
            page += 1

    def close_milestone(self, owner: str, repo: str, milestone_number: int) -> None:
        self._rest(
            "PATCH",
            f"repos/{owner}/{repo}/milestones/{milestone_number}",
            json_body={"state": "closed"},
        )

    def log_json(self, label: str, payload: Dict[str, Any]) -> None:
        print(f"{label}: {json.dumps(payload, indent=2, sort_keys=True)}")
