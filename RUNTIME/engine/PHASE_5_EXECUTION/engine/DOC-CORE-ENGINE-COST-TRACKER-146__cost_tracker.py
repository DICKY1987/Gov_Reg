# DOC_LINK: DOC-CORE-ENGINE-COST-TRACKER-146
"""
Cost Tracker

Tracks costs for execution requests including API calls,
compute time, and resource usage.

Author: AI Development Pipeline
Created: 2025-11-23
WS: WS-NEXT-002-004
"""

# DOC_ID: DOC-CORE-ENGINE-COST-TRACKER-146

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Dict, List, Optional


@dataclass
class UsageInfo:
    """Resource usage information"""

    quantity: float
    unit: str
    rate: float

    @property
    def cost(self) -> float:
        """Calculate cost from quantity and rate"""
        return self.quantity * self.rate

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {"quantity": self.quantity, "unit": self.unit, "rate": self.rate}


class CostTracker:
    """
    Tracks and aggregates costs for execution requests.

    Supports multiple resource types:
        - api_call: API/LLM calls (tokens, requests)
        - compute_time: Compute resources (CPU, GPU time)
        - storage: Storage usage (GB, files)
        - network: Network transfer (GB)
        - tool_usage: External tool usage
        - custom: Custom resource types
    """

    VALID_RESOURCE_TYPES = {
        "api_call",
        "compute_time",
        "storage",
        "network",
        "tool_usage",
        "custom",
    }

    def __init__(self, db):
        """
        Initialize CostTracker.

        Args:
            db: Database instance for persistence
        """
        self.db = db
        self._ensure_table()

    def _ensure_table(self):
        """Ensure costs table exists"""
        try:
            self.db.conn.execute("SELECT 1 FROM costs LIMIT 1")
        except Exception:
            schema_path = "schema/migrations/005_add_costs_table.sql"
            with open(schema_path, "r") as f:
                self.db.conn.executescript(f.read())
            self.db.conn.commit()

    def record_cost(
        self,
        cost_id: str,
        resource_type: str,
        amount: float,
        currency: str = "USD",
        execution_request_id: Optional[str] = None,
        project_id: Optional[str] = None,
        resource_name: Optional[str] = None,
        usage: Optional[UsageInfo] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        """
        Record a cost entry.

        Args:
            cost_id: Unique cost identifier (ULID)
            resource_type: Type of resource
            amount: Cost amount
            currency: Currency code (default: USD)
            execution_request_id: Optional execution request ID
            project_id: Optional project ID
            resource_name: Optional specific resource name
            usage: Optional usage details
            metadata: Additional metadata

        Returns:
            cost_id

        Raises:
            ValueError: If resource_type invalid or amount negative
        """
        if resource_type not in self.VALID_RESOURCE_TYPES:
            raise ValueError(f"Invalid resource_type: {resource_type}")

        if amount < 0:
            raise ValueError("Amount must be non-negative")

        if len(currency) != 3 or not currency.isupper():
            raise ValueError("Currency must be 3-letter uppercase code")

        self.db.conn.execute(
            """
            INSERT INTO costs (
                cost_id, execution_request_id, project_id, resource_type,
                resource_name, amount, currency, usage, recorded_at, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cost_id,
                execution_request_id,
                project_id,
                resource_type,
                resource_name,
                amount,
                currency,
                json.dumps(usage.to_dict()) if usage else None,
                datetime.now(UTC).isoformat(),
                json.dumps(metadata) if metadata else None,
            ),
        )
        self.db.conn.commit()

        return cost_id

    def get_cost(self, cost_id: str) -> Optional[Dict]:
        """
        Get cost record by ID.

        Args:
            cost_id: Cost identifier

        Returns:
            Cost data dict or None if not found
        """
        row = self.db.conn.execute(
            "SELECT * FROM costs WHERE cost_id = ?", (cost_id,)
        ).fetchone()

        if not row:
            return None

        return self._row_to_dict(row)

    def _row_to_dict(self, row) -> Dict:
        """Convert database row to dict"""
        data = dict(row)

        # Deserialize JSON fields
        for field in ["usage", "metadata"]:
            if data.get(field):
                data[field] = json.loads(data[field])

        return data

    def get_total_cost(
        self,
        execution_request_id: Optional[str] = None,
        project_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        currency: str = "USD",
    ) -> float:
        """
        Get total cost with optional filters.

        Args:
            execution_request_id: Filter by execution request
            project_id: Filter by project
            resource_type: Filter by resource type
            currency: Currency to return (default: USD)

        Returns:
            Total cost in specified currency

        Note:
            Currently only supports single currency.
            Multi-currency conversion would require exchange rates.
        """
        query = "SELECT SUM(amount) as total FROM costs WHERE currency = ?"
        params = [currency]

        if execution_request_id:
            query += " AND execution_request_id = ?"
            params.append(execution_request_id)

        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)

        if resource_type:
            query += " AND resource_type = ?"
            params.append(resource_type)

        row = self.db.conn.execute(query, params).fetchone()
        total = row["total"] if row and row["total"] is not None else 0.0

        return total

    def get_cost_breakdown(
        self,
        execution_request_id: Optional[str] = None,
        project_id: Optional[str] = None,
        currency: str = "USD",
    ) -> Dict[str, float]:
        """
        Get cost breakdown by resource type.

        Args:
            execution_request_id: Filter by execution request
            project_id: Filter by project
            currency: Currency to return

        Returns:
            Dict mapping resource_type to total cost
        """
        query = """
            SELECT resource_type, SUM(amount) as total
            FROM costs
            WHERE currency = ?
        """
        params = [currency]

        if execution_request_id:
            query += " AND execution_request_id = ?"
            params.append(execution_request_id)

        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)

        query += " GROUP BY resource_type"

        rows = self.db.conn.execute(query, params).fetchall()

        breakdown = {}
        for row in rows:
            breakdown[row["resource_type"]] = row["total"]

        return breakdown

    def list_costs(
        self,
        execution_request_id: Optional[str] = None,
        project_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict]:
        """
        List cost records with optional filters.

        Args:
            execution_request_id: Filter by execution request
            project_id: Filter by project
            resource_type: Filter by resource type
            limit: Maximum number of records to return

        Returns:
            List of cost dicts
        """
        query = "SELECT * FROM costs WHERE 1=1"
        params = []

        if execution_request_id:
            query += " AND execution_request_id = ?"
            params.append(execution_request_id)

        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)

        if resource_type:
            query += " AND resource_type = ?"
            params.append(resource_type)

        query += " ORDER BY recorded_at DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        rows = self.db.conn.execute(query, params).fetchall()
        return [self._row_to_dict(row) for row in rows]

    def delete_cost(self, cost_id: str) -> bool:
        """
        Delete a cost record.

        Args:
            cost_id: Cost identifier

        Returns:
            True if deleted, False if not found
        """
        cursor = self.db.conn.execute("DELETE FROM costs WHERE cost_id = ?", (cost_id,))
        self.db.conn.commit()

        return cursor.rowcount > 0
