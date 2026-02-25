"""
Text Normalizer for mapp_py Analysis Pipeline

Normalizes Python source code encoding and formatting for deterministic hashing.

Technical Specs:
- Python: 3.9+
- Input: bytes | str (raw source code)
- Output: NormalizedText with canonical hash
- Thread-safe: Yes
- Stdlib only: Yes

Author: mapp_py system
Version: 1.0.0
"""

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import List, Union


@dataclass
class NormalizedText:
    """Result of text normalization."""

    normalized: str
    canonical_hash: str
    changes_made: List[str]
    original_encoding: str


class TextNormalizer:
    """Normalizes text encoding and formatting for deterministic hashing."""

    def __init__(self):
        """Initialize text normalizer."""
        pass

    def normalize(self, source: Union[bytes, str, Path]) -> NormalizedText:
        """
        Normalize source code for deterministic hashing.

        Args:
            source: Raw source as bytes, str, or Path to file

        Returns:
            NormalizedText with normalized content and hash

        Raises:
            UnicodeDecodeError: If encoding cannot be detected
            ValueError: If source is binary file
        """
        changes = []

        # Handle Path input
        if isinstance(source, Path):
            with open(source, "rb") as f:
                source = f.read()

        # Detect and convert encoding
        if isinstance(source, bytes):
            text, encoding = self.normalize_encoding(source)
            changes.append(f"decoded from {encoding}")
        else:
            text = source
            encoding = "utf-8 (assumed)"

        # Remove BOM if present
        if text.startswith("\ufeff"):
            text = text[1:]
            changes.append("removed BOM")

        # Normalize newlines
        original_newlines = self._detect_newline_style(text)
        text = self.normalize_newlines(text)
        if original_newlines != "LF":
            changes.append(f"normalized newlines ({original_newlines}->LF)")

        # Strip trailing whitespace per line
        lines = text.split("\n")
        original_lines = len(lines)
        lines = [line.rstrip() for line in lines]
        if any(len(line) != len(orig) for line, orig in zip(lines, text.split("\n"))):
            changes.append("stripped trailing whitespace")

        # Ensure file ends with single newline
        text = "\n".join(lines)
        if not text.endswith("\n"):
            text += "\n"
            changes.append("added final newline")
        elif text.endswith("\n\n"):
            text = text.rstrip("\n") + "\n"
            changes.append("removed extra final newlines")

        # Calculate canonical hash
        canonical_hash = self.calculate_canonical_hash(text)

        return NormalizedText(
            normalized=text,
            canonical_hash=canonical_hash,
            changes_made=changes if changes else ["no changes needed"],
            original_encoding=encoding,
        )

    def normalize_encoding(self, source: bytes) -> tuple[str, str]:
        """
        Convert bytes to UTF-8 string.

        Args:
            source: Raw bytes

        Returns:
            Tuple of (decoded string, detected encoding)

        Raises:
            UnicodeDecodeError: If cannot decode
            ValueError: If appears to be binary file
        """
        # Check for binary content (high proportion of non-text bytes)
        sample = source[:1024] if len(source) > 1024 else source
        non_text_bytes = sum(1 for b in sample if b < 32 and b not in (9, 10, 13))
        if non_text_bytes > len(sample) * 0.1:
            raise ValueError("Appears to be binary file (too many non-text bytes)")

        # Try UTF-8 first (most common)
        try:
            return source.decode("utf-8"), "utf-8"
        except UnicodeDecodeError:
            pass

        # Try UTF-8 with BOM
        try:
            if source.startswith(b"\xef\xbb\xbf"):
                return source.decode("utf-8-sig"), "utf-8-sig"
        except UnicodeDecodeError:
            pass

        # Try common encodings
        for encoding in ["latin-1", "cp1252", "iso-8859-1"]:
            try:
                return source.decode(encoding), encoding
            except (UnicodeDecodeError, LookupError):
                continue

        # Last resort: try UTF-8 with replace
        return source.decode("utf-8", errors="replace"), "utf-8 (with replacements)"

    def normalize_newlines(self, text: str) -> str:
        """
        Normalize all newlines to LF (Unix style).

        Args:
            text: Source text

        Returns:
            Text with LF newlines only
        """
        # CRLF -> LF
        text = text.replace("\r\n", "\n")
        # CR -> LF
        text = text.replace("\r", "\n")
        return text

    def calculate_canonical_hash(self, text: str) -> str:
        """
        Calculate SHA256 hash of normalized text.

        Args:
            text: Normalized text

        Returns:
            64-character hex hash
        """
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _detect_newline_style(self, text: str) -> str:
        """Detect predominant newline style."""
        crlf_count = text.count("\r\n")
        lf_count = text.count("\n") - crlf_count
        cr_count = text.count("\r") - crlf_count

        if crlf_count > max(lf_count, cr_count):
            return "CRLF"
        elif cr_count > max(lf_count, crlf_count):
            return "CR"
        else:
            return "LF"


def normalize_file(file_path: Union[str, Path]) -> NormalizedText:
    """
    Convenience function to normalize a file.

    Args:
        file_path: Path to Python source file

    Returns:
        NormalizedText result
    """
    normalizer = TextNormalizer()
    return normalizer.normalize(Path(file_path))


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python text_normalizer.py <file.py>")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    result = normalize_file(file_path)
    print(f"File: {file_path}")
    print(f"Original encoding: {result.original_encoding}")
    print(f"Changes: {', '.join(result.changes_made)}")
    print(f"Canonical hash: {result.canonical_hash}")
    print(f"Normalized length: {len(result.normalized)} characters")
