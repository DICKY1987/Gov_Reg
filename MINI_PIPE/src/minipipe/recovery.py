"""Failure handling and retry orchestration (Phase 6 bridge)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional

from src.minipipe.scheduler import ExecutionScheduler, Task
from core.events.event_bus import EventBus, EventType


@dataclass
class RecoveryConfig:
    """Policy for retries after error recovery."""

    max_retries: int = 2
    backoff_strategy: Callable[[int], float] = staticmethod(lambda attempt: 0.0)


class RecoveryCoordinator:
    """Listens for TASK_FAILED and coordinates retries via Phase 6 outputs."""

    def __init__(
        self,
        scheduler: ExecutionScheduler,
        event_bus: EventBus,
        recovery_config: Optional[RecoveryConfig] = None,
    ):
        self.scheduler = scheduler
        self.event_bus = event_bus
        self.config = recovery_config or RecoveryConfig()
        self._subscribe()

    def _subscribe(self) -> None:
        self.event_bus.subscribe(EventType.TASK_FAILED, self._on_task_failed)
        self.event_bus.subscribe(EventType.FIX_APPLIED, self._on_fix_applied)

    def _on_task_failed(self, event) -> None:
        """Handle task failure by scheduling a retry if allowed."""
        payload = self._extract_payload(event)
        task_id = payload.get("task_id")
        if not task_id:
            return

        task = self.scheduler.get_task(task_id)
        if not task:
            return

        retries = int(task.metadata.get("retries", 0))
        if retries >= self.config.max_retries:
            return

        task.metadata["retries"] = retries + 1
        task.status = "pending"
        task.error = None

    def _on_fix_applied(self, event) -> None:
        """When a fix is applied, requeue dependent tasks if any."""
        payload = self._extract_payload(event)
        task_ids: Iterable[str] = payload.get("retry_task_ids", [])
        for task_id in task_ids:
            task = self.scheduler.get_task(task_id)
            if not task:
                continue
            task.status = "pending"
            task.error = None

    @staticmethod
    def _extract_payload(event) -> Dict[str, any]:
        """Support both Event objects and plain dict payloads."""
        if isinstance(event, dict):
            return event
        return getattr(event, "payload", {}) or {}


__all__ = ["RecoveryCoordinator", "RecoveryConfig"]
