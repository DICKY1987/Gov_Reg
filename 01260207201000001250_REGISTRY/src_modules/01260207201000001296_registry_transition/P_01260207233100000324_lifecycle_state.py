"""
Lifecycle State - Enums and Dataclasses

Defines the 6-state lifecycle and associated data structures.
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional

class LifecycleState(str, Enum):
    PLANNED = "PLANNED"
    PRESENT = "PRESENT"
    DEPRECATED = "DEPRECATED"
    DELETED = "DELETED"
    ORPHANED = "ORPHANED"
    CONFLICT = "CONFLICT"

class ConflictKind(str, Enum):
    MULTI_MATCH = "MULTI_MATCH"
    DUPLICATE_PLANS = "DUPLICATE_PLANS"
    PATH_COLLISION = "PATH_COLLISION"
    ID_COLLISION = "ID_COLLISION"

@dataclass
class PlannedRecord:
    """Registry record with path tracking."""
    record_id: str
    file_id: str
    canonical_path: str
    lifecycle_state: LifecycleState
    path_history: List[str] = field(default_factory=list)
    path_aliases: List[str] = field(default_factory=list)

@dataclass
class MatchResult:
    """Result of identity resolution."""
    observed_path: str
    match_kind: Optional[str] = None
    matched_record_id: Optional[str] = None
    conflict_kind: Optional[ConflictKind] = None
    candidates: List[dict] = field(default_factory=list)

@dataclass
class TransitionResult:
    """Result of state machine transition."""
    success: bool
    from_state: str
    to_state: str
    transition_name: str
    errors: List[str] = field(default_factory=list)
    applied_effects: List[dict] = field(default_factory=list)

@dataclass
class Condition:
    """Transition condition specification."""
    field: str
    operator: str  # eq, not_null, in, gt
    value: Optional[any] = None

@dataclass
class Effect:
    """Transition effect specification."""
    action: str  # set_field, apply
    target: str
    value: Optional[str] = None
    rule: Optional[str] = None

@dataclass
class Transition:
    """Complete transition specification."""
    name: str
    from_states: List[str]
    to_state: str
    conditions: List[Condition] = field(default_factory=list)
    effects: List[Effect] = field(default_factory=list)
