"""
Registry Transition - Core Implementation

This package implements the deterministic registry transition specification
including identity resolution, field precedence, and lifecycle state management.

Modules:
- lifecycle_state: Enums and dataclasses for lifecycle states
- state_machine: Contract loader and transition enforcer
- identity_resolver: 4-step matching algorithm
- field_precedence: Per-column transition rules
- registry_writer: Single-writer chokepoint with atomic operations
- gates: Split completeness and validity gates

Version: 2.0.0
Created: 2026-01-30
"""

from .P_01260207233100000324_lifecycle_state import (
    LifecycleState,
    ConflictKind,
    PlannedRecord,
    MatchResult,
    TransitionResult,
    Condition,
    Effect,
    Transition
)
from .P_01260207233100000326_state_machine import StateMachine
from .P_01260207233100000323_identity_resolver import IdentityResolver
from .P_01260207233100000321_field_precedence import FieldPrecedence, ImmutableConflict
from .P_01260207233100000325_registry_writer import RegistryWriter, WriteResult
from .P_01260207233100000322_gates import CompletenessGate, ValidityGate

__version__ = "2.0.0"
__all__ = [
    "LifecycleState",
    "ConflictKind",
    "PlannedRecord",
    "MatchResult",
    "TransitionResult",
    "Condition",
    "Effect",
    "Transition",
    "StateMachine",
    "IdentityResolver",
    "FieldPrecedence",
    "ImmutableConflict",
    "RegistryWriter",
    "WriteResult",
    "CompletenessGate",
    "ValidityGate",
]
