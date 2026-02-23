"""
GEU Reconciler

Normalizes GEU fields to canonical format.

Features:
1. Type normalization (string → array for geu_ids)
2. Label→ID mapping (GEU-2 → 99016012500600000002)
3. Primary GEU ID enforcement
4. Shared ownership validation
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class GEUReconciliationResult:
    """Result of GEU field reconciliation."""

    file_id: str
    changes_made: List[str]
    warnings: List[str]
    original_values: Dict[str, Any]
    new_values: Dict[str, Any]


class GEUReconciler:
    """
    Reconciles GEU fields to canonical format.

    Usage:
        label_map = {"GEU-1": "99011234567800000001", ...}
        reconciler = GEUReconciler(label_map)
        result = reconciler.reconcile_record(record)
    """

    def __init__(self, label_map: Dict[str, str]):
        """
        Initialize reconciler with GEU label map.

        Args:
            label_map: Dict mapping GEU labels to canonical IDs
                      e.g., {"GEU-1": "99011234567800000001"}
        """
        self.label_map = label_map

        # Validate label map
        for label, geu_id in label_map.items():
            if not re.match(r"^99\d{18}$", geu_id):
                raise ValueError(f"Invalid canonical GEU ID in label map: {geu_id}")

    @classmethod
    def load_label_map(cls, path: Path) -> "GEUReconciler":
        """Load GEU label map from JSON file."""
        if not path.exists():
            raise FileNotFoundError(f"GEU label map not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        mappings = data.get("mappings", {})
        return cls(mappings)

    def map_label_to_id(self, label: str) -> Optional[str]:
        """
        Map GEU label to canonical ID.

        Args:
            label: GEU label (e.g., "GEU-2")

        Returns:
            Canonical ID or None if not in map
        """
        return self.label_map.get(label)

    def normalize_geu_ids_type(self, value: Any) -> List[str]:
        """
        Normalize geu_ids value to array type.

        Args:
            value: Current value (string, array, or null)

        Returns:
            Array of GEU values (may still be labels)

        Examples:
            "GEU-2" → ["GEU-2"]
            ["GEU-2"] → ["GEU-2"]
            null → []
        """
        if value is None:
            return []
        elif isinstance(value, str):
            # Convert string to array
            return [value]
        elif isinstance(value, list):
            # Already array
            return value
        else:
            raise ValueError(f"Cannot normalize geu_ids type: {type(value).__name__}")

    def map_geu_values(self, values: List[str]) -> List[str]:
        """
        Map GEU values (labels or IDs) to canonical IDs.

        Args:
            values: List of GEU values (may be labels or IDs)

        Returns:
            List of canonical GEU IDs

        Raises:
            ValueError: If a label is not in label map
        """
        mapped = []

        for value in values:
            if value.startswith("GEU-"):
                # It's a label - map to ID
                canonical = self.map_label_to_id(value)
                if not canonical:
                    raise ValueError(f"GEU label not in map: {value}")
                mapped.append(canonical)
            elif re.match(r"^99\d{18}$", value):
                # Already canonical ID
                mapped.append(value)
            else:
                raise ValueError(f"Invalid GEU value: {value}")

        return mapped

    def reconcile_record(self, record: Dict[str, Any]) -> GEUReconciliationResult:
        """
        Reconcile all GEU fields in a record.

        Args:
            record: Registry record

        Returns:
            GEUReconciliationResult with changes
        """
        file_id = record.get("file_id", "unknown")
        changes = []
        warnings = []
        original_values = {}
        new_values = {}

        # ========================================
        # 1. Normalize geu_ids type (string → array)
        # ========================================
        geu_ids = record.get("geu_ids")
        if geu_ids is not None:
            original_values["geu_ids"] = geu_ids

            try:
                normalized_array = self.normalize_geu_ids_type(geu_ids)

                if isinstance(geu_ids, str):
                    changes.append(f"geu_ids: type string → array")
                    record["geu_ids"] = normalized_array
                    new_values["geu_ids"] = normalized_array

                # Map labels to IDs
                if normalized_array:
                    try:
                        mapped_ids = self.map_geu_values(normalized_array)
                        if mapped_ids != normalized_array:
                            changes.append(f"geu_ids: mapped labels → canonical IDs")
                            record["geu_ids"] = mapped_ids
                            new_values["geu_ids"] = mapped_ids
                    except ValueError as e:
                        warnings.append(f"geu_ids mapping failed: {e}")
            except ValueError as e:
                warnings.append(f"geu_ids normalization failed: {e}")

        # ========================================
        # 2. Normalize primary_geu_id
        # ========================================
        primary_geu_id = record.get("primary_geu_id")
        if primary_geu_id:
            original_values["primary_geu_id"] = primary_geu_id

            if isinstance(primary_geu_id, str) and primary_geu_id.startswith("GEU-"):
                # Map label to ID
                try:
                    canonical = self.map_label_to_id(primary_geu_id)
                    if canonical:
                        record["primary_geu_id"] = canonical
                        new_values["primary_geu_id"] = canonical
                        changes.append(f"primary_geu_id: mapped label → canonical ID")
                    else:
                        warnings.append(
                            f"primary_geu_id label not in map: {primary_geu_id}"
                        )
                except ValueError as e:
                    warnings.append(f"primary_geu_id mapping failed: {e}")

        # ========================================
        # 3. Enforce: geu_ids → primary_geu_id must exist
        # ========================================
        final_geu_ids = record.get("geu_ids")
        final_primary = record.get("primary_geu_id")

        if final_geu_ids and not final_primary:
            # Auto-assign primary_geu_id from first geu_id
            if isinstance(final_geu_ids, list) and len(final_geu_ids) > 0:
                record["primary_geu_id"] = final_geu_ids[0]
                new_values["primary_geu_id"] = final_geu_ids[0]
                changes.append(f"primary_geu_id: auto-assigned from geu_ids[0]")
                warnings.append(f"Auto-assigned primary_geu_id (was missing)")

        # ========================================
        # 4. Normalize owner_geu_id
        # ========================================
        owner_geu_id = record.get("owner_geu_id")
        if owner_geu_id:
            original_values["owner_geu_id"] = owner_geu_id

            if isinstance(owner_geu_id, str) and owner_geu_id.startswith("GEU-"):
                # Map label to ID
                try:
                    canonical = self.map_label_to_id(owner_geu_id)
                    if canonical:
                        record["owner_geu_id"] = canonical
                        new_values["owner_geu_id"] = canonical
                        changes.append(f"owner_geu_id: mapped label → canonical ID")
                    else:
                        warnings.append(
                            f"owner_geu_id label not in map: {owner_geu_id}"
                        )
                except ValueError as e:
                    warnings.append(f"owner_geu_id mapping failed: {e}")

        # ========================================
        # 5. Validate: is_shared → owner_geu_id should exist
        # ========================================
        is_shared = record.get("is_shared")
        if is_shared and not record.get("owner_geu_id"):
            warnings.append("is_shared=true but owner_geu_id is missing")

        return GEUReconciliationResult(
            file_id=file_id,
            changes_made=changes,
            warnings=warnings,
            original_values=original_values,
            new_values=new_values,
        )


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python geu_reconciler.py <geu_label_map_path>")
        sys.exit(1)

    label_map_path = Path(sys.argv[1])

    print(f"Loading GEU label map: {label_map_path}")
    reconciler = GEUReconciler.load_label_map(label_map_path)

    print(f"✓ Loaded {len(reconciler.label_map)} GEU mappings")

    # Test reconciliation
    print("\nTesting GEU reconciliation:")

    test_records = [
        {
            "file_id": "01999000042260124001",
            "geu_ids": "GEU-2",  # String (wrong type)
            "primary_geu_id": "GEU-2",  # Label (wrong format)
        },
        {
            "file_id": "01999000042260124002",
            "geu_ids": ["GEU-1", "GEU-5"],  # Array of labels
            "primary_geu_id": None,  # Missing (should be auto-assigned)
        },
        {
            "file_id": "01999000042260124003",
            "geu_ids": ["99016012500600000002"],  # Already canonical
            "primary_geu_id": "99016012500600000002",  # Already canonical
        },
    ]

    for i, record in enumerate(test_records, 1):
        print(f"\n  Test {i}:")
        print(
            f"    Before: geu_ids={record.get('geu_ids')}, primary={record.get('primary_geu_id')}"
        )

        result = reconciler.reconcile_record(record)

        print(
            f"    After:  geu_ids={record.get('geu_ids')}, primary={record.get('primary_geu_id')}"
        )
        print(f"    Changes: {len(result.changes_made)}")
        for change in result.changes_made:
            print(f"      - {change}")
        if result.warnings:
            print(f"    Warnings: {len(result.warnings)}")
            for warning in result.warnings:
                print(f"      ! {warning}")
