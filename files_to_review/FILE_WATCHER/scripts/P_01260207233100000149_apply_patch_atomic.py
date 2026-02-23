#!/usr/bin/env python3
"""
apply_patch_atomic.py

Deterministic RFC-6902 patch applier for JSON files with:
- Optional preflight pointer checks
- Optional enforcement that patches include `test` ops
- JSON Schema validation on the final document
- Atomic write (temp file -> replace) + optional backup
- Patch generation (diff mode)
- Structured logging via structlog

Requires:
  pip install jsonschema jsonpatch structlog

Optional:
  pip install colorama  (for colored output on Windows)
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Dependency checks with helpful error messages
_MISSING_DEPS: List[str] = []

try:
    import jsonpatch
except ImportError:
    _MISSING_DEPS.append("jsonpatch")
    jsonpatch = None  # type: ignore

try:
    from jsonschema import Draft7Validator
except ImportError:
    _MISSING_DEPS.append("jsonschema")
    Draft7Validator = None  # type: ignore

try:
    import structlog
    _HAS_STRUCTLOG = True
except ImportError:
    _HAS_STRUCTLOG = False
    structlog = None  # type: ignore


__all__ = [
    "apply_patch",
    "enforce_patch_rules",
    "generate_patch",
    "get_parent_and_token",
    "load_json",
    "pointer_exists",
    "pointer_tokens",
    "preflight_pointer_checks",
    "save_json_atomic",
    "validate_schema",
]


# -----------------------------------------------------------------------------
# Exit codes (structured for pipeline integration)
# -----------------------------------------------------------------------------

class ExitCode:
    """Structured exit codes for deterministic error handling."""
    SUCCESS = 0
    FILE_ERROR = 1          # File not found, permission denied, JSON parse error
    VALIDATION_ERROR = 2    # Schema validation, type errors, rule violations
    PREFLIGHT_ERROR = 3     # Pointer doesn't exist (preflight check)
    PATCH_ERROR = 4         # Patch application failed
    DIFF_ERROR = 5          # Diff generation failed
    SYSTEM_ERROR = 99       # Unexpected errors


# -----------------------------------------------------------------------------
# Logging setup
# -----------------------------------------------------------------------------

def _configure_logging(verbose: bool = False, quiet: bool = False) -> Any:
    """
    Configure structured logging.

    Returns a logger instance (structlog if available, else a simple fallback).
    """
    if _HAS_STRUCTLOG and structlog is not None:
        # Configure structlog for console output
        structlog.configure(
            processors=[
                structlog.stdlib.add_log_level,
                structlog.processors.TimeStamper(fmt="ISO"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.dev.ConsoleRenderer(colors=True)
                if not quiet else structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(
                10 if verbose else 20 if not quiet else 40  # DEBUG=10, INFO=20, ERROR=40
            ),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
        return structlog.get_logger()
    else:
        # Fallback logger without structlog
        return _FallbackLogger(verbose=verbose, quiet=quiet)


class _FallbackLogger:
    """Simple fallback logger when structlog is not available."""

    def __init__(self, verbose: bool = False, quiet: bool = False):
        self._verbose = verbose
        self._quiet = quiet

    def _format(self, level: str, event: str, **kwargs: Any) -> str:
        ts = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        extra = " ".join(f"{k}={v!r}" for k, v in kwargs.items())
        return f"[{ts}] {level}: {event}" + (f" ({extra})" if extra else "")

    def debug(self, event: str, **kwargs: Any) -> None:
        if self._verbose:
            print(self._format("DEBUG", event, **kwargs))

    def info(self, event: str, **kwargs: Any) -> None:
        if not self._quiet:
            print(self._format("INFO", event, **kwargs))

    def warning(self, event: str, **kwargs: Any) -> None:
        if not self._quiet:
            print(self._format("WARN", event, **kwargs), file=sys.stderr)

    def error(self, event: str, **kwargs: Any) -> None:
        print(self._format("ERROR", event, **kwargs), file=sys.stderr)


# Module-level logger (configured in main())
_log: Any = _FallbackLogger()


# -----------------------------------------------------------------------------
# JSON Pointer helpers (RFC 6901)
# -----------------------------------------------------------------------------

def _unescape_token(tok: str) -> str:
    """RFC 6901: '~1' => '/', '~0' => '~' (order matters)."""
    return tok.replace("~1", "/").replace("~0", "~")


def _escape_token(tok: str) -> str:
    """RFC 6901: '~' => '~0', '/' => '~1' (order matters)."""
    return tok.replace("~", "~0").replace("/", "~1")


def pointer_tokens(ptr: str) -> List[str]:
    """
    Parse a JSON Pointer into its component tokens.

    Args:
        ptr: JSON Pointer string (e.g., "/foo/bar/0")

    Returns:
        List of unescaped tokens

    Raises:
        ValueError: If pointer is malformed
    """
    if ptr == "":
        return []
    if not ptr.startswith("/"):
        raise ValueError(f"Invalid JSON Pointer (must start with '/'): {ptr}")
    toks = ptr.split("/")[1:]
    return [_unescape_token(t) for t in toks]


def tokens_to_pointer(tokens: List[Union[str, int]]) -> str:
    """
    Convert a list of tokens back to a JSON Pointer string.

    Args:
        tokens: List of path components

    Returns:
        JSON Pointer string
    """
    if not tokens:
        return ""
    return "/" + "/".join(_escape_token(str(t)) for t in tokens)


def get_parent_and_token(doc: Any, ptr: str) -> Tuple[Any, str]:
    """
    Navigate to the parent container and return (parent, final_token).

    Args:
        doc: The JSON document
        ptr: JSON Pointer to resolve

    Returns:
        Tuple of (parent_container, final_token)

    Raises:
        ValueError: If pointer refers to root
        KeyError: If path doesn't exist
    """
    toks = pointer_tokens(ptr)
    if not toks:
        raise ValueError("Pointer refers to root; no parent/token.")

    parent_toks, last = toks[:-1], toks[-1]
    cur = doc

    for t in parent_toks:
        if isinstance(cur, dict):
            if t not in cur:
                raise KeyError(f"Pointer missing object key '{t}' in path '{ptr}'")
            cur = cur[t]
        elif isinstance(cur, list):
            if t == "-":
                raise KeyError(f"'-' is not valid in the middle of a pointer: {ptr}")
            try:
                idx = int(t)
            except ValueError:
                raise KeyError(f"Invalid array index '{t}' in pointer: {ptr}")
            if idx < 0 or idx >= len(cur):
                raise KeyError(f"Array index {idx} out of bounds in pointer: {ptr}")
            cur = cur[idx]
        else:
            raise KeyError(f"Pointer traversed non-container at token '{t}' for path '{ptr}'")

    return cur, last


def pointer_exists(doc: Any, ptr: str) -> bool:
    """
    Check whether a JSON Pointer path exists in the document.

    Args:
        doc: The JSON document
        ptr: JSON Pointer to check

    Returns:
        True if the pointer resolves to an existing value
    """
    if ptr == "":
        return True
    try:
        parent, tok = get_parent_and_token(doc, ptr)
        if isinstance(parent, dict):
            return tok in parent
        if isinstance(parent, list):
            if tok == "-":
                return False  # "-" refers to nonexistent end-of-array
            try:
                idx = int(tok)
                return 0 <= idx < len(parent)
            except ValueError:
                return False
        return False
    except (KeyError, ValueError, TypeError):
        return False


# -----------------------------------------------------------------------------
# File I/O with atomic write and Windows retry logic
# -----------------------------------------------------------------------------

def load_json(path: Path) -> Any:
    """
    Load and parse a JSON file.

    Args:
        path: Path to the JSON file

    Returns:
        Parsed JSON data

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _replace_with_retry(
    src: str,
    dst: Path,
    max_retries: int = 3,
    retry_delay: float = 0.1,
) -> None:
    """
    Replace destination file with source, with retry logic for Windows.

    On Windows, os.replace() fails if the target is open by another process.
    This function retries with exponential backoff.

    Args:
        src: Source file path (temp file)
        dst: Destination file path
        max_retries: Maximum retry attempts
        retry_delay: Initial delay between retries (doubles each attempt)
    """
    last_error: Optional[Exception] = None

    for attempt in range(max_retries + 1):
        try:
            os.replace(src, dst)
            return
        except PermissionError as e:
            last_error = e
            if attempt < max_retries:
                _log.debug(
                    "replace_retry",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    delay=retry_delay,
                )
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                raise OSError(
                    f"Failed to replace '{dst}' after {max_retries + 1} attempts. "
                    f"File may be locked by another process. Last error: {e}"
                ) from last_error


