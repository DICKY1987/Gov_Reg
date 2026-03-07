#!/usr/bin/env python3
"""
Text Normalizer - Phase A Core Script
Produces: py_canonical_text_hash, py_encoding_detected, py_newline_style

Deterministic text normalization with canonical encoding detection.
Stdlib-only implementation with defined fallback sequence.
"""
import hashlib
import sys
from pathlib import Path
from typing import Tuple, Optional


def detect_encoding(raw_bytes: bytes) -> Tuple[str, str]:
    """
    Detect encoding using deterministic fallback sequence.

    Returns: (encoding_name, confidence_level)
    Raises: UnicodeDecodeError if all methods fail
    """
    # Try UTF-8 with BOM
    if raw_bytes.startswith(b"\xef\xbb\xbf"):
        try:
            raw_bytes[3:].decode("utf-8")
            return ("utf-8-sig", "high")
        except UnicodeDecodeError:
            pass

    # Try UTF-8 (most common for Python)
    try:
        raw_bytes.decode("utf-8")
        return ("utf-8", "high")
    except UnicodeDecodeError:
        pass

    # Try Latin-1 (always succeeds but may be wrong)
    try:
        raw_bytes.decode("latin-1")
        return ("latin-1", "low")
    except UnicodeDecodeError:
        pass

    # Try Windows CP-1252
    try:
        raw_bytes.decode("cp1252")
        return ("cp1252", "low")
    except UnicodeDecodeError:
        pass

    # Try ISO-8859-1 (similar to Latin-1)
    try:
        raw_bytes.decode("iso-8859-1")
        return ("iso-8859-1", "low")
    except UnicodeDecodeError:
        pass

    # Fail-fast: undetectable encoding
    raise UnicodeDecodeError(
        "unknown",
        raw_bytes[:100],
        0,
        len(raw_bytes[:100]),
        "All encoding detection methods failed",
    )


def detect_newline_style(text: str) -> str:
    """
    Detect predominant newline style.

    Returns: 'CRLF', 'LF', 'CR', or 'MIXED'
    """
    crlf_count = text.count("\r\n")
    lf_count = text.count("\n") - crlf_count
    cr_count = text.count("\r") - crlf_count

    total = crlf_count + lf_count + cr_count
    if total == 0:
        return "NONE"

    # Check for mixed (no single style dominates)
    styles = sum([crlf_count > 0, lf_count > 0, cr_count > 0])
    if styles > 1:
        return "MIXED"

    if crlf_count > 0:
        return "CRLF"
    elif lf_count > 0:
        return "LF"
    else:
        return "CR"


def normalize_text(text: str) -> str:
    """
    Normalize text to canonical form:
    - Strip BOM if present
    - Normalize all newlines to LF
    - Strip trailing whitespace per line
    - Ensure single trailing newline
    """
    # Remove BOM if present
    if text.startswith("\ufeff"):
        text = text[1:]

    # Normalize newlines to LF
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Strip trailing whitespace per line
    lines = text.split("\n")
    lines = [line.rstrip() for line in lines]

    # Ensure single trailing newline
    text = "\n".join(lines)
    if text and not text.endswith("\n"):
        text += "\n"

    return text


def compute_canonical_hash(text: str) -> str:
    """
    Compute SHA-256 hash of canonical text.

    Uses UTF-8 encoding (deterministic).
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def analyze_file(file_path: Path) -> dict:
    """
    Analyze a single file and return normalization results.

    Returns dict with:
    - py_canonical_text_hash: str
    - py_encoding_detected: str
    - py_newline_style: str
    - success: bool
    - error: Optional[str]
    """
    try:
        raw_bytes = file_path.read_bytes()

        # Detect encoding
        encoding, confidence = detect_encoding(raw_bytes)

        # Decode text
        text = raw_bytes.decode(encoding)

        # Detect original newline style
        newline_style = detect_newline_style(text)

        # Normalize text
        normalized = normalize_text(text)

        # Compute hash
        text_hash = compute_canonical_hash(normalized)

        return {
            "py_canonical_text_hash": text_hash,
            "py_encoding_detected": encoding,
            "py_newline_style": newline_style,
            "success": True,
            "error": None,
        }

    except UnicodeDecodeError as e:
        return {
            "py_canonical_text_hash": None,
            "py_encoding_detected": "UNKNOWN",
            "py_newline_style": "UNKNOWN",
            "success": False,
            "error": f"Encoding detection failed: {e}",
        }

    except Exception as e:
        return {
            "py_canonical_text_hash": None,
            "py_encoding_detected": "ERROR",
            "py_newline_style": "ERROR",
            "success": False,
            "error": f"Normalization failed: {e}",
        }


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: text_normalizer.py <file_path>", file=sys.stderr)
        sys.exit(1)

    file_path = Path(sys.argv[1])

    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    result = analyze_file(file_path)
    
    # Handle --json flag
    if '--json' in sys.argv:
        idx = sys.argv.index('--json')
        out_path = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
        if out_path:
            with open(out_path, 'w') as f:
                json.dump(result, f, indent=2, sort_keys=True)
        else:
            print(json.dumps(result, indent=2, sort_keys=True))
        sys.exit(0)

    if result["success"]:
        print(f"Hash: {result['py_canonical_text_hash']}")
        print(f"Encoding: {result['py_encoding_detected']}")
        print(f"Newlines: {result['py_newline_style']}")
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
