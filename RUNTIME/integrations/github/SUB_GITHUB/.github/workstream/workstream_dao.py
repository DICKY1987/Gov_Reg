"""
Data Access Object for Workstream entities.

Reference: DOC-SSOT-STATE-MACHINES-001 §6
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from core.dao.base import BaseDAO


class WorkstreamDAO(BaseDAO):
    """DAO for workstreams table."""

    @property
    def table_name(self) -> str:
        return "workstreams"

    @property
    def id_column(self) -> str:
        return "workstream_id"

    def find_by_state(self, state: str) -> List[Dict[str, Any]]:
        """Find all workstreams in a given state."""
        return self.find_by(state=state)

    def find_by_run(self, run_id: str) -> List[Dict[str, Any]]:
        """Find all workstreams for a run."""
        return self.find_by(run_id=run_id)
