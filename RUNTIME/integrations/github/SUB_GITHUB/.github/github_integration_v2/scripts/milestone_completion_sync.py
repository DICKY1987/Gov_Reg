import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional

# Add shared module to path
.parent.parent.parent / "shared"))
from DOC-CORE-SUB-GITHUB-GITHUB-CLIENT-767__github_client import GitHubProjectClient


def load_event() -> Dict:
    path = os.getenv("GITHUB_EVENT_PATH")
    if not path or not os.path.exists(path):
        raise RuntimeError("Missing GITHUB_EVENT_PATH")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_milestone(event: Dict) -> Optional[Dict]:
    data = event.get("issue") or event.get("pull_request")
    if not data:
        return None
    return data.get("milestone")


def run() -> None:
    event = load_event()
    milestone = extract_milestone(event)
    if not milestone:
        print("No milestone attached; exiting")
        return

    owner = os.getenv("TARGET_ORG") or os.getenv("GITHUB_REPOSITORY_OWNER")
    repo = os.getenv("TARGET_REPO") or os.getenv("GITHUB_REPOSITORY")
    if not owner or not repo:
        raise RuntimeError("TARGET_ORG or TARGET_REPO missing")
    if "/" in repo:
        owner, repo = repo.split("/", 1)

    project_id = os.getenv("PROJECT_NODE_ID")
    if not project_id:
        project_number = int(os.getenv("PROJECT_NUMBER", "1"))
        client_temp = GitHubProjectClient()
        project_id, _ = client_temp.resolve_project_and_fields(owner, project_number)

    status_field_id = os.getenv("STATUS_FIELD_ID")
    status_done_id = os.getenv("STATUS_DONE_ID")
    completion_field_id = os.getenv("COMPLETION_FIELD_ID")

    client = GitHubProjectClient()
    milestone_number = milestone["number"]

    issues = list(client.list_milestone_items(owner, repo, milestone_number))
    all_closed = all(item.get("state") == "closed" for item in issues)

    if all_closed and milestone.get("state") != "closed":
        client.close_milestone(owner, repo, milestone_number)

    title = milestone.get("title") or f"Milestone {milestone_number}"
    item_id = client.find_draft_item_by_title(project_id, title)
    if not item_id:
        item_id = client.add_draft_item(project_id, title)

    if status_field_id and status_done_id:
        client.update_single_select(
            project_id, item_id, status_field_id, status_done_id
        )
    if completion_field_id:
        completion_value = (
            100.0
            if all_closed
            else float(
                sum(1 for item in issues if item.get("state") == "closed")
                / max(len(issues), 1)
                * 100.0
            )
        )
        client.update_number_field(
            project_id, item_id, completion_field_id, completion_value
        )

    client.log_json(
        "milestone_sync_result",
        {
            "milestone_number": milestone_number,
            "project_item_id": item_id,
            "all_closed": all_closed,
            "issue_count": len(issues),
        },
    )


if __name__ == "__main__":
    run()
