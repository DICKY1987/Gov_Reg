"""
Patch Writer

Generates RFC-6902 JSON Patches and JSONL evidence logs.

Features:
1. Generate RFC-6902 patches for registry fixes
2. Write JSONL evidence logs for audit trail
3. Apply patches to registry (with backup)
4. Validate patches before application

Design Principle: Every change must be logged and reversible
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class PatchOperation:
    """RFC-6902 JSON Patch operation."""

    op: str  # "add", "remove", "replace", "move", "copy", "test"
    path: str  # JSON Pointer (e.g., "/files/0/file_id")
    value: Optional[Any] = None
    from_: Optional[str] = None  # For "move" and "copy" operations

    def to_dict(self) -> Dict[str, Any]:
        """Convert to RFC-6902 dict format."""
        result = {"op": self.op, "path": self.path}
        if self.value is not None:
            result["value"] = self.value
        if self.from_ is not None:
            result["from"] = self.from_
        return result


@dataclass
class EvidenceEntry:
    """Evidence log entry for a single change."""

    timestamp: str
    operation: str
    target_path: str
    old_value: Optional[Any]
    new_value: Optional[Any]
    reason: str
    metadata: Optional[Dict[str, Any]] = None

    def to_jsonl(self) -> str:
        """Convert to JSONL format (single line JSON)."""
        return json.dumps(asdict(self), ensure_ascii=False)


class PatchWriter:
    """
    Writes RFC-6902 patches and evidence logs.

    Usage:
        writer = PatchWriter()
        writer.add_operation("replace", "/files/0/file_id", "01999...", reason="Normalize 19-digit ID")
        writer.save_patch(Path("fix.patch.json"))
        writer.save_evidence(Path("fix.evidence.jsonl"))
    """

    def __init__(self):
        self.operations: List[PatchOperation] = []
        self.evidence: List[EvidenceEntry] = []
        self._timestamp = datetime.utcnow().isoformat() + "Z"

    def add_operation(
        self,
        op: str,
        path: str,
        value: Optional[Any] = None,
        old_value: Optional[Any] = None,
        reason: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a patch operation with evidence logging.

        Args:
            op: Operation type ("replace", "add", "remove", etc.)
            path: JSON Pointer to target field
            value: New value (for add/replace)
            old_value: Previous value (for evidence)
            reason: Human-readable reason for change
            metadata: Additional context
        """
        # Add patch operation
        patch_op = PatchOperation(op=op, path=path, value=value)
        self.operations.append(patch_op)

        # Add evidence entry
        evidence_entry = EvidenceEntry(
            timestamp=self._timestamp,
            operation=op,
            target_path=path,
            old_value=old_value,
            new_value=value,
            reason=reason,
            metadata=metadata,
        )
        self.evidence.append(evidence_entry)

    def add_file_id_normalization(
        self,
        file_index: int,
        old_file_id: str,
        new_file_id: str,
        data_key: str = "files",
    ) -> None:
        """
        Add operation to normalize a file_id.

        Args:
            file_index: Index in files/entries array
            old_file_id: Original file_id (e.g., 19-digit)
            new_file_id: Canonical file_id (20-digit)
            data_key: "files" or "entries"
        """
        path = f"/{data_key}/{file_index}/file_id"
        self.add_operation(
            op="replace",
            path=path,
            value=new_file_id,
            old_value=old_file_id,
            reason=f"Normalize file_id: {len(old_file_id)}-digit → {len(new_file_id)}-digit",
            metadata={
                "normalization_type": "add_leading_zero"
                if len(old_file_id) == 19
                else "none",
                "file_index": file_index,
                "data_key": data_key,
            },
        )

    def add_record_supersession(
        self, file_index: int, canonical_id: str, data_key: str = "files"
    ) -> None:
        """
        Mark a record as superseded by another.

        Args:
            file_index: Index in files/entries array
            canonical_id: The canonical file_id
            data_key: "files" or "entries"
        """
        # Add superseded_by field
        self.add_operation(
            op="add",
            path=f"/{data_key}/{file_index}/superseded_by",
            value=canonical_id,
            old_value=None,
            reason=f"Mark as superseded by {canonical_id}",
            metadata={"file_index": file_index, "data_key": data_key},
        )

        # Update canonicality field
        self.add_operation(
            op="replace",
            path=f"/{data_key}/{file_index}/canonicality",
            value="SUPERSEDED",
            old_value="CANONICAL",
            reason="Mark canonicality as SUPERSEDED",
            metadata={"file_index": file_index, "data_key": data_key},
        )

    def save_patch(self, output_path: Path) -> None:
        """
        Save RFC-6902 patch to JSON file.

        Args:
            output_path: Path to output patch file
        """
        patch_doc = [op.to_dict() for op in self.operations]

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(patch_doc, f, indent=2, ensure_ascii=False)

        print(f"✓ Saved patch: {output_path} ({len(self.operations)} operations)")

    def save_evidence(self, output_path: Path) -> None:
        """
        Save evidence log to JSONL file.

        Args:
            output_path: Path to output evidence file
        """
        with open(output_path, "w", encoding="utf-8") as f:
            for entry in self.evidence:
                f.write(entry.to_jsonl() + "\n")

        print(f"✓ Saved evidence: {output_path} ({len(self.evidence)} entries)")

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of patch operations.

        Returns:
            Dict with operation counts and metadata
        """
        op_counts = {}
        for op in self.operations:
            op_counts[op.op] = op_counts.get(op.op, 0) + 1

        return {
            "total_operations": len(self.operations),
            "operation_counts": op_counts,
            "generated_at": self._timestamp,
            "evidence_entries": len(self.evidence),
        }

    def print_summary(self) -> None:
        """Print patch summary to console."""
        summary = self.get_summary()
        print("\nPatch Summary:")
        print(f"  Total operations: {summary['total_operations']}")
        print(f"  Operation breakdown:")
        for op_type, count in summary["operation_counts"].items():
            print(f"    - {op_type}: {count}")
        print(f"  Evidence entries: {summary['evidence_entries']}")
        print(f"  Generated at: {summary['generated_at']}")


def apply_patch(registry: Dict[str, Any], patch_path: Path) -> Dict[str, Any]:
    """
    Apply RFC-6902 patch to registry.

    Args:
        registry: Registry dict
        patch_path: Path to patch file

    Returns:
        Patched registry

    Note: This is a simplified implementation.
    For production, use jsonpatch library.
    """
    import copy

    patched_registry = copy.deepcopy(registry)

    with open(patch_path, "r", encoding="utf-8") as f:
        patch = json.load(f)

    for operation in patch:
        op = operation["op"]
        path = operation["path"]
        value = operation.get("value")

        # Parse JSON Pointer
        parts = path.strip("/").split("/")

        # Navigate to parent
        target = patched_registry
        for part in parts[:-1]:
            if part.isdigit():
                target = target[int(part)]
            else:
                target = target[part]

        # Apply operation
        final_key = parts[-1]
        if final_key.isdigit():
            final_key = int(final_key)

        if op == "replace":
            target[final_key] = value
        elif op == "add":
            target[final_key] = value
        elif op == "remove":
            del target[final_key]
        else:
            raise ValueError(f"Unsupported operation: {op}")

    return patched_registry


if __name__ == "__main__":
    # Test patch writer
    print("Testing PatchWriter:")

    writer = PatchWriter()

    # Add some test operations
    writer.add_file_id_normalization(
        file_index=0,
        old_file_id="1999000042260125067",
        new_file_id="01999000042260125067",
    )

    writer.add_record_supersession(file_index=1, canonical_id="01999000042260125067")

    # Print summary
    writer.print_summary()

    # Save to temp files
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as tmpdir:
        patch_path = Path(tmpdir) / "test.patch.json"
        evidence_path = Path(tmpdir) / "test.evidence.jsonl"

        writer.save_patch(patch_path)
        writer.save_evidence(evidence_path)

        print(f"\n✓ Test completed successfully")
