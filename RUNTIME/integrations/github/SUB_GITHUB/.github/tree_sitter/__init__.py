# DOC_LINK: DOC-PAT-TREE-SITTER-INIT-371
# DOC_LINK: DOC-PAT-TREE-SITTER-INIT-327
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional


@dataclass
class Node:
    type: str = "ROOT"
    start_point: tuple[int, int] = (0, 0)
    end_point: tuple[int, int] = (0, 0)
    children: List["Node"] = None
    has_error: bool = False
    is_missing: bool = False

    def __post_init__(self):
        if self.children is None:
            self.children = []


class Tree:
    def __init__(self, text: str = "") -> None:
        self.text = text
        self.root_node = Node()


class Language:
    def __init__(self, name: str = "generic") -> None:
        self.name = name


class Parser:
    def __init__(self, language: Language) -> None:
        self.language = language

    def parse(self, source: bytes) -> Tree:
        text = source.decode("utf-8") if isinstance(source, (bytes, bytearray)) else str(source)
        return Tree(text)


__all__ = ["Language", "Parser", "Tree", "Node"]