def save_json_atomic(
    path: Path,
    data: Any,
    backup_dir: Optional[Path] = None,
    indent: int = 2,
    sort_keys: bool = True,
    max_replace_retries: int = 3,
) -> Optional[Path]:
    """
    Atomically write JSON data to a file with optional backup.

    Uses temp file + rename pattern to prevent corruption on crash/interrupt.

    Args:
        path: Destination file path
        data: JSON-serializable data
        backup_dir: If provided, back up existing file before overwrite
        indent: JSON indentation (default: 2)
        sort_keys: Sort object keys (default: True for determinism)
        max_replace_retries: Retry attempts for Windows file locking

    Returns:
        Path to backup file if created, else None
    """
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    backup_path: Optional[Path] = None

    # Create backup if requested and file exists
    if backup_dir is not None and path.exists():
        backup_dir = Path(backup_dir).resolve()
        backup_dir.mkdir(parents=True, exist_ok=True)
        ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_path = backup_dir / f"{path.name}.{ts}.bak"
        shutil.copy2(path, backup_path)
        _log.debug("backup_created", backup_path=str(backup_path))

    # Write to temp file in same directory (ensures same filesystem for rename)
    tmp_fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )

    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, indent=indent, sort_keys=sort_keys)
            f.write("\n")  # Trailing newline
            f.flush()
            os.fsync(f.fileno())  # Force write to disk

        # Atomic replace with retry logic for Windows
        _replace_with_retry(tmp_name, path, max_retries=max_replace_retries)

    except Exception:
        # Clean up temp file on any error
        if os.path.exists(tmp_name):
            try:
                os.remove(tmp_name)
            except OSError:
                pass
        raise

    return backup_path


