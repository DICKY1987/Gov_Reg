"""Analyzer interface and adapter implementations for the consolidated pipeline.

This module defines a common `Analyzer` protocol along with a `FileContext` helper
type that is constructed once per file.  Each analyzer implements the
`run` method, consumes the pre‑parsed context, and returns a structured
`AnalyzerResult` describing its output.  Adapters for the existing
dependency, I/O surface, deliverable, complexity and semantic analyzers
wrap the legacy functions so they can be used interchangeably within
the new pipeline.
"""

from __future__ import annotations

import ast
import datetime
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

# Import legacy analyzer functions.  These modules must be present in
# the environment; adapters will gracefully fail if they cannot parse
# the input file.
from P_01260202173939000063_dependency_analyzer import analyze_dependencies
from P_01260202173939000064_i_o_surface_visitor import analyze_io_surface
from P_01260202173939000065_deliverable_analyzer import analyze_deliverable
from P_01260202173939000071_complexity_visitor import analyze_complexity
from P_01260202173939000067_extract_semantic_features import extract_semantic_features


@dataclass
class AnalyzerResult:
    """Container for analyzer outputs.

    Attributes
    ----------
    analyzer_id: str
        Unique identifier of the analyzer producing this result.
    analyzer_version: str
        Version string of the analyzer implementation.
    deterministic: bool
        Whether this analyzer produces deterministic outputs suitable for
        inclusion in the facts hash.
    output: Dict[str, Any]
        A mapping of high level field name to extracted data.  Each
        adapter returns a nested dictionary keyed by the top level
        category (e.g. ``imports``, ``io_surface``).
    success: bool
        Indicates whether the analysis completed successfully.
    error: Optional[str]
        An error message when ``success`` is False.
    """

    analyzer_id: str
    analyzer_version: str
    deterministic: bool
    output: Dict[str, Any]
    success: bool = True
    error: Optional[str] = None


class Analyzer(Protocol):
    """Protocol for all analyzers used by the consolidated pipeline.

    Every analyzer must declare a stable identifier and version along
    with whether it produces deterministic facts.  The ``provides``
    attribute lists the top level fields (relative to the ``facts``
    object) that the analyzer produces.  The ``run`` method accepts a
    ``FileContext`` and returns an ``AnalyzerResult``.  Implementers
    should catch their own exceptions and set ``success`` and ``error``
    accordingly.
    """

    analyzer_id: str
    analyzer_version: str
    deterministic: bool
    provides: List[str]

    def run(self, ctx: "FileContext") -> AnalyzerResult:
        ...


@dataclass
class FileContext:
    """Lightweight object representing a single file under analysis.

    ``FileContext`` is responsible for computing basic metadata such
    as relative paths, content hashes, modification times, and for
    parsing Python source into an AST.  Other analyzers may reuse the
    parsed AST and source text to avoid redundant work.
    """

    file_path: Path
    repo_root: Path
    path_rel: Path
    ext: str
    size_bytes: int
    mtime_utc: str
    content_sha256: str
    source_text: Optional[str]
    ast_tree: Optional[ast.AST]

    @classmethod
    def from_path(cls, file_path: Path, repo_root: Path) -> "FileContext":
        """Construct a ``FileContext`` from a file on disk.

        Parameters
        ----------
        file_path: Path
            Absolute path to the file being analyzed.
        repo_root: Path
            Absolute path to the repository root.  Relative paths are
            computed against this location.
        """
        file_path = file_path.resolve()
        repo_root = repo_root.resolve()
        try:
            path_rel = file_path.relative_to(repo_root)
        except ValueError:
            # If file is not under repo_root we still store the basename
            path_rel = Path(file_path.name)

        stat = file_path.stat()
        size_bytes = stat.st_size
        mtime = datetime.datetime.fromtimestamp(stat.st_mtime, tz=datetime.timezone.utc)
        mtime_utc = mtime.isoformat()
        content_sha256 = hashlib.sha256(file_path.read_bytes()).hexdigest()
        ext = file_path.suffix.lower()

        source_text: Optional[str] = None
        ast_tree: Optional[ast.AST] = None
        if ext == ".py":
            try:
                source_text = file_path.read_text(encoding="utf-8")
                ast_tree = ast.parse(source_text, filename=str(file_path))
            except Exception:
                # Leave source_text and ast_tree as None on failure
                source_text = None
                ast_tree = None

        return cls(
            file_path=file_path,
            repo_root=repo_root,
            path_rel=path_rel,
            ext=ext,
            size_bytes=size_bytes,
            mtime_utc=mtime_utc,
            content_sha256=content_sha256,
            source_text=source_text,
            ast_tree=ast_tree,
        )


