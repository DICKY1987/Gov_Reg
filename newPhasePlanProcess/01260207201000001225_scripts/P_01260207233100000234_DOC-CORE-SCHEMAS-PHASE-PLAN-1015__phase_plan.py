# DOC_LINK: DOC-CORE-SCHEMAS-PHASE-PLAN-1015
"""Phase Plan schema.

DAG-organized structure of workstreams.
"""
DOC_ID: DOC - CORE - SCHEMAS - PHASE - PLAN - 1015

from typing import Any, Dict, List, Literal
from pydantic import BaseModel, Field


class Phase(BaseModel):
    """Individual phase in the phase plan."""

    phase_id: str
    workstreams: List[str] = Field(description="Workstream IDs in this phase")
    depends_on: List[str] = Field(
        default_factory=list, description="Phase IDs that must complete first"
    )
    status: Literal["pending", "in_progress", "completed", "failed"] = "pending"
    acceptance: List[str] = Field(default_factory=list)


class PhasePlan(BaseModel):
    """Phase Plan - DAG-organized phase structure."""

    id: str = Field(description="Phase Plan identifier")
    derived_from: str = Field(description="Source WS ID(s)")
    phases: List[Phase] = Field(min_length=1)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "PHASE-PLAN-001",
                "derived_from": "WS-0001",
                "phases": [
                    {
                        "phase_id": "PH-03",
                        "workstreams": ["WS-0001"],
                        "depends_on": ["PH-02"],
                        "status": "pending",
                        "acceptance": ["All workstreams complete", "No test failures"],
                    }
                ],
            }
        }
