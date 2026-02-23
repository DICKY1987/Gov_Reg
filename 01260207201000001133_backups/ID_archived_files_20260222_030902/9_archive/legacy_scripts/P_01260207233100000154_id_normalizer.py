"""
ID Normalizer

Canonicalizes file_id format and merges duplicates deterministically.

Key Features:
1. Detect 19-digit file_ids (missing leading zero)
2. Generate canonical 20-digit form
3. Group duplicates by canonical form
4. Merge duplicates using deterministic priority
5. Generate RFC-6902 patches for fixes

Design Principle: NEVER cast file_id to int (preserves leading zeros)
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
from datetime import datetime


@dataclass
class IDNormalizationResult:
    """Result of ID normalization analysis."""

    canonical_id: str
    original_ids: List[str]
    is_duplicate: bool
    needs_normalization: bool
    canonical_record: Optional[Dict[str, Any]] = None
    superseded_records: List[Dict[str, Any]] = None


def normalize_file_id(file_id: str) -> str:
    """
    Return canonical 20-digit form of file_id.

    Args:
        file_id: File ID string (may be 19 or 20 digits)

    Returns:
        Canonical 20-digit file_id

    Raises:
        ValueError: If file_id cannot be normalized

    Examples:
        >>> normalize_file_id("1999000042260125067")
        "01999000042260125067"

        >>> normalize_file_id("01999000042260125067")
        "01999000042260125067"

        >>> normalize_file_id("invalid")
        ValueError: Cannot normalize file_id: invalid
    """
    # Type check
    if not isinstance(file_id, str):
        raise ValueError(f"file_id must be string, got {type(file_id).__name__}")

    # Digit check
    if not file_id.isdigit():
        raise ValueError(f"Cannot normalize file_id: {file_id} (contains non-digits)")

    # Length-based normalization
    if len(file_id) == 19:
        # Add leading zero
        return "0" + file_id
    elif len(file_id) == 20:
        # Already canonical (accept any 20-digit format)
        return file_id
    else:
        raise ValueError(
            f"Cannot normalize file_id: {file_id} (length={len(file_id)}, expected 19 or 20)"
        )


def validate_canonical_file_id(file_id: str) -> bool:
    """
    Check if file_id matches canonical format.

    Canonical format: ^[0-9]{20}$ (20 digits)
    Expected prefix: 01999...

    Args:
        file_id: File ID to validate

    Returns:
        True if canonical, False otherwise
    """
    if not isinstance(file_id, str):
        return False

    if len(file_id) != 20:
        return False

    if not file_id.isdigit():
        return False

    # Optionally check prefix (01999...)
    # For now, just ensure 20 digits
    return True


def detect_duplicates(records: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group records by canonical file_id.

    Args:
        records: List of registry records

    Returns:
        Dict mapping canonical_id -> list of records
        Only includes groups with 2+ records (actual duplicates)

    Example:
        >>> records = [
        ...     {"file_id": "1999000042260125067", "path": "a.py"},
        ...     {"file_id": "01999000042260125067", "path": "a.py"},
        ... ]
        >>> duplicates = detect_duplicates(records)
        >>> len(duplicates["01999000042260125067"])
        2
    """
    # Group by canonical form
    canonical_groups = defaultdict(list)

    for record in records:
        file_id = record.get("file_id")

        if not file_id:
            continue  # Skip records without file_id

        try:
            canonical = normalize_file_id(file_id)
            canonical_groups[canonical].append(record)
        except ValueError as e:
            print(f"Warning: Skipping invalid file_id: {e}")
            continue

    # Filter to only duplicates (2+ records)
    duplicates = {
        canonical: group
        for canonical, group in canonical_groups.items()
        if len(group) > 1
    }

    return duplicates


def _get_merge_priority(record: Dict[str, Any]) -> Tuple[int, int, str, int]:
    """
    Calculate merge priority for a record.

    Priority order (lower number = higher priority):
    1. Format correctness (20-digit > 19-digit)
    2. Path completeness (has relative_path + repo_root_id)
    3. Timestamp (newer > older)
    4. Content richness (more non-null fields)

    Returns:
        Tuple for sorting (lower = better)
    """
    file_id = record.get("file_id", "")

    # 1. Format correctness (0 = 20-digit, 1 = 19-digit)
    format_score = 0 if len(file_id) == 20 else 1

    # 2. Path completeness (0 = complete, 1 = incomplete)
    has_path = bool(record.get("relative_path"))
    has_repo = bool(record.get("repo_root_id"))
    completeness_score = 0 if (has_path and has_repo) else 1

    # 3. Timestamp (newer = better, use negative for sorting)
    # Parse ISO 8601 timestamps
    timestamp_str = (
        record.get("updated_utc")
        or record.get("first_seen_utc")
        or "1970-01-01T00:00:00Z"
    )
    try:
        # Simple ISO 8601 parsing (handles most cases)
        timestamp_str = (
            timestamp_str.split(".")[0].split("+")[0].split("-")[0:3]
        )  # Remove microseconds/tz
        timestamp_str = (
            "-".join(timestamp_str) if len(timestamp_str) == 3 else timestamp_str[0]
        )
    except:
        timestamp_str = "1970-01-01T00:00:00Z"

    # 4. Content richness (more non-null fields = better)
    non_null_count = sum(1 for v in record.values() if v is not None and v != "")
    richness_score = -non_null_count  # Negative so higher count = lower score

    return (format_score, completeness_score, timestamp_str, richness_score)


