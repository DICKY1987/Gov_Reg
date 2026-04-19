#!/usr/bin/env python3
from __future__ import annotations

from typing import Any


def escape(token: str) -> str:
    return token.replace("~", "~0").replace("/", "~1")


def unescape(token: str) -> str:
    return token.replace("~1", "/").replace("~0", "~")


def pointer_get(document: Any, pointer: str) -> Any:
    if pointer == "":
        return document
    node = document
    for token in pointer.split("/")[1:]:
        key = unescape(token)
        if isinstance(node, list):
            node = node[int(key)]
        else:
            node = node[key]
    return node


def resolve_from_artifact(artifact: dict[str, Any], semantic_id: str) -> str:
    matches: list[str] = []
    for entries in artifact.get("maps", {}).values():
        if semantic_id in entries:
            matches.append(entries[semantic_id])
    if not matches:
        raise KeyError(f"Unknown semantic id: {semantic_id}")
    if len(matches) > 1:
        raise KeyError(f"Ambiguous semantic id: {semantic_id}")
    return matches[0]
