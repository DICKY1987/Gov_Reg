# DOC_LINK: DOC-CORE-CORE-PANEL-REGISTRY-121
"""Panel registry for managing available panels.

Provides registration and lookup for panel plugins.
"""

# DOC_ID: DOC-CORE-CORE-PANEL-REGISTRY-121

from typing import Callable, Dict, Optional, Type

from .panel_plugin import PanelPlugin


class PanelRegistry:
    """Registry for managing panel plugins."""

    def __init__(self):
        self._panels: Dict[str, Type[PanelPlugin]] = {}

    def register(self, panel_id: str, panel_class: Type[PanelPlugin]) -> None:
        """Register a panel plugin.

        Args:
            panel_id: Unique identifier for the panel
            panel_class: Panel class implementing PanelPlugin protocol
        """
        self._panels[panel_id] = panel_class

    def get(self, panel_id: str) -> Optional[Type[PanelPlugin]]:
        """Get panel class by ID.

        Args:
            panel_id: Panel identifier

        Returns:
            Panel class if found, None otherwise
        """
        return self._panels.get(panel_id)

    def list_panels(self) -> list[str]:
        """List all registered panel IDs.

        Returns:
            List of panel identifiers
        """
        return list(self._panels.keys())

    def create_panel(self, panel_id: str) -> Optional[PanelPlugin]:
        """Create a panel instance by ID.

        Args:
            panel_id: Panel identifier

        Returns:
            Panel instance if panel_id is registered, None otherwise
        """
        panel_class = self.get(panel_id)
        if panel_class:
            return panel_class()
        return None


# Global registry instance
_registry = PanelRegistry()


def register_panel(panel_id: str) -> Callable:
    """Decorator for registering panel classes.

    Args:
        panel_id: Unique identifier for the panel

    Returns:
        Decorator function

    Example:
        @register_panel("dashboard")
        class DashboardPanel:
            ...
    """

    def decorator(cls: Type[PanelPlugin]) -> Type[PanelPlugin]:
        _registry.register(panel_id, cls)
        return cls

    return decorator


def get_registry() -> PanelRegistry:
    """Get the global panel registry.

    Returns:
        Global PanelRegistry instance
    """
    return _registry