# -----------------------------------------------------------------------------
# Patch generation (diff mode)
# -----------------------------------------------------------------------------

def generate_patch(
    source: Any,
    target: Any,
    include_tests: bool = True,
) -> List[Dict[str, Any]]:
    """
    Generate an RFC-6902 patch that transforms source into target.

    Args:
        source: Original document
        target: Desired document
        include_tests: If True, prepend 'test' ops for modified values

    Returns:
        List of RFC-6902 patch operations
    """
    if jsonpatch is None:
        raise ImportError("jsonpatch is required for diff generation")

    # Generate basic patch
    patch = jsonpatch.make_patch(source, target)
    ops = list(patch)

    if not include_tests:
        return ops

    # Prepend test operations for paths being modified
    test_ops: List[Dict[str, Any]] = []
    for op in ops:
        op_type = op.get("op")
        path = op.get("path", "")

        if op_type in {"replace", "remove"}:
            # Add test for the value being replaced/removed
            if pointer_exists(source, path):
                try:
                    parent, tok = get_parent_and_token(source, path)
                    if isinstance(parent, dict) and tok in parent:
                        test_ops.append({
                            "op": "test",
                            "path": path,
                            "value": parent[tok],
                        })
                    elif isinstance(parent, list):
                        idx = int(tok)
                        if 0 <= idx < len(parent):
                            test_ops.append({
                                "op": "test",
                                "path": path,
                                "value": parent[idx],
                            })
                except (KeyError, ValueError, IndexError):
                    pass  # Skip test if we can't resolve

    return test_ops + ops


# -----------------------------------------------------------------------------
# Validation
# -----------------------------------------------------------------------------

