# DOC_LINK: DOC-CORE-FILE-WATTCH-GIT-PIPE-EVENTS-1181
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class ChangeType(str, Enum):
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"


class Hook(str, Enum):
    ON_FILE_DETECTED = "onFileDetected"
    BEFORE_STAGE = "beforeStage"
    AFTER_STAGE = "afterStage"
    BEFORE_COMMIT = "beforeCommit"
    AFTER_COMMIT = "afterCommit"
    BEFORE_PUSH = "beforePush"
    AFTER_PUSH = "afterPush"
    BEFORE_PULL = "beforePull"
    AFTER_PULL = "afterPull"
    ON_CONFLICT = "onConflict"


@dataclass
class FileDetectedEvent:
    path: str
    change_type: ChangeType
    ts: float
    repo: str


@dataclass
class StageRequest:
    paths: List[str]
    repo: str
    ctx: Dict[str, object]


@dataclass
class StageDecision:
    allow: bool
    reasons: Optional[List[str]] = None
    transforms: Optional[Dict[str, object]] = None


@dataclass
class CommitRequest:
    staged_summary: List[str]
    repo: str
    author: Optional[str] = None


@dataclass
class CommitDecision:
    allow: bool
    message_override: Optional[str] = None
    sign: Optional[bool] = None


@dataclass
class PushRequest:
    remote: str
    branch: str
    commits: Optional[List[str]] = None


@dataclass
class PushDecision:
    allow: bool
    force: Optional[bool] = None


@dataclass
class PullRequest:
    remote: str
    branch: str


@dataclass
class PullDecision:
    allow: bool
    strategy: Optional[str] = None


@dataclass
class ConflictInfo:
    files: List[str]
    base: Optional[str] = None
    local: Optional[str] = None
    remote: Optional[str] = None


@dataclass
class PullResult:
    updated: bool
    conflicts: Optional[List[str]] = None