class DependencyAnalyzerAdapter:
    """Adapter for the legacy dependency analyzer.

    Produces a nested dictionary under the ``imports`` key containing the
    full import list, its canonical hash, and counts for stdlib,
    external and relative imports.
    """

    analyzer_id = "dependency"
    analyzer_version = "1.0"
    deterministic = True
    provides = ["imports"]

    def run(self, ctx: FileContext) -> AnalyzerResult:
        if ctx.ext != ".py":
            # Nothing to do for non‑Python files
            return AnalyzerResult(
                analyzer_id=self.analyzer_id,
                analyzer_version=self.analyzer_version,
                deterministic=self.deterministic,
                output={},
                success=True,
            )
        try:
            result = analyze_dependencies(ctx.file_path)
            if not result.get("success", False):
                return AnalyzerResult(
                    analyzer_id=self.analyzer_id,
                    analyzer_version=self.analyzer_version,
                    deterministic=self.deterministic,
                    output={},
                    success=False,
                    error=result.get("error"),
                )
            output = {
                "imports": {
                    "entries": result.get("py_imports_list", []),
                    "hash": result.get("py_imports_hash"),
                    "stdlib_count": result.get("py_stdlib_imports_count", 0),
                    "external_count": result.get("py_external_imports_count", 0),
                    "relative_count": result.get("py_relative_imports_count", 0),
                }
            }
            return AnalyzerResult(
                analyzer_id=self.analyzer_id,
                analyzer_version=self.analyzer_version,
                deterministic=self.deterministic,
                output=output,
            )
        except Exception as exc:
            return AnalyzerResult(
                analyzer_id=self.analyzer_id,
                analyzer_version=self.analyzer_version,
                deterministic=self.deterministic,
                output={},
                success=False,
                error=str(exc),
            )


class IOSurfaceAnalyzerAdapter:
    """Adapter for the legacy I/O surface analyzer.

    Produces a nested dictionary under the ``io_surface`` key containing
    file operations, network calls, security calls and a security
    surface hash.  Non‑Python files yield empty lists.
    """

    analyzer_id = "io_surface"
    analyzer_version = "1.0"
    deterministic = True
    provides = ["io_surface"]

    def run(self, ctx: FileContext) -> AnalyzerResult:
        if ctx.ext != ".py":
            # Nothing to do for non‑Python files
            return AnalyzerResult(
                analyzer_id=self.analyzer_id,
                analyzer_version=self.analyzer_version,
                deterministic=self.deterministic,
                output={},
                success=True,
            )
        try:
            # The visitor module expects a Path to the file.  It will
            # handle parsing internally.
            result = analyze_io_surface(ctx.file_path)
            if not result.get("success", False):
                return AnalyzerResult(
                    analyzer_id=self.analyzer_id,
                    analyzer_version=self.analyzer_version,
                    deterministic=self.deterministic,
                    output={},
                    success=False,
                    error=result.get("error"),
                )
            output = {
                "io_surface": {
                    "file_ops": result.get("py_file_operations_list", []),
                    "network_calls": result.get("py_network_calls_list", []),
                    "security_calls": result.get("py_security_calls_list", []),
                    "security_hash": result.get("py_security_surface_hash"),
                }
            }
            return AnalyzerResult(
                analyzer_id=self.analyzer_id,
                analyzer_version=self.analyzer_version,
                deterministic=self.deterministic,
                output=output,
            )
        except Exception as exc:
            return AnalyzerResult(
                analyzer_id=self.analyzer_id,
                analyzer_version=self.analyzer_version,
                deterministic=self.deterministic,
                output={},
                success=False,
                error=str(exc),
            )


