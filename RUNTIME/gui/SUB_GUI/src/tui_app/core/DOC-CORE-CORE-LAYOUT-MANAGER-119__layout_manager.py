# DOC_LINK: DOC-CORE-CORE-LAYOUT-MANAGER-119
"""Layout manager for organizing panels in the TUI.

Manages panel mounting and layout configuration.
"""

# DOC_ID: DOC-CORE-CORE-LAYOUT-MANAGER-119

from typing import Optional

from textual.widget import Widget

from .panel_plugin import PanelContext, PanelPlugin


class BasicLayoutManager:
    """Simple layout manager that hosts a single panel.

    Designed to be extended for multi-panel split layouts in the future.
    """

    def __init__(self):
        self._current_panel: Optional[PanelPlugin] = None
        self._current_context: Optional[PanelContext] = None
        self._current_widget: Optional[Widget] = None

    def mount_panel(self, panel: PanelPlugin, context: PanelContext) -> Widget:
        """Mount a panel and get its widget.

        Args:
            panel: Panel plugin to mount
            context: Panel context with state clients

        Returns:
            Widget to be displayed in the app
        """
        # Unmount previous panel if any
        if self._current_panel and self._current_context:
            self._current_panel.on_unmount(self._current_context)

        # Mount new panel
        self._current_panel = panel
        self._current_context = context

        # Create widget
        widget = panel.create_widget(context)
        self._current_widget = widget

        # Call mount hook
        panel.on_mount(context)

        return widget

    def unmount_current(self) -> None:
        """Unmount the current panel."""
        if self._current_panel and self._current_context:
            self._current_panel.on_unmount(self._current_context)
            self._current_panel = None
            self._current_context = None
            self._current_widget = None

    def get_current_panel(self) -> Optional[PanelPlugin]:
        """Get the currently mounted panel.

        Returns:
            Current panel or None
        """
        return self._current_panel


class MultiPanelLayoutManager(BasicLayoutManager):
    """Layout manager for multi-panel split layouts (future extension).

    Supports rows, columns, and weighted splits.
    This is a placeholder for future implementation.
    """

    def __init__(self):
        super().__init__()
        # Future: self._layout_config, self._splits, etc.

    # Future methods:
    # - add_split(direction, weight)
    # - mount_panel_in_region(panel, region_id)
    # - link_panels(panel_ids, link_group_id)
