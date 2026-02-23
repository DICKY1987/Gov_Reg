"""Argparse command extractor.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class ArgparseCommand:
    name: str
    help: Optional[str]
    lineno: int


class ArgparseExtractor(ast.NodeVisitor):
    """Extract argparse subcommands via AST traversal."""

    def __init__(self) -> None:
        self.parser_names = set()
        self.subparser_names = set()
        self.commands: List[ArgparseCommand] = []

    def visit_Assign(self, node: ast.Assign) -> None:
        if isinstance(node.value, ast.Call):
            func_name = self._get_func_name(node.value.func)
            if func_name.endswith("ArgumentParser"):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.parser_names.add(target.id)
            if isinstance(node.value.func, ast.Attribute):
                if node.value.func.attr == "add_subparsers":
                    base_name = self._get_base_name(node.value.func.value)
                    if base_name in self.parser_names:
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                self.subparser_names.add(target.id)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Attribute) and node.func.attr == "add_parser":
            base_name = self._get_base_name(node.func.value)
            if base_name in self.subparser_names:
                cmd_name = self._get_str_arg(node)
                help_text = self._get_kwarg_str(node, "help")
                if cmd_name:
                    self.commands.append(ArgparseCommand(cmd_name, help_text, node.lineno))
        self.generic_visit(node)

    @staticmethod
    def _get_func_name(node: ast.expr) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return ast.unparse(node)
        return ast.unparse(node)

    @staticmethod
    def _get_base_name(node: ast.expr) -> Optional[str]:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return None

    @staticmethod
    def _get_str_arg(node: ast.Call) -> Optional[str]:
        if not node.args:
            return None
        try:
            value = ast.literal_eval(node.args[0])
        except Exception:
            return None
        return value if isinstance(value, str) else None

    @staticmethod
    def _get_kwarg_str(node: ast.Call, key: str) -> Optional[str]:
        for kw in node.keywords:
            if kw.arg == key:
                try:
                    value = ast.literal_eval(kw.value)
                except Exception:
                    return None
                return value if isinstance(value, str) else None
        return None


def extract_argparse_commands(source_text: str) -> List[ArgparseCommand]:
    """Extract argparse subcommands from source text."""
    tree = ast.parse(source_text)
    extractor = ArgparseExtractor()
    extractor.visit(tree)
    return sorted(extractor.commands, key=lambda c: (c.lineno, c.name))
