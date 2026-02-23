#!/usr/bin/env python3
"""
Capability Tagger - Metadata Script
Produces: py_capability_tags

Tags files with capabilities they provide (e.g., "data_processing", "api", "cli", "testing").
"""
import ast
import json
import sys
from pathlib import Path
from typing import List, Set, Dict, Any


# Capability detection patterns
CAPABILITY_PATTERNS = {
    "data_processing": {
        "imports": ["pandas", "numpy", "polars", "csv", "json"],
        "keywords": ["dataframe", "array", "matrix", "dataset"],
    },
    "api": {
        "imports": ["fastapi", "flask", "django", "starlette", "aiohttp"],
        "keywords": ["@app.route", "@router", "APIRouter", "endpoint"],
    },
    "cli": {
        "imports": ["argparse", "click", "typer"],
        "keywords": ["if __name__", "main()", "ArgumentParser", "command"],
    },
    "database": {
        "imports": ["sqlite3", "psycopg2", "pymongo", "sqlalchemy", "peewee"],
        "keywords": ["query", "cursor", "execute", "commit", "connection"],
    },
    "testing": {
        "imports": ["pytest", "unittest", "nose", "testtools"],
        "keywords": ["test_", "assert", "mock", "fixture"],
    },
    "async": {
        "imports": ["asyncio", "aiohttp", "aiofiles"],
        "keywords": ["async def", "await", "asyncio.run"],
    },
    "ml_ai": {
        "imports": ["sklearn", "tensorflow", "torch", "keras", "transformers"],
        "keywords": ["model", "train", "predict", "fit", "neural"],
    },
    "web_scraping": {
        "imports": ["requests", "beautifulsoup4", "scrapy", "selenium"],
        "keywords": ["scrape", "parse", "extract", "crawl"],
    },
    "file_io": {
        "imports": ["pathlib", "os", "shutil", "io"],
        "keywords": ["open(", "read", "write", "file", "path"],
    },
    "logging": {
        "imports": ["logging", "loguru"],
        "keywords": ["logger", "log.", "debug", "info", "warning", "error"],
    },
    "configuration": {
        "imports": ["configparser", "yaml", "toml", "json"],
        "keywords": ["config", "settings", "configuration", "environment"],
    },
    "security": {
        "imports": ["hashlib", "hmac", "secrets", "cryptography", "jwt"],
        "keywords": ["encrypt", "decrypt", "hash", "token", "auth"],
    },
}


class CapabilityDetector(ast.NodeVisitor):
    """Detect capabilities from AST."""

    def __init__(self, source_text: str):
        self.source_text = source_text
        self.imports = set()
        self.keywords_found = set()

    def visit_Import(self, node: ast.Import):
        """Track imports."""
        for alias in node.names:
            self.imports.add(alias.name.split(".")[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Track from imports."""
        if node.module:
            self.imports.add(node.module.split(".")[0])
        self.generic_visit(node)


def detect_capabilities(file_path: Path) -> Set[str]:
    """
    Detect capabilities in a Python file.

    Returns set of capability tags.
    """
    try:
        source_text = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source_text, filename=str(file_path))

        detector = CapabilityDetector(source_text)
        detector.visit(tree)

        capabilities = set()

        # Check each capability pattern
        for capability, patterns in CAPABILITY_PATTERNS.items():
            matched = False

            # Check import matches
            for import_pattern in patterns.get("imports", []):
                if import_pattern in detector.imports:
                    matched = True
                    break

            # Check keyword matches
            if not matched:
                for keyword in patterns.get("keywords", []):
                    if keyword.lower() in source_text.lower():
                        matched = True
                        break

            if matched:
                capabilities.add(capability)

        return capabilities

    except Exception:
        return set()


def tag_file_capabilities(file_path: Path) -> dict:
    """
    Tag a file with capability labels.

    Returns dict with:
    - py_capability_tags: List[str]
    - success: bool
    - error: Optional[str]
    """
    try:
        capabilities = detect_capabilities(file_path)

        return {
            "py_capability_tags": sorted(list(capabilities)),
            "success": True,
            "error": None,
        }

    except Exception as e:
        return {
            "py_capability_tags": [],
            "success": False,
            "error": f"Capability tagging failed: {e}",
        }


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: capability_tagger.py <file_path>", file=sys.stderr)
        sys.exit(1)

    file_path = Path(sys.argv[1])

    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    result = tag_file_capabilities(file_path)

    if result["success"]:
        print(f"Capabilities: {', '.join(result['py_capability_tags'])}")
        print(json.dumps(result, indent=2))
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