def merge_duplicates(
    duplicate_group: List[Dict[str, Any]], canonical_id: str
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Merge duplicate records deterministically.

    Selection priority:
    1. Format correctness (20-digit > 19-digit)
    2. Path completeness (has relative_path + repo_root_id)
    3. Timestamp (newer > older)
    4. Content richness (more non-null fields)

    Merge strategy:
    - Keep canonical record
    - Union-merge array fields (e.g., geu_ids)
    - Mark non-canonical records as superseded

    Args:
        duplicate_group: List of duplicate records
        canonical_id: The canonical file_id

    Returns:
        (canonical_record, superseded_records)

    Example:
        >>> group = [
        ...     {"file_id": "1999...", "geu_ids": ["GEU-2"]},
        ...     {"file_id": "01999...", "geu_ids": ["GEU-5"]},
        ... ]
        >>> canonical, superseded = merge_duplicates(group, "01999...")
        >>> canonical["geu_ids"]
        ["GEU-2", "GEU-5"]  # Union of both
    """
    if len(duplicate_group) < 2:
        raise ValueError("merge_duplicates requires at least 2 records")

    # Sort by priority (lowest priority value = best record)
    sorted_group = sorted(duplicate_group, key=_get_merge_priority)

    # Select canonical record (first in sorted order)
    canonical_record = sorted_group[0].copy()
    superseded_records = sorted_group[1:]

    # Ensure canonical record has canonical file_id
    canonical_record["file_id"] = canonical_id

    # Union-merge array fields from superseded records
    array_fields = [
        "geu_ids",
        "depends_on_file_ids",
        "enforced_by_file_ids",
        "enforces_rule_ids",
    ]

    for field in array_fields:
        # Collect all values from all records
        all_values = set()

        for record in duplicate_group:
            value = record.get(field)
            if value:
                if isinstance(value, list):
                    all_values.update(value)
                elif isinstance(value, str):
                    all_values.add(value)

        # Set union result in canonical record
        if all_values:
            canonical_record[field] = sorted(list(all_values))

    # Mark superseded records
    for record in superseded_records:
        record["superseded_by"] = canonical_id
        record["canonicality"] = "SUPERSEDED"

    return canonical_record, superseded_records


def analyze_normalization_needs(
    records: List[Dict[str, Any]]
) -> List[IDNormalizationResult]:
    """
    Analyze all records and determine normalization needs.

    Args:
        records: List of registry records

    Returns:
        List of normalization results (one per canonical ID)
    """
    results = []

    # Detect duplicates
    duplicates = detect_duplicates(records)

    # Process each canonical ID
    canonical_ids = set()
    for record in records:
        file_id = record.get("file_id")
        if not file_id:
            continue

        try:
            canonical = normalize_file_id(file_id)
            canonical_ids.add(canonical)
        except ValueError:
            continue

    for canonical_id in canonical_ids:
        # Get all records with this canonical ID
        matching_records = [
            r
            for r in records
            if r.get("file_id") and normalize_file_id(r["file_id"]) == canonical_id
        ]

        # Check if any need normalization (19-digit)
        original_ids = [r["file_id"] for r in matching_records]
        needs_norm = any(len(fid) == 19 for fid in original_ids)
        is_dup = len(matching_records) > 1

        result = IDNormalizationResult(
            canonical_id=canonical_id,
            original_ids=original_ids,
            is_duplicate=is_dup,
            needs_normalization=needs_norm,
        )

        # If duplicate, compute merge
        if is_dup:
            canonical_rec, superseded = merge_duplicates(matching_records, canonical_id)
            result.canonical_record = canonical_rec
            result.superseded_records = superseded

        results.append(result)

    return results


if __name__ == "__main__":
    # Test normalization
    test_ids = [
        "1999000042260125067",  # 19-digit
        "01999000042260125067",  # 20-digit
        "01999000042260124027",  # 20-digit
    ]

    print("Testing file_id normalization:")
    for test_id in test_ids:
        try:
            canonical = normalize_file_id(test_id)
            print(f"  {test_id} → {canonical}")
        except ValueError as e:
            print(f"  {test_id} → ERROR: {e}")

    # Test duplicate detection
    print("\nTesting duplicate detection:")
    test_records = [
        {"file_id": "1999000042260125067", "path": "a.py", "repo_root_id": "ALL_AI"},
        {"file_id": "01999000042260125067", "path": "a.py", "repo_root_id": "ALL_AI"},
        {"file_id": "01999000042260124027", "path": "b.py"},
    ]

    duplicates = detect_duplicates(test_records)
    print(f"  Found {len(duplicates)} duplicate groups")

    for canonical, group in duplicates.items():
        print(f"  Group {canonical}: {len(group)} records")
        merged, superseded = merge_duplicates(group, canonical)
        print(f"    → Canonical: {merged['file_id']}")
        print(f"    → Superseded: {[r['file_id'] for r in superseded]}")