def validate_schema(doc: Any, schema: Dict[str, Any], max_errors: int = 25) -> None:
    """
    Validate a document against a JSON Schema.

    Args:
        doc: The document to validate
        schema: JSON Schema dict
        max_errors: Maximum number of errors to report

    Raises:
        ValueError: If validation fails, with formatted error list
    """
    if Draft7Validator is None:
        raise ImportError("jsonschema is required for schema validation")

    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(doc), key=lambda e: list(e.path))

    if errors:
        lines = [f"Schema validation failed ({len(errors)} error(s)):"]
        for e in errors[:max_errors]:
            loc = "/" + "/".join(str(p) for p in e.path) if e.path else "(root)"
            lines.append(f"  - {loc}: {e.message}")
        if len(errors) > max_errors:
            lines.append(f"  ... and {len(errors) - max_errors} more errors")
        raise ValueError("\n".join(lines))


def enforce_patch_rules(
    patch_ops: List[Dict[str, Any]],
    require_test_ops: bool = False,
) -> None:
    """
    Enforce policy rules on a patch before applying.

    Args:
        patch_ops: List of RFC-6902 patch operations
        require_test_ops: If True, reject patches without 'test' operations

    Raises:
        ValueError: If patch violates rules
    """
    if not patch_ops:
        raise ValueError("Patch rejected: empty patch (no operations)")

    valid_ops = {"add", "remove", "replace", "move", "copy", "test"}
    for i, op in enumerate(patch_ops):
        op_type = op.get("op")
        if op_type not in valid_ops:
            raise ValueError(f"Patch rejected: op[{i}] has invalid 'op': {op_type!r}")
        if "path" not in op:
            raise ValueError(f"Patch rejected: op[{i}] missing required 'path' field")

    if require_test_ops:
        has_test = any(op.get("op") == "test" for op in patch_ops)
        if not has_test:
            raise ValueError(
                "Patch rejected: require_test_ops=True but no 'test' operations found. "
                "Add at least one 'test' op to verify preconditions."
            )


def preflight_pointer_checks(doc: Any, patch_ops: List[Dict[str, Any]]) -> None:
    """
    Validate pointer paths before applying patch.

    Catches common errors deterministically:
    - remove/replace/test must target an existing pointer
    - move/copy 'from' must exist

    Args:
        doc: The target document
        patch_ops: List of RFC-6902 patch operations

    Raises:
        KeyError: If a required pointer doesn't exist
    """
    must_exist_ops = {"remove", "replace", "test"}

    for i, op in enumerate(patch_ops):
        op_type = op.get("op")
        path = op.get("path", "")

        if op_type in must_exist_ops:
            if not pointer_exists(doc, path):
                raise KeyError(
                    f"Preflight failed: op[{i}] '{op_type}' path does not exist: {path}"
                )

        if op_type in {"move", "copy"}:
            from_path = op.get("from", "")
            if not from_path:
                raise KeyError(
                    f"Preflight failed: op[{i}] '{op_type}' missing required 'from' field"
                )
            if not pointer_exists(doc, from_path):
                raise KeyError(
                    f"Preflight failed: op[{i}] '{op_type}' from-path does not exist: {from_path}"
                )


def apply_patch(doc: Any, patch_ops: List[Dict[str, Any]]) -> Any:
    """
    Apply an RFC-6902 JSON Patch to a document.

    Args:
        doc: The target document
        patch_ops: List of RFC-6902 patch operations

    Returns:
        New document with patch applied (original unchanged)

    Raises:
        jsonpatch.JsonPatchException: If patch application fails
    """
    if jsonpatch is None:
        raise ImportError("jsonpatch is required for patch application")

    patch = jsonpatch.JsonPatch(patch_ops)
    return patch.apply(doc, in_place=False)


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

def _create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        description="Apply or generate RFC-6902 JSON Patches atomically with validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  Apply (default): Apply a patch file to a target JSON file
  Diff (--diff):   Generate a patch from two JSON files

