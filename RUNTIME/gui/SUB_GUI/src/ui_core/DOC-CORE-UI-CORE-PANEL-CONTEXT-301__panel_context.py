# DOC_LINK: DOC-CORE-UI-CORE-PANEL-CONTEXT-301
"""Framework-agnostic panel context.

Defines the contract for panel contexts WITHOUT framework-specific imports.
This allows both TUI and GUI panels to share the same context type.
"""

# DOC_ID: DOC-CORE-UI-CORE-PANEL-CONTEXT-301

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class PanelEvent(Enum):
    """Events that can be emitted by panels."""

    MOUNTED = "mounted"
    UNMOUNTED = "unmounted"
    DATA_UPDATED = "data_updated"
    ERROR = "error"
    SELECTION_CHANGED = "selection_changed"


@dataclass
class PanelContext:
    """Context provided to panels for accessing shared resources.

    This is framework-agnostic - no Textual or Qt imports.
    """

    panel_id: str
    state_client: Optional[Any] = None  # Will be StateClient instance
    pattern_client: Optional[Any] = None  # Will be PatternClient instance
    config: Optional[Any] = None
    event_bus: Optional[Any] = None  # For future event pub/sub

    def emit_event(self, event: PanelEvent, data: Optional[dict] = None) -> None:
        """Emit an event from this panel."""
        # Placeholder for event emission logic
        pass
