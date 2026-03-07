# DOC_LINK: DOC-CORE-CORE-PANEL-PLUGIN-120
"""Panel plugin protocol and core types.

Defines the contract that all TUI panels must implement.
"""

# DOC_ID: DOC-CORE-CORE-PANEL-PLUGIN-120

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Protocol

from textual.widget import Widget


class PanelEvent(Enum):
    """Events that can be emitted by panels."""

    MOUNTED = "mounted"
    UNMOUNTED = "unmounted"
    DATA_UPDATED = "data_updated"
    ERROR = "error"
    SELECTION_CHANGED = "selection_changed"


@dataclass
class PanelContext:
    """Context provided to panels for accessing shared resources."""

    panel_id: str
    state_client: Optional[Any] = None  # Will be StateClient instance
    pattern_client: Optional[Any] = None  # Will be PatternClient instance
    config: Optional[Any] = None
    event_bus: Optional[Any] = None  # For future event pub/sub

    def emit_event(self, event: PanelEvent, data: Optional[dict] = None) -> None:
        """Emit an event from this panel."""
        # Placeholder for event emission logic
        pass


class PanelPlugin(Protocol):
    """Protocol that all TUI panels must implement.

    Panels are self-contained widgets that can be mounted in the TUI layout.
    They receive a PanelContext for accessing shared state and services.
    """

    @property
    def panel_id(self) -> str:
        """Unique identifier for this panel type."""
        ...

    @property
    def title(self) -> str:
        """Human-readable title for this panel."""
        ...

    def create_widget(self, context: PanelContext) -> Widget:
        """Create the Textual widget for this panel.

        Args:
            context: Panel context with state clients and config

        Returns:
            Textual Widget instance to be mounted in the layout
        """
        ...

    def on_mount(self, context: PanelContext) -> None:
        """Called when panel is mounted in the layout.

        Args:
            context: Panel context with state clients and config
        """
        ...

    def on_unmount(self, context: PanelContext) -> None:
        """Called when panel is unmounted from the layout.

        Args:
            context: Panel context with state clients and config
        """
        ...