Exit Codes:
  0  - Success
  1  - File error (not found, permission denied, invalid JSON)
  2  - Validation error (schema, type, rule violations)
  3  - Preflight error (pointer doesn't exist)
  4  - Patch application failed
  5  - Diff generation failed
  99 - Unexpected system error

Examples:
  # Apply a patch
  %(prog)s --target data.json --patch changes.json

  # Apply with schema validation and backup
  %(prog)s -t data.json -p changes.json -s schema.json -b ./backups

  # Dry run (validate without writing)
  %(prog)s -t data.json -p changes.json --dry-run

  # Require test operations for safety
  %(prog)s -t data.json -p changes.json --require-test-ops

  # Generate a patch (diff mode)
  %(prog)s --diff old.json new.json -o changes.json

  # Generate patch to stdout
  %(prog)s --diff old.json new.json

  # Write to different output file (not in-place)
  %(prog)s -t source.json -p patch.json -o result.json
""",
    )

    # Mode selection
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--diff",
        nargs=2,
        metavar=("SOURCE", "TARGET"),
        help="Generate patch from SOURCE to TARGET (diff mode)",
    )

    # Apply mode arguments
    apply_group = parser.add_argument_group("Apply mode options")
    apply_group.add_argument(
        "--target", "-t",
        type=Path,
        help="Target JSON file to patch (required for apply mode)",
    )
    apply_group.add_argument(
        "--patch", "-p",
        type=Path,
        help="RFC-6902 patch file (required for apply mode)",
    )
    apply_group.add_argument(
        "--require-test-ops",
        action="store_true",
        help="Reject patches without at least one 'test' operation",
    )
    apply_group.add_argument(
        "--no-preflight",
        action="store_true",
        help="Skip pointer existence preflight checks",
    )

    # Output options (shared)
    output_group = parser.add_argument_group("Output options")
    output_group.add_argument(
        "--output", "-o",
        type=Path,
        help="Output file (default: modify target in-place for apply, stdout for diff)",
    )
    output_group.add_argument(
        "--schema", "-s",
        type=Path,
        default=None,
        help="JSON Schema to validate result against",
    )
    output_group.add_argument(
        "--backup-dir", "-b",
        type=Path,
        default=None,
        help="Directory for backup files before overwrite",
    )
    output_group.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Validate only; do not write changes",
    )

    # Diff mode options
    diff_group = parser.add_argument_group("Diff mode options")
    diff_group.add_argument(
        "--no-test-ops",
        action="store_true",
        help="Don't include 'test' operations in generated patch",
    )

    # Logging options
    log_group = parser.add_argument_group("Logging options")
    log_group.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug logging",
    )
    log_group.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress non-error output",
    )

    return parser


def _run_apply_mode(args: argparse.Namespace) -> int:
    """Execute apply mode."""
    global _log

    if not args.target:
        _log.error("apply_mode_error", message="--target is required for apply mode")
        return ExitCode.VALIDATION_ERROR
    if not args.patch:
        _log.error("apply_mode_error", message="--patch is required for apply mode")
        return ExitCode.VALIDATION_ERROR

    # Load inputs
    _log.debug("loading_target", path=str(args.target))
    target_doc = load_json(args.target)

    _log.debug("loading_patch", path=str(args.patch))
    patch_ops = load_json(args.patch)

    if not isinstance(patch_ops, list):
        raise TypeError(
            f"Patch file must be a JSON array of operations (RFC-6902), "
            f"got {type(patch_ops).__name__}"
        )

    # Validate patch structure
    _log.debug("enforcing_patch_rules", require_test_ops=args.require_test_ops)
    enforce_patch_rules(patch_ops, require_test_ops=args.require_test_ops)

    # Preflight checks
    if not args.no_preflight:
        _log.debug("running_preflight_checks")
        preflight_pointer_checks(target_doc, patch_ops)

    # Apply patch
    _log.debug("applying_patch", op_count=len(patch_ops))
    updated_doc = apply_patch(target_doc, patch_ops)

    # Schema validation
    if args.schema is not None:
        _log.debug("validating_schema", schema=str(args.schema))
        schema_doc = load_json(args.schema)
        validate_schema(updated_doc, schema_doc)

    # Determine output path
    output_path = args.output if args.output else args.target

    # Dry run - don't write
    if args.dry_run:
        _log.info(
            "dry_run_ok",
            target=str(args.target),
            patch=str(args.patch),
            op_count=len(patch_ops),
            schema=str(args.schema) if args.schema else None,
            output=str(output_path),
        )
        return ExitCode.SUCCESS

    # Write atomically
    backup_path = save_json_atomic(
        output_path,
        updated_doc,
        backup_dir=args.backup_dir,
    )

    _log.info(
        "patch_applied",
        target=str(args.target),
        output=str(output_path),
        op_count=len(patch_ops),
        backup=str(backup_path) if backup_path else None,
    )

    return ExitCode.SUCCESS


def _run_diff_mode(args: argparse.Namespace) -> int:
    """Execute diff mode."""
    global _log

    source_path, target_path = Path(args.diff[0]), Path(args.diff[1])

    _log.debug("loading_source", path=str(source_path))
    source_doc = load_json(source_path)

    _log.debug("loading_target", path=str(target_path))
    target_doc = load_json(target_path)

    # Generate patch
    _log.debug("generating_patch", include_tests=not args.no_test_ops)
    patch_ops = generate_patch(
        source_doc,
        target_doc,
        include_tests=not args.no_test_ops,
    )

    if not patch_ops:
        _log.info("no_differences", source=str(source_path), target=str(target_path))
        # Still output empty array if output specified
        if args.output:
            save_json_atomic(args.output, [])
        else:
            print("[]")
        return ExitCode.SUCCESS

    # Schema validation on the target (optional)
    if args.schema is not None:
        _log.debug("validating_schema", schema=str(args.schema))
        schema_doc = load_json(args.schema)
        validate_schema(target_doc, schema_doc)

    # Output
    if args.dry_run:
        _log.info(
            "dry_run_ok",
            source=str(source_path),
            target=str(target_path),
            op_count=len(patch_ops),
        )
        return ExitCode.SUCCESS

    if args.output:
        save_json_atomic(args.output, patch_ops, backup_dir=args.backup_dir)
        _log.info(
            "patch_generated",
            source=str(source_path),
            target=str(target_path),
            output=str(args.output),
            op_count=len(patch_ops),
        )
    else:
        # Output to stdout
        print(json.dumps(patch_ops, indent=2, sort_keys=True))
        _log.info(
            "patch_generated",
            source=str(source_path),
            target=str(target_path),
            output="stdout",
            op_count=len(patch_ops),
        )

    return ExitCode.SUCCESS


def main(argv: Optional[List[str]] = None) -> int:
    """
    Main entry point.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:])

    Returns:
        Exit code (see ExitCode class)
    """
    global _log

    # Check dependencies
    if _MISSING_DEPS:
        print(
            f"ERROR: Missing required dependencies: {', '.join(_MISSING_DEPS)}\n"
            f"Install with: pip install {' '.join(_MISSING_DEPS)}",
            file=sys.stderr,
        )
        return ExitCode.SYSTEM_ERROR

    parser = _create_parser()
    args = parser.parse_args(argv)

    # Configure logging
    _log = _configure_logging(verbose=args.verbose, quiet=args.quiet)

    try:
        if args.diff:
            return _run_diff_mode(args)
        else:
            return _run_apply_mode(args)

    except FileNotFoundError as e:
        _log.error("file_not_found", message=str(e))
        return ExitCode.FILE_ERROR

    except json.JSONDecodeError as e:
        _log.error("json_parse_error", message=str(e), line=e.lineno, column=e.colno)
        return ExitCode.FILE_ERROR

    except PermissionError as e:
        _log.error("permission_denied", message=str(e))
        return ExitCode.FILE_ERROR

    except TypeError as e:
        _log.error("type_error", message=str(e))
        return ExitCode.VALIDATION_ERROR

    except ValueError as e:
        _log.error("validation_error", message=str(e))
        return ExitCode.VALIDATION_ERROR

    except KeyError as e:
        _log.error("preflight_error", message=str(e))
        return ExitCode.PREFLIGHT_ERROR

    except ImportError as e:
        _log.error("import_error", message=str(e))
        return ExitCode.SYSTEM_ERROR

    except Exception as e:
        if jsonpatch is not None and isinstance(e, jsonpatch.JsonPatchException):
            _log.error("patch_error", message=str(e))
            return ExitCode.PATCH_ERROR
        _log.error("unexpected_error", error_type=type(e).__name__, message=str(e))
        return ExitCode.SYSTEM_ERROR


if __name__ == "__main__":
    sys.exit(main())
