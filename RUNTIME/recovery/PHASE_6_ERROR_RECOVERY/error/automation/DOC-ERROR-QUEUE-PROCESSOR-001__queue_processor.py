# DOC_LINK: DOC-ERROR-QUEUE-PROCESSOR-001
"""Manual review queue processor

EXECUTION PATTERN: EXEC-002 (Batch Validation)
- Processes queue entries in batches
- Validates state before updates
- Atomic file operations

DOC_ID: DOC-ERROR-QUEUE-PROCESSOR-001
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import tempfile
import shutil


class ReviewQueueProcessor:
    """Manages manual review queue for low-confidence patches"""

    def __init__(self, queue_path: Optional[Path] = None):
        self.queue_path = queue_path or Path(".state/manual_review_queue.jsonl")
        self.queue_path.parent.mkdir(parents=True, exist_ok=True)

    def list_pending(self, min_confidence: float = 0.0) -> List[Dict[str, Any]]:
        """List pending reviews, optionally filtered by min confidence.

        Pattern: EXEC-002 - Batch read with validation
        """
        if not self.queue_path.exists():
            return []

        pending = []

        with open(self.queue_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                try:
                    entry = json.loads(line)

                    # Validate entry structure
                    self._validate_entry(entry, line_num)

                    # Filter by status and confidence
                    if entry.get("status") != "processed":
                        if entry["confidence"]["overall"] >= min_confidence:
                            pending.append(entry)

                except json.JSONDecodeError as e:
                    print(f"Warning: Invalid JSON at line {line_num}: {e}")
                except KeyError as e:
                    print(f"Warning: Missing key at line {line_num}: {e}")

        # Sort by confidence descending
        pending.sort(key=lambda x: x["confidence"]["overall"], reverse=True)
        return pending

    def approve(self, patch_path: str) -> Dict[str, Any]:
        """Approve a patch for manual merge.

        Pattern: EXEC-004 - Atomic update operation
        """
        self._update_status(
            patch_path,
            "approved",
            {
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "approved_by": os.getenv("USER", os.getenv("USERNAME", "unknown")),
            },
        )

        return {
            "status": "approved",
            "next_steps": f"Apply patch: git apply {patch_path}",
        }

    def reject(self, patch_path: str, reason: str) -> Dict[str, Any]:
        """Reject a patch.

        Pattern: EXEC-004 - Atomic update operation
        """
        self._update_status(
            patch_path,
            "rejected",
            {
                "rejected_at": datetime.now(timezone.utc).isoformat(),
                "rejected_by": os.getenv("USER", os.getenv("USERNAME", "unknown")),
                "reason": reason,
            },
        )

        return {"status": "rejected"}

    def get_queue_metrics(self) -> Dict[str, Any]:
        """Get queue health metrics."""
        pending = self.list_pending()

        if not pending:
            return {
                "total_pending": 0,
                "oldest_age_hours": 0,
                "avg_confidence": 0,
                "health": "good",
            }

        # Calculate oldest age
        oldest_ts = min(
            datetime.fromisoformat(e["queued_at"].replace("Z", "+00:00"))
            for e in pending
        )
        age_hours = (datetime.now(timezone.utc) - oldest_ts).total_seconds() / 3600

        # Calculate average confidence
        avg_conf = sum(e["confidence"]["overall"] for e in pending) / len(pending)

        # Determine health
        health = "good"
        if len(pending) > 10 or age_hours > 72:
            health = "critical"
        elif len(pending) > 5 or age_hours > 24:
            health = "warning"

        return {
            "total_pending": len(pending),
            "oldest_age_hours": age_hours,
            "avg_confidence": avg_conf,
            "health": health,
        }

    def _validate_entry(self, entry: Dict[str, Any], line_num: int) -> None:
        """Validate queue entry structure."""
        required_keys = ["patch_path", "confidence", "queued_at"]
        for key in required_keys:
            if key not in entry:
                raise KeyError(f"Missing required key '{key}' at line {line_num}")

        # Validate confidence structure
        conf_keys = ["overall", "tests_passed", "lint_passed"]
        for key in conf_keys:
            if key not in entry["confidence"]:
                raise KeyError(f"Missing confidence key '{key}' at line {line_num}")

    def _update_status(self, patch_path: str, status: str, metadata: Dict) -> None:
        """Update entry status in queue atomically.

        Pattern: EXEC-004 - Atomic file operation
        - Read all entries
        - Update in memory
        - Write to temp file
        - Atomic rename
        """
        if not self.queue_path.exists():
            raise FileNotFoundError(f"Queue file not found: {self.queue_path}")

        # Read all entries
        entries = []
        found = False

        with open(self.queue_path, "r", encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line)
                if entry["patch_path"] == patch_path:
                    entry["status"] = status
                    entry.update(metadata)
                    found = True
                entries.append(entry)

        if not found:
            raise ValueError(f"Patch not found in queue: {patch_path}")

        # Write to temporary file
        temp_fd, temp_path = tempfile.mkstemp(
            dir=self.queue_path.parent, prefix=".queue_", suffix=".tmp"
        )

        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                for entry in entries:
                    f.write(json.dumps(entry) + "\n")

            # Atomic rename
            shutil.move(temp_path, self.queue_path)

        except Exception:
            # Clean up temp file on error
            try:
                os.unlink(temp_path)
            except Exception:
                pass
            raise
