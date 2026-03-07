# DOC_LINK: DOC-PAT-TEXTUAL-APP-363
# DOC_LINK: DOC-PAT-TEXTUAL-APP-319
from __future__ import annotations

from typing import List, Optional

from textual.containers import Container
from textual.widget import Widget


class Stylesheet:
    def __init__(self) -> None:
        self.sources: List[str] = []

    def add_source(self, source: str) -> None:
        self.sources.append(source)


class ComposeResult(list):
    pass


class App:
    def __init__(self) -> None:
        self.stylesheet = Stylesheet()
        self.title: str = ""
        self.sub_title: str = ""
        self.mounts: List[Widget] = []

    def compose(self) -> ComposeResult:
        return ComposeResult()

    def run(self) -> None:
        self.compose()

    def action_refresh(self) -> None:
        pass

    def query_one(self, selector: str, widget_class: type[Widget]) -> Container:
        return Container()

    def exit(self, code: int = 0, message: Optional[str] = None) -> None:
        raise SystemExit(message or code)


__all__ = ["App", "ComposeResult"]
