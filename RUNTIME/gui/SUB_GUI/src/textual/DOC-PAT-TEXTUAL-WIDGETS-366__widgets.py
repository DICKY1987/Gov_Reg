# DOC_LINK: DOC-PAT-TEXTUAL-WIDGETS-366
# DOC_LINK: DOC-PAT-TEXTUAL-WIDGETS-322
from __future__ import annotations

from typing import Any

from textual.widget import Widget


class Static(Widget):
    def update(self, text: str) -> None:
        self.content = text

    def set_interval(self, interval: float, callback: Any) -> None:
        # No-op interval handling in stub
        pass


class Header(Static):
    pass


class Footer(Static):
    pass


class DataTable(Widget):
    def __init__(
        self, *args: object, zebra_stripes: bool = False, **kwargs: object
    ) -> None:
        super().__init__(*args, **kwargs)
        self.zebra_stripes = zebra_stripes
        self.columns: list[str] = []
        self.rows: list[tuple[Any, ...]] = []
        self.cursor_type: str = "row"

    def add_columns(self, *columns: str) -> None:
        self.columns.extend(columns)

    def clear(self) -> None:
        self.rows.clear()

    def add_row(self, *values: Any) -> None:
        self.rows.append(tuple(values))
