# DOC_LINK: DOC-CORE-SUB-GUI-EVENT-BUS-772
"""Compatibility shim exposing the event bus interface."""
# DOC_ID: DOC-CORE-SUB-GUI-EVENT-BUS-772

from core.events.event_bus import Event, EventBus, EventSeverity, EventType

__all__ = ["Event", "EventBus", "EventSeverity", "EventType"]
