# DOC_LINK: DOC-PAT-TEXTUAL-WIDGET-365
# DOC_LINK: DOC-PAT-TEXTUAL-WIDGET-321
from __future__ import annotations

from typing import List, Optional, Sequence


class Widget:
    def __init__(
        self,
        content: str | None = None,
        *,
        id: Optional[str] = None,
        classes: Sequence[str] | None = None,
    ) -> None:
        self.content = content or ""
        self.id = id
        self.classes = list(classes or [])
        self.children: List["Widget"] = []

    def mount(self, widget: "Widget") -> "Widget":
        self.children.append(widget)
        return widget

    def remove_children(self) -> None:
        self.children.clear()

    def __repr__(self) -> str:
        return f"<Widget id={self.id} classes={self.classes}>"
