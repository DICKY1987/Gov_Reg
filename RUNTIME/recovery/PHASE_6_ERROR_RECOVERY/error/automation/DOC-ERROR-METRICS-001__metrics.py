# DOC_LINK: DOC-ERROR-METRICS-001
"""Error automation metrics and monitoring

EXECUTION PATTERN: EXEC-001 (Type-Safe Operations)
- Strong typing for all metrics
- Validated time ranges
- Defensive parsing

DOC_ID: DOC-ERROR-METRICS-001
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone


class ErrorAutomationMetrics:
    """Collects and reports error automation metrics"""

    def __init__(
        self, decision_log: Optional[Path] = None, review_queue: Optional[Path] = None
    ):
        self.decision_log = decision_log or Path(".state/patch_decisions.jsonl")
        self.review_queue = review_queue or Path(".state/manual_review_queue.jsonl")

    def get_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get metrics for last N days.

        Args:
            days: Number of days to analyze (must be > 0)

        Returns:
            Dictionary with metrics
        """
        if days < 1:
            raise ValueError("days must be >= 1")

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        decisions = self._load_decisions_since(cutoff)

        total = len(decisions)

        return {
            "total_patches": total,
            "auto_merged": sum(
                1 for d in decisions if d.get("decision") == "auto_merge"
            ),
            "pr_created": sum(
                1 for d in decisions if d.get("decision") == "auto_merge_pr"
            ),
            "manual_review": sum(
                1 for d in decisions if d.get("decision") == "manual_review"
            ),
            "rejected": sum(1 for d in decisions if d.get("decision") == "rejected"),
            "avg_confidence": self._calculate_avg_confidence(decisions),
            "pending_reviews": self._count_pending_reviews(),
            "review_queue_age_hours": self._oldest_queue_age_hours(),
        }

    def get_daily_breakdown(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get per-day breakdown of metrics."""
        if days < 1:
            raise ValueError("days must be >= 1")

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        decisions = self._load_decisions_since(cutoff)

        # Group by date
        by_date: Dict[str, List[Dict]] = {}

        for decision in decisions:
            try:
                ts = datetime.fromisoformat(
                    decision["timestamp"].replace("Z", "+00:00")
                )
                date_key = ts.date().isoformat()

                if date_key not in by_date:
                    by_date[date_key] = []

                by_date[date_key].append(decision)

            except (KeyError, ValueError) as e:
                print(f"Warning: Invalid decision entry: {e}")

        # Build daily breakdown
        breakdown = []
        for date_str in sorted(by_date.keys()):
            day_decisions = by_date[date_str]
            breakdown.append(
                {
                    "date": date_str,
                    "total": len(day_decisions),
                    "auto_merged": sum(
                        1 for d in day_decisions if d.get("decision") == "auto_merge"
                    ),
                    "avg_confidence": self._calculate_avg_confidence(day_decisions),
                }
            )

        return breakdown

    def _load_decisions_since(self, cutoff: datetime) -> List[Dict]:
        """Load decisions since cutoff time."""
        if not self.decision_log.exists():
            return []

        decisions = []

        with open(self.decision_log, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)

                    # Parse timestamp
                    ts_str = entry.get("timestamp")
                    if not ts_str:
                        continue

                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))

                    if ts >= cutoff:
                        decisions.append(entry)

                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    print(f"Warning: Skipping invalid decision entry: {e}")

        return decisions

    def _calculate_avg_confidence(self, decisions: List[Dict]) -> float:
        """Calculate average confidence score."""
        if not decisions:
            return 0.0

        total = 0.0
        count = 0

        for d in decisions:
            try:
                conf = d.get("confidence", {}).get("overall")
                if conf is not None:
                    total += float(conf)
                    count += 1
            except (TypeError, ValueError):
                continue

        return total / count if count > 0 else 0.0

    def _count_pending_reviews(self) -> int:
        """Count pending manual reviews."""
        if not self.review_queue.exists():
            return 0

        count = 0

        with open(self.review_queue, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry.get("status") != "processed":
                        count += 1
                except json.JSONDecodeError:
                    continue

        return count

    def _oldest_queue_age_hours(self) -> float:
        """Get age of oldest pending review in hours."""
        if not self.review_queue.exists():
            return 0.0

        oldest = None

        with open(self.review_queue, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)

                    if entry.get("status") != "processed":
                        ts_str = entry.get("queued_at")
                        if ts_str:
                            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                            if oldest is None or ts < oldest:
                                oldest = ts

                except (json.JSONDecodeError, ValueError, KeyError):
                    continue

        if oldest:
            return (datetime.now(timezone.utc) - oldest).total_seconds() / 3600

        return 0.0
