import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

# Add shared module to path
.parent.parent.parent / "shared"))
from DOC-CORE-SUB-GITHUB-GITHUB-CLIENT-767__github_client import GitHubProjectClient


def load_event() -> Dict:
    event_path = os.getenv("GITHUB_EVENT_PATH")
    if not event_path or not os.path.exists(event_path):
        raise RuntimeError("GITHUB_EVENT_PATH missing; cannot parse event payload")
    with open(event_path, "r", encoding="utf-8") as f:
        return json.load(f)


def classify_event(event: Dict) -> Tuple[str, Dict]:
    if "issue" in event:
        return "issue", event["issue"]
    if "pull_request" in event:
        return "pull_request", event["pull_request"]
    raise RuntimeError("Unsupported event payload")


def desired_status(
    item: Dict,
    status_ids: Dict[str, Optional[str]],
) -> Optional[str]:
    state = item.get("state")
    merged = item.get("merged") or False
    if merged:
        return status_ids.get("done")
    if state == "closed":
        return status_ids.get("done")
    if state == "open":
        return status_ids.get("in_progress") or status_ids.get("todo")
    return None


def derive_phase_label(item: Dict, label_map: Dict[str, str]) -> Optional[str]:
    labels = item.get("labels", [])
    for label in labels:
        name = (label.get("name") or "").lower()
        if name in label_map:
            return label_map[name]
    return None


def run() -> None:
    event = load_event()
    kind, item = classify_event(event)
    client = GitHubProjectClient()

    project_id = os.getenv("PROJECT_NODE_ID")
    if not project_id:
        project_number = int(os.getenv("PROJECT_NUMBER", "1"))
        org = os.getenv("TARGET_ORG") or os.getenv("GITHUB_REPOSITORY_OWNER")
        if not org:
            raise RuntimeError("TARGET_ORG missing")
        project_id, _ = client.resolve_project_and_fields(org, project_number)

    status_ids = {
        "todo": os.getenv("STATUS_TODO_ID"),
        "in_progress": os.getenv("STATUS_IN_PROGRESS_ID"),
        "in_review": os.getenv("STATUS_IN_REVIEW_ID"),
        "done": os.getenv("STATUS_DONE_ID"),
    }
    phase_field_id = os.getenv("PHASE_FIELD_ID")
    status_field_id = os.getenv("STATUS_FIELD_ID")

    default_phase_map = {
        "phase-0": "Phase 0",
        "phase-1": "Phase 1",
        "phase-2": "Phase 2",
        "phase-3": "Phase 3",
        "phase-4": "Phase 4",
        "phase-5": "Phase 5",
        "phase-6": "Phase 6",
        "phase-7": "Phase 7",
    }
    phase_label_map = (
        json.loads(os.getenv("PHASE_LABEL_MAP_JSON", "{}")) or default_phase_map
    )
    phase_option_map = json.loads(os.getenv("PHASE_OPTION_MAP_JSON", "{}"))

    content_id = item.get("node_id")
    if not content_id:
        raise RuntimeError("Content node_id missing from event payload")

    item_id = client.find_project_item_id(content_id, project_id)
    if not item_id:
        item_id = client.add_content_to_project(project_id, content_id)

    status_option = desired_status(item, status_ids)
    if status_field_id and status_option:
        client.update_single_select(project_id, item_id, status_field_id, status_option)

    phase_label = derive_phase_label(item, phase_label_map)
    if phase_label and phase_field_id:
        option_id = phase_option_map.get(phase_label)
        if option_id:
            client.update_single_select(project_id, item_id, phase_field_id, option_id)

    client.log_json(
        "sync_result",
        {
            "item_type": kind,
            "item_id": item_id,
            "content_id": content_id,
            "status_option": status_option,
            "phase_label": phase_label,
        },
    )


if __name__ == "__main__":
    run()
