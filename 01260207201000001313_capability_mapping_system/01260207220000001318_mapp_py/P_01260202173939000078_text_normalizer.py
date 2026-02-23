#!/usr/bin/env python3
"""
Text Normalizer for mapp_py Analysis Pipeline
Produces: py_text_normalized, py_canonical_text_hash

Deterministic text normalization with stable encoding detection.
Uses stdlib-only for maximum portability and reproducibility.
"""

import hashlib
import sys
from pathlib import Path
from typing import Tuple, Optional

# Encoding detection cascade (deterministic order)
ENCODING_CASCADE = [
    "utf-8",
    "utf-8-sig",  # UTF-8 with BOM
    "latin-1",
    "cp1252",  # Windows-1252
    "iso-8859-1",
]


def normalize_text(file_path: Path, strict_mode: bool = False) -> Tuple[str, str, bool]:
    """
    Normalize text file content with deterministic encoding detection.

    Args:
        file_path: Path to file to normalize
        strict_mode: If True, fail on encoding errors; if False, use replacement

    Returns:
        Tuple of (normalized_text, canonical_hash, success_flag)
    """
    raw_bytes = file_path.read_bytes()

    # Try encoding cascade
    decoded_text = None
    detected_encoding = None

    for encoding in ENCODING_CASCADE:
        try:
            decoded_text = raw_bytes.decode(encoding)
            detected_encoding = encoding
            break
        except UnicodeDecodeError:
            continue

    # Fallback handling
    if decoded_text is None:
        if strict_mode:
            raise UnicodeDecodeError(
                "cascade",
                raw_bytes,
                0,
                len(raw_bytes),
                f"Failed all encodings: {ENCODING_CASCADE}",
            )
        else:
            # Last resort: decode with replacement
            decoded_text = raw_bytes.decode("utf-8", errors="replace")
            detected_encoding = "utf-8-replacement"

    # Normalize line endings to \n
    normalized = decoded_text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove BOM if present (after decoding)
    if normalized.startswith("\ufeff"):
        normalized = normalized[1:]

    # Ensure single trailing newline
    normalized = normalized.rstrip("\n") + "\n" if normalized else "\n"

    # Compute canonical hash (stable: sort_keys not needed, separators explicit)
    canonical_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    return normalized, canonical_hash, True


def analyze_file(file_path: str, strict_mode: bool = False) -> dict:
    """
    Analyze a single file and return normalization results.

    Args:
        file_path: Path to Python file
        strict_mode: Whether to fail on encoding errors

    Returns:
        Dictionary with py_text_normalized and py_canonical_text_hash
    """
    path = Path(file_path)

    if not path.exists():
        return {
            "py_text_normalized": None,
            "py_canonical_text_hash": None,
            "error": f"File not found: {file_path}",
        }

    try:
        normalized, hash_val, success = normalize_text(path, strict_mode)

        return {
            "py_text_normalized": normalized,
            "py_canonical_text_hash": hash_val,
            "success": success,
        }

    except Exception as e:
        return {
            "py_text_normalized": None,
            "py_canonical_text_hash": None,
            "error": f"{type(e).__name__}: {str(e)}",
        }


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Normalize Python file text with deterministic encoding detection"
    )
    parser.add_argument("file_path", help="Path to Python file")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on encoding errors instead of using replacement",
    )
    parser.add_argument(
        "--output",
        choices=["hash", "text", "both"],
        default="both",
        help="What to output",
    )

    args = parser.parse_args()

    result = analyze_file(args.file_path, args.strict)

    if "error" in result:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        sys.exit(1)

    if args.output in ("hash", "both"):
        print(f"py_canonical_text_hash: {result['py_canonical_text_hash']}")

    if args.output in ("text", "both"):
        print(f"\npy_text_normalized:\n{result['py_text_normalized'][:500]}...")

    sys.exit(0)


if __name__ == "__main__":
    main()