class DeliverableAnalyzerAdapter:
    """Adapter for the deliverable analyzer.

    Produces a nested dictionary under the ``deliverable`` key
    containing the deliverable kind, interface signature and interface
    hash.  For non‑Python files the analyzer returns an empty output.
    """

    analyzer_id = "deliverable"
    analyzer_version = "1.0"
    deterministic = True
    provides = ["deliverable"]

    def run(self, ctx: FileContext) -> AnalyzerResult:
        if ctx.ext != ".py":
            return AnalyzerResult(
                analyzer_id=self.analyzer_id,
                analyzer_version=self.analyzer_version,
                deterministic=self.deterministic,
                output={},
                success=True,
            )
        try:
            result = analyze_deliverable(ctx.file_path)
            if not result.get("success", False):
                return AnalyzerResult(
                    analyzer_id=self.analyzer_id,
                    analyzer_version=self.analyzer_version,
                    deterministic=self.deterministic,
                    output={},
                    success=False,
                    error=result.get("error"),
                )
            output = {
                "deliverable": {
                    "kind": result.get("py_deliverable_kind"),
                    "interface_signature": result.get("py_interface_signature", {}),
                    "interface_hash": result.get("py_interface_hash"),
                }
            }
            return AnalyzerResult(
                analyzer_id=self.analyzer_id,
                analyzer_version=self.analyzer_version,
                deterministic=self.deterministic,
                output=output,
            )
        except Exception as exc:
            return AnalyzerResult(
                analyzer_id=self.analyzer_id,
                analyzer_version=self.analyzer_version,
                deterministic=self.deterministic,
                output={},
                success=False,
                error=str(exc),
            )


class ComplexityAnalyzerAdapter:
    """Adapter for the cyclomatic complexity analyzer.

    Produces a nested dictionary under the ``complexity`` key with
    average, max and total complexity.  On failure the result's
    ``success`` flag will be False.
    """

    analyzer_id = "complexity"
    analyzer_version = "1.0"
    deterministic = True
    provides = ["complexity"]

    def run(self, ctx: FileContext) -> AnalyzerResult:
        if ctx.ext != ".py":
            return AnalyzerResult(
                analyzer_id=self.analyzer_id,
                analyzer_version=self.analyzer_version,
                deterministic=self.deterministic,
                output={},
                success=True,
            )
        try:
            result = analyze_complexity(ctx.file_path)
            if not result.get("success", False):
                return AnalyzerResult(
                    analyzer_id=self.analyzer_id,
                    analyzer_version=self.analyzer_version,
                    deterministic=self.deterministic,
                    output={},
                    success=False,
                    error=result.get("error"),
                )
            output = {
                "complexity": {
                    "total": result.get("py_total_complexity"),
                    "average": result.get("py_cyclomatic_complexity"),
                    "max": result.get("py_max_complexity"),
                    "function_complexities": result.get("function_complexities", {}),
                }
            }
            return AnalyzerResult(
                analyzer_id=self.analyzer_id,
                analyzer_version=self.analyzer_version,
                deterministic=self.deterministic,
                output=output,
            )
        except Exception as exc:
            return AnalyzerResult(
                analyzer_id=self.analyzer_id,
                analyzer_version=self.analyzer_version,
                deterministic=self.deterministic,
                output={},
                success=False,
                error=str(exc),
            )


class SemanticSignatureAnalyzerAdapter:
    """Adapter for semantic signature extraction.

    Produces a nested dictionary under the ``semantic`` key with token
    frequencies, unique identifiers, unique strings and a signature
    hash.  This analyzer runs on Python files only.
    """

    analyzer_id = "semantic"
    analyzer_version = "1.0"
    deterministic = True
    provides = ["semantic"]

    def run(self, ctx: FileContext) -> AnalyzerResult:
        if ctx.ext != ".py":
            return AnalyzerResult(
                analyzer_id=self.analyzer_id,
                analyzer_version=self.analyzer_version,
                deterministic=self.deterministic,
                output={},
                success=True,
            )
        try:
            features = extract_semantic_features(ctx.file_path)
            if "error" in features:
                return AnalyzerResult(
                    analyzer_id=self.analyzer_id,
                    analyzer_version=self.analyzer_version,
                    deterministic=self.deterministic,
                    output={},
                    success=False,
                    error=features.get("error"),
                )
            # Build deterministic signature dict
            sig_dict = {
                "token_frequencies": features.get("token_frequencies", {}),
                "unique_identifiers": sorted(list(features.get("unique_identifiers", []))),
                "unique_strings": sorted(list(features.get("unique_strings", []))),
            }
            canonical = json.dumps(sig_dict, sort_keys=True, separators=(",", ":"))
            signature_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            sig_dict["signature_hash"] = signature_hash
            output = {"semantic": sig_dict}
            return AnalyzerResult(
                analyzer_id=self.analyzer_id,
                analyzer_version=self.analyzer_version,
                deterministic=self.deterministic,
                output=output,
            )
        except Exception as exc:
            return AnalyzerResult(
                analyzer_id=self.analyzer_id,
                analyzer_version=self.analyzer_version,
                deterministic=self.deterministic,
                output={},
                success=False,
                error=str(exc),
            )